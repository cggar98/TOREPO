import glob
import streamlit as st
import os
import subprocess
import datetime
import logging
import shutil
import tarfile
import time
import tempfile
import base64
import paramiko

# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_ssh_command(server, username, key_file, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=username, key_filename=key_file)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return output, error
    except Exception as e:
        return None, str(e)


def run_topology_cmd(input_file, renumber_pdb, assign_residues,
                     filemap, separate_chains, pattern, isunwrap, guess_improper):


    command = f"topology_cmd -i {input_file}"

    if renumber_pdb:
        command += f" -r {renumber_pdb}"
    if assign_residues:
        command += f" -a {assign_residues}"
    if filemap:
        command += f" --filemap {filemap}"
    if separate_chains:
        command += " --separate_chains"
    if pattern:
        command += f" -p {pattern}"
    if isunwrap:
        command += " -w"
    if guess_improper:
        command += " --guess_improper"


    process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = run_ssh_command(name_server, name_user, key_file, command)
    return output, error


    # st.success("All required programs are installed.")

    if output:
        st.success("Command executed successfully:")
        st.code(output)
        st.sidebar.success(f"Connected to the server: {get_host_name(name_server, name_user, key_file)}")
    elif error:
        st.error("Error executing command:")
        st.code(error)
        st.sidebar.error("Could not connect to the server")
    else:
        st.error("Error executing command: No output or error.")
        st.sidebar.error("Could not connect to the server")


def save_uploaded_file(uploaded_file, temp_dir):
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path


def show_output_files_content(output_file_paths):

    # Check if 'InfoTopology.log' is present in the output file list
    info_topology_log_path = next((path for path in output_file_paths if "InfoTopology.log" in path), None)

    if info_topology_log_path:
        st.write(f"### {os.path.basename(info_topology_log_path)}")
        with open(info_topology_log_path, "r") as output_file:
            file_content = output_file.read()
            st.text_area("File content:", value=file_content, height=300)
    else:
        st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                    'padding: 10px; border-radius: 10px;'
                    '">Warning: InfoTopology.log not found in the output files.</p>',
                    unsafe_allow_html=True)


def create_tar_gz(output_folder, output_file_paths):
    # Create a temporary file to store the .tar.gz
    temp_tar_path = os.path.join(output_folder, "output_files.tar.gz")

    # Create the .tar.gz file
    with tarfile.open(temp_tar_path, "w:gz") as tar:
        for file_path in output_file_paths:
            tar.add(file_path, arcname=os.path.basename(file_path))

    return temp_tar_path


# ToDo: How to visualize molecules: VMD or JSMol?


def func_page_topology():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Topology</h1>", unsafe_allow_html=True)

    # Displaying the welcome text
    st.text("""
    ***********************************************************************
                     Manipulate topology for polymers
              ----------------------------------------------

                                Version None

                              Dr. Javier Ramos
                      Macromolecular Physics Department
                Instituto de Estructura de la Materia (IEM-CSIC)
                               Madrid (Spain)

        Topology is an open-source python library to quickly modify topology 
        of polymer molecules

        This software is distributed under the terms of the
        GNU General Public License v3.0 (GNU GPLv3). A copy of
        the license (LICENSE.txt) is included with this distribution.

    ***********************************************************************
    """)

    # Displaying the help expandable box
    with st.expander("OPTIONS"):

        # Displaying mandatory program options in the interface
        st.subheader("Essentials")

        input_file = st.file_uploader("Select input file (XSD, PDB, or MOL2)", type=["xsd", "pdb", "mol2"],
                                      key="input_file")

        # Displaying the content of the input_file right after loading it
        if input_file is not None:
            edit_content_key = "edit_content_input_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(input_file, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_input_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_input_file")
                        save_filename = st.text_input("Enter the name of the edited file:", key="Enter_name_input_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_input_file"
                            if st.button("Save content", key=save_content_key):
                                save_filepath = os.path.join(save_path, save_filename)
                                with open(save_filepath, "w") as f:
                                    f.write(edited_content)
                                st.success(f"Content saved successfully as {save_filename}")

                        else:
                            st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                        'padding: 10px; border-radius: 10px;'
                                        '">Warning: Please enter path and/or name of the edited file.</p>',
                                        unsafe_allow_html=True)

        # Non-mandatory options (conditionally present)
        st.subheader("Optional")

    # ===========================================

        renumber_pdb = st.file_uploader("Select HEAD TAIL file for renumbering pdb", type=["dat"])

        # Displaying the content of the HEAD TAIL file right after loading it
        if renumber_pdb is not None:
            edit_content_key = "edit_content_HEADTAIL_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(renumber_pdb, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_HEADTAIL_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_HEADTAIL_file")
                        save_filename = st.text_input("Enter the name of the edited file:",
                                                      key="Enter_name_HEADTAIL_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_HEADTAIL_file"
                            if st.button("Save content", key=save_content_key):
                                save_filepath = os.path.join(save_path, save_filename)
                                with open(save_filepath, "w") as f:
                                    f.write(edited_content)
                                st.success(f"Content saved successfully as {save_filename}")
                        else:
                            st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                        'padding: 10px; border-radius: 10px;'
                                        '">Warning: Please enter path and/or name of the edited file.</p>',
                                        unsafe_allow_html=True)

        # ===========================================

        assign_residues = st.file_uploader("Select SETUP RESIDUE file for assigning residues", type=["dat"])

        # Displaying the content of the RESIDUES file right after loading it
        if assign_residues is not None:
            edit_content_key = "edit_content_RESIDUES_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(assign_residues, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_RESIDUES_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_RESIDUES_file")
                        save_filename = st.text_input("Enter the name of the edited file:",
                                                      key="Enter_name_RESIDUES_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_RESIDUES_file"
                            if st.button("Save content", key=save_content_key):
                                save_filepath = os.path.join(save_path, save_filename)
                                with open(save_filepath, "w") as f:
                                    f.write(edited_content)
                                st.success(f"Content saved successfully as {save_filename}")
                        else:
                            st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                        'padding: 10px; border-radius: 10px;'
                                        '">Warning: Please enter path and/or name of the edited file.</p>',
                                        unsafe_allow_html=True)

        # ===========================================

        filemap = st.file_uploader("Select FILEMAP for matching LAMMPS type with name and element", type=["dat"])

        # Displaying the content of the FILEMAP file right after loading it
        if filemap is not None:
            edit_content_key = "edit_content_FILEMAP_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(filemap, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_FILEMAP_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_FILEMAP_file")
                        save_filename = st.text_input("Enter the name of the edited file:",
                                                      key="Enter_name_FILEMAP_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_FILEMAP_file"
                            if st.button("Save content", key=save_content_key):
                                save_filepath = os.path.join(save_path, save_filename)
                                with open(save_filepath, "w") as f:
                                    f.write(edited_content)
                                st.success(f"Content saved successfully as {save_filename}")
                        else:
                            st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                        'padding: 10px; border-radius: 10px;'
                                        '">Warning: Please enter path and/or name of the edited file.</p>',
                                        unsafe_allow_html=True)

        # ===========================================

        pattern = st.text_input("String pattern to name the new files")
        if pattern.strip() == "":
            pattern = "topology"

        separate_chains = st.checkbox("Create a pdb file for each chain")
        isunwrap = st.checkbox("Unwrap coordinates in the final structure")
        guess_improper = st.checkbox("Guess improper angles in the system")
        compressed_file_name = st.text_input("Enter the name for the output compressed file")

        # Button to execute the program with the select options
        if st.button("RUN"):
            if not input_file:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please upload an input file before running the program.</p>',
                            unsafe_allow_html=True)
                return

            if not pattern:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please string pattern to name the new files.</p>',
                            unsafe_allow_html=True)
                return

            if not compressed_file_name:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please enter the name for the output compressed file.</p>',
                            unsafe_allow_html=True)
                return

            if input_file is not None:
                with st.spinner("Running Topology. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Topology is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique folder
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        input_file_path = save_uploaded_file(input_file, temp_dir)
                        renumber_pdb_path = save_uploaded_file(renumber_pdb, temp_dir) if renumber_pdb else None
                        assign_residues_path = save_uploaded_file(assign_residues,
                                                                  temp_dir) if assign_residues else None
                        filemap_path = save_uploaded_file(filemap, temp_dir) if filemap else None

                        output, error = run_topology_cmd(
                            input_file_path,
                            renumber_pdb_path,
                            assign_residues_path,
                            filemap_path,
                            separate_chains, pattern, isunwrap, guess_improper
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Topology.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Topology Program executed successfully!")
                        st.success("Output files generated")
                        warning_container.empty()

                        #   Output list of common files
                        output_files = [
                            f"{pattern}.pdb",
                            "InfoTopology.log"
                        ]

                        # If RESIDUES file is loaded, include these aditional files
                        if assign_residues_path:
                            output_files.extend([
                                f"{pattern}_residues.gro",
                                f"{pattern}_residues.pdb",
                                f"{pattern}_residues.psf",
                            ])

                        # If RESIDUES file is not loaded, but HEADTAIL is loaded, include these aditional files

                        if not assign_residues_path:
                            if renumber_pdb_path:
                                output_files.extend([
                                    f"{pattern}_renumber.gro",
                                    f"{pattern}_renumber.pdb",
                                    f"{pattern}_renumber.psf",
                                ])

                        #   =====================

                        # If 'separate_chains' option is selected, add files for each chain (NO OPTIMO)
                        if separate_chains:
                            pattmp = r"{}_[0-9][0-9][0-9][0-9].pdb".format(pattern)
                            separate_chains_files = glob.glob(pattmp)
                            for item in separate_chains_files:
                                print(item)
                                output_files.extend([item])

                        #   =====================

                        # Move generated files to single folder
                        for filename in os.listdir(temp_dir):
                            filepath = os.path.join(temp_dir, filename)
                            if os.path.isfile(filepath):
                                shutil.move(filepath, os.path.join(output_folder, filename))

                        if compressed_file_name:

                            tar_file_path = create_tar_gz(output_folder, output_files)

                            # Generate download link for output files
                            download_link = (f'<a href="data:application/tar+gzip;base64,'
                                                f'{base64.b64encode(open(tar_file_path, "rb").read()).decode()}'
                                                f'" download="{compressed_file_name}_files.tar.gz">'
                                                f'Download {compressed_file_name} output files</a>')
                            st.markdown(download_link, unsafe_allow_html=True)

                            # Show output file names
                            show_output_files_content(output_files)

                            if st.button("RESET"):
                                st.experimental_rerun()


def run_page_topology():

    func_page_topology()