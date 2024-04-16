import streamlit as st
import paramiko
import json
import subprocess
import os
from tkinter import *
from tkinter import filedialog


# Función para ejecutar comandos SSH
def run_ssh_command(server, username, key_file, command):

    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=username, key_filename=key_file)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return output, error
    except Exception as e:
        return None, str(e)


# Función para obtener el nombre del host
def get_host_name(server, username, key_file):
    command = "hostname"
    output, error = run_ssh_command(server, username, key_file, command)
    return output.strip() if output else None


# Función para verificar si un programa está instalado en el servidor
def check_program_installed(server, username, key_file, program):

    command = f"which {program}"
    output, error = run_ssh_command(server, username, key_file, command)
    return output.strip() if output else None


# Función para verificar programas requeridos para un comando específico
def check_required_programs(server, username, key_file, command):

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
            result = check_program_installed(server, username, key_file, program)
            if result:
                installed_programs.append(program)
            else:
                missing_programs.append(program)

        return installed_programs, missing_programs

    return [], []  # Si no se especifican programas requeridos para el comando, retorna listas vacías


# Función para guardar las opciones en formato JSON
def save_options_to_json(name_server, name_user, key_file, json_filename):

    if not json_filename:
        return None

    options = {
        "Name Server": "{}".format(name_server),
        "Username": "{}".format(name_user),
        "Key SSH file path": "{}".format(key_file),
    }

    json_string = json.dumps(options, indent=4)

    return json_string


# Página del test server
def func_page_test_server():

    st.subheader("Server options")

    # Obtener opciones guardadas
    options = st.session_state.get("options", {"Name Server": "", "Username": "", "Key SSH file path": ""})

    # Entradas para las opciones del servidor
    name_server = st.text_input("Name Server", options["Name Server"], key="name_server")
    name_user = st.text_input("Username", options["Username"])
    key_file = st.text_input("Key SSH file path", options["Key SSH file path"])
    browse_key_file = st.button("Browse local directory")

    if browse_key_file:
        wkdir = os.getcwd()
        print(wkdir)
        filename = filedialog.askopenfilename(initialdir=wkdir,
                                              title="Select a File containing a ssh key")
        print(filename)



    command_options = st.selectbox("Command:", ["List", "Currently directory", "Hostname", "Topology", "Another"])

    if command_options == "Another":
        write_another_command = st.text_input("Write another command")

    # if command_options == "Topology":
    #     virtual_env = st.text_input("Enter the virtual env path")
    #     if virtual_env:
    #         source_activate = subprocess.run(f"source {virtual_env}", shell=True, executable="/bin/bash")

    # Botones para guardar y cargar opciones en formato JSON
    col1, col2 = st.columns(2)

    with col1:
        json_filename = st.text_input("Enter a .json filename (optional):", key="json_filename")
        options = save_options_to_json(name_server, name_user, key_file, json_filename)
        if json_filename:

            button_download = st.download_button(label="Download .json file", data=options,
                                                 file_name=f"{json_filename}.json",
                                                 mime="application/json")

            if button_download:
                st.success(f"File saved successfully as '{json_filename}.json'")
            # else:
                # st.error("Please enter a .json filename")


    #   =========================

    with col2:
        json_filepath = st.text_input("Enter the path of .json file on your PC (optional):", key="json_filepath")
        button_load = st.button("Load .json file")
        if button_load is not None:
            if json_filepath:
                try:
                    with open(json_filepath, "r") as f:
                        options = json.load(f)
                    if options:
                        name_server = options.get("Name Server", "")
                        name_user = options.get("Username", "")
                        key_file = options.get("Key SSH file path", "")
                        # Actualizar opciones guardadas
                        st.session_state.options = {"Name Server": name_server, "Username": name_user, "Key SSH file path": key_file}
                        st.success(f" .json file loaded successfully")
                except Exception as e:
                    st.error(f"Error loading .json file: {str(e)}")

            else:
                st.error("Please enter the path of .json file.")

    #   =========================

    if st.button("TEST"):
        if not name_server or not name_user or not key_file or not command_options:
            st.error("Please fill in all the fields.")
            return

        if command_options == "Another" and not write_another_command:
            st.error("Please write another command.")
            return

        # if command_options == "Topology" and not virtual_env:
        #     st.error("Please enter the virtual env path.")
        #     return

        if command_options == "List":
            command = "ls -l"
        elif command_options == "Currently directory":
            command = "pwd"
        elif command_options == "Hostname":
            command = "hostname"
        elif command_options == "Topology": #   and source_activate
            command = "topology_cmd"
        else:
            command = write_another_command

        # Verificar programas requeridos antes de ejecutar el comando
        installed_programs, missing_programs = check_required_programs(name_server, name_user, key_file,
                                                                               command)
        if missing_programs:    #   CUANDO NO ESTÁ INSTALADO EL PROGRAMA
                                #   EN EL SERVIDOR, NO TE COGE EL MENSAJE
                                #   DE ERROR.
            st.error(f"The following programs are required but not installed: {', '.join(missing_programs)}")
        else:
            output, error = run_ssh_command(name_server, name_user, key_file, command)
            #st.success("All required programs are installed.")

            if output:
                st.success("Command executed successfully:")
                st.code(output)
                st.sidebar.success(f"Connected to the server: {get_host_name(name_server, name_user, key_file)}")
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