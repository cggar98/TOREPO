import paramiko
import os
import streamlit as st
from torepo_gui_external.topology_gui import run_topology_cmd


def execute_on_remote_server(server, username, ssh_key_path, command):
    # Crear una instancia de cliente SSH
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        # Cargar la clave SSH
        ssh_key = paramiko.RSAKey.from_private_key_file(ssh_key_path)

        # Conectar al servidor remoto
        ssh.connect(server, username=username, pkey=ssh_key)

        # Ejecutar el script remoto (topology_gui.py) en el servidor
        stdin, stdout, stderr = ssh.exec_command(command)

        # Recoger la salida del script
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        # Imprimir la salida o el error
        if output:
            st.write("Output:")
            st.code(output)
        if error:
            st.write("Error:")
            st.code(error)

    except Exception as e:
        st.error(f"Error executing on remote server: {str(e)}")
    finally:
        # Cerrar la conexión SSH
        if ssh:
            ssh.close()

def func_remote_server():
    # Interfaz de usuario para configurar la conexión SSH y la ejecución remota
    st.title("Remote Server Execution")

    # Obtener la configuración del usuario
    remote_server = st.text_input("Remote Server IP:", "161.111.23.64")
    remote_username = st.text_input("Username:", "cgarcia")
    ssh_private_key_path = st.text_input("Private Key Path:", "/home/cgarcia/.ssh/local_id_rsa")


    # Botón para ejecutar en el servidor remoto
    if st.button("Execute on Remote Server"):
        if remote_server.strip() and remote_username.strip() and ssh_private_key_path.strip():
            output, error = run_topology_cmd(remote_server, remote_username, ssh_private_key_path)
            if output:
                st.success("Command executed successfully:")
                st.code(output)
#                st.sidebar.success(f"Connected to the server: {get_host_name(name_server, name_user, ssh_key)}")
            elif error:
                st.error("Error executing command:")
                st.code(error)
                st.sidebar.error("Could not connect to the server")
            else:
                st.error("Error executing command: No output or error.")
                st.sidebar.error("Could not connect to the server")

        else:
            st.error("Please fill in all fields.")

def run():
    func_remote_server()