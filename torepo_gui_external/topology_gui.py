import streamlit as st
import glob
import os
import logging
import shutil
import tempfile
import json
import paramiko
from torepo_functions import (save_uploaded_file, upload_file_to_server,
                              create_tar_gz, ensure_json_extension,
                              save_options_to_json)
from tkinter import filedialog


# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_topology_cmd_remote(name_server, name_user, ssh_key_options, path_virtualenv,
                            input_file, renumber_pdb, assign_residues, filemap,
                            separate_chains, pattern, isunwrap, guess_improper):

    activate_virtualenv = f"source {path_virtualenv}"

    command = f"topology_cmd -i /tmp/{os.path.basename(input_file)}"

    if renumber_pdb:
        command += f" -r /tmp/{os.path.basename(renumber_pdb)}"
    if assign_residues:
        command += f" -a /tmp/{os.path.basename(assign_residues)}"
    if filemap:
        command += f" --filemap /tmp/{os.path.basename(filemap)}"
    if separate_chains:
        command += " --separate_chains"
    if pattern:
        command += f" -p /tmp/{pattern}"
    if isunwrap:
        command += " -w"
    if guess_improper:
        command += " --guess_improper"

    full_command = f"{activate_virtualenv} && {command}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    # Upload input files to the remote server
    upload_file_to_server(ssh, input_file, f"/tmp/{os.path.basename(input_file)}")

    if renumber_pdb:
        upload_file_to_server(ssh, renumber_pdb, f"/tmp/{os.path.basename(renumber_pdb)}")

    if assign_residues:
        upload_file_to_server(ssh, assign_residues, f"/tmp/{os.path.basename(assign_residues)}")

    if filemap:
        upload_file_to_server(ssh, filemap, f"/tmp/{os.path.basename(filemap)}")

    # Ejecuta el comando en el servidor remoto
    stdin, stdout, stderr = ssh.exec_command(full_command)

    # Lee la salida y los errores del comando
    output = stdout.read().decode()
    error = stderr.read().decode()

    # Descargar archivos generados desde el servidor remoto
    sftp = ssh.open_sftp()
    output_folder = "output_files"  # Carpeta local para almacenar los archivos descargados DEBE IRSE AL REMOTO
    os.makedirs(output_folder, exist_ok=True)

    # Lista de archivos a descargar (puedes ajustar esta lista según lo que genere tu comando)
    output_files = [f"{pattern}.pdb", "InfoTopology.log"]

    if assign_residues:
        output_files.extend([f"{pattern}_residues.gro", f"{pattern}_residues.pdb", f"{pattern}_residues.psf"])

    if renumber_pdb and not assign_residues:
        output_files.extend([f"{pattern}_renumber.gro", f"{pattern}_renumber.pdb", f"{pattern}_renumber.psf"])

    if separate_chains:
        # Correct the method to get the separate chains files
        separate_chains_files = sftp.listdir('/tmp')
        separate_chains_files = [f for f in separate_chains_files if f.startswith(pattern) and f.endswith('.pdb')]
        output_files.extend(separate_chains_files)

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

    # Cierra la conexión SSH
    ssh.close()

    return output, error, output_folder  # Agregar output_folder para devolver la ruta de los archivos descargados


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


def func_page_topology():

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

    st.markdown("<h1 style='font-size:32px;'>Topology</h1>", unsafe_allow_html=True)

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

    #   ============================    Topology options   ============================    #

    st.markdown("<h1 style='font-size:22px;'>Program options</h1>", unsafe_allow_html=True)

    st.write("Fields with '*' are required")

    input_file = st.file_uploader("Choose input file*", type=["xsd", "pdb", "mol2"])
    renumber_pdb = st.file_uploader("Choose file for renumbering residues (optional)", type=["dat"])
    assign_residues = st.file_uploader("Choose file for assign residues (optional)", type=["dat"])
    filemap = st.file_uploader("Choose filemap (optional)", type=["dat"])
    separate_chains = st.toggle("Separate chains", value=False)

    pattern = st.text_input("Pattern")
    if pattern.strip() == "":
        pattern = "topology"

    isunwrap = st.toggle("Isunwrap", value=False)
    guess_improper = st.toggle("Guess improper", value=False)
    # remote_output_dir = st.text_input("Enter the server path to save output files*")

    #   ============================    TOPOLOGY RUN   ============================    #

    # Button to launch the topology command
    button_run = st.button("Run Topology")
    if button_run:
        # Ensure required inputs are provided
        if not input_file:
            st.error("Please provide all required inputs")
        else:
            # Save uploaded files to a temporary directory
            temp_dir = tempfile.mkdtemp()
            try:
                input_file_path = save_uploaded_file(input_file, temp_dir)
                renumber_pdb_path = save_uploaded_file(renumber_pdb, temp_dir) if renumber_pdb else None
                assign_residues_path = save_uploaded_file(assign_residues, temp_dir) if assign_residues else None
                filemap_path = save_uploaded_file(filemap, temp_dir) if filemap else None

                # Run the topology command remotely
                output, error, output_folder = run_topology_cmd_remote(name_server, name_user, ssh_key_options,
                                                                       path_virtualenv, input_file_path,
                                                                       renumber_pdb_path,
                                                                       assign_residues_path, filemap_path,
                                                                       separate_chains,
                                                                       pattern, isunwrap, guess_improper)

                st.subheader("InfoTopology.log")
                st.text_area("Output:", output, height=150)
                st.text_area("Error:", error, height=150)

                # Find all output files in the output folder
                output_file_paths = glob.glob(os.path.join(output_folder, "*"))

                if output_file_paths:
                    show_info_topology_content(output_file_paths)

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


def run_page_topology():
    func_page_topology()
