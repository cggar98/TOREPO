import streamlit as st
import paramiko
import json
import subprocess
import os
from tkinter import *
from tkinter import filedialog



def ensure_json_extension(json_filename):
    #"""Función para asegurar que el nombre de archivo termine con '.json' si no lo hace."""
    if not json_filename.endswith('.json'):
        json_filename += '.json'
    return json_filename


# Función para ejecutar comandos SSH
def run_ssh_command(server, username, ssh_key, command):

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=username, key_filename=ssh_key)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return output, error
    except Exception as e:
        return None, str(e)


# Función para obtener el nombre del host
def get_host_name(server, username, ssh_key):
    command = "hostname"
    output, error = run_ssh_command(server, username, ssh_key, command)
    return output.strip() if output else None


# Función para verificar si un programa está instalado en el servidor
def check_program_installed(server, username, ssh_key, program):

    command = f"which {program}"
    output, error = run_ssh_command(server, username, ssh_key, command)
    return output.strip() if output else None


# Función para verificar programas requeridos para un comando específico
def check_required_programs(server, username, ssh_key, command):

    required_programs = {
        "List": ["ls"],
        "Currently directory": ["pwd"],
        "Hostname": ["hostname"],
        "Topology": ["topology_cmd"],
        "Replicate": ["replicate_polymer"],
        "Polyanagro": ["Polyanagro", "Subprogram1", "Subprogram2"]
    }

    if command in required_programs:
        programs = required_programs[command]
        missing_programs = []
        installed_programs = []
        for program in programs:
            result = check_program_installed(server, username, ssh_key, program)
            if result:
                installed_programs.append(program)
            else:
                missing_programs.append(program)

        return installed_programs, missing_programs

    return [], []  # Si no se especifican programas requeridos para el comando, retorna listas vacías


# Función para guardar las opciones en formato JSON
def save_options_to_json(name_server, name_user, ssh_key, json_filename):

    if not json_filename:
        return None

    options = {
        "Name Server": "{}".format(name_server),
        "Username": "{}".format(name_user),
        "Key SSH file path": "{}".format(ssh_key),
    }

    json_string = json.dumps(options, indent=4)

    return json_string


# Página del test server
def func_page_test_server():

    st.subheader("Server options")

    # Obtener opciones guardadas
    options = st.session_state.get("options", {
        "Name Server": "",
        "Username": "",
        "Key SSH file path": ""
    })

    # Entradas para las opciones del servidor
    name_server = st.text_input("Name Server", options.get("Name Server", ""), key="name_server")
    name_user = st.text_input("Username", options.get("Username", ""))

    tip_ssh_key = "Upload a file for load ssh key"
    ssh_key = st.text_input("Key SSH file path", options.get("Key SSH file path", ""), help=tip_ssh_key)

# # ####    chajkfnkjfjnfkjrfn
#     #ssh_key = st.empty()
#     ssh_key = st.text_input("Key SSH file path", options["Key SSH file path"], key="ssh_filepath", help=tip_ssh_key)
#     browse_ssh_file = st.button("Browse key ssh file", key="browse_ssh")
#     if browse_ssh_file:
#         wkdir = os.getcwd()
#         ssh_filename = filedialog.askopenfilename(initialdir=wkdir,
#                                               title="Select a file containing ssh key")
#         if ssh_filename:
#             ssh_filepath = ssh_filename
#             ssh_key = st.text_input("Key SSH file path", ssh_filepath, key="ssh_input")
#             st.success("File selected successfully")

    command_options = st.selectbox("Command for test conection:", ["List (ls -l)", "Currently directory (pwd)", "Hostname", "Another command"])

    if command_options == "Another command":
        write_another_command = st.text_input("Enter another command for test conection")

    # Botones para guardar y cargar opciones en formato JSON
    col1, col2 = st.columns(2)

    with col1:
        tip_filename = "Enter a filename for save server options"
        json_filename = st.text_input("Save server options (optional):", key="json_filename", help=tip_filename)

        if json_filename.strip():
            json_filename = ensure_json_extension(json_filename.strip())
            options = save_options_to_json(name_server, name_user, ssh_key, json_filename)
            button_download = st.download_button(label="Save", data=options,
                                                     file_name=json_filename,
                                                     mime="application/json")
            if button_download:
                st.success(f"File saved successfully as '{json_filename}'")


    #   =========================

    with col2:  ######  INSERT AUTOMATIC SERVER OPTIONS #####
        tip_browse = "Upload a file for load server options"
        input_placeholder = st.empty()
        input_placeholder.text_input("Load server options (optional):", key="json_filepath", help=tip_browse)
        browse_load_file = st.button("Browse", key="browse_load")
        if browse_load_file:
            wkdir = os.getcwd()
            filename = filedialog.askopenfilename(initialdir=wkdir,
                                                  title="Select a file containing a server options", filetypes=[("JSON files", "*.json")])
            if filename:
                json_filepath = filename
                input_placeholder.text_input("Load server options (optional):", key="json_input", value=json_filepath, help=tip_browse)
                st.success("File selected successfully")

                button_load = st.button("Load")
                if button_load is not None:
                    if json_filepath:
                        try:
                            with open(json_filepath, "r") as f:
                                options = json.load(f)
                            if options:
                                name_server = options.get("Name Server", "")
                                name_user = options.get("Username", "")
                                ssh_key = options.get("Key SSH file path", "")
                                # Actualizar opciones guardadas
                                st.session_state.options = {"Name Server": name_server, "Username": name_user, "Key SSH file path": ssh_key}
                        except Exception as e:
                            st.error(f"Error loading file: {str(e)}")

     # =========================

    if st.button("TEST"):
        if not name_server or not name_user or not ssh_key or not command_options:
            st.error("Please fill in all the fields.")
            return

        if command_options == "Another command" and not write_another_command:
            st.error("Please enter another command for test conection.")
            return

        if command_options.lower() == "list (ls -l)":
            command = "ls -l"
        elif command_options.lower() == "currently directory (pwd)":
            command = "pwd"
        elif command_options.lower() == "hostname":
            command = "hostname"
        else:
            command = write_another_command

        # Verificar programas requeridos antes de ejecutar el comando
        installed_programs, missing_programs = check_required_programs(name_server, name_user, ssh_key,
                                                                               command)
        if missing_programs:
            st.error(f"The following programs are required but not installed: {', '.join(missing_programs)}")
        else:
            output, error = run_ssh_command(name_server, name_user, ssh_key, command)
            #st.success("All required programs are installed.")

            if output:
                st.success("Command executed successfully:")
                st.code(output)
                st.sidebar.success(f"Connected to the server: {get_host_name(name_server, name_user, ssh_key)}")
            elif error:
                st.error("Error executing command:")
                st.code(error)
                st.sidebar.error("Could not connect to the server")
            else:
                st.error("Error executing command: No output or error.")
                st.sidebar.error("Could not connect to the server")


# Función para ejecutar la página del test server
def run_page_test_server():
    func_page_test_server()