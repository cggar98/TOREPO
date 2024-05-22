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
import glob
from tkinter import filedialog


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
                      impropers, npairs, verbose):

    bash_command = f"replicate_polymer -p {structure_file} -f {xml_file} --images {image_x} {image_y} {image_z}"

    if mdengine:
        bash_command += f" -e {mdengine}"
    if noh:
        bash_command += " --noh"
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
        bash_command += " --verbose"
    # if pattern:
    #     bash_command += f" -pat {pattern}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return output, error


def run_bash(input_sh_file_path):
    bash_command = f"bash {input_sh_file_path}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output_impropers, error_impropers = process.communicate()
    return output_impropers, error_impropers


def save_uploaded_file(uploaded_file_path, temp_dir):
    file_path = os.path.join(temp_dir, os.path.basename(uploaded_file_path))
    shutil.copy(uploaded_file_path, file_path)
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
        st.error("'Info.log' not found in the output files")
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


# ToDo: How to visualize molecules: VMD or JSMol?


def func_page_replicate():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    impropers_unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Replicate Polymer</h1>", unsafe_allow_html=True)

    # Displaying the welcome text
    with st.expander("INFO"):
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
        st.text("Fields with '*' are required")

        #####   ============================    Input options   ============================    #####

        options = st.session_state.get("options", {})
        if not options:
            options = {}

        input_options = [
            "Select a pdb file containing the structure to be replicated (PDB)*",
            "Select a forcefield (XML)*",
            "Select impropers file (NDX)"
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

                    if option == "Select a pdb file containing the structure to be replicated (PDB)*":
                        filetypes = [("PDB files", "*.pdb")]

                    if option == "Select a forcefield (XML)*":
                        filetypes = [("XML files", "*.xml")]

                    if option == "Select impropers file (NDX)":
                        filetypes = [("NDX files", "*.ndx")]


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

        #####   ============================    Generate impropers file   ============================    #####

        without_impropers = st.radio("Do you need an impropers file?", ["Yes", "No"])
        need_impropers = (without_impropers == "Yes")
        if need_impropers:
            option_get_sh = st.session_state.get("option_get_sh", {})
            if not option_get_sh:
                option_get_sh = {}

            input_sh_option = [
                "Select a bash script to generate an impropers file (SH)*"
            ]

            for index_get_sh, option_sh in enumerate(input_sh_option, start=1):
                input_sh_key = f"sh_file_{index_get_sh}"

                if input_sh_key not in option_get_sh:
                    option_get_sh[input_sh_key] = ""

                input_sh_filepath = st.text_input(
                    option_sh,
                    option_get_sh[input_sh_key],
                    key=f"{input_sh_key}_input_text"
                )

                col1, col2 = st.columns(2)
                with col1:
                    browse_button_sh_key = f"browse_{input_sh_key}"
                    if st.button("Browse file", key=browse_button_sh_key):
                        wkdir = os.getcwd()
                        filetypes = []

                        if option_sh == "Select a bash script to generate an impropers file (SH)*":
                            filetypes = [("SH files", "*.sh")]

                        sh_input_filename = filedialog.askopenfilename(
                            initialdir=wkdir,
                            title="Select a '.sh' file",
                            filetypes=filetypes
                        )

                        if sh_input_filename:
                            option_get_sh[input_sh_key] = sh_input_filename

                with col2:
                    if option_get_sh[input_sh_key]:
                        remove_button_sh_key = f"remove_{input_sh_key}"
                        if st.button("Remove file", key=remove_button_sh_key):
                            option_get_sh[input_sh_key] = ""

            st.session_state["option_get_sh"] = option_get_sh

            # Button to execute the script
            if st.button("Generate impropers file"):
                input_sh_file_path = option_get_sh.get("sh_file_1", "")
                if not input_sh_file_path:
                    st.error("Please select a script to generate an impropers file")
                    return

                # Save updated input files in session state
                st.session_state["option_get_sh"] = option_get_sh


                if input_sh_file_path is not None:
                    with st.spinner("Running script. Please wait..."):
                        with tempfile.TemporaryDirectory() as improper_temp_dir:
                            # Use the unique identifier to create a unique folder
                            impropers_output_folder = os.path.join(improper_temp_dir, "impropers.ndx")
                            os.makedirs(impropers_output_folder)

                            input_sh_file_path = save_uploaded_file(input_sh_file_path, improper_temp_dir)

                            output_impropers, error_impropers = run_bash(input_sh_file_path)

                            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                            m = f"\n\t\tOutput from Running script.({now})"
                            m += f"\n\t\t{'*' * len(m)}\n"
                            m += output_impropers.decode()
                            m += error_impropers.decode()
                            print(m) if improper_logger is None else improper_logger.info(m)

                            st.success("Impropers file has been generated")

                            #   Output list of common files
                            output_impropers_files = ["impropers.ndx"]

                            # Move generated files to single folder
                            for filename_improper in os.listdir(improper_temp_dir):
                                filepath_improper = os.path.join(improper_temp_dir, filename_improper)
                                if os.path.isfile(filepath_improper):
                                    shutil.move(filepath_improper, os.path.join(impropers_output_folder, filename_improper))


                            tar_file_path_impropers = create_tar_gz(impropers_output_folder, output_impropers_files)

                            # Generate download link for output files
                            download_link = (f'<a href="data:application/tar+gzip;base64,'
                                             f'{base64.b64encode(open(tar_file_path_impropers, "rb").read()).decode()}'
                                             f'" download="impropers_file.tar.gz">'
                                             f'Download impropers file</a>')
                            st.markdown(download_link, unsafe_allow_html=True)

                            if st.button("RESET"):
                                st.experimental_rerun()

        #####   ============================    Images options   ============================    #####

        # Mandatory entry for --images image_x image_y image_z
        image_x = st.number_input("Number of Images to Replicate in Dimension X*", min_value=1, step=1, value=1)
        image_y = st.number_input("Number of Images to Replicate in Dimension Y*", min_value=1, step=1, value=1)
        image_z = st.number_input("Number of Images to Replicate in Dimension Z*", min_value=1, step=1, value=1)

        #####   ============================    Index options   ============================    #####

        index = st.text_input("Indices of Atoms to be Removed from the PDB")

        #####   ============================    Boxlength options   ============================    #####

        boxlength_a = st.number_input("Box Length (a) in Nanometers", min_value=0.0, step=0.1, value=None)
        boxlength_b = st.number_input("Box Length (b) in Nanometers", min_value=0.0, step=0.1, value=None)
        boxlength_c = st.number_input("Box Length (c) in Nanometers", min_value=0.0, step=0.1, value=None)

        #####   ============================    Boxangle options   ============================    #####

        boxangle_alpha = st.number_input("Box Angle (alpha) in Degrees", min_value=0.0, step=0.1, value=None)
        boxangle_beta = st.number_input("Box Angle (beta) in Degrees", min_value=0.0, step=0.1, value=None)
        boxangle_gamma = st.number_input("Box Angle (gamma) in Degrees", min_value=0.0, step=0.1, value=None)

        #####   ============================    Npairs options   ============================    #####

        npairs = st.number_input("Monomer or Residue Inclusions (e.g., 1)", step=1.0, value=None)

        #####   ============================    MDengine options   ============================    #####

        mdengine = st.text_input("MD Package to Perform Calculations")

        #####   ============================    NOH options   ============================    #####

        noh = st.toggle("Remove Hydrogens for a United Atom Representation")

        #####   ============================    Verbose options   ============================    #####

        verbose = st.toggle("Verbose Checking of Angles and Dihedral")

        # #####   ============================    Pattern options (NO FUNCIONA)   ============================    #####
        #
        # default_pattern = "replicate"
        # pattern = st.text_input("String pattern to name the new files", default_pattern)

        #####   ============================    Compressed file options   ============================    #####

        compressed_file_name = st.text_input("Enter the name for the output compressed file*")

        #####   ============================    REPLICATE RUN   ============================    #####

        # Button to execute the program with the select options
        if st.button("RUN"):

            structure_file_path = options.get("input_file_1", "")
            xml_file_path = options.get("input_file_2", "")
            impropers_file_path = options.get("input_file_3", "")

            if not structure_file_path:
                st.error("Please upload a pdb file before running the program")
                return

            if not xml_file_path:
                st.error("Please upload a FORCEFIELD file before running the program")
                return

            # Save updated input files in session state
            st.session_state["options"] = options

            if not image_x:
                st.error("Please enter the number of images to Replicate in Dimension X")
                return

            if not image_y:
                st.error("Please enter the number of images to Replicate in Dimension Y")
                return

            if not image_z:
                st.error("Please enter the number of images to Replicate in Dimension Z")
                return

            if not (isinstance(image_x, int) and image_x >= 1 and image_x % 1 == 0 and
                    isinstance(image_y, int) and image_y >= 1 and image_y % 1 == 0 and
                    isinstance(image_z, int) and image_z >= 1 and image_z % 1 == 0):
                st.error("Please enter valid integer values greater than or equal "
                         "to 1 for Number of Images before running the program")
                return

            if not compressed_file_name:
                st.error("Please enter the name for the output compressed file")
                return

            if structure_file_path and xml_file_path and image_x and image_y and image_z is not None:
                with st.spinner("Running Replicate Polymer. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Replicate Polymer is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique directory to the output
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        # Save selected files in the temporal directory
                        structure_file_path = save_uploaded_file(structure_file_path, temp_dir)
                        xml_file_path = save_uploaded_file(xml_file_path, temp_dir)
                        impropers_file_path = save_uploaded_file(impropers_file_path,
                                                                  temp_dir) if impropers_file_path else None

                        # Execute the Replicate Polymer command with path files provided
                        output, error = run_replicate_cmd(
                            structure_file_path,
                            xml_file_path,
                            image_x, image_y, image_z,
                            mdengine, noh, index,
                            boxlength_a, boxlength_b, boxlength_c,
                            boxangle_alpha, boxangle_beta, boxangle_gamma,
                            impropers_file_path, npairs, verbose
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
                                f"{structure_file_path}_noH.gro",
                                f"{structure_file_path}_noH.pdb",
                                f"{structure_file_path}_noH.top",
                                f"{structure_file_path}_noH_replicate.gro",
                                f"{structure_file_path}_noH_replicate.pdb",
                                f"{structure_file_path}_noH_replicate.top",
                                ])
                            else:
                                output_files.extend([
                                    f"{structure_file_path}_noH_replicate_clean.inp",
                                    f"{structure_file_path}_noH_replicate_clean.lmp",
                                    f"{structure_file_path}_noH.gro",
                                    f"{structure_file_path}_noH.pdb",
                                    f"{structure_file_path}_noH.top",
                                    f"{structure_file_path}_noH_replicate.gro",
                                    f"{structure_file_path}_noH_replicate.pdb",
                                    f"{structure_file_path}_noH_replicate.top",
                                ])

                        #   =====================

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

                        # Show 'Info.log' content
                        show_output_files_content(output_files)

                        if st.button("RESET"):
                            st.experimental_rerun()


def run_page_replicate():

    func_page_replicate()
