import os
import tarfile
import json


def save_uploaded_file(uploaded_file, directory):
    """Save uploaded file to the specified directory."""
    if isinstance(uploaded_file, str):
        # If uploaded_file is a string, it's already a path
        file_path = uploaded_file
    else:
        # If uploaded_file is an uploaded file object
        file_path = os.path.join(directory, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
    return file_path


def upload_file_to_server(ssh, local_path, remote_path):
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()


def create_tar_gz(output_folder, output_file_paths):
    # Create a temporary file to store the .tar.gz
    temp_tar_path = os.path.join(output_folder, "output_files.tar.gz")

    # Create the .tar.gz file
    with tarfile.open(temp_tar_path, "w:gz") as tar:
        for file_path in output_file_paths:
            if os.path.exists(file_path):  # Check if file exists
                tar.add(file_path, arcname=os.path.basename(file_path))
            else:
                print(f"Warning: File not found - {file_path}")

    if os.path.exists(temp_tar_path):
        return temp_tar_path
    else:
        return None


def ensure_json_extension(json_filename):
    if not json_filename.endswith('.json'):
        json_filename += '.json'
    return json_filename


def save_options_to_json(name_server, name_user, ssh_key_options, path_virtualenv, json_filename):

    if not json_filename:
        return None

    options = {
        "Name Server*": "{}".format(name_server),
        "Username*": "{}".format(name_user),
        "Key SSH file path*": "{}".format(ssh_key_options),
        "Virtual environment path*": "{}".format(path_virtualenv),
    }

    json_string = json.dumps(options, indent=4)

    return json_string
