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


def run_pair_distribution(traj_files, topo_file,
                          log_filename, stride, sets, dr):

    bash_command = f"pair_distribution -t {traj_files}"

    if topo_file.endswith(".tpr"):
        bash_command += f" --tpr {topo_file}"

    if topo_file.endswith(".psf"):
        bash_command += f" --psf {topo_file}"

    if log_filename:
        bash_command += f" --log {log_filename}"

    if stride:
        bash_command += f" --stride {stride}"

    if sets:
        bash_command += f" --sets {sets}"

    if dr:
        bash_command += f" --dr {dr}"

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
            if os.path.exists(file_path):  # Check if file exists
                tar.add(file_path, arcname=os.path.basename(file_path))
            else:
                print(f"Warning: File not found - {file_path}")

    if os.path.exists(temp_tar_path):
        return temp_tar_path
    else:
        return None


# ToDo: How to visualize molecules: VMD or JSMol?


def func_page_pair_distribution():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Pair Distribution</h1>", unsafe_allow_html=True)
    with st.expander("INFO"):

        # Displaying the welcome text
        st.text("""
        ***********************************************************************
                             Pair distribution calculations 
                  ----------------------------------------------
    
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
            "Select a topology file (TPR or PSF)*"
        ]

        for index, option in enumerate(input_options, start=1):
            input_key = f"input_file_{index}"

            if input_key not in options:
                options[input_key] = ""

            st.text_input(
                option,
                options[input_key],
                key=f"{input_key}_input_text"
            )

            col1, col2 = st.columns(2)
            with col1:
                browse_button_key = f"browse_{input_key}"
                if st.button("Browse file", key=browse_button_key):
                    wkdir = os.getcwd()

                    if option == "Select a list of trajectories from MD simulations (XTC or TRR)*":
                        filetypes = [("XTC files", "*.xtc"), ("TRR files", "*.trr")]
                    else:
                        filetypes = [("PSF files", "*.psf"), ("TPR files", "*.tpr")]

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

    #   ============================    Log options   ============================    #

        log_filename = st.text_input("Name of the file to write logs from this command")

        if log_filename.strip() == "":
            log_filename = "pol_rdf.log"    # No file found #

        #   ============================    Stride options   ============================    #

        stride = st.number_input("Frame numbers for each stride frames", min_value=1, step=1, value=None)

        #   ============================    Sets options   ============================    #

        sets = st.text_input("Enter the set of atoms to calculate the g(r)",
                             help="E.g., 1-100 150-200")

        if sets.strip() == "":  # NO FUNCIONA #
            sets = "all"

        #   ============================    Bin width options   ============================    #

        dr = st.number_input("Enter the bin width for the histogram (angstroms)", step=0.1, value=None, format="%.1f")

        #   ============================    Compressed file options   ============================    #

        compressed_file_name = st.text_input("Enter the name for the output compressed file*")

        #   ============================    PAIR DISTRIBUTION RUN   ============================    #

        # Button to execute the subprogram with the select options
        if st.button("RUN"):
            traj_files_path = options.get("input_file_1", "")
            topo_file_path = options.get("input_file_2", "")

            if not traj_files_path:
                st.error("Please select a list of trajectories before running the program")
                return
            if not topo_file_path:
                st.error("Please select a topology file before running the program")
                return

            # Save updated input files in session state
            st.session_state["options"] = options

            if not compressed_file_name:
                st.error("Please enter the name for the output compressed file")
                return

            if traj_files_path and topo_file_path is not None:
                with st.spinner("Running Pair Distribution. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Pair Distribution is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique directory to the output
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        # Save selected files in the temporal directory
                        traj_files_path = save_uploaded_file(traj_files_path, temp_dir)
                        topo_file_path = save_uploaded_file(topo_file_path, temp_dir)

                        # Execute the command with path files provided
                        output, error = run_pair_distribution(
                            traj_files_path, topo_file_path,
                            log_filename, stride, sets, dr
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Pair Distribution.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Pair Distribution subprogram executed successfully!")
                        warning_container.empty()

                        if not log_filename or log_filename.strip() == "":
                            log_filename = "pol_rdf.log"

                        #   Output list of common files
                        output_files = [
                            f"{log_filename}.log"   # Error: Not file found
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
                                             f'" download="{compressed_file_name}.tar.gz">'
                                             f'Download {compressed_file_name} compressed file</a>')
                            st.markdown(download_link, unsafe_allow_html=True)

                            # Show output file names
                            show_output_files_content(output_files, log_filename)

                            if st.button("RESET"):
                                st.experimental_rerun()


def run_page_pair_distribution():

    func_page_pair_distribution()
