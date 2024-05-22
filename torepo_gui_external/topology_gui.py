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
from tkinter import filedialog
from .test_server_gui import *


# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def save_uploaded_file(uploaded_file_path, temp_dir):
    file_path = os.path.join(temp_dir, os.path.basename(uploaded_file_path))
    shutil.copy(uploaded_file_path, file_path)
    return file_path


def run_topology_cmd(input_file, renumber_pdb, assign_residues,
                     filemap, separate_chains, pattern, isunwrap, guess_improper):

    bash_command = f"topology_cmd -i {input_file}"

    if renumber_pdb:
        bash_command += f" -r {renumber_pdb}"
    if assign_residues:
        bash_command += f" -a {assign_residues}"
    if filemap:
        bash_command += f" --filemap {filemap}"
    if separate_chains:
        bash_command += " --separate_chains"
    if pattern:
        bash_command += f" -p {pattern}"
    if isunwrap:
        bash_command += " -w"
    if guess_improper:
        bash_command += " --guess_improper"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return output, error


def show_info_topology_content(output_file_paths):

    # Check if 'InfoTopology.log' is present in the output file list
    info_topology_log_path = next((path for path in output_file_paths if "InfoTopology.log" in path), None)

    if info_topology_log_path:
        st.write(f"### {os.path.basename(info_topology_log_path)}")
        with open(info_topology_log_path, "r") as output_file:
            file_content = output_file.read()
            st.text_area("File content:", value=file_content, height=300)
    else:
        st.error("'InfoTopology.log' not found in the output files")
        return


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


# ToDo: How to visualize molecules: VMD, JSMol or stmol?


def func_page_topology():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Topology</h1>", unsafe_allow_html=True)

    # Displaying the welcome text
    with st.expander("INFO"):
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

    # Displaying the options expandable box
    with st.expander("OPTIONS"):
        st.text("Fields with '*' are required")

        #####   ============================    Input options   ============================    #####

        options = st.session_state.get("options", {})
        if not options:
            options = {}

        input_options = [
            "Select input file (XSD, PDB, or MOL2)*",
            "Select HEAD TAIL file for renumbering pdb (DAT)",
            "Select SETUP RESIDUE file for assigning residues (DAT)",
            "Select FILEMAP for matching LAMMPS type with name and element (DAT)"
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

                    if option == "Select input file (XSD, PDB, or MOL2)*":
                        filetypes = [("PDB files", "*.pdb"), ("XSD files", "*.xsd"), ("MOL2 files", "*.mol2")]
                    else:
                        filetypes = [("DAT files", "*.dat")]

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

        #####   ============================    Pattern options   ============================    #####

        pattern = st.text_input("String pattern to name the new files")
        if pattern.strip() == "":
            pattern = "topology"

        #####   ============================    Separate chains options   ============================    #####

        separate_chains = st.toggle("Create a pdb file for each chain")

        #####   ============================    Isunwrap options   ============================    #####

        isunwrap = st.toggle("Unwrap coordinates in the final structure")

        #####   ============================    Guess impropers options   ============================    #####

        guess_improper = st.toggle("Guess improper angles in the system")

        #####   ============================    Compressed file options   ============================    #####

        compressed_file_name = st.text_input("Enter the name for the output compressed file*")

        #####   ============================    TOPOLOGY RUN   ============================    #####

        # Button to execute the program
        if st.button("RUN"):
            input_file_path = options.get("input_file_1", "")
            renumber_pdb_path = options.get("input_file_2", "")
            assign_residues_path = options.get("input_file_3", "")
            filemap_path = options.get("input_file_4", "")

            if not input_file_path:
                st.error("Please select an input file before running the program")
                return

            # Save updated input files in session state
            st.session_state["options"] = options

            if not compressed_file_name:
                st.error("Please enter the name for the output compressed file")
                return

            if input_file_path is not None:
                with st.spinner("Running Topology. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Topology is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique directory to the output
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        # Save selected files in the temporal directory
                        input_file_path = save_uploaded_file(input_file_path, temp_dir)
                        renumber_pdb_path = save_uploaded_file(renumber_pdb_path,
                                                               temp_dir) if renumber_pdb_path else None
                        assign_residues_path = save_uploaded_file(assign_residues_path,
                                                                  temp_dir) if assign_residues_path else None
                        filemap_path = save_uploaded_file(filemap_path, temp_dir) if filemap_path else None

                        # Execute the Topology command with path files provided
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

                        # If 'separate_chains' option is selected, add files for each chain
                        if separate_chains:
                            pattmp = r"{}_[0-9][0-9][0-9][0-9].pdb".format(pattern)
                            separate_chains_files = glob.glob(pattmp)
                            for item in separate_chains_files:
                                print(item)
                                output_files.extend([item])

                        # Move generated files to the output directory
                        for filename in os.listdir(temp_dir):
                            filepath = os.path.join(temp_dir, filename)
                            if os.path.isfile(filepath):
                                shutil.move(filepath, os.path.join(output_folder, filename))

                        # Build compressed file '.tar.gz' of the output files
                        tar_file_path = create_tar_gz(output_folder, output_files)

                        # Generate download link to the compressed output files
                        download_link = (f'<a href="data:application/tar+gzip;base64,'
                                         f'{base64.b64encode(open(tar_file_path, "rb").read()).decode()}'
                                         f'" download="{compressed_file_name}_files.tar.gz">'
                                         f'Download {compressed_file_name} output files</a>')
                        st.markdown(download_link, unsafe_allow_html=True)

                        # Show 'InfoTopology.log' content
                        show_info_topology_content(output_files)

                        if st.button("RESET"):
                            st.experimental_rerun()


def run_page_topology():

    func_page_topology()
