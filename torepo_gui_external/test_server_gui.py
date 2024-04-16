import streamlit as st
import paramiko
import json

#from torepo_gui_external.topology_gui import run_page_topology


def ejecutar_comando_remoto(host, username, key_file, command_options, comando):
    # Crear una instancia del cliente SSH
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Conectar al servidor remoto
        ssh_client.connect(hostname=host, username=username, key_filename=key_file)

        if command_options == "Topology":
            # Comando para activar el entorno virtual y luego ejecutar el script
            comando_completo = comando

        # Ejecutar el comando en el servidor remoto
        stdin, stdout, stderr = ssh_client.exec_command(comando_completo)

        # Leer la salida estándar y la salida de error
        salida_estandar = stdout.read().decode('utf-8')
        salida_error = stderr.read().decode('utf-8')

        # Cerrar la conexión SSH
        ssh_client.close()

        if salida_error:
            return f"Error al ejecutar '{comando}': {salida_error}"
        else:
            return salida_estandar
    except Exception as e:
        return f"Error al conectar al servidor remoto: {str(e)}"


def save_options_to_json(host, username, key_file, json_filename):

    if not json_filename:
        return None

    options = {
        "Name Server": "{}".format(host),
        "Username": "{}".format(username),
        "Key SSH file path": "{}".format(key_file),
    }

    json_string = json.dumps(options, indent=4)

    return json_string


def func_page_test_server():

    st.subheader("Server options")

    options = st.session_state.get("options", {"Name Server": "", "Username": "", "Key SSH file path": ""})

    # Entradas del usuario
    host = st.text_input("Name Server", options["Name Server"], key="name_server")
    username = st.text_input("Username", options["Username"])
    key_file = st.text_input("Key SSH file path", options["Key SSH file path"])

    command_options = st.selectbox("Select a command:", ["List", "Currently directory", "Topology", "Hostname", "Another"])
    if command_options == "Another":
        write_another_command = st.text_input("Write another command")

    comando_completo = ""

    if command_options == "Topology":
        path_virtual_env = st.text_input("Enter the virtual env path", key="path_virtual_env")
        activate_virtual_env = f"source {path_virtual_env}"

        comando_completo = "topology_cmd"

    # Botones para guardar y cargar opciones en formato JSON
    col1, col2 = st.columns(2)

    with col1:
        json_filename = st.text_input("Enter a .json filename (optional):", key="json_filename")
        options = save_options_to_json(host, username, key_file, json_filename)
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
                        host = options.get("Name Server", "")
                        username = options.get("Username", "")
                        key_file = options.get("Key SSH file path", "")
                        # Actualizar opciones guardadas
                        st.session_state.options = {"Name Server": host, "Username": username,
                                                    "Key SSH file path": key_file}
                        st.success(f" .json file loaded successfully")
                except Exception as e:
                    st.error(f"Error loading .json file: {str(e)}")

            else:
                st.error("Please enter the path of .json file.")

    #   =========================

    # Ejecutar el comando
    if st.button("TEST command"):

        if command_options == "List":
            comando_completo = "ls -l"
        elif command_options == "Currently directory":
            comando_completo = "pwd"
        elif command_options == "Hostname":
            comando_completo = "hostname"
        elif command_options == "Topology":
            comando_completo = "topology_cmd"
        else:
            comando_completo = write_another_command

            # # Comando para ejecutar el script Python dentro del entorno virtual
            # comando_completo = f"python {ruta_completa}"

        # Ejecutar el comando en el servidor remoto
        resultado = ejecutar_comando_remoto(host, username, key_file, command_options, comando_completo)
        st.code(resultado, language='text')
    else:
        st.warning("Por favor, completa todos los campos.")


def run_page_test_server():
    func_page_test_server()