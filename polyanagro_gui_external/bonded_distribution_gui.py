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

def run_bonded_distribution_generate(traj_files, listbb_file, topo_file, log_filename):

    bash_command = f"bonded_distribution generate -t {traj_files} --listbb {listbb_file}"

    if topo_file:
        bash_command += f" --topo {topo_file}"
    if log_filename:
        bash_command += f" --log {log_filename}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    return output, error


def run_bonded_distribution_calculate(traj_files, topo_file, bond_list_file,
                                      angle_list_file, dihedral_list_file,
                                      improper_list_file, stride, log_filename,
                                      unwrap_coordinates):

    bash_command = f"bonded_distribution calculate -t {traj_files} --topo {topo_file}"

    if unwrap_coordinates:
        bash_command += " --unwrap True"
    else:
        bash_command += " --unwrap False"

    if bond_list_file:
        bash_command += f" -b {bond_list_file}"

    if angle_list_file:
        bash_command += f" -a {angle_list_file}"

    if dihedral_list_file:
        bash_command += f" -d {dihedral_list_file}"

    if improper_list_file:
        bash_command += f" -i {improper_list_file}"

    if stride:
        bash_command += f" --stride {stride}"

    if log_filename:
        bash_command += f" --log {log_filename}"


    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    return output, error



def save_uploaded_file(uploaded_file, temp_dir):
    file_path = os.path.join(temp_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.read())
    return file_path


def show_output_files_content(output_file_paths, log_filename):
    # Check if the log file is present in the list of output files
    log_file_path = next((path for path in output_file_paths if log_filename in path), None)

    if log_file_path:
        st.write(f"### {os.path.basename(log_file_path)}")
        with open(log_file_path, "r") as output_file:
            file_content = output_file.read()
            st.text_area("File content:", value=file_content, height=300)
    else:
        st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                    'padding: 10px; border-radius: 10px;'
                    f'">Warning: {log_filename} not found in the output files.</p>',
                    unsafe_allow_html=True)


def create_tar_gz(output_folder, output_file_paths):
    # Create a temporary file to store the .tar.gz
    temp_tar_path = os.path.join(output_folder, "output_files.tar.gz")

    # Create the .tar.gz file
    with tarfile.open(temp_tar_path, "w:gz") as tar:
        for file_path in output_file_paths:
            tar.add(file_path, arcname=os.path.basename(file_path))

    return temp_tar_path


def func_page_bonded_distribution():


    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Bonded Distribution</h1>", unsafe_allow_html=True)

    #	Displaying the welcome text
    st.text("""
    ***********************************************************************
            Bonded Distributions (bond, angle, dihedral, improper)
        -------------------------------------------------------------

                                Version {}

                              Dr. Javier Ramos
                      Macromolecular Physics Department
                Instituto de Estructura de la Materia (IEM-CSIC)
                               Madrid (Spain)

        This utility is part of the polyanagro library. Polyanagro is an
        open-source python library to analyze simulations of polymer systems.

        This software is distributed under the terms of the
        GNU General Public License v3.0 (GNU GPLv3). A copy of
        the license (LICENSE.txt) is included with this distribution.

    ***********************************************************************
        """)


    options = st.radio("For this subprogram, you must choose one of these two options", ["Generate", "Calculate"])
    generate_option = (options == "Generate")
    calculate_option = (options == "Calculate")

    if generate_option:

        # Displaying the help expandable box
        with st.expander("OPTIONS"):

            # Displaying mandatory subprogram options in the interface
            st.subheader("Essentials")

            traj_files = st.file_uploader("Select a list of trajectories from MD simulations (XTC or TRR)",
                                          type=["xtc", "trr"],
                                          key="traj_files")

            #   =====================================

            listbb_file = st.file_uploader("Upload file for assign backbone atoms of a polymer", type=["txt", "pdb", "dat"],help="This option can be:"
                                                                                                                       "a) a pdb file template (using the beta field 1 for backbone and 0 for a branch atom)"
                                                                                                                       "b) a file with the following format:"
                                                                                                                       "i) a label [ mol01 ], ii) after a list of the backbone atoms in the mol01."
                                                                                                                       "You need as much labels as chains or molecules in your system."
                                                                                                                       "Keep in mind that in this case the indices start at 0."
                                                                                                                       "c) 'all' to label all atoms as backbone ones.")

            # Displaying the content of the listbb_file right after loading it
            if listbb_file is not None:
                edit_content_key = "edit_content_listbb_file"
                edit_content = st.checkbox("Edit content", key=edit_content_key)

                # Getting the original file name
                if edit_content:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        file_path = save_uploaded_file(listbb_file, temp_dir)
                        with open(file_path, "rb") as file:
                            edited_content = st.text_area("Edit the content below:",
                                                          value=file.read().decode("latin-1"),
                                                          height=300)

                        # State variable to control the visibility of the boxes
                        show_save_options = st.checkbox("Show save options", key="show_save_options_listbb_file")

                        if show_save_options:
                            # Asking the user for the path and file name to save
                            save_path = st.text_input("Enter the path to save the edited file:",
                                                      key="Enter_path_listbb_file")
                            save_filename = st.text_input("Enter the name of the edited file:",
                                                          key="Enter_name_listbb_file")

                            # Checking if both the path and the file name are specified
                            if save_path and save_filename:
                                # Here you can save 'edited_content' with the specified path and name
                                save_content_key = "save_content_listbb_file"
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

            #   =====================================

            # Non-mandatory options (conditionally present)
            st.subheader("Optional")

            #   =====================================

            topo_file = st.file_uploader("Select a topology file (TPR, DAT or PDB)",
                                         type=["tpr", "dat", "pdb"], key="topo_file")

            # Displaying the content of the topo_file right after loading it
            if topo_file is not None:
                edit_content_key = "edit_content_topo_file"
                edit_content = st.checkbox("Edit content", key=edit_content_key)

                # Getting the original file name
                if edit_content:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        file_path = save_uploaded_file(topo_file, temp_dir)
                        with open(file_path, "rb") as file:
                            edited_content = st.text_area("Edit the content below:",
                                                          value=file.read().decode("latin-1"),
                                                          height=300)

                        # State variable to control the visibility of the boxes
                        show_save_options = st.checkbox("Show save options", key="show_save_options_topo_file")

                        if show_save_options:
                            # Asking the user for the path and file name to save
                            save_path = st.text_input("Enter the path to save the edited file:",
                                                      key="Enter_path_topo_file")
                            save_filename = st.text_input("Enter the name of the edited file:",
                                                          key="Enter_name_topo_file")

                            # Checking if both the path and the file name are specified
                            if save_path and save_filename:
                                # Here you can save 'edited_content' with the specified path and name
                                save_content_key = "save_content_topo_file"
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

            #   =====================================

            log_filename = st.text_input("Name of the file to write logs from this command")

            if log_filename.strip() == "":
                log_filename = "pol_bonddist_gen.log"

            #   =====================================

            compressed_file_name = st.text_input("Enter the name for the output compressed file")

            #   =====================================

            # Button to execute the subprogram with the select options
            if st.button("RUN"):
                if not traj_files:
                    st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                'padding: 10px; border-radius: 10px;'
                                '">Warning: Please upload a list of trajectories before running the subprogram.</p>',
                                unsafe_allow_html=True)
                    return

                if not listbb_file:
                    st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                'padding: 10px; border-radius: 10px;'
                                '">Warning: Please upload a file for assign backbone atoms of a polymer.</p>',
                                unsafe_allow_html=True)
                    return

                if not compressed_file_name:
                    st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                'padding: 10px; border-radius: 10px;'
                                '">Warning: Please enter the name for the output compressed file.</p>',
                                unsafe_allow_html=True)
                    return

                if traj_files and listbb_file is not None:
                    with st.spinner("Running Bonded Distributions. Please wait..."):
                        warning_container = st.warning("Do not close the interface while Bonded Distributions is running.")
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Use the unique identifier to create a unique folder
                            output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                            os.makedirs(output_folder)

                            traj_files_path = save_uploaded_file(traj_files, temp_dir)
                            listbb_file_path = save_uploaded_file(listbb_file, temp_dir)
                            topo_file_path = save_uploaded_file(topo_file, temp_dir) if topo_file else None

                            output, error = run_bonded_distribution_generate(
                                traj_files_path,
                                listbb_file_path,
                                topo_file_path,
                                log_filename
                            )

                            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                            m = f"\n\t\tOutput from Bonded Distributions.({now})"
                            m += f"\n\t\t{'*' * len(m)}\n"
                            m += output.decode()
                            m += error.decode()
                            print(m) if logger is None else logger.info(m)

                            st.success("Bonded Distributions Subprogram executed successfully!")
                            st.success("Output files generated")
                            warning_container.empty()

                            ####    CONTINUE    ####

                            #   Output common files
                            output_files = [
                                f"{log_filename}"  ##  At de moment, we do not know the output files
                            ]


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
                                show_output_files_content(output_files, log_filename)

                                if st.button("RESET"):
                                    st.experimental_rerun()


    if calculate_option:

        # Displaying the help expandable box
        with st.expander("OPTIONS"):

            # Displaying mandatory subprogram options in the interface
            st.subheader("Essentials")

            traj_files = st.file_uploader("Select a list of trajectories from MD simulations (XTC or TRR)",
                                          type=["xtc", "trr"],
                                          key="traj_files")

            #   =====================================

            topo_file = st.file_uploader("Select a topology file (TPR, DAT or PDB)",
                                         type=["tpr", "dat", "pdb"], key="topo_file")

            # Displaying the content of the topo_file right after loading it
            if topo_file is not None:
                edit_content_key = "edit_content_topo_file"
                edit_content = st.checkbox("Edit content", key=edit_content_key)

                # Getting the original file name
                if edit_content:
                    with tempfile.TemporaryDirectory() as temp_dir:
                        file_path = save_uploaded_file(topo_file, temp_dir)
                        with open(file_path, "rb") as file:
                            edited_content = st.text_area("Edit the content below:",
                                                          value=file.read().decode("latin-1"),
                                                          height=300)

                        # State variable to control the visibility of the boxes
                        show_save_options = st.checkbox("Show save options", key="show_save_options_topo_file")

                        if show_save_options:
                            # Asking the user for the path and file name to save
                            save_path = st.text_input("Enter the path to save the edited file:",
                                                      key="Enter_path_topo_file")
                            save_filename = st.text_input("Enter the name of the edited file:",
                                                          key="Enter_name_topo_file")

                            # Checking if both the path and the file name are specified
                            if save_path and save_filename:
                                # Here you can save 'edited_content' with the specified path and name
                                save_content_key = "save_content_topo_file"
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

            #   =====================================

            unwrap_coordinates = st.checkbox("Unwrap coordinates")

            #   =====================================

            # Non-mandatory options (conditionally present)
            st.subheader("Optional")

            #   =====================================

            bond_list_file = st.file_uploader("Select a list of labels contained in the file 'bonds_data_dist.ndx'",
                                         type=["ndx"], key="bond_list_file")

            # Displaying the content of the bond_list_file right after loading it
            if bond_list_file is not None:
                if bond_list_file.name == "bonds_data_dist.ndx":
                    edit_content_key = "edit_content_bond_list_file"
                    edit_content = st.checkbox("Edit content", key=edit_content_key)

                    # Getting the original file name
                    if edit_content:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            file_path = save_uploaded_file(bond_list_file, temp_dir)
                            with open(file_path, "rb") as file:
                                edited_content = st.text_area("Edit the content below:",
                                                              value=file.read().decode("latin-1"),
                                                              height=300)

                            # State variable to control the visibility of the boxes
                            show_save_options = st.checkbox("Show save options", key="show_save_options_bond_list_file")

                            if show_save_options:
                                # Asking the user for the path and file name to save
                                save_path = st.text_input("Enter the path to save the edited file:",
                                                          key="Enter_path_bond_list_file")
                                save_filename = st.text_input("Enter the name of the edited file:",
                                                              key="Enter_name_bond_list_file")

                                # Checking if both the path and the file name are specified
                                if save_path and save_filename:
                                    # Here you can save 'edited_content' with the specified path and name
                                    save_content_key = "save_content_bond_list_file"
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
                    st.error("The file must name 'bonds_data_dist.ndx'")
                    return

            #   =====================================

            angle_list_file = st.file_uploader("Select a list of labels contained in the file 'angle_data_dist.ndx'",
                                              type=["ndx"], key="angle_list_file")

            # Displaying the content of the angle_list_file right after loading it
            if angle_list_file is not None:
                if angle_list_file.name == "angle_data_dist.ndx":
                    edit_content_key = "edit_content_angle_list_file"
                    edit_content = st.checkbox("Edit content", key=edit_content_key)

                    # Getting the original file name
                    if edit_content:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            file_path = save_uploaded_file(angle_list_file, temp_dir)
                            with open(file_path, "rb") as file:
                                edited_content = st.text_area("Edit the content below:",
                                                              value=file.read().decode("latin-1"),
                                                              height=300)

                            # State variable to control the visibility of the boxes
                            show_save_options = st.checkbox("Show save options", key="show_save_options_angle_list_file")

                            if show_save_options:
                                # Asking the user for the path and file name to save
                                save_path = st.text_input("Enter the path to save the edited file:",
                                                          key="Enter_path_angle_list_file")
                                save_filename = st.text_input("Enter the name of the edited file:",
                                                              key="Enter_name_angle_list_file")

                                # Checking if both the path and the file name are specified
                                if save_path and save_filename:
                                    # Here you can save 'edited_content' with the specified path and name
                                    save_content_key = "save_content_angle_list_file"
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
                    st.error("The file must name 'angle_data_dist.ndx'")
                    return

            #   =====================================

            dihedral_list_file = st.file_uploader("Select a list of labels contained in the file 'dihedral_data_dist.ndx'",
                                               type=["ndx"], key="dihedral_list_file")

            # Displaying the content of the dihedral_list_file right after loading it
            if dihedral_list_file is not None:
                if dihedral_list_file.name == "dihedral_data_dist.ndx":
                    edit_content_key = "edit_content_dihedral_list_file"
                    edit_content = st.checkbox("Edit content", key=edit_content_key)

                    # Getting the original file name
                    if edit_content:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            file_path = save_uploaded_file(dihedral_list_file, temp_dir)
                            with open(file_path, "rb") as file:
                                edited_content = st.text_area("Edit the content below:",
                                                              value=file.read().decode("latin-1"),
                                                              height=300)

                            # State variable to control the visibility of the boxes
                            show_save_options = st.checkbox("Show save options", key="show_save_options_dihedral_list_file")

                            if show_save_options:
                                # Asking the user for the path and file name to save
                                save_path = st.text_input("Enter the path to save the edited file:",
                                                          key="Enter_path_dihedral_list_file")
                                save_filename = st.text_input("Enter the name of the edited file:",
                                                              key="Enter_name_dihedral_list_file")

                                # Checking if both the path and the file name are specified
                                if save_path and save_filename:
                                    # Here you can save 'edited_content' with the specified path and name
                                    save_content_key = "save_content_dihedral_list_file"
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
                    st.error("The file must name 'dihedral_data_dist.ndx'")
                    return

            #   =====================================

            improper_list_file = st.file_uploader(
                "Select a list of labels contained in the file 'improper_data_dist.ndx'",
                type=["ndx"], key="improper_list_file")

            # Displaying the content of the improper_list_file right after loading it
            if improper_list_file is not None:
                if improper_list_file.name == "improper_data_dist.ndx":
                    edit_content_key = "edit_content_improper_list_file"
                    edit_content = st.checkbox("Edit content", key=edit_content_key)

                    # Getting the original file name
                    if edit_content:
                        with tempfile.TemporaryDirectory() as temp_dir:
                            file_path = save_uploaded_file(improper_list_file, temp_dir)
                            with open(file_path, "rb") as file:
                                edited_content = st.text_area("Edit the content below:",
                                                              value=file.read().decode("latin-1"),
                                                              height=300)

                            # State variable to control the visibility of the boxes
                            show_save_options = st.checkbox("Show save options", key="show_save_options_improper_list_file")

                            if show_save_options:
                                # Asking the user for the path and file name to save
                                save_path = st.text_input("Enter the path to save the edited file:",
                                                          key="Enter_path_improper_list_file")
                                save_filename = st.text_input("Enter the name of the edited file:",
                                                              key="Enter_name_improper_list_file")

                                # Checking if both the path and the file name are specified
                                if save_path and save_filename:
                                    # Here you can save 'edited_content' with the specified path and name
                                    save_content_key = "save_content_improper_list_file"
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
                    st.error("The file must name 'improper_data_dist.ndx'")
                    return

            #   =====================================

            stride = st.number_input("Frame numbers for each stride frames", min_value=1, step=1.0, value=None)

            #   =====================================

            log_filename = st.text_input("Name of the file to write logs from this command")

            if log_filename.strip() == "":
                log_filename = "pol_bonddist_gen.log"

            #   =====================================

            compressed_file_name = st.text_input("Enter the name for the output compressed file")

            #   =====================================

            # Button to execute the subprogram with the select options
            if st.button("RUN"):
                if not traj_files:
                    st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                'padding: 10px; border-radius: 10px;'
                                '">Warning: Please upload a list of trajectories before running the subprogram.</p>',
                                unsafe_allow_html=True)
                    return

                if not topo_file:
                    st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                'padding: 10px; border-radius: 10px;'
                                '">Warning: Please upload a topology file.</p>',
                                unsafe_allow_html=True)
                    return

                if not compressed_file_name:
                    st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                                'padding: 10px; border-radius: 10px;'
                                '">Warning: Please enter the name for the output compressed file.</p>',
                                unsafe_allow_html=True)
                    return

                if traj_files and topo_file is not None:
                    with st.spinner("Running Bonded Distributions. Please wait..."):
                        warning_container = st.warning(
                            "Do not close the interface while Bonded Distributions is running.")
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Use the unique identifier to create a unique folder
                            output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                            os.makedirs(output_folder)

                            traj_files_path = save_uploaded_file(traj_files, temp_dir)
                            topo_file_path = save_uploaded_file(topo_file, temp_dir)
                            bond_list_file_path = save_uploaded_file(bond_list_file, temp_dir) if bond_list_file else None
                            angle_list_file_path = save_uploaded_file(angle_list_file,
                                                                     temp_dir) if angle_list_file else None
                            dihedral_list_file_path = save_uploaded_file(dihedral_list_file,
                                                                     temp_dir) if dihedral_list_file else None
                            improper_list_file_path = save_uploaded_file(improper_list_file,
                                                                     temp_dir) if improper_list_file else None


                            output, error = run_bonded_distribution_calculate(
                                traj_files_path, topo_file_path,
                                bond_list_file_path, angle_list_file_path,
                                dihedral_list_file_path, improper_list_file_path,
                                stride, log_filename, unwrap_coordinates
                            )

                            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                            m = f"\n\t\tOutput from Bonded Distributions.({now})"
                            m += f"\n\t\t{'*' * len(m)}\n"
                            m += output.decode()
                            m += error.decode()
                            print(m) if logger is None else logger.info(m)

                            st.success("Bonded Distributions Subprogram executed successfully!")
                            st.success("Output files generated")
                            warning_container.empty()


                            #   Output common files
                            output_files = [
                                f"{log_filename}"
                            ]

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
                                show_output_files_content(output_files, log_filename)

                                if st.button("RESET"):
                                    st.experimental_rerun()


def run_page_bonded_distribution():

    func_page_bonded_distribution()