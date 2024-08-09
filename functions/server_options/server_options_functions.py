import streamlit as st
import json
import paramiko


def reset_server_options():
    st.session_state.server_options = {}
    st.session_state.json_filename = ""
    st.session_state.input_placeholder = ""


def ensure_json_extension(json_filename):
    if not json_filename.endswith('.json'):
        json_filename += '.json'
    return json_filename


def save_options_to_json(name_server, name_user, ssh_key_options, path_virtualenv,
                         working_directory, json_filename):
    if not json_filename:
        return None

    options = {
        "Name Server*": "{}".format(name_server),
        "Username*": "{}".format(name_user),
        "Key SSH file path*": "{}".format(ssh_key_options),
        "Virtual environment path*": "{}".format(path_virtualenv),
        "Working directory*": "{}".format(working_directory)
    }

    json_string = json.dumps(options, indent=4)
    return json_string


def check_username_and_name_server(name_server, name_user, ssh_key_options):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(name_server, username=name_user, key_filename=ssh_key_options, timeout=0.5)
        ssh.close()
        return True  # Succesfull conection
    except paramiko.AuthenticationException:
        return False
    except (paramiko.SSHException, paramiko.ssh_exception.NoValidConnectionsError) as e:
        return False
    except Exception as e:  # Failed conection
        return False


def verify_virtualenv_path(name_server, name_user, ssh_key_options, path_virtualenv):
    """Verifies if the virtual environment path exists on the remote server."""

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    stdin, stdout, stderr = ssh.exec_command(f"test -f '{path_virtualenv}' && echo 'exists' || echo 'not exists'")
    env_check = stdout.read().decode().strip()
    return env_check == 'exists'


def verify_working_directory(name_server, name_user, ssh_key_options, working_directory):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    stdin, stdout, stderr = ssh.exec_command(f"if [ -d '{working_directory}' ];"
                                             f" then echo 'exists'; else echo 'not exists'; fi")
    result = stdout.read().decode().strip()
    return result == "exists"


def clean_server_options():  # Only clean if you have loaded it
    if st.sidebar.button("Clean server options"):
        reset_server_options()
        st.rerun()
