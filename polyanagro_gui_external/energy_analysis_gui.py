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


def run_energy_analysis_info(energy_list, log_filename):

    bash_command = f"energy_analysis info -e {energy_list}"

    if log_filename:
        bash_command += f" --log {log_filename}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return output, error


def run_energy_analysis_calc(energy_list, log_filename, tbegin, tend,
                             join_energy, groupterms, avg, acf_list):

    bash_command = f"energy_analysis calc -e {energy_list}"

    if log_filename:
        bash_command += f" --log {log_filename}"
    if tbegin:
        bash_command += f" --tbegin {tbegin}"
    if tend:
        bash_command += f" --tend {tend}"
    if join_energy:
        bash_command += f" --joinpath {join_energy}"
    if groupterms:
        bash_command += " --groupterms"
    if avg:
        bash_command += " --avg"
    if acf_list:
        bash_command += f" --acf {acf_list}"

    process = subprocess.Popen(bash_command.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    return output, error


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
    # Crear un archivo temporal para almacenar el .tar.gz
    temp_tar_path = os.path.join(output_folder, "output_files.tar.gz")

    # Crear el archivo .tar.gz
    with tarfile.open(temp_tar_path, "w:gz") as tar:
        for file_path in output_file_paths:
            if isinstance(file_path, list):  # Si es una lista, iterar sobre ella
                for sub_path in file_path:
                    if os.path.exists(sub_path):
                        tar.add(sub_path, arcname=os.path.basename(sub_path))
                    else:
                        print(f"Warning: File not found - {sub_path}")
            else:  # Si no es una lista, procesar normalmente
                if os.path.exists(file_path):
                    tar.add(file_path, arcname=os.path.basename(file_path))
                else:
                    print(f"Warning: File not found - {file_path}")

    if os.path.exists(temp_tar_path):
        return temp_tar_path
    else:
        return None


# ToDo: How to visualize molecules: VMD, JSMol or stmol?


def func_page_energy_analysis():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Energy Analysis</h1>", unsafe_allow_html=True)

    # Displaying the welcome text
    with st.expander("INFO"):
        st.text("""
    ***********************************************************************
                                Energy Analysis 
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

    with st.expander("OPTIONS"):

        options = st.radio("For this subprogram, you must choose one of these two options", ["Info", "Calculate"])
        info_option = (options == "Info")
        calculate_option = (options == "Calculate")

    #   ============================    INFO OPTIONS   ============================    #

        if info_option:
            st.write("Fields with '*' are required")

            #   ============================    Input options   ============================    #

            options = st.session_state.get("options", {})
            if not options:
                options = {}

            input_options = [
                "Select energy file from MD package*"
            ]

            st.write("The package is detected by the extension of the file entered below")

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
                        filetypes = [("EDR files", "*.edr")]

                        input_filename = filedialog.askopenfilename(
                            initialdir=wkdir,
                            title="Select energy file",
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
                log_filename = "energy_analysis_info.log"

            #   ============================    Compressed file options   ============================    #

            compressed_file_name = st.text_input("Enter the name for the output compressed file*")

            #   ============================    ENERGY ANALYSIS RUN   ============================    #

            # Button to execute the program
            if st.button("RUN"):
                energy_list_path = options.get("input_file_1", "")

                if not energy_list_path:
                    st.error("Please select energy file before running the program")
                    return

                # Save updated input files in session state
                st.session_state["options"] = options

                if not compressed_file_name:
                    st.error("Please enter the name for the output compressed file")
                    return

                if energy_list_path is not None:
                    with st.spinner("Running Energy Analysis. Please wait..."):
                        warning_container = st.warning("Do not close the interface while Energy Analysis is running.")
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Use the unique identifier to create a unique directory to the output
                            output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                            os.makedirs(output_folder)

                            # Save selected files in the temporal directory
                            energy_list_path = save_uploaded_file(energy_list_path, temp_dir)

                            # Execute the command with path files provided
                            output, error = run_energy_analysis_info(
                                energy_list_path,
                                log_filename)

                            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                            m = f"\n\t\tOutput from Energy Analysis.({now})"
                            m += f"\n\t\t{'*' * len(m)}\n"
                            m += output.decode()
                            m += error.decode()
                            print(m) if logger is None else logger.info(m)

                            st.success("Energy Analysis subprogram executed successfully!")
                            warning_container.empty()

                            #   Output list of common files
                            output_files = [
                                f"{log_filename}"
                            ]

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
                                             f'" download="{compressed_file_name}.tar.gz">'
                                             f'Download {compressed_file_name} compressed file</a>')
                            st.markdown(download_link, unsafe_allow_html=True)

                            # Show output file names
                            show_output_files_content(output_files, log_filename)

                            if st.button("RESET"):
                                st.experimental_rerun()

    #   ============================    CALCULATE OPTIONS   ============================    #

        if calculate_option:
            st.write("Fields with '*' are required")

            #   ============================    Input options   ============================    #

            options = st.session_state.get("options", {})
            if not options:
                options = {}

            input_options = [
                "Select energy file from MD package*",
                "Select path to the program to join energy files",
                "Select a list with the labels of the parameter to calculate the ACF of the time series"
                # Tendría que meterse más de un fichero
            ]

            # st.write("The package is detected by the extension of the file")
            # st.write("Example: For GROMACS -->/usr/bin/gmx")

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

                        if option == "Select energy file from MD package*":
                            filetypes = [("EDR files", "*.edr")]
                        else:
                            filetypes = [("ALL files", "*")]

                        input_filename = filedialog.askopenfilename(
                            initialdir=wkdir,
                            title="Select file or program",
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
                log_filename = "energy_analysis.log"

            #   ============================    Starting time options   ============================    #

            help_tbegin = "Example: A value of 10, start the analysis at 10ps"
            tbegin = st.number_input("Starting time (ps)", min_value=0.0, step=0.1,
                                     format="%.1f", value=None, help=help_tbegin)

            #   ============================    Ending time options   ============================    #

            help_tend = "Example: A value of 30, end the analysis at 30ps"
            tend = st.number_input("Ending time (ps)", min_value=tbegin, step=0.1,
                                   format="%.1f", value=None, help=help_tend)

            #   ============================    Group terms options   ============================    #

            groupterms = st.toggle("Group energy terms (bond, nonbond, ...)")

            #   ============================    Average options   ============================    #

            avg = st.toggle("Calculate averages from strating to ending time")

            #   ============================    Compressed file options   ============================    #

            compressed_file_name = st.text_input("Enter the name for the output compressed file*")

            #   ============================    ENERGY ANALYSIS RUN   ============================    #

            # Button to execute the program
            if st.button("RUN"):    # ValueError: Multi-dimensional indexing
                # (e.g. `obj[:, None]`) is no longer supported.
                # Convert to a numpy array before indexing instead
                energy_list_path = options.get("input_file_1", "")
                join_energy_path = options.get("input_file_2", "")
                acf_list_path = options.get("input_file_3", "")

                if not energy_list_path:
                    st.error("Please select energy file before running the program")
                    return

                # Save updated input files in session state
                st.session_state["options"] = options

                if not compressed_file_name:
                    st.error("Please enter the name for the output compressed file")
                    return

                if energy_list_path is not None:
                    with st.spinner("Running Energy Analysis. Please wait..."):
                        warning_container = st.warning("Do not close the interface while Energy Analysis is running.")
                        with tempfile.TemporaryDirectory() as temp_dir:
                            # Use the unique identifier to create a unique directory to the output
                            output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                            os.makedirs(output_folder)

                            # Save selected files in the temporal directory
                            energy_list_path = save_uploaded_file(energy_list_path, temp_dir)
                            join_energy_path = save_uploaded_file(join_energy_path,
                                                                  temp_dir) if join_energy_path else None
                            acf_list_path = save_uploaded_file(acf_list_path,
                                                               temp_dir) if acf_list_path else None

                            # Execute the command with path files provided
                            output, error = run_energy_analysis_calc(
                                energy_list_path, log_filename, tbegin, tend,
                                join_energy_path, groupterms, avg, acf_list_path)

                            now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                            m = f"\n\t\tOutput from Energy Analysis.({now})"
                            m += f"\n\t\t{'*' * len(m)}\n"
                            m += output.decode()
                            m += error.decode()
                            print(m) if logger is None else logger.info(m)

                            st.success("Energy Analysis subprogram executed successfully!")
                            warning_container.empty()

                            # Output common directories
                            output_directories = 'individual_energy'
                            if not os.path.exists(output_directories):
                                os.makedirs(output_directories)

                            #   Output list of common files
                            output_files = [
                                f"{log_filename}"
                            ]

                            #   PROBLEMS WITH others output files

                            # When use --joinpath options, include this aditional file
                            if join_energy_path:
                                output_files.extend([
                                    "united_edr.edr"
                                ])

                            if groupterms:
                                output_directories_add = ['grouped_energy', 'grouped_density']
                                for directory in output_directories_add:
                                    if not os.path.exists(directory):
                                        os.makedirs(directory)
                                output_files.extend(
                                    output_directories_add)

                            if acf_list_path:
                                output_directories.append('individual_acf')
                                output_files.extend([
                                    "acf_data.dat"
                                ])

                            output_files.append(output_directories)

                            # Move generated files to the output directory
                            for filename in os.listdir(temp_dir):
                                filepath = os.path.join(temp_dir, filename)
                                if os.path.isfile(filepath):
                                    shutil.move(filepath, os.path.join(output_folder, filename))

                            output_files.append(output_directories)  # Add directories
                            # output_files.append(output_directories_add)

                            # Build compressed file '.tar.gz' of the output files
                            tar_file_path = create_tar_gz(output_folder, output_files)

                            # Generate download link to the compressed output files
                            download_link = (f'<a href="data:application/tar+gzip;base64,'
                                             f'{base64.b64encode(open(tar_file_path, "rb").read()).decode()}'
                                             f'" download="{compressed_file_name}.tar.gz">'
                                             f'Download {compressed_file_name} compressed file</a>')
                            st.markdown(download_link, unsafe_allow_html=True)

                            # Show output file names
                            show_output_files_content(output_files, log_filename)

                            if st.button("RESET"):
                                st.experimental_rerun()


def run_page_energy_analysis():

    func_page_energy_analysis()
