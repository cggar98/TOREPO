import streamlit as st
import paramiko
import json
import os
from tkinter import filedialog


def ensure_json_extension(json_filename):
    if not json_filename.endswith('.json'):
        json_filename += '.json'
    return json_filename


def run_ssh_command(server, username, ssh_key_path, command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(server, username=username, key_filename=ssh_key_path)
        stdin, stdout, stderr = ssh.exec_command(command)
        output = stdout.read().decode()
        error = stderr.read().decode()
        ssh.close()
        return output, error
    except Exception as e:
        return None, str(e)


def get_host_name(server, username, ssh_key_path):
    command = "hostname"
    output, error = run_ssh_command(server, username, ssh_key_path, command)
    return output.strip() if output else None


def check_program_installed(server, username, ssh_key_path, program):
    command = f"which {program}"
    output, error = run_ssh_command(server, username, ssh_key_path, command)
    return output.strip() if output else None


def check_required_programs(server, username, ssh_key_path, command):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    neighbor_sphere_script = os.path.join(script_dir, "neighbor_sphere.py")

    required_programs = {
        "List": ["ls"],
        "Currently directory": ["pwd"],
        "Hostname": ["hostname"],
        "Topology": ["topology_cmd"],
        "Replicate": ["replicate_polymer"],
        "2D Torsion Density Maps": ["2D_torsion_density_maps"],
        "Bonded Distribution": ["bonded_distribution"],
        "Energy Analysis": ["energy_analysis"],
        "Info TRJ": ["info_trj"],
        "Neighbor Sphere": [f"python {neighbor_sphere_script}"],
        "Pair Distribution": ["pair_distribution"],
        "Polymer Size": ["polymer_size"],
        "VOTCA Analysis": ["votca_analysis ibi"]
    }

    if command in required_programs:
        programs = required_programs[command]
        missing_programs = []
        installed_programs = []
        for program in programs:
            result = check_program_installed(server, username, ssh_key_path, program)
            if result:
                installed_programs.append(program)
            else:
                missing_programs.append(program)

        return installed_programs, missing_programs

    return [], []


def save_options_to_json(name_server, name_user, ssh_key_options, json_filename):

    if not json_filename:
        return None

    ssh_key_path = ssh_key_options.get("input_file_1", "")

    options = {
        "Name Server*": "{}".format(name_server),
        "Username*": "{}".format(name_user),
        "Key SSH file path*": "{}".format(ssh_key_path),
    }

    json_string = json.dumps(options, indent=4)

    return json_string


def func_page_test_server():

    st.markdown("<h1 style='font-size:24px;'>Server options</h1>", unsafe_allow_html=True)

    #   ============================    Server options   ============================    #

    options = st.session_state.get("options", {
        "Name Server*": "",
        "Username*": "",
        "Key SSH file path*": ""
    })

    name_server = st.text_input("Name Server*", options.get("Name Server*", ""), key="name_server")
    name_user = st.text_input("Username*", options.get("Username*", ""))

    #   ============================    Key ssh filepath options (NO SÉ SI PONER st.text_input)   ============================    #

    ssh_key_options = st.session_state.get("ssh_key_options", {})
    if not ssh_key_options:
        ssh_key_options = {}

    input_options = [
        "Key SSH file path*"
    ]

    for index, option in enumerate(input_options, start=1):
        input_key = f"input_file_{index}"

        if input_key not in ssh_key_options:
            ssh_key_options[input_key] = ""

        st.text_input(
            option,
            ssh_key_options[input_key],
            key=f"{input_key}_key_ssh"
        )

        col1, col2 = st.columns(2)
        with col1:
            browse_button_key = f"browse_key_ssh{input_key}"
            if st.button("Browse file", key=browse_button_key):
                wkdir = os.getcwd()
                filetypes = [("All files", "*")]

                input_filename = filedialog.askopenfilename(
                    initialdir=wkdir,
                    title="Select a key ssh file",
                    filetypes=filetypes
                )

                if input_filename:
                    ssh_key_options[input_key] = input_filename

        with col2:
            if ssh_key_options[input_key]:
                remove_button_key = f"remove_ssh_key_{input_key}"
                if st.button("Remove file", key=remove_button_key):
                    ssh_key_options[input_key] = ""

    st.session_state["ssh_key_options"] = ssh_key_options

    #   ============================    Command options   ============================    #

    command_options = st.selectbox("Command for test conection:", ["List (ls -l)", "Currently directory (pwd)", "Hostname", "Another command"])

    if command_options == "Another command":
        write_another_command = st.text_input("Enter another command for test conection")

    #   ============================    JSON loaded and saved options   ============================    #

    # Botones para guardar y cargar opciones en formato JSON
    col1, col2 = st.columns(2)

    with col1:
        tip_filename = "Enter a filename for save server options"
        json_filename = st.text_input("Save server options (optional):", key="json_filename", help=tip_filename)

        if json_filename.strip():
            json_filename = ensure_json_extension(json_filename.strip())
            options = save_options_to_json(name_server, name_user, ssh_key_options, json_filename)
            button_download = st.download_button(label="Save", data=options,
                                                     file_name=json_filename,
                                                     mime="application/json")
            if button_download:
                st.success(f"File saved successfully as '{json_filename}'")

    #   === TEST CHANGE === #

    with col2:
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
                input_placeholder.text_input("Load server options (optional):", key="json_input", value=json_filepath,
                                             help=tip_browse)
                st.success("File selected successfully")

                button_load = st.button("Load")
                if button_load is not None:
                    if json_filepath:
                        try:
                            with open(json_filepath, "r") as f:
                                options = json.load(f)
                            if options:
                                name_server = options.get("Name Server*", "")  # Deja estas claves como están en el JSON
                                name_user = options.get("Username*", "")  # Deja estas claves como están en el JSON
                                ssh_key_path = options.get("Key SSH file path*",
                                                           "")  # Deja estas claves como están en el JSON
                                st.session_state.options = {"Name Server*": name_server, "Username*": name_user,
                                                            "Key SSH file path*": ssh_key_path}
                        except Exception as e:
                            st.error(f"Error loading file: {str(e)}")

     #   ============================    COMMAND REMOTE RUN   ============================    #

    run_button = "run_button"
    if st.button("RUN", key=run_button):
        ssh_key_path = ssh_key_options.get("input_file_1", "")

        if not ssh_key_path:
            st.error("Please enter key ssh file")
            return

        # Save updated input files in session state
        st.session_state["ssh_keyoptions"] = ssh_key_options

        if not name_server:
            st.error("Please enter a name server")
            return

        if not name_user:
            st.error("Please enter a username")
            return

        if not command_options:
            st.error("Please enter a command")
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
        installed_programs, missing_programs = check_required_programs(name_server, name_user, ssh_key_path,
                                                                               command)
        if missing_programs:
            st.error(f"The following programs are required but not installed: {', '.join(missing_programs)}")
        else:
            output, error = run_ssh_command(name_server, name_user, ssh_key_path, command)
            #st.success("All required programs are installed.")

            if output:
                st.success("Command executed successfully:")
                st.code(output)
                st.sidebar.success(f"Connected to the server: {get_host_name(name_server, name_user, ssh_key_path)}")
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
