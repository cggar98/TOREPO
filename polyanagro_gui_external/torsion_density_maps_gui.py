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
from tkinter import filedialog


# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_2d_torsion_density_maps(traj_files, topo_file, phipsi, phipsi_2,
                                log_filename, stride, unwrap_coordinates):

    bash_command = f"2D_torsion_density_maps -t {traj_files} --topo {topo_file} --phipsi {phipsi} {phipsi_2}"

    if unwrap_coordinates:
        bash_command += " --unwrap True"
    else:
        bash_command += " --unwrap False"

    if log_filename:
        bash_command += f" --log {log_filename}"

    if stride:
        bash_command += f" --stride {stride}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()

    return output, error


def save_uploaded_file(uploaded_file, directory):
    """Save uploaded file to the specified directory."""
    if isinstance(uploaded_file, str):
        # If uploaded_file is a string, it's already a path
        file_path = uploaded_file
    else:
        # If uploaded_file is an uploaded file object
        file_path = os.path.join(directory, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
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
        st.error(f"Warning: {log_filename} not found in the output files")


def create_tar_gz(output_folder, output_file_paths):
    # Create a temporary file to store the .tar.gz
    temp_tar_path = os.path.join(output_folder, "output_files.tar.gz")

    # Create the .tar.gz file
    with tarfile.open(temp_tar_path, "w:gz") as tar:
        for file_path in output_file_paths:
            tar.add(file_path, arcname=os.path.basename(file_path))

    return temp_tar_path


# ToDo: How to visualize molecules: VMD or JSMol?


def func_page_2d_torsion():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>2D Torsion Density Maps</h1>", unsafe_allow_html=True)

    # Displaying the welcome text
    with st.expander("INFO"):
        st.text("""
        ***********************************************************************
                      Generate a 2DMap for a pair of dyhedral types
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

    # Displaying the help expandable box
    with st.expander("OPTIONS"):
        st.write("Fields with '*' are required")

        #   ============================    Input options   ============================    #

        options = st.session_state.get("options", {})
        if not options:
            options = {}

        input_options = [
            "Select a list of trajectories from MD simulations (XTC or TRR)*",
            "Select a topology file (TPR, DAT or PDB)*",
            "Select a file with two labels contained in the file 'dihedral_data_dist.ndx'*",
            "Select another file 'dihedral_data_dist.ndx'*"
        ]

        for index, option in enumerate(input_options, start=1):
            input_key = f"input_file_{index}"

            if input_key not in options:
                options[input_key] = ""

            input_filepath = st.text_input(
                option,
                options[input_key],
                key=f"{input_key}_input_text"
            )

            col1, col2 = st.columns(2)
            with col1:
                browse_button_key = f"browse_{input_key}"
                if st.button("Browse file", key=browse_button_key):
                    wkdir = os.getcwd()
                    filetypes = []

                    if option == "Select a list of trajectories from MD simulations (XTC or TRR)*":
                        filetypes = [("XTC files", "*.xtc"), ("TRR files", "*.trr")]
                    if option == "Select a topology file (TPR, DAT or PDB)*":
                        filetypes = [("TPR files", "*.tpr"), ("DAT files", "*.dat"), ("PDB files", "*.pdb")]
                    if option == "Select a file with two labels contained in the file 'dihedral_data_dist.ndx'*":
                        filetypes = [("NDX files", "dihedral_data_dist.ndx")]
                    if option == "Select another file 'dihedral_data_dist.ndx'*":
                        filetypes = [("NDX files", "dihedral_data_dist.ndx")]

                    input_filename = filedialog.askopenfilename(
                        initialdir=wkdir,
                        title="Select an input file",
                        filetypes=filetypes
                    )

                    if input_filename:
                        options[input_key] = input_filename

            with col2:
                if options[input_key]:
                    remove_button_key = f"remove_{input_key}"
                    if st.button("Remove file", key=remove_button_key):
                        options[input_key] = ""

        st.session_state["options"] = options

        #   ============================    Unwrap options   ============================    #

        unwrap_coordinates = st.toggle("Unwrap coordinates")

        #   ============================    Log options   ============================    #

        log_filename = st.text_input("Name of the file to write logs from this command")

        if log_filename.strip() == "":
            log_filename = "pol_2DMap.log"

        #   ============================    Stride options   ============================    #

        stride = st.number_input("Frame numbers for each stride frames", min_value=1, step=1, value=None)

        #   ============================    Compressed file options   ============================    #

        compressed_file_name = st.text_input("Enter the name for the output compressed file*")

        #   ============================    2D TORSION DENSITY MAPS RUN   ============================    #

        # Button to execute the subprogram with the select options
        if st.button("RUN"):
            traj_files_path = options.get("input_file_1", "")
            topo_file_path = options.get("input_file_2", "")
            phipsi_path = options.get("input_file_3", "")
            phipsi_path_2 = options.get("input_file_4", "")

            if not traj_files_path:
                st.error("Please select a list of trajectories before running the program")
                return
            if not topo_file_path:
                st.error("Please select a topology file before running the program")
                return
            if not phipsi_path:
                st.error("Please select a file with two labels contained "
                         "in the file 'dihedral_data_dist.ndx' before running the program")
                return
            if not phipsi_path_2:
                st.error("Please select another file 'dihedral_data_dist.ndx' before running the program")
                return

            # Save updated input files in session state
            st.session_state["options"] = options

            if not compressed_file_name:
                st.error("Please enter the name for the output compressed file")
                return

            if traj_files_path and topo_file_path and phipsi_path and phipsi_path_2 is not None:
                with st.spinner("Running 2D Torsion Density Maps. Please wait..."):
                    warning_container = st.warning("Do not close the interface "
                                                   "while 2D Torsion Density Maps is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique directory to the output
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        # Save selected files in the temporal directory
                        traj_files_path = save_uploaded_file(traj_files_path, temp_dir)
                        topo_file_path = save_uploaded_file(topo_file_path, temp_dir)
                        phipsi_path = save_uploaded_file(phipsi_path, temp_dir)
                        phipsi_path_2 = save_uploaded_file(phipsi_path_2, temp_dir)

                        # Execute command with path files provided
                        output, error = run_2d_torsion_density_maps(
                            traj_files_path,
                            topo_file_path,
                            phipsi_path,
                            phipsi_path_2,
                            log_filename, stride, unwrap_coordinates
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from 2D Torsion Density Maps.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("2D Torsion Density Maps subprogram executed successfully!")
                        warning_container.empty()

                        #   Output list of common files
                        output_files = [
                            f"{log_filename}"
                        ]

                        #   ====    CONTINUE ...   ====

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
                                             f'" download="{compressed_file_name}.tar.gz">'
                                             f'Download {compressed_file_name} compressed file</a>')
                            st.markdown(download_link, unsafe_allow_html=True)

                            # Show output file names
                            show_output_files_content(output_files, log_filename)

                            if st.button("RESET"):
                                st.experimental_rerun()


def run_page_2d_torsion():

    func_page_2d_torsion()
