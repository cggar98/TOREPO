import streamlit as st
import paramiko
import os


# Conect to remote server
def connect_to_server(hostname, username, password):
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(hostname, username=username, password=password)
    return ssh_client


# Upload file to remote server
def upload_file_to_server(ssh_client, local_file_path, remote_working_dir):
    sftp = ssh_client.open_sftp()
    remote_file_path = os.path.join(remote_working_dir, os.path.basename(local_file_path))
    sftp.put(local_file_path, remote_file_path)
    sftp.close()
    return remote_file_path


# Execute 'sbatch' command
def execute_sbatch(ssh_client, remote_file_path):
    stdin, stdout, stderr = ssh_client.exec_command(f'cd {os.path.dirname(remote_file_path)}'
                                                    f' && sbatch {os.path.basename(remote_file_path)}')
    return stdout.read().decode(), stderr.read().decode()


# Streamlit interface
st.title("Running scripts .sh in the remote server ")

# Server options
st.sidebar.title("Server options")
hostname = st.sidebar.text_input("Hostname")
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")
remote_working_dir = st.sidebar.text_input("Working directory")
uploaded_file = st.sidebar.file_uploader("Upload a SH file", type=["sh"])

# Botton RUN
if st.sidebar.button("RUN"):
    if not uploaded_file:
        st.sidebar.error("Please, upload a SH file.")
    else:
        try:
            ssh_client = connect_to_server(hostname, username, password)
            st.sidebar.success("Successfullt connected")

            # Save file temporaly
            local_file_path = os.path.join("/tmp", uploaded_file.name)
            with open(local_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.write(f"{uploaded_file.name} file uploaded correctly.")

            # Upload file to remote server
            remote_file_path = upload_file_to_server(ssh_client, local_file_path, remote_working_dir)
            st.write(f"Uploaded file to server: {remote_file_path}")

            # Execute 'sbatch' in the file
            stdout, stderr = execute_sbatch(ssh_client, remote_file_path)
            st.write("Execution output:")
            st.text(stdout)
            if stderr:
                st.error(stderr)

        except Exception as e:
            st.sidebar.error(f"Error al conectar o ejecutar: {e}")
        finally:
            if 'ssh_client' in locals():
                ssh_client.close()
