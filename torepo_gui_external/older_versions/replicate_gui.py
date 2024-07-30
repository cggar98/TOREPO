import streamlit as st
import os
import logging
import shutil
import tempfile
import glob
import json
import paramiko
from tkinter import filedialog
from functions.common.common_functions import (upload_file_to_server,
                              create_tar_gz)
from functions.server_options.server_options_functions import ensure_json_extension, save_options_to_json


# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Logger configuration impropers file
logging.basicConfig(level=logging.INFO)
improper_logger = logging.getLogger(__name__)


def save_uploaded_file(uploaded_file, directory):
    """Save uploaded file to the specified directory."""
    if isinstance(uploaded_file, str):
        # If uploaded_file is a string, it's already a path
        file_path = uploaded_file
    else:
        # If uploaded_file is an uploaded file object
        file_path = os.path.join(directory, uploaded_file.name)
        with open(file_path, "wb") as f:
            shutil.copyfileobj(uploaded_file.file, f)

    return file_path


def run_replicate_cmd_remote(name_server, name_user, ssh_key_options, path_virtualenv,
                             structure_file, xml_file,
                             image_x, image_y, image_z,
                             mdengine, noh, index,
                             boxlength_a, boxlength_b, boxlength_c,
                             boxangle_alpha, boxangle_beta, boxangle_gamma,
                             impropers, npairs, verbose):

    activate_virtualenv = f"source {path_virtualenv}"

    command = (f"replicate_polymer -p /tmp/{os.path.basename(structure_file)} "
               f"-f /tmp/{os.path.basename(xml_file)} "
               f"--images /tmp/{os.path.basename(image_x)} "
               f"/tmp/{os.path.basename(image_y)} "
               f"/tmp/{os.path.basename(image_z)}")

    if mdengine:
        command += f" -e /tmp/{os.path.basename(mdengine)}"
    if noh:
        command += " --noh"
    if index:
        command += f" --index /tmp/{os.path.basename(index)}"
    if boxlength_a and boxlength_b and boxlength_c:
        command += (f" --boxlength /tmp/{os.path.basename(boxlength_a)} "
                    f"/tmp/{os.path.basename(boxlength_b)} "
                    f"/tmp/{os.path.basename(boxlength_c)}")
    if boxangle_alpha and boxangle_beta and boxangle_gamma:
        command += (f" --boxangle /tmp/{os.path.basename(boxangle_alpha)} "
                    f"/tmp/{os.path.basename(boxangle_beta)} "
                    f"/tmp/{os.path.basename(boxangle_gamma)}")
    if impropers:
        command += f" --impropers /tmp/{os.path.basename(impropers)}"
    if npairs:
        command += f" --npairs /tmp/{os.path.basename(npairs)}"
    if verbose:
        command += " --verbose"

    full_command = f"{activate_virtualenv} && {command}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    # Upload input files to the remote server
    upload_file_to_server(ssh, structure_file, f"/tmp/{os.path.basename(structure_file)}")
    upload_file_to_server(ssh, xml_file, f"/tmp/{os.path.basename(xml_file)}")

    if impropers:
        upload_file_to_server(ssh, impropers, f"/tmp/{os.path.basename(impropers)}")

    # Run command within remote server
    stdin, stdout, stderr = ssh.exec_command(full_command)

    # Read command's output and errors
    output = stdout.read().decode()
    error = stderr.read().decode()

    # Download generated files from remote server
    sftp = ssh.open_sftp()
    output_folder = "output_files"  # YOU MUST MAKE A DIRECTORY IN THE REMOTE SERVER!!!
    os.makedirs(output_folder, exist_ok=True)

    # Files list to download
    output_files = ["allatom_idx_replicate.dat",
                    "backbone_idx_replicate.dat",
                    "listendtoend_replicate.dat",
                    "Info.log"]
    # ESTO PUEDE RESULTAR ÚTIL
    structure_file_name = os.path.splitext(os.path.basename(structure_file))[0]

    if noh:
        if not mdengine:
            output_files.extend([f"{structure_file_name}_noH.gro",
                                 f"{structure_file_name}_noH.pdb",
                                 f"{structure_file_name}_noH.top",
                                 f"{structure_file_name}_noH_replicate.gro",
                                 f"{structure_file_name}_noH_replicate.pdb",
                                 f"{structure_file_name}_noH_replicate.top"])
        else:
            output_files.extend([f"{structure_file_name}_noH_replicate_clean.inp",
                                 f"{structure_file_name}_noH_replicate_clean.lmp",
                                 f"{structure_file_name}_noH.gro",
                                 f"{structure_file_name}_noH.pdb",
                                 f"{structure_file_name}_noH.top",
                                 f"{structure_file_name}_noH_replicate.gro",
                                 f"{structure_file_name}_noH_replicate.pdb",
                                 f"{structure_file_name}_noH_replicate.top"])

    # Check and download each output file
    for file in output_files:
        remote_file_path = f"/tmp/{file}"
        local_file_path = os.path.join(output_folder, file)
        try:
            sftp.stat(remote_file_path)  # Check if the file exists
            sftp.get(remote_file_path, local_file_path)
        except FileNotFoundError:
            logger.error(f"File not found: {file}")

    sftp.close()

    # Close ssh conection
    ssh.close()

    return output, error, output_folder


def run_bash_remote(name_server, name_user, ssh_key_options, path_virtualenv, input_sh_file_path):

    activate_virtualenv = f"source {path_virtualenv}"

    command = f"bash /tmp/{os.path.basename(input_sh_file_path)}"

    full_command = f"{activate_virtualenv} && {command}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    # Upload input files to the remote server
    upload_file_to_server(ssh, input_sh_file_path, f"/tmp/{os.path.basename(input_sh_file_path)}")

    # Run command within remote server
    stdin, stdout, stderr = ssh.exec_command(full_command)

    # Read command's output and errors
    output = stdout.read().decode()
    error = stderr.read().decode()

    # Download generated files from remote server
    sftp = ssh.open_sftp()
    output_folder = "output_files"  # YOU MUST MAKE A DIRECTORY IN THE REMOTE SERVER!!!
    os.makedirs(output_folder, exist_ok=True)

    # Files list to download
    output_files = ["impropers.ndx"]

    # Check and download each output file
    for file in output_files:
        remote_file_path = f"/tmp/{file}"
        local_file_path = os.path.join(output_folder, file)
        try:
            sftp.stat(remote_file_path)  # Check if the file exists
            sftp.get(remote_file_path, local_file_path)
        except FileNotFoundError:
            logger.error(f"File not found: {file}")

    sftp.close()

    # Close ssh connection
    ssh.close()

    return output, error, output_folder


def show_info_log_content(output_file_paths):

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


# ToDo: How to visualize molecules: VMD or JSMol?


def func_page_replicate():

    #   ============================    Server options   ============================    #

    st.sidebar.subheader("Server options")
    st.sidebar.write("Fields with '*' are required")

    options = st.session_state.get("options", {
        "Name Server*": "",
        "Username*": "",
        "Key SSH file path*": ""
    })

    name_server = st.sidebar.text_input("Name Server*", options.get("Name Server*", ""), key="name_server")
    name_user = st.sidebar.text_input("Username*", options.get("Username*", ""))
    ssh_key_options = st.sidebar.text_input("Key SSH file path*", options.get("Key SSH file path*", ""))
    path_virtualenv = st.sidebar.text_input("Virtual environment path*", options.get("Virtual environment path*", ""))

    #   ============================    JSON loaded and saved options   ============================    #

    # Buttons for save and load JSON format
    col1, col2 = st.columns(2)

    with col1:
        tip_filename = "Enter a filename for save server options"
        json_filename = st.sidebar.text_input("Save server options:", key="json_filename", help=tip_filename)

        if json_filename.strip() and name_server and name_user and ssh_key_options and path_virtualenv:
            json_filename = ensure_json_extension(json_filename.strip())
            options = save_options_to_json(name_server, name_user, ssh_key_options, path_virtualenv, json_filename)
            button_download = st.sidebar.download_button(label="Save", data=options,
                                                         file_name=json_filename,
                                                         mime="application/json")
            if button_download:
                st.sidebar.success(f"File saved successfully as '{json_filename}'")

    with col2:
        tip_browse = "Upload a file for load server options"
        input_placeholder = st.sidebar.empty()
        input_placeholder.text_input("Load server options:", key="json_filepath",
                                     help=tip_browse)
        browse_load_file = st.sidebar.button("Browse", key="browse_load")
        if browse_load_file:
            wkdir = os.getcwd()
            filename = filedialog.askopenfilename(initialdir=wkdir,
                                                  title="Select a file containing a server options",
                                                  filetypes=[("JSON files", "*.json")])
            if filename:
                json_filepath = filename
                input_placeholder.text_input("Load server options (optional):", key="json_input",
                                             value=json_filepath,
                                             help=tip_browse)
                st.sidebar.success("File selected successfully")

                button_load = st.sidebar.button("Load")
                if button_load is not None:
                    if json_filepath:
                        try:
                            with open(json_filepath, "r") as f:
                                options = json.load(f)
                            if options:
                                name_server = options.get("Name Server*", "")
                                name_user = options.get("Username*", "")
                                ssh_key_options = options.get("Key SSH file path*", "")
                                path_virtualenv = options.get("Virtual environment path*", "")
                                st.session_state.options = {"Name Server*": name_server,
                                                            "Username*": name_user,
                                                            "Key SSH file path*": ssh_key_options,
                                                            "Virtual environment path*": path_virtualenv}
                        except Exception as e:
                            st.error(f"Error loading file: {str(e)}")

    #   ============================    Welcome program   ============================    #

    st.markdown("<h1 style='font-size:32px;'>Replicate Polymer</h1>", unsafe_allow_html=True)

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

    #   ============================    Replicate options   ============================    #

    st.markdown("<h1 style='font-size:22px;'>Program options</h1>", unsafe_allow_html=True)

    st.write("Fields with '*' are required")

    structure_file = st.file_uploader("Select a pdb file containing the structure to be replicated*", type=["pdb"])
    xml_file = st.file_uploader("Select a forcefield*", type=["xml"])
    impropers = st.file_uploader("Select impropers file", type=["ndx"])

    #   ============================    Generate impropers file   ============================    #

    without_impropers = st.radio("Do you need an impropers file?", ["Yes", "No"])
    need_impropers = (without_impropers == "Yes")
    if need_impropers:
        input_sh_file = st.file_uploader("Select a bash script to generate an impropers file*", type=["sh"])

        # Button to launch the bash command
        button_sh_run = st.button("Generate impropers file")
        if button_sh_run:
            # Ensure required 'input_sh_file' are provided
            if not input_sh_file:
                st.error("Please select a bash script to generate an impropers file")
            else:
                # Save uploaded file to a temporary directory
                temp_dir = tempfile.mkdtemp()
                try:
                    input_sh_file_path = save_uploaded_file(input_sh_file, temp_dir)

                    # Run the bash command remotely
                    output, error, output_folder = run_bash_remote(name_server, name_user,
                                                                   ssh_key_options, path_virtualenv,
                                                                   input_sh_file_path)

                    # Find 'impropers.ndx' in the output folder
                    output_file_paths = glob.glob(os.path.join(output_folder, "*"))

                    if output_file_paths:

                        # Create .tar.gz of 'impropers.ndx'
                        tar_gz_path = create_tar_gz(output_folder, output_file_paths)
                        if tar_gz_path:
                            with open(tar_gz_path, "rb") as f:
                                btn = st.download_button(
                                    label="Download 'impropers.ndx'",
                                    data=f,
                                    file_name="impropers.tar.gz",
                                    mime="application/gzip"
                                )
                                if btn:  # HASTA AQUI FUNCIONA #
                                    st.success("'impropers.ndx' downloaded successfully!")
                        else:
                            st.error("Failed to create .tar.gz of output file.")
                    else:
                        st.error("No output file found.")

                finally:
                    shutil.rmtree(temp_dir)  # Clean up temporary directory

    #   ============================    Images options   ============================    #

    # Mandatory entry for --images image_x image_y image_z
    image_x = st.number_input("Number of images to replicate in dimension X*", min_value=1, step=1, value=1)
    image_y = st.number_input("Number of images to replicate in dimension Y*", min_value=1, step=1, value=1)
    image_z = st.number_input("Number of images to replicate in dimension Z*", min_value=1, step=1, value=1)

    #   ============================    Index options   ============================    #

    index = st.text_input("Indices of atoms to be removed from the PDB")

    #   ============================    Boxlength options   ============================    #

    boxlength_a = st.number_input("Box length (a) in nanometers", min_value=0.0, step=0.1, value=None)
    boxlength_b = st.number_input("Box length (b) in nanometers", min_value=0.0, step=0.1, value=None)
    boxlength_c = st.number_input("Box length (c) in nanometers", min_value=0.0, step=0.1, value=None)

    #   ============================    Boxangle options   ============================    #

    boxangle_alpha = st.number_input("Box angle (alpha) in degrees", min_value=0.0, step=0.1, value=None)
    boxangle_beta = st.number_input("Box angle (beta) in degrees", min_value=0.0, step=0.1, value=None)
    boxangle_gamma = st.number_input("Box angle (gamma) in degrees", min_value=0.0, step=0.1, value=None)

    #   ============================    npairs options   ============================    #

    npairs_help = ("A value of 1 indicates that only non-bonded interactions between "
                   "the current residue (i) and the nearest-neighbours are taken into account (i-1, i and i+1)")
    npairs = st.number_input("Monomer or residue inclusions", step=1, value=None, help=npairs_help)

    #   ============================    mdengine options   ============================    #

    mdengine = st.text_input("MD package to perform calculations")

    #   ============================    noh options   ============================    #

    noh = st.toggle("Remove hydrogens for a united atom representation")

    #   ============================    Verbose options   ============================    #

    verbose = st.toggle("Verbose checking of angles and dihedral")

    #   ============================    REPLICATE RUN   ============================    #

    # Button to launch the topology command
    button_run = st.button("Run Replicate Polymer")
    if button_run:
        # Ensure required inputs are provided
        if not structure_file:
            st.error("Please upload a pdb file structure before running the program")
        if not xml_file:
            st.error("Please upload a forcefield file before running the program")
        if not image_x:
            st.error("Please enter the number of images to Replicate in Dimension X")
        if not image_y:
            st.error("Please enter the number of images to Replicate in Dimension Y")
        if not image_z:
            st.error("Please enter the number of images to Replicate in Dimension Z")
        if not (isinstance(image_x, int) and image_x >= 1 and image_x % 1 == 0 and
                isinstance(image_y, int) and image_y >= 1 and image_y % 1 == 0 and
                isinstance(image_z, int) and image_z >= 1 and image_z % 1 == 0):
            st.error("Please enter valid integer values greater than or equal "
                     "to 1 for Number of Images before running the program")
        else:
            # Save uploaded files to a temporary directory
            temp_dir = tempfile.mkdtemp()
            try:
                structure_file_path = save_uploaded_file(structure_file, temp_dir)
                xml_file_path = save_uploaded_file(xml_file, temp_dir)
                impropers_path = save_uploaded_file(impropers, temp_dir) if impropers else None

                # Run the replicate command remotely
                output, error, output_folder = run_replicate_cmd_remote(name_server, name_user, ssh_key_options,
                                                                        path_virtualenv, structure_file_path,
                                                                        xml_file_path, impropers_path,
                                                                        image_x, image_y, image_z, mdengine, noh, index,
                                                                        boxlength_a, boxlength_b, boxlength_c,
                                                                        boxangle_alpha, boxangle_beta, boxangle_gamma,
                                                                        npairs, verbose)

                st.subheader("Info.log")
                st.text_area("Output:", output, height=150)
                st.text_area("Error:", error, height=150)

                # Find all output files in the output folder
                output_file_paths = glob.glob(os.path.join(output_folder, "*"))

                if output_file_paths:
                    show_info_log_content(output_file_paths)

                    # Create .tar.gz of output files
                    tar_gz_path = create_tar_gz(output_folder, output_file_paths)

                    if tar_gz_path:
                        with open(tar_gz_path, "rb") as f:
                            btn = st.download_button(
                                label="Download output files (tar.gz)",
                                data=f,
                                file_name="output_files.tar.gz",
                                mime="application/gzip"
                            )
                            if btn:  # HASTA AQUI FUNCIONA #
                                st.success("Output files downloaded successfully!")
                    else:
                        st.error("Failed to create .tar.gz of output files.")
                else:
                    st.error("No output files found.")

            finally:
                shutil.rmtree(temp_dir)  # Clean up temporary directory


def run_page_replicate():
    func_page_replicate()
