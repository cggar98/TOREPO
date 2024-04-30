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


def run_pair_distribution(traj_files, topo_format,
                          log_filename, stride, sets, dr):

    if topo_format.endswith(".tpr"):
        bash_command = f"pair_distribution -t {traj_files} --tpr {topo_format}"

    elif topo_format.endswith(".psf"):
        bash_command = f"pair_distribution -t {traj_files} --psf {topo_format}"

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


def func_page_pair_distribution():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Pair Distribution</h1>", unsafe_allow_html=True)

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

        # Displaying mandatory subprogram options in the interface
        st.subheader("Essentials")

        traj_files = st.file_uploader("Select a list of trajectories from MD simulations (XTC or TRR)",
                                      type=["xtc", "trr"],
                                      key="traj_files")

        #   =====================================

        topo_file = st.radio("Select a topology file format", ("tpr", "psf"))

        if topo_file == "tpr":
            topo_format = st.file_uploader("Upload a topology file in tpr format", type=["tpr"])
        else:
            topo_format = st.file_uploader("Upload a topology file in psf format", type=["psf"])


        # ===========================================

        # Non-mandatory options (conditionally present)
        st.subheader("Optional")

    # ===========================================

        log_filename = st.text_input("Name of the file to write logs from this command")

        if log_filename.strip() == "":
            log_filename = "pol_rdf.log"

        # ===========================================

        stride = st.number_input("Frame numbers for each stride frames", min_value=1, step=1, value=None)

        # ===========================================

        sets = st.text_input("Enter the set of atoms to calculate the g(r)",
                             help="E.g., 1-100 150-200")

        if sets.strip() == "":  #   ====    NO FUNCIONA ====    #
            sets = "all"

        # ===========================================

        dr = st.number_input("Enter the bin width for the histogram (angstroms)", step=0.1, value=None, format="%.1f")

        # ===========================================

        compressed_file_name = st.text_input("Enter the name for the output compressed file")

        # ===========================================

        # Button to execute the subprogram with the select options
        if st.button("RUN"):
            if not traj_files:
                st.markdown('<p style="color: white; background-color: rgba(255, 0, 0, 0.5); '
                            'padding: 10px; border-radius: 10px;'
                            '">Warning: Please select a list of trajectories before running the subprogram.</p>',
                            unsafe_allow_html=True)
                return

            if not topo_format:
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

            if traj_files and topo_format is not None:
                with st.spinner("Running Pair Distribution. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Pair Distribution is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique folder
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        traj_files_path = save_uploaded_file(traj_files, temp_dir)
                        topo_format_path = save_uploaded_file(topo_format, temp_dir)

                        output, error = run_pair_distribution(
                            traj_files_path,
                            topo_format_path,
                            log_filename,
                            stride,
                            sets, dr
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Pair Distribution.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Pair Distribution Subrogram executed successfully!")
                        st.success("Output files generated")
                        warning_container.empty()

                        #   Output list of common files
                        output_files = [
                            f"{log_filename}"   #   NO FILE FOUND
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


def run_page_pair_distribution():

    func_page_pair_distribution()
