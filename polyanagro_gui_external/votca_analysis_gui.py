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


def run_votca_analysis(path_steps, begin_step, temp_k,
                     end_step, dir_tmp, log_filename, press_path):
    bash_command = f"votca_analysis -p {path_steps}"

    if begin_step:
        bash_command += f" -b {begin_step}"
    if temp_k:
        bash_command += f" -t {temp_k}"
    if end_step:
        bash_command += f" -e {end_step}"
    if dir_tmp:
        bash_command += " --tmpdir"
    if log_filename:
        bash_command += f" --log {log_filename}"
    if press_path:
        bash_command += f" --press {press_path}"

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


def func_page_votca_analysis():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>VOTCA Analysis</h1>", unsafe_allow_html=True)

    # Displaying the welcome text
    st.text("""
    ***********************************************************************
                           Votca Analysis Tool
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

        # Displaying mandatory subprogram options in the interface
        st.subheader("Essentials")

        path_steps = st.text_input("Select path to the directory containing the step_* folders")

        # ===========================================

        # Non-mandatory options (conditionally present)
        st.subheader("Optional")

        begin_step = st.number_input("Select the begin step", min_value=0, step=1, value=0)

        # ===========================================

        temp_k = st.number_input("Select a temperature (K)", min_value=0.0, step=0.01, value=500.0)

        # ===========================================

        end_step = st.number_input("Select the end step (By default the last one presents in the path folder)", step=1)

        # ===========================================

        dir_tmp = st.checkbox("Create a temporal directory where png of each step is stored")

        # ===========================================

        log_filename = st.text_input("Name of the file to write logs from this command")

        if log_filename.strip() == "":
            log_filename = "votca_analysis.log"

        # ===========================================

        press_path = st.text_input("Select path to GROMACS command to extract pressure from edr files in each step")

        # ===========================================

        compressed_file_name = st.text_input("Enter the name for the output compressed file")

        # Button to execute the subprogram with the select options
        if st.button("RUN"):
            if not path_steps:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please select a path to the directory containing the step_* folders before running the subprogram.</p>',
                            unsafe_allow_html=True)
                return

            if not compressed_file_name:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please enter the name for the output compressed file.</p>',
                            unsafe_allow_html=True)
                return

            if path_steps is not None:
                with st.spinner("Running Votca Analysis. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Votca Analysis is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique folder
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        output, error = run_votca_analysis(
                            path_steps, begin_step, temp_k,
                            end_step, dir_tmp, log_filename, press_path
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Votca Analysis.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Votca Analysis Subprogram executed successfully!")
                        st.success("Output files generated")
                        warning_container.empty()

                        #   Output list of common files
                        output_files = [
                            f"{log_filename}"
                        ]
                        #   ====    CONTINUE ... NO SABES QUÉ OUTPUT SALEN  ====

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






def run_page_votca_analysis():

    func_page_votca_analysis()
