import streamlit as st
import os
import tarfile
import shutil
import paramiko
import tempfile
from tkinter import filedialog
from functions.replicate_polymer.replicate_func import reset_replicate_options
from functions.topology.topology_func import reset_topology_options
from stmol import render_pdb, showmol


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


def upload_file_to_server(ssh, local_path, remote_path):
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()


def create_tar_gz(output_folder, output_file_paths):
    temp_tar_path = os.path.join(output_folder, "output_files.tar.gz")
    with tarfile.open(temp_tar_path, "w:gz") as tar:
        for file_path in output_file_paths:
            if os.path.exists(file_path):
                tar.add(file_path, arcname=os.path.basename(file_path))
            else:
                print(f"Warning: File not found - {file_path}")
    if os.path.exists(temp_tar_path):
        return temp_tar_path
    else:
        return None


def clean_options(program):
    if st.button("Clean all program options"):
        if program == "Topology":
            reset_topology_options()
            st.rerun()
        if program == "Replicate Polymer":
            reset_replicate_options()
            st.rerun()


def get_host_name(name_server, name_user, ssh_key_options):  # At the moment, we are not using it
    command = "hostname"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    stdin, stdout, stderr = ssh.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()
    ssh.close()
    return output, error


def print_pdb_content(pdb_path):
    with open(pdb_path, "r") as file:
        content = file.read()
        st.text_area("PDB File Content", content, height=200)


def handle_button_click_visualization(option, input_key, action):
    if action == "browse":
        visual_selection_options(option, input_key)
    elif action == "remove":
        st.session_state["input_visual"][input_key] = ""
        st.experimental_rerun()


def visual_selection_options(option, input_key):
    wkdir = os.getcwd()
    if option == "Enter a file to see the molecule (PDB or GRO)":
        filetypes = [("PDB files", "*.pdb"), ("GRO files", "*.gro")]

    input_filename = filedialog.askopenfilename(
        initialdir=wkdir,
        title="Select a file",
        filetypes=filetypes
    )

    if input_filename:
        st.session_state["input_visual"][input_key] = input_filename
        st.experimental_rerun()


def see_molecular_structure(input_visual_files):
    input_visual = st.session_state.get("input_visual", {})
    if not input_visual:
        input_visual = {}

    for index, option in enumerate(input_visual_files):
        input_key = "input_visual_file_{0:03d}".format(index)
        if input_key not in input_visual:
            input_visual[input_key] = ""

        st.text_input(
            option,
            input_visual[input_key],
            key=f"{input_key}_input_text"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Browse file", key=f"browse_{input_key}"):
                handle_button_click_visualization(option, input_key, "browse")

        with col2:
            if input_visual[input_key]:
                if st.button("Remove file", key=f"remove_{input_key}"):
                    handle_button_click_visualization(option, input_key, "remove")

    st.session_state["input_visual"] = input_visual

    button_visual = st.button("See molecule")
    if button_visual:
        visor_file_path = input_visual.get("input_visual_file_000", "")

        if not visor_file_path:
            st.error("Please enter a PDB or GRO file for visualization")
            return

        st.session_state["input_visual"] = input_visual

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdb") as tmp_file:
            with open(visor_file_path, "rb") as file:
                tmp_file.write(file.read())
            pdb_path = tmp_file.name

        if os.path.exists(pdb_path):
            st.markdown("### 3D Structure of the Molecule")
            # Imprime el contenido del archivo PDB para verificar que no esté vacío o corrompido
            print_pdb_content(pdb_path)

            # Renderiza el archivo PDB
            try:
                xyzview = render_pdb(pdb_path)
                showmol(xyzview, height=500, width=800)
            except Exception as e:
                st.error(f"Error rendering PDB file: {e}")
        else:
            st.error("PDB file not found for visualization")
