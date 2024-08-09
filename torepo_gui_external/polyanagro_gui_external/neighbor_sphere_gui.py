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


def run_neighbor_sphere(coord_file, topo_file, log_filename):

    # Get the directory path of the main code
    # script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the 'neighbor_sphere.py' code
    neighbor_sphere_script = "/home/cgarcia/Programs/polyanagro/polyanagro/cmds/neighbor_sphere.py"

    bash_command = f"python {neighbor_sphere_script} -c {coord_file}"

    if topo_file:
        bash_command += f" -t {topo_file}"

    if log_filename:
        bash_command += f" --log {log_filename}"

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


def func_page_neighbor_sphere():

    st.markdown("<h1 style='font-size:24px;'>Neighbor Sphere</h1>", unsafe_allow_html=True)

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    with st.expander("INFO"):

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
        st.write("Fields with '*' are required")

        #   ============================    Input options   ============================    #

        options = st.session_state.get("options", {})
        if not options:
            options = {}

        input_options = [
            "Select a file containing the coordinates (GRO or PDB)*",
            "Select a topology file (TPR, DAT or PDB)"
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

                    if option == "Select a file containing the coordinates (GRO or PDB)*":
                        filetypes = [("GRO files", "*.gro"), ("PDB files", "*.pdb")]
                    else:
                        filetypes = [("DAT files", "*.dat"), ("TPR files", "*.tpr"), ("PDB files", "*.pdb")]

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
            log_filename = "neigh_sphere.log"

        #   ============================    Compressed file options   ============================    #

        compressed_file_name = st.text_input("Enter the name for the output compressed file*")

        #   ============================    NEIGHBOR SPHERE RUN   ============================    #

        # Button to execute the program with the select options
        if st.button("RUN"):
            coord_file_path = options.get("input_file_1", "")
            topo_file_path = options.get("input_file_2", "")

            if not coord_file_path:
                st.error("Please select a file containing the coordinates before running the program")
                return

            # Save updated input files in session state
            st.session_state["options"] = options

            if not compressed_file_name:
                st.error("Please enter the name for the output compressed file")
                return

            if coord_file_path is not None:
                with st.spinner("Running Neighbor Sphere. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Neighbor Sphere is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique directory to the output
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        # Save selected files in the temporal directory
                        coord_file_path = save_uploaded_file(coord_file_path, temp_dir)
                        topo_file_path = save_uploaded_file(topo_file_path,
                                                            temp_dir) if topo_file_path else None

                        # Execute the command with path files provided
                        output, error = run_neighbor_sphere(
                            coord_file_path,
                            topo_file_path,
                            log_filename
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Neighbor Sphere.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Neighbor Sphere subprogram executed successfully!")
                        warning_container.empty()

                        #   Output list of common files
                        output_files = [
                            f"{log_filename}",
                            "coords_com.pdb", "vmd_com.tcl", "wrapped.pdb"
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


def run_page_neighbor_sphere():

    func_page_neighbor_sphere()
