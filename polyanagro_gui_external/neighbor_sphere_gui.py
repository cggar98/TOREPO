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


# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_neighbor_sphere(coord_file, topo_file, log_filename):

    # Get the directory path of the main code
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the 'neighbor_sphere.py' code
    neighbor_sphere_script = os.path.join(script_dir, "neighbor_sphere.py")

    bash_command = f"python {neighbor_sphere_script} -c {coord_file}"

    if topo_file:
        bash_command += f" -t {topo_file}"

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


# ToDo: How to visualize molecules: VMD or JSMol?


def func_page_neighbor_sphere():


    st.markdown("<h1 style='font-size:24px;'>Neighbor Sphere</h1>", unsafe_allow_html=True)

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))


    # Displaying the welcome text
    st.text("""
    ***********************************************************************
             Find and extract all neighbor molecules in a sphere 
             ---------------------------------------------------

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

    # Displaying the help expandable box
    with st.expander("OPTIONS"):

        # Displaying mandatory subprogram options in the interface
        st.subheader("Essentials")

        coord_file = st.file_uploader("Select a file containing the coordinates", type=["pdb"],
                                      key="coord_file")

        # Displaying the content of the coord_file right after loading it
        if coord_file is not None:
            edit_content_key = "edit_content_coord_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(coord_file, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_coord_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_coord_file")
                        save_filename = st.text_input("Enter the name of the edited file:", key="Enter_name_coord_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_coord_file"
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

        # Non-mandatory options (conditionally present)
        st.subheader("Optional")

        topo_file = st.file_uploader("Select a topology file (TPR, DAT or PDB)", type=["tpr", "dat", "pdb"],
                                     key="topo_file")

        # Displaying the content of the topo_file right after loading it
        if topo_file is not None:
            edit_content_key = "edit_content_topo_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(topo_file, temp_dir)
                    with open(file_path, "rb") as file:
                        edited_content = st.text_area("Edit the content below:", value=file.read().decode("latin-1"),
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

        # ===========================================

        log_filename = st.text_input("Name of the file to write logs from this command")

        if log_filename.strip() == "":
            log_filename = "neigh_sphere.log"

        # ===========================================

        compressed_file_name = st.text_input("Enter the name for the output compressed file")

        # Button to execute the program with the select options
        if st.button("RUN"):
            if not coord_file:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please upload a file containing the coordinates before running the subprogram.</p>',
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

            if coord_file and topo_file is not None:
                with st.spinner("Running Neighbor Sphere. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Neighbor Sphere is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique folder
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        coord_file_path = save_uploaded_file(coord_file, temp_dir)
                        topo_file_path = save_uploaded_file(topo_file, temp_dir)

                        output, error = run_neighbor_sphere(
                            coord_file_path,
                            topo_file_path,
                            log_filename,
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Neighbor Sphere.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Neighbor Sphere Subprogram executed successfully!")
                        st.success("Output files generated")
                        warning_container.empty()

                        #   Output list of common files
                        output_files = [
                            f"{log_filename}",  ####    NO FILES FOUND
                            "coords_com.pdb", "vmd_com.tcl", "wrapped.pdb"
                        ]

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


def run_page_neighbor_sphere():

    func_page_neighbor_sphere()
