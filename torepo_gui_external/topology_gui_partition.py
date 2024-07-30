import streamlit as st
import os
import tempfile
import base64
import shutil
from tkinter import filedialog
from torepo_gui_external.server_options import ServerScreen
from functions.common.common_functions import save_uploaded_file, create_tar_gz
from functions.topology.topology_func import (reset_program_options, run_topology_cmd_remote_with_partition,
                                              show_info_topology_content)


class TopologyScreen:

    def __init__(self):

        self._about = """
                         Manipulate topology for polymers
                  ----------------------------------------------

                                    Version 1.1

                            Dr. Javier Ramos and Carlos Garcia
                          Macromolecular Physics Department
                    Instituto de Estructura de la Materia (IEM-CSIC)
                                   Madrid (Spain)

            Topology is an open-source python library to quickly modify topology
            of polymer molecules

            This software is distributed under the terms of the
            GNU General Public License v3.0 (GNU GPLv3). A copy of
            the license (LICENSE.txt) is included with this distribution.
                    """

        self._input_files = [
            "Select input file (XSD, PDB, or MOL2)*",
            "Select HEAD TAIL file for renumbering pdb (DAT)",
            "Select SETUP RESIDUE file for assigning residues (DAT)",
            "Select FILEMAP for matching LAMMPS type with name and element (DAT)"
        ]

        self._input_options = None
        self._pattern = None
        self._separate_chains = None
        self._isunwrap = None
        self._guess_improper = None

        # ===================================================================================
    def show_screen(self):

        #   ============================    Welcome Topology Program   ============================    #

        st.markdown("<h1 style='font-size:32px;'>Topology</h1>", unsafe_allow_html=True)

        with st.expander("INFO"):
            st.text(self._about)

        st.markdown("<h1 style='font-size:22px;'>Program options</h1>", unsafe_allow_html=True)
        st.write("Fields with '*' are required")

        #   ============================    Server configuration   ============================    #

        server_screen = ServerScreen()
        server_valid = server_screen.show_screen_sidebar()

        self._name_server = server_screen._name_server
        self._name_user = server_screen._name_user
        self._ssh_key_options = server_screen._ssh_key_options
        self._path_virtualenv = server_screen._path_virtualenv
        self._working_directory = server_screen._working_directory

        #   ============================    Input options   ============================    #

        self._input_options = st.session_state.get("input_options", {})
        if not self._input_options:
            self._input_options = {}

        for index, option in enumerate(self._input_files):
            input_key = "input_file_{0:03d}".format(index)
            if input_key not in self._input_options:
                self._input_options[input_key] = ""

            st.text_input(
                option,
                self._input_options[input_key],
                key=f"{input_key}_input_text"
            )

            col1, col2 = st.columns(2)
            with col1:
                browse_button_key = f"browse_{input_key}"
                if st.button("Browse file", key=browse_button_key):
                    wkdir = os.getcwd()

                    if option == "Select input file (XSD, PDB, or MOL2)*":
                        filetypes = [("PDB files", "*.pdb"), ("XSD files", "*.xsd"), ("MOL2 files", "*.mol2")]
                    else:
                        filetypes = [("DAT files", "*.dat")]

                    input_filename = filedialog.askopenfilename(
                        initialdir=wkdir,
                        title="Select an input file",
                        filetypes=filetypes
                    )

                    if input_filename:
                        self._input_options[input_key] = input_filename
                        st.session_state["input_options"] = self._input_options

                        if self._input_options[input_key]:
                            load_button_key = f"load_{input_key}"
                            st.button("Load file", key=load_button_key)

            with col2:
                if self._input_options[input_key]:
                    remove_button_key = f"remove_{input_key}"
                    if st.button("Remove file", key=remove_button_key):
                        self._input_options[input_key] = ""
                        st.session_state["input_options"] = self._input_options

        st.session_state["input_options"] = self._input_options

        #   ============================    Pattern options   ============================    #
        self._pattern = st.text_input("String pattern to name the new files*", st.session_state.get("pattern", ""))
        st.session_state.pattern = self._pattern

        #   ============================    Separate chains options   ============================    #

        self._separate_chains = st.toggle("Create a pdb file for each chain",
                                          st.session_state.get("separate_chains", False))
        st.session_state.separate_chains = self._separate_chains

        #   ============================    Isunwrap options   ============================    #

        self._isunwrap = st.toggle("Unwrap coordinates in the final structure", st.session_state.get("isunwrap", False))
        st.session_state.isunwrap = self._isunwrap

        #   ============================    Guess impropers options   ============================    #

        self._guess_improper = st.toggle("Guess improper angles in the system",
                                         st.session_state.get("guess_improper", False))
        st.session_state.guess_improper = self._guess_improper

        #   ============================    RESET OPTIONS   ============================    #

        button_clean_options = st.button("Clean all program options")
        if button_clean_options:
            reset_program_options()
            st.rerun()

        #   ============================    TOPOLOGY RUN   ============================    #

        # Button to launch the topology command
        button_run = st.button("RUN TOPOLOGY")
        if button_run:
            if not server_valid:
                st.error("Server options are not valid. Please check the server options in the sidebar.")
                return

            input_file_path = self._input_options.get("input_file_000", "")
            renumber_pdb_path = self._input_options.get("input_file_001", "")
            assign_residues_path = self._input_options.get("input_file_002", "")
            filemap_path = self._input_options.get("input_file_003", "")

            if not input_file_path:
                st.error("Please select an input file (XSD, PDB or MOL2) before running the program")
                return

            st.session_state["input_options"] = self._input_options

            if not self._pattern:
                st.error("Please string pattern to name the new files")
                return

            temp_dir = tempfile.mkdtemp()
            st.write(f"Temporary directory created: {temp_dir}")

            try:
                input_file_path = save_uploaded_file(input_file_path, temp_dir)
                renumber_pdb_path = save_uploaded_file(renumber_pdb_path,
                                                       temp_dir) if renumber_pdb_path else None
                assign_residues_path = save_uploaded_file(assign_residues_path,
                                                          temp_dir) if assign_residues_path else None
                filemap_path = save_uploaded_file(filemap_path, temp_dir) if filemap_path else None

                output_folder = temp_dir
                st.write(f"Using output folder: {output_folder}")

                # Verificar si el directorio existe antes de listar
                if os.path.exists(output_folder):
                    [os.path.join(output_folder, f) for f in os.listdir(output_folder)]
                else:
                    st.error(f"The directory {output_folder} does not exist.")
                    return

                with st.spinner("Running Topology. Please wait..."):
                    warning_close_interface = st.warning("Do not close the interface while Topology is running.")

                    output, error, output_folder = run_topology_cmd_remote_with_partition(self._name_server,
                                                                                          self._name_user,
                                                                                          self._ssh_key_options,
                                                                                          self._path_virtualenv,
                                                                                          input_file_path,
                                                                                          renumber_pdb_path,
                                                                                          assign_residues_path,
                                                                                          filemap_path,
                                                                                          self._separate_chains,
                                                                                          self._pattern,
                                                                                          self._isunwrap,
                                                                                          self._guess_improper,
                                                                                          self._working_directory,
                                                                                          # use_queuing_system=False,
                                                                                          # submit_with=None,
                                                                                          # check_status=None,
                                                                                          # script_before_run="",
                                                                                          # script_after_run=""
                                                                                          )

                    warning_close_interface.empty()
                    st.success("Job Done!")

                    #   ERROR: No such file or directory: '/tmp/tmpl3cae66c'
                    output_file_paths = [os.path.join(output_folder, f) for f in os.listdir(output_folder)]

                    show_info_topology_content(output_file_paths)

                    tar_file_path = create_tar_gz(output_folder, output_file_paths)

                    download_link = (f'<a href="data:application/tar+gzip;base64,'
                                     f'{base64.b64encode(open(tar_file_path, "rb").read()).decode()}'
                                     f'" download="topology_output_files.tar.gz">'
                                     f'Download all output files</a>')
                    st.markdown(download_link, unsafe_allow_html=True)

            finally:
                shutil.rmtree(temp_dir)
                st.write(f"Temporary directory removed: {temp_dir}")
