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

def run_polymer_size(traj_files, topo_file, unwrap_coordinates,
                     stride, fraction_trj_average, end_to_end_distances,
                     end_to_end_acf, c2n_input, log_filename,
                     ree_rg_distributions, bond_orientation, rg_massw,
                     legendre_polynomials):

    bash_command = f"polymer_size -t {traj_files} --topo {topo_file}"

    if stride:
        bash_command += f" --stride {stride}"
    if fraction_trj_average:
        bash_command += f" --fraction_trj_avg {fraction_trj_average}"
    if end_to_end_distances:
        bash_command += f" --e2e {end_to_end_distances}"
    if end_to_end_acf:
        bash_command += " --e2acf"
    if c2n_input:
        bash_command += f" --c2n {c2n_input}"
    if log_filename:
        bash_command += f" --log {log_filename}"
    if ree_rg_distributions:
        bash_command += " -d"
    if bond_orientation:
        bash_command += " --bondorientation"
    if unwrap_coordinates:
        bash_command += " --unwrap True"
    else:
        bash_command += " --unwrap False"

    if rg_massw:
        bash_command += " --rg_massw"
    if legendre_polynomials:
        bash_command += " --isodf"

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


def func_page_polymer_size():

    # Create a unique identifier for this run
    unique_id = str(int(time.time()))

    st.markdown("<h1 style='font-size:24px;'>Polymer Size</h1>", unsafe_allow_html=True)

    #	Displaying the welcome text
    st.text("""
    ***********************************************************************
                         Polymer size calculations
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
                        edited_content = st.text_area("Edit the content below:", value=file.read().decode("latin-1"),
                                                      height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_topo_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_topo_file")
                        save_filename = st.text_input("Enter the name of the edited file:", key="Enter_name_topo_file")

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
        #   AL SELECCIONAR ESTA OPCIÓN, PARECE COMO SI COGISE UNA PREVIA EJECUCIÓN

        #   =====================================

        # Non-mandatory options (conditionally present)
        st.subheader("Optional")

        stride = st.number_input("Frame numbers for each stride frames", min_value=1, step=1, value=None)
            #   AL SELECCIONAR ESTA OPCIÓN, PARECE COMO SI COGISE UNA PREVIA EJECUCIÓN

        #   =====================================

        fraction_trj_average = st.number_input("Fraction of the trajectory to calculate the averages", min_value=0.0, max_value= 1.0, step=0.01, value=None)

        #   =====================================

        end_to_end_distances = st.file_uploader("Select a file for calculate the end to end distances",
                                                help="The format of the files must be a line for chain (ich ihead itail).The index must start in zero.",
                                                type=["txt", "dat", "csv"], key="end_to_end_distances_file")

        if not end_to_end_distances:
            st.write("Example:")

            example_content = """
            #ich ihead itail (indexes start at 0)
            0 1 608
            1 615 1222
            2 1229 1836
            3 1843 2450
            ...
            """

            # Show st.code content
            st.code(example_content)

        # Displaying the content of the end_to_end_distances file right after loading it
        if end_to_end_distances is not None:
            edit_content_key = "edit_content_end_to_end_distances_file"
            edit_content = st.checkbox("Edit content", key=edit_content_key)

            # Getting the original file name
            if edit_content:
                with tempfile.TemporaryDirectory() as temp_dir:
                    file_path = save_uploaded_file(end_to_end_distances, temp_dir)
                    edited_content = st.text_area("Edit the content below:", value=open(file_path, "r").read(),
                                                  height=300)

                    # State variable to control the visibility of the boxes
                    show_save_options = st.checkbox("Show save options", key="show_save_options_end_to_end_distances_file")

                    if show_save_options:
                        # Asking the user for the path and file name to save
                        save_path = st.text_input("Enter the path to save the edited file:",
                                                  key="Enter_path_end_to_end_distances_file")
                        save_filename = st.text_input("Enter the name of the edited file:", key="Enter_name_end_to_end_distances_file")

                        # Checking if both the path and the file name are specified
                        if save_path and save_filename:
                            # Here you can save 'edited_content' with the specified path and name
                            save_content_key = "save_content_end_to_end_distances_file"
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

        end_to_end_acf = st.checkbox("Calculate the end to end autocorrelation function")
            #   AL SELECCIONAR ESTA OPCIÓN, PARECE COMO SI COGISE UNA PREVIA EJECUCIÓN

        #   =====================================

        c2n_input = st.file_uploader("Data to calculate the Cn of a polymer (THIS OPTION EN PROGRESS...)")
                                 #help="Enter the data for --c2n LISTBB. It can be a pdb file template or a file with labels and backbone atoms.")

        # Show example and description
        #st.write("Example:")
        #st.code("1\n[ mol01 ]\nbackbone_atom_1\nbackbone_atom_2\n...")

        #st.write("Data to calculate the Cn of a polymer.")

        #   =====================================

        log_filename = st.text_input("Name of the file to write logs from this command")

        if log_filename.strip() == "":
            log_filename = "pol_size.log"

        #   =====================================

        ree_rg_distributions = st.checkbox("Calculate Ree and Rg distributions")
            #   PROGRAM_ERROR

        #   =====================================

        bond_orientation = st.checkbox("Calculate intermolecular bond orientation")

        #   =====================================

        rg_massw = st.checkbox("Calculate the mass weighted radius of gyration")

        #   =====================================

        legendre_polynomials = st.checkbox("Calculate 1st and 2nd Legendre polynomials for"
                                           " the correlation between bonds in a polymer chain")

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
                with st.spinner("Running Polymer Size. Please wait..."):
                    warning_container = st.warning("Do not close the interface while Polymer Size is running.")
                    with tempfile.TemporaryDirectory() as temp_dir:
                        # Use the unique identifier to create a unique folder
                        output_folder = os.path.join(temp_dir, f"output_{unique_id}")
                        os.makedirs(output_folder)

                        traj_files_path = save_uploaded_file(traj_files, temp_dir)
                        topo_file_path = save_uploaded_file(topo_file, temp_dir)
                        end_to_end_distances_path = save_uploaded_file(end_to_end_distances, temp_dir) if end_to_end_distances else None
                        c2n_input_path = save_uploaded_file(c2n_input, temp_dir) if c2n_input else None

                        output, error = run_polymer_size(
                            traj_files_path,
                            topo_file_path,
                            end_to_end_distances_path,
                            c2n_input_path,
                            unwrap_coordinates,
                            stride, fraction_trj_average, end_to_end_acf, log_filename,
                            ree_rg_distributions, bond_orientation, rg_massw, legendre_polynomials
                        )

                        now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                        m = f"\n\t\tOutput from Polymer Size.({now})"
                        m += f"\n\t\t{'*' * len(m)}\n"
                        m += output.decode()
                        m += error.decode()
                        print(m) if logger is None else logger.info(m)

                        st.success("Polymer Size Subprogram executed successfully!")
                        st.success("Output files generated")
                        warning_container.empty()

                        #   Output common files
                        output_files = [
                            f"{log_filename}",
                            "gnuplot_charratio.gnu", "gnuplot_dimensions.gnu",
                            "gnuplot_distributions.gnu", "Rg.dat"
                        ]

                        # If end_to_end_distances file is activated, include these aditional files
                        if end_to_end_distances_path:
                            output_files.extend([
                                "Ree2Rg2.dat",  #   not file found
                                "Ree.dat"   #   not file found
                            ])

                        # If rg_masss is activated, include these aditional files
                        if rg_massw:
                            output_files.extend([
                                "Rg_mass.dat"
                            ])


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


def run_page_polymer_size():

    func_page_polymer_size()
