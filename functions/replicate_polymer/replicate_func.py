import streamlit as st
import paramiko
import tempfile
import os
import time
import logging
import shutil
from tkinter import filedialog


# Logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def upload_file_to_server(ssh, local_path, remote_path):
    sftp = ssh.open_sftp()
    sftp.put(local_path, remote_path)
    sftp.close()


def run_replicate_cmd_remote(name_server, name_user, ssh_key_options, path_virtualenv,
                             working_directory, structure_file, xml_file,
                             image_x, image_y, image_z,
                             mdengine, noh, index,
                             boxlength_a, boxlength_b, boxlength_c,
                             boxangle_alpha, boxangle_beta, boxangle_gamma,
                             impropers, npairs, verbose):

    activate_virtualenv = f"source {path_virtualenv}"

    # Navigate to the remote working directory before running the command
    command = (f"cd {working_directory} && replicate_polymer -p {working_directory}/{os.path.basename(structure_file)}"
               f" -f {working_directory}/{os.path.basename(xml_file)}"
               f" --images {working_directory}/{image_x}"
               f" {working_directory}/{image_y}"
               f" {working_directory}/{image_z}")

    if mdengine:
        command += f" -e {working_directory}/{mdengine}"
    if noh:
        command += f" --noh"
    if index:
        command += f" --index {working_directory}/{index}"
    if boxlength_a and boxlength_b and boxlength_c:
        command += (f" --boxlength {working_directory}/{boxlength_a}"
                    f" {working_directory}/{boxlength_b}"
                    f" {working_directory}/{boxlength_c}")
    if boxangle_alpha and boxangle_beta and boxangle_gamma:
        command += (f" --boxangle {working_directory}/{boxangle_alpha}"
                    f" {working_directory}/{boxangle_beta}"
                    f" {working_directory}/{boxangle_gamma}")
    if impropers:
        command += f" --impropers {working_directory}/{os.path.basename(impropers)}"
    if npairs:
        command += f" --npairs {working_directory}/{npairs}"
    if verbose:
        command += f" --verbose"

    full_command = f"{activate_virtualenv} && {command}"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    # Upload input files to the remote server's working directory
    upload_file_to_server(ssh, structure_file, f"{working_directory}/{os.path.basename(structure_file)}")
    upload_file_to_server(ssh, xml_file, f"{working_directory}/{os.path.basename(xml_file)}")

    if impropers:
        upload_file_to_server(ssh, impropers, f"{working_directory}/{os.path.basename(impropers)}")

    # Execute command in the remote server
    stdin, stdout, stderr = ssh.exec_command(full_command)

    # Read output and errors of the command
    output = stdout.read().decode()
    error = stderr.read().decode()

    # Download generated files from remote server
    sftp = ssh.open_sftp()
    output_folder = tempfile.mkdtemp()
    os.makedirs(output_folder, exist_ok=True)

    # File list to download
    output_files = ["allatom_idx_replicate.dat",
                    "backbone_idx_replicate.dat",
                    "listendtoend_replicate.dat",
                    "Info.log"]

    structure_file_name = os.path.splitext(os.path.basename(structure_file))[0]

    if noh:
        if not mdengine:
            output_files.extend([f"{structure_file_name}_noH.gro",
                                 f"{structure_file_name}_noH.pdb",
                                 f"{structure_file_name}_noH.top",
                                 f"{structure_file_name}_noH_replicate.gro",
                                 f"{structure_file_name}_noH_replicate.pdb",
                                 f"{structure_file_name}_noH_replicate.top"])
        else:
            output_files.extend([f"{structure_file_name}_noH_replicate_clean.inp",
                                 f"{structure_file_name}_noH_replicate_clean.lmp",
                                 f"{structure_file_name}_noH.gro",
                                 f"{structure_file_name}_noH.pdb",
                                 f"{structure_file_name}_noH.top",
                                 f"{structure_file_name}_noH_replicate.gro",
                                 f"{structure_file_name}_noH_replicate.pdb",
                                 f"{structure_file_name}_noH_replicate.top"])

    # Check and download each output file
    for file in output_files:
        remote_file_path = f"{working_directory}/{file}"
        local_file_path = os.path.join(output_folder, file)
        try:
            sftp.stat(remote_file_path)  # Check if the file exists
            sftp.get(remote_file_path, local_file_path)
        except FileNotFoundError:
            logger.error(f"File not found in {working_directory}: {file}")

            # Check if Info.log exists in the home directory and is recently modified
            if file == "Info.log":
                command_find_file = f"find $HOME -name {file} -mmin -10 2>/dev/null"
                stdin, stdout, stderr = ssh.exec_command(command_find_file)
                find_results = stdout.read().decode().splitlines()
                find_errors = stderr.read().decode().splitlines()

                if find_errors:
                    logger.error(f"Find command errors: {find_errors}")

                if find_results:
                    remote_file_path_home = find_results[0]
                    try:
                        sftp.stat(remote_file_path_home)
                        sftp.get(remote_file_path_home, local_file_path)
                        logger.info(f"Successfully downloaded {file} from {remote_file_path_home}")
                    except FileNotFoundError:
                        logger.error(f"File not found in home directory: {file}")
                else:
                    logger.error(f"No recent 'Info.log' found in home directory")

                # Check if allatom_idx_replicate.dat exists in the home directory and is recently modified
                if file == "allatom_idx_replicate.dat":
                    command_find_file = f"find $HOME -name {file} -mmin -10 2>/dev/null"
                    stdin, stdout, stderr = ssh.exec_command(command_find_file)
                    find_results = stdout.read().decode().splitlines()
                    find_errors = stderr.read().decode().splitlines()

                    if find_errors:
                        logger.error(f"Find command errors: {find_errors}")

                    if find_results:
                        remote_file_path_home = find_results[0]
                        try:
                            sftp.stat(remote_file_path_home)
                            sftp.get(remote_file_path_home, local_file_path)
                            logger.info(f"Successfully downloaded {file} from {remote_file_path_home}")
                        except FileNotFoundError:
                            logger.error(f"File not found in home directory: {file}")
                    else:
                        logger.error(f"No recent 'allatom_idx_replicate.dat' found in home directory")

    try:
        sftp.remove(f"{working_directory}/{os.path.basename(structure_file)}")
        sftp.remove(f"{working_directory}/{os.path.basename(xml_file)}")
        # if impropers is not None:
        #     sftp.remove(f"{working_directory}/{os.path.basename(impropers)}")

    except FileNotFoundError:
        logger.error(f"File {os.path.basename(structure_file)} not found in remote directory")
        logger.error(f"File {os.path.basename(xml_file)} not found in remote directory")
        logger.error(f"File {os.path.basename(impropers)} not found in remote directory")

    sftp.close()
    ssh.close()

    return output, error, output_folder


def run_replicate_cmd_remote_with_partition(name_server, name_user, ssh_key_options, path_virtualenv,
                                            input_file, renumber_pdb, assign_residues, filemap,
                                            separate_chains, pattern, isunwrap, guess_improper,
                                            working_directory, submit_with=None,
                                            check_status=None, script_before_run="", script_after_run=""):

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(name_server, username=name_user, key_filename=ssh_key_options)

    temp_dir = None

    try:
        # Create local temporal working directory
        temp_dir = tempfile.mkdtemp()
        output_folder = os.path.join(temp_dir, "output")
        os.makedirs(output_folder, exist_ok=True)
        print(f"Temporary directory created: {temp_dir}")
        print(f"Using output folder: {output_folder}")

        # Create SLURM script
        slurm_script_path = os.path.join(temp_dir, "slurm_job.sh")
        slurm_script_content = "#!/bin/bash\n"
        slurm_script_content += "#SBATCH --job-name=topology_job\n"
        slurm_script_content += "#SBATCH --output=topology_job.out\n"
        slurm_script_content += "#SBATCH --error=topology_job.err\n"
        if submit_with:
            slurm_script_content += f"#SBATCH --{submit_with}\n"

        # Add the script before job run
        if script_before_run:
            slurm_script_content += script_before_run + "\n"

        # Commands to activate the virtual environment and execute the program
        slurm_script_content += f"source {path_virtualenv}\n"
        slurm_script_content += "export LD_LIBRARY_PATH=/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH\n"
        slurm_script_content += f"cd {working_directory}\n"
        slurm_script_content += f"topology_cmd -i {os.path.basename(input_file)}"

        if renumber_pdb:
            slurm_script_content += f" -r {os.path.basename(renumber_pdb)}"
        if assign_residues:
            slurm_script_content += f" -a {os.path.basename(assign_residues)}"
        if filemap:
            slurm_script_content += f" --filemap {os.path.basename(filemap)}"
        if separate_chains:
            slurm_script_content += " --separate_chains"
        if pattern:
            slurm_script_content += f" -p {pattern}"
        if isunwrap:
            slurm_script_content += " -w"
        if guess_improper:
            slurm_script_content += " --guess_improper"

        # # Add the script after job run
        if script_after_run:
            slurm_script_content += "\n" + script_after_run + "\n"

        with open(slurm_script_path, "w") as slurm_script:
            slurm_script.write(slurm_script_content)

        # Upload SLURM script and needed files to remote server
        upload_file_to_server(ssh, slurm_script_path, f"{working_directory}/slurm_job.sh")
        upload_file_to_server(ssh, input_file, f"{working_directory}/{os.path.basename(input_file)}")
        if renumber_pdb:
            upload_file_to_server(ssh, renumber_pdb, f"{working_directory}/{os.path.basename(renumber_pdb)}")
        if assign_residues:
            upload_file_to_server(ssh, assign_residues, f"{working_directory}/{os.path.basename(assign_residues)}")
        if filemap:
            upload_file_to_server(ssh, filemap, f"{working_directory}/{os.path.basename(filemap)}")

        # Execute SLURM script using SBATCH
        stdin, stdout, stderr = ssh.exec_command(f"cd {working_directory} && sbatch slurm_job.sh")
        job_submission_output = stdout.read().decode()
        job_submission_error = stderr.read().decode()

        if job_submission_error:
            return f"Error submitting job: {job_submission_error}", "", temp_dir
        else:
            job_id = job_submission_output.strip().split()[-1]

        if check_status:
            while True:
                stdin, stdout, stderr = ssh.exec_command(f"squeue -j {job_id}")
                job_status_output = stdout.read().decode()
                if job_id not in job_status_output:
                    break
                time.sleep(10)

        # Download output files
        sftp = ssh.open_sftp()
        output_files = [f"{pattern}.pdb", "topology_job.out", "topology_job.err", "InfoTopology.log"]
        if assign_residues:
            output_files.extend([f"{pattern}_residues.gro", f"{pattern}_residues.pdb", f"{pattern}_residues.psf"])
        if renumber_pdb and not assign_residues:
            output_files.extend([f"{pattern}_renumber.gro", f"{pattern}_renumber.pdb", f"{pattern}_renumber.psf"])
        if separate_chains:
            separate_chains_files = sftp.listdir(working_directory)
            separate_chains_files = [f for f in separate_chains_files if f.startswith(pattern) and f.endswith('.pdb')]
            output_files.extend(separate_chains_files)

        for file in output_files:
            remote_file_path = f"{working_directory}/{file}"
            local_file_path = os.path.join(output_folder, file)
            try:
                sftp.stat(remote_file_path)
                sftp.get(remote_file_path, local_file_path)
            except FileNotFoundError:
                print(f"File not found: {file}")

        # try:
        #     sftp.remove(f"{working_directory}/{os.path.basename(input_file)}")
        #     if renumber_pdb is not None:
        #         sftp.remove(f"{working_directory}/{os.path.basename(renumber_pdb)}")
        #     if assign_residues is not None:
        #         sftp.remove(f"{working_directory}/{os.path.basename(assign_residues)}")
        #     if filemap is not None:
        #         sftp.remove(f"{working_directory}/{os.path.basename(filemap)}")
        #
        # except FileNotFoundError:
        #     logger.error(f"File {os.path.basename(input_file)} not found in remote directory")
        #     logger.error(f"File {os.path.basename(renumber_pdb)} not found in remote directory")
        #     logger.error(f"File {os.path.basename(assign_residues)} not found in remote directory")
        #     logger.error(f"File {os.path.basename(filemap)} not found in remote directory")

        sftp.close()
        print("Job Done!")
        print(f"Output folder content: {os.listdir(output_folder)}")
        return "Job completed successfully", "", output_folder

    finally:
        # If exists temporal directory, remove it
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Temporary directory removed: {temp_dir}")
        ssh.close()


def handle_button_click(option, input_key, action):
    if action == "browse":
        file_selection_options(option, input_key)
    elif action == "remove":
        st.session_state["input_options"][input_key] = ""
        st.experimental_rerun()


def file_selection_options(option, input_key):
    wkdir = os.getcwd()
    if option == "Select a pdb file containing the structure to be replicated*":
        filetypes = [("PDB files", "*.pdb")]
    if option == "Select a forcefield*":
        filetypes = [("XML files", "*.xml")]
    if option == "Select impropers file":
        filetypes = [("NDX files", "*.ndx")]

    input_filename = filedialog.askopenfilename(
        initialdir=wkdir,
        title="Select an input file",
        filetypes=filetypes
    )

    if input_filename:
        st.session_state["input_options"][input_key] = input_filename
        st.experimental_rerun()


def reset_replicate_options():
    st.session_state.input_options = {}
    st.session_state.image_x = ""
    st.session_state.image_y = ""
    st.session_state.image_z = ""
    st.session_state.index = ""

    st.session_state.boxlength_a = ""
    st.session_state.boxlength_b = ""
    st.session_state.boxlength_c = ""
    st.session_state.boxangle_alpha = ""
    st.session_state.boxangle_beta = ""
    st.session_state.boxangle_gamma = ""

    st.session_state.npairs = ""
    st.session_state.mdengine = ""
    st.session_state.noh = False
    st.session_state.verbose = False


def show_info_log_content(output_file_paths):

    # Check if 'Info.log' is present in the output file list
    info_replicate_log_path = next((path for path in output_file_paths if "Info.log" in path), None)

    if info_replicate_log_path:
        st.write(f"### {os.path.basename(info_replicate_log_path)}")
        with open(info_replicate_log_path, "r") as output_file:
            file_content = output_file.read()
            st.text_area("File content:", value=file_content, height=300)
    else:
        st.error("'Info.log' not found in the output files")
        return
