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


# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Logger configuration impropers file
logging.basicConfig(level=logging.INFO)
improper_logger = logging.getLogger(__name__)


def run_replicate_cmd(structure_file, xml_file,
                      image_x, image_y, image_z,
                      mdengine, noh, index,
                      boxlength_a, boxlength_b, boxlength_c,
                      boxangle_alpha, boxangle_beta, boxangle_gamma,
                      impropers, npairs, verbose, pattern):
    bash_command = f"replicate_polymer -p {structure_file} -f {xml_file} --images {image_x} {image_y} {image_z}"

    if mdengine:
        bash_command += f" -e {mdengine}"
    if noh:
        bash_command += f" --noh"
    if index:
        bash_command += f" --index {index}"
    if boxlength_a and boxlength_b and boxlength_c:
        bash_command += f" --boxlength {boxlength_a} {boxlength_b} {boxlength_c}"
    if boxangle_alpha and boxangle_beta and boxangle_gamma:
        bash_command += f" --boxangle {boxangle_alpha} {boxangle_beta} {boxangle_gamma}"
    if impropers:
        bash_command += f" --impropers {impropers}"
    if npairs:
        bash_command += f" --npairs {npairs}"
    if verbose:
        bash_command += f" --verbose"
    if pattern:
        bash_command += f" -pat {pattern}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    return output, error


def run_bash(script_content):
    bash_command = f"bash {script_content}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_impropers, error_impropers = process.communicate()

    return output_impropers, error_impropers


def save_uploaded_file(uploaded_file, temp_dir):
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path


def show_output_files_content(output_file_paths):

    # Check if 'Info.log' is present in the output file list
    info_replicate_log_path = next((path for path in output_file_paths if "Info.log" in path), None)

    if info_replicate_log_path:
        st.write(f"### {os.path.basename(info_replicate_log_path)}")
        with open(info_replicate_log_path, "r") as output_file:
            file_content = output_file.read()
            st.text_area("File content:", value=file_content, height=300)
    else:
        st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                    'padding: 10px; border-radius: 10px;'
                    '">Warning: Info.log not found in the output files.</p>',
                    unsafe_allow_html=True)


def show_output_impropers_file_content(impropers_output_file_paths):

    # Check if 'impropers.ndx' is present in the output file
    impropers_ndx_path = next((path for path in impropers_output_file_paths if "impropers.ndx" in path), None)

    if impropers_ndx_path:
        st.write(f"### {os.path.basename(impropers_ndx_path)}")
        with open(impropers_ndx_path, "r") as output_impropers_file:
            impropers_file_content = output_impropers_file.read()
            st.text_area("File content:", value=impropers_file_content, height=300)
    else:
        st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                    'padding: 10px; border-radius: 10px;'
                    '">Warning: impropers.ndx not found in the output file.</p>',
                    unsafe_allow_html=True)


def create_tar_gz(output_folder, output_file_paths):
    # Create a temporary file to store the .tar.gz
    temp_tar_path = os.path.join(output_folder, "output_files.tar.gz")

    # Create the .tar.gz file
    with tarfile.open(temp_tar_path, "w:gz") as tar:
        for file_path in output_file_paths:
            # Check if the file exists before adding it to the archive
            if os.path.exists(file_path):
                tar.add(file_path, arcname=os.path.basename(file_path))
            else:
                print(f"File not found: {file_path}")

    return temp_tar_path


# ToDo: How to visualize molecules: VMD or JSMol?


def func_page_replicate():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    impropers_unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Replicate Polymer</h1>", unsafe_allow_html=True)

    # Displaying the welcome text
    st.text("""
    ***********************************************************************
              Replicate a molecule or polymer chain (ReMoPo)
              ----------------------------------------------

                                Version 3.0

                              Dr. Javier Ramos
                      Macromolecular Physics Department
                Instituto de Estructura de la Materia (IEM-CSIC)
                               Madrid (Spain)

        ReMoPo is an open-source python library to quickly replicate a molecule
        from a pdb file containing the seed molecule. After that, the script assigns
        the force field parameters using the foyer library (https://mosdef.org/)
        This program generates GROMACS and LAMMPS files to run simulations.

        This software is distributed under the terms of the
        GNU General Public License v3.0 (GNU GPLv3). A copy of
        the license (LICENSE.txt) is included with this distribution.

    ***********************************************************************    
    """)

    # Displaying the help expandable box
    with st.expander("OPTIONS"):

        # Displaying mandatory program options in the interface
        st.subheader("Essentials")

        structure_file = st.file_uploader("Select a pdb file containing the structure to be replicated", type=["pdb"])

        # Displaying the content of the structure file right after loading it
        if structure_file is not None:
            edit_content_key = "edit_content_structure_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(structure_file, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_structure_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_structure_file")
                        save_filename = st.text_input("Enter the name of the edited file:",
                                                      key="Enter_name_structure_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_structure_file"
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

        xml_file = st.file_uploader("Select a forcefield", type=["xml"])

        # Displaying the content of the FORCEFIELD file right after loading it
        if xml_file is not None:
            edit_content_key = "edit_content_FORCEFIELD_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(xml_file, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_FORCEFIELD_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_FORCEFIELD_file")
                        save_filename = st.text_input("Enter the name of the edited file:",
                                                      key="Enter_name_FORCEFIELD_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_FORCEFIELD_file"
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

        # Mandatory entry for --images image_x image_y image_z
        image_x = st.number_input("Number of Images to Replicate in Dimension X", min_value=1, step=1, value=1)
        image_y = st.number_input("Number of Images to Replicate in Dimension Y", min_value=1, step=1, value=1)
        image_z = st.number_input("Number of Images to Replicate in Dimension Z", min_value=1, step=1, value=1)

        # ===========================================

        # Non-mandatory options (conditionally present)
        st.subheader("Optional")

        impropers = st.file_uploader("Select impropers file", type=["ndx"])

        # Displaying the content of the IMPROPERS file right after loading it
        if impropers is not None:
            edit_content_key = "edit_content_IMPROPERS_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(impropers, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_IMPROPERS_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_IMPROPERS_file")
                        save_filename = st.text_input("Enter the name of the edited file:",
                                                      key="Enter_name_IMPROPERS_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_IMPROPERS_file"
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

        else:
            without_impropers = st.radio("Do you need an impropers file?", ["Yes", "No"])
            need_impropers = (without_impropers == "Yes")

            if need_impropers:
                script_content = st.file_uploader("Select a script to generate an impropers file", type=["sh"])
                if script_content is not None:
                    edit_content_key = "edit_content_script_file"
                    edit_content = st.checkbox("Edit content", key=edit_content_key)

                    # Getting the original file name
                    if edit_content:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            file_path = save_uploaded_file(script_content, temp_dir)
                            edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                          height=300)

                            # State variable to control the visibility of the boxes
                            show_save_options = st.checkbox("Show save options", key="show_save_options_script_file")

                            if show_save_options:
                                # Asking the user for the path and file name to save
                                save_path = st.text_input("Enter the path to save the edited file:",
                                                          key="Enter_path_script_file")
                                save_filename = st.text_input("Enter the name of the edited file:",
                                                              key="Enter_name_script_file")

                                # Checking if both the path and the file name are specified
                                if save_path and save_filename:
                                    # Here you can save 'edited_content' with the specified path and name
                                    save_content_key = "save_content_script_file"
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

                if script_content:

                    compressed_impropers_name = st.text_input("Enter the name for the output compressed impropers file")

                    # Button to execute the script
                    if st.button("Run Script and Generate IMPROPERS File"):
                        if not script_content:
                            st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                        'padding: 10px; border-radius: 10px;'
                                        '">Warning: Please upload a script to generate an impropers file.</p>',
                                        unsafe_allow_html=True)
                            return

                        if not compressed_impropers_name:
                            st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                        'padding: 10px; border-radius: 10px;'
                                        '">Warning: Please enter the name for the output compressed impropers file.</p>',
                                        unsafe_allow_html=True)
                            return


                        if script_content is not None:
                            with st.spinner("Running script. Please wait..."):
                                with tempfile.TemporaryDirectory() as improper_temp_dir:
                                    # Use the unique identifier to create a unique folder
                                    impropers_output_folder = os.path.join(improper_temp_dir, "impropers.ndx")
                                    os.makedirs(impropers_output_folder)

                                    script_content_path = save_uploaded_file(script_content, improper_temp_dir)

                                    output_impropers, error_impropers = run_bash(script_content_path)

                                    now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                                    m = f"\n\t\tOutput from Running script.({now})"
                                    m += f"\n\t\t{'*' * len(m)}\n"
                                    m += output_impropers.decode()
                                    m += error_impropers.decode()
                                    print(m) if improper_logger is None else improper_logger.info(m)

                                    st.success("Success run")
                                    st.success("Output impropers file generated")

                                    #   Output list of common files
                                    output_impropers_files = ["impropers.ndx"]

                                    # Move generated files to single folder
                                    for filename_improper in os.listdir(improper_temp_dir):
                                        filepath_improper = os.path.join(improper_temp_dir, filename_improper)
                                        if os.path.isfile(filepath_improper):
                                            shutil.move(filepath_improper, os.path.join(impropers_output_folder, filename_improper))

                                    if compressed_impropers_name:
                                        tar_file_path_impropers = create_tar_gz(impropers_output_folder, output_impropers_files)

                                        # Generate download link for output files
                                        download_link = (f'<a href="data:application/tar+gzip;base64,'
                                                         f'{base64.b64encode(open(tar_file_path_impropers, "rb").read()).decode()}'
                                                         f'" download="{compressed_impropers_name}_file.tar.gz">'
                                                         f'Download {compressed_impropers_name} output file</a>')
                                        st.markdown(download_link, unsafe_allow_html=True)

                                        # Show output file name
                                        show_output_impropers_file_content(output_impropers_files)

                                        if st.button("RESET"):
                                            st.experimental_rerun()


        # ===========================================

        index = st.text_input("Indices of Atoms to be Removed from the PDB")

        # ===========================================

        boxlength_a = st.number_input("Box Length (a) in Nanometers", min_value=0.0, step=0.1, value=None)
        boxlength_b = st.number_input("Box Length (b) in Nanometers", min_value=0.0, step=0.1, value=None)
        boxlength_c = st.number_input("Box Length (c) in Nanometers", min_value=0.0, step=0.1, value=None)

        # ===========================================

        boxangle_alpha = st.number_input("Box Angle (alpha) in Degrees", min_value=0.0, step=0.1, value=None)
        boxangle_beta = st.number_input("Box Angle (beta) in Degrees", min_value=0.0, step=0.1, value=None)
        boxangle_gamma = st.number_input("Box Angle (gamma) in Degrees", min_value=0.0, step=0.1, value=None)

        # ===========================================

        npairs = st.number_input("Monomer or Residue Inclusions (e.g., 1)", step=1.0, value=None)

        # ===========================================

        mdengine = st.text_input("MD Package to Perform Calculations")

        # ===========================================

        noh = st.checkbox("Remove Hydrogens for a United Atom Representation")

        # ===========================================

        verbose = st.checkbox("Verbose Checking of Angles and Dihedral")

        default_pattern = "replicate"
        pattern = st.text_input("String pattern to name the new files", default_pattern)

        # ===========================================

        compressed_file_name = st.text_input("Enter the name for the output compressed file")

        # ===========================================

        # Button to execute the program with the select options
        if st.button("RUN"):
            if not structure_file:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please upload a pdb file before running the program.</p>',
                            unsafe_allow_html=True)
                return

            if not xml_file:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please upload a FORCEFIELD file before running the program.</p>',
                            unsafe_allow_html=True)
                return

            if not image_x:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please enter the number of images to Replicate in Dimension X.</p>',
                            unsafe_allow_html=True)
                return

            if not image_y:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please enter the number of images to Replicate in Dimension Y.</p>',
                            unsafe_allow_html=True)
                return

            if not image_z:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please enter the number of images to Replicate in Dimension Z.</p>',
                            unsafe_allow_html=True)
                return

            if not (isinstance(image_x, int) and image_x >= 1 and image_x % 1 == 0 and
                    isinstance(image_y, int) and image_y >= 1 and image_y % 1 == 0 and
                    isinstance(image_z, int) and image_z >= 1 and image_z % 1 == 0):
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please enter valid integer values greater than or equal '
                            'to 1 for Number of Images before running the program.</p>',
                            unsafe_allow_html=True)
                return

            if not compressed_file_name:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please enter the name for the output compressed file.</p>',
                            unsafe_allow_html=True)
                return

            if structure_file and xml_file and image_x and image_y and image_z is not None:
                with st.spinner("Running Replicate Polymer. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Topology is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique folder
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        structure_file_path = save_uploaded_file(structure_file, temp_dir)
                        xml_file_path = save_uploaded_file(xml_file, temp_dir)
                        impropers_path = save_uploaded_file(impropers, temp_dir) if impropers else None

                        output, error = run_replicate_cmd(
                            structure_file_path, xml_file_path, impropers_path,
                            image_x, image_y, image_z,
                            mdengine, index,
                            boxlength_a, boxlength_b, boxlength_c,
                            boxangle_alpha, boxangle_beta, boxangle_gamma,
                            npairs, noh, verbose, pattern
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Replicate Polymer.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Replicate Polymer Program executed successfully!")
                        st.success("Output files generated")
                        warning_container.empty()

                        #  ====    HERE OK ====    #

                        #   Output list of common files #####

                        output_files = [
                            "allatom_idx_replicate.dat",
                            "backbone_idx_replicate.dat",
                            "listendtoend_replicate.dat",
                            "Info.log"
                        ]

                        # If '--noh' is inserted, include these aditional files
                        if noh:
                            if not mdengine:
                                output_files.extend([
                                f"{structure_file}_noH.gro",
                                f"{structure_file}_noH.pdb",
                                f"{structure_file}_noH.top",
                                f"{structure_file}_noH_replicate.gro",
                                f"{structure_file}_noH_replicate.pdb",
                                f"{structure_file}_noH_replicate.top",
                                ])
                            else:
                                output_files.extend([
                                    f"{structure_file}_noH_replicate_clean.inp",
                                    f"{structure_file}_noH_replicate_clean.lmp",
                                    f"{structure_file}_noH.gro",
                                    f"{structure_file}_noH.pdb",
                                    f"{structure_file}_noH.top",
                                    f"{structure_file}_noH_replicate.gro",
                                    f"{structure_file}_noH_replicate.pdb",
                                    f"{structure_file}_noH_replicate.top",
                                ])

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


def run_page_replicate():

    func_page_replicate()
