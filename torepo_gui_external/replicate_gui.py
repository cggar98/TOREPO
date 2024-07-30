import streamlit as st
import os
import tempfile
import base64
import shutil
from torepo_gui_external.server_options import ServerScreen
from functions.common.common_functions import save_uploaded_file, create_tar_gz, clean_options
from functions.replicate_polymer.replicate_func import (handle_button_click, run_replicate_cmd_remote,
                                                        show_info_log_content)


class ReplicateScreen:
    def __init__(self):
        self._about = """
                    Replicate a molecule or polymer chain (ReMoPo)
                  ----------------------------------------------

                                    Version 3.0

                        Dr. Javier Ramos and Carlos Garcia
                          Macromolecular Physics Department
                    Instituto de Estructura de la Materia (IEM-CSIC)
                                   Madrid (Spain)

            ReMoPo is an open-source python library to quickly replicate a molecule
            from a pdb file containing the seed molecule. After that, the script assigns
            the force field parameters using the foyer library (https://mosdef.org/)
            This program generates GROMACS and LAMMPS files to run simulations.

            This software is distributed under the terms of the
            GNU General Public License v3.0 (GNU GPLv3). A copy of
            the license (LICENSE.txt) is included with this distribution.
                    """

        self._input_files = [
            "Select a pdb file containing the structure to be replicated*",
            "Select a forcefield*",
            "Select impropers file"
        ]

        self._input_options = None
        self._image_x = None
        self._image_y = None
        self._image_z = None
        self._index = None
        self._boxlength_a = None
        self._boxlength_b = None
        self._boxlength_c = None
        self._boxangle_alpha = None
        self._boxangle_beta = None
        self._boxangle_gamma = None
        self._npairs_help = ("A value of 1 indicates that only non-bonded interactions between "
                             "the current residue (i) and the nearest-neighbours are "
                             "taken into account (i-1, i and i+1)")
        self._npairs = None
        self._mdengine = None
        self._noh = None
        self._verbose = None

        server_screen = ServerScreen()
        self._server_valid = server_screen.show_screen_sidebar()

        self._name_server = server_screen._name_server
        self._name_user = server_screen._name_user
        self._ssh_key_options = server_screen._ssh_key_options
        self._path_virtualenv = server_screen._path_virtualenv
        self._working_directory = server_screen._working_directory

    def show_screen(self):

        #   ============================    Welcome Replicate Program   ============================    #

        st.markdown("<h1 style='font-size:32px;'>Replicate Polymer</h1>", unsafe_allow_html=True)

        with st.expander("INFO"):
            st.text(self._about)

        st.markdown("<h1 style='font-size:22px;'>Program options</h1>", unsafe_allow_html=True)
        st.write("Fields with '*' are required")

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
                if st.button("Browse file", key=f"browse_{input_key}"):
                    handle_button_click(option, input_key, "browse")

            with col2:
                if self._input_options[input_key]:
                    if st.button("Remove file", key=f"remove_{input_key}"):
                        handle_button_click(option, input_key, "remove")

        st.session_state["input_options"] = self._input_options

        #   ============================    Images options   ============================    #

        self._image_x = (st.number_input("Number of images to replicate in dimension X*", min_value=1, step=1, value=1))
        st.session_state.image_x = self._image_x

        self._image_y = (st.number_input("Number of images to replicate in dimension Y*", min_value=1, step=1, value=1))
        st.session_state.image_y = self._image_y

        self._image_z = (st.number_input("Number of images to replicate in dimension Z*", min_value=1, step=1, value=1))
        st.session_state.image_z = self._image_z

        #   ============================    Index options   ============================    #

        self._index = st.text_input("Indices of atoms to be removed from the PDB", st.session_state.get("index", ""))
        st.session_state.index = self._index

        #   ============================    Boxlength options   ============================    #

        self._boxlength_a = (st.number_input("Box length (a) in nanometers", min_value=0.0, step=0.1, value=None))
        st.session_state.boxlength_a = self._boxlength_a

        self._boxlength_b = (st.number_input("Box length (b) in nanometers", min_value=0.0, step=0.1, value=None))
        st.session_state.boxlength_b = self._boxlength_b

        self._boxlength_c = (st.number_input("Box length (c) in nanometers", min_value=0.0, step=0.1, value=None))
        st.session_state.boxlength_c = self._boxlength_c

        #   ============================    Boxangle options   ============================    #

        self._boxangle_alpha = (st.number_input("Box angle (alpha) in degrees", min_value=0.0, step=0.1, value=None))
        st.session_state.boxangle_alpha = self._boxangle_alpha

        self._boxangle_beta = (st.number_input("Box angle (beta) in degrees", min_value=0.0, step=0.1, value=None))
        st.session_state.boxangle_beta = self._boxangle_beta

        self._boxangle_gamma = (st.number_input("Box angle (gamma) in degrees", min_value=0.0, step=0.1, value=None))
        st.session_state.boxangle_gamma = self._boxangle_gamma

        #   ============================    Npairs options   ============================    #

        self._npairs = (st.number_input("Monomer or residue inclusions", step=1, value=None, help=self._npairs_help))
        st.session_state.npairs = self._npairs

        #   ============================    MDengine options   ============================    #

        self._mdengine = st.text_input("MD package to perform calculations", st.session_state.get("mdengine", ""))
        st.session_state.mdengine = self._mdengine

        #   ============================    NOH options   ============================    #

        self._noh = st.toggle("Remove hydrogens for a united atom representation",
                              st.session_state.get("noh", False))
        st.session_state.noh = self._noh

        #   ============================    Verbose options   ============================    #

        self._verbose = st.toggle("Verbose checking of angles and dihedral",
                                  st.session_state.get("verbose", False))
        st.session_state.verbose = self._verbose

        #   ============================    Clean and run buttons   ============================    #
        left, right = st.columns(2)
        #   ========    Clean button   ========    #
        with right:
            clean_options("Replicate Polymer")
        #   ========    Run button   ========    #
        with left:
            button_run = st.button("RUN REPLICATE POLYMER")
        if button_run:
            if not self._server_valid:
                st.error("Please check if server options are filled correctly")
                return

            structure_file_path = self._input_options.get("input_file_000", "")
            xml_file_path = self._input_options.get("input_file_001", "")
            impropers_file_path = self._input_options.get("input_file_002", "")

            if not structure_file_path:
                st.error("Please upload a pdb file before running the program")
                return

            if not xml_file_path:
                st.error("Please upload a FORCEFIELD file before running the program")
                return

            st.session_state["input_options"] = self._input_options

            if not self._image_x:
                st.error("Please enter the number of images to Replicate in Dimension X")
                return

            if not self._image_y:
                st.error("Please enter the number of images to Replicate in Dimension Y")
                return

            if not self._image_z:
                st.error("Please enter the number of images to Replicate in Dimension Z")
                return

            if not (isinstance(self._image_x, int) and self._image_x >= 1 and self._image_x % 1 == 0 and
                    isinstance(self._image_y, int) and self._image_y >= 1 and self._image_y % 1 == 0 and
                    isinstance(self._image_z, int) and self._image_z >= 1 and self._image_z % 1 == 0):
                st.error("Please enter valid integer values greater than or equal "
                         "to 1 for Number of Images before running the program")
                return

            stop_button = st.button("STOP")
            if stop_button:
                st.warning("Replicate Polymer program has been stopped")

            temp_dir = tempfile.mkdtemp()
            try:
                structure_file_path = save_uploaded_file(structure_file_path, temp_dir)
                xml_file_path = save_uploaded_file(xml_file_path, temp_dir)
                impropers_file_path = save_uploaded_file(impropers_file_path,
                                                         temp_dir) if impropers_file_path else None

                with st.spinner("Running Replicate Polymer. Please wait..."):
                    warning_close_interface = st.warning("Do not close the interface "
                                                         "while Replicate Polymer is running.")
                    output, error, output_folder = run_replicate_cmd_remote(self._name_server, self._name_user,
                                                                            self._ssh_key_options,
                                                                            self._path_virtualenv,
                                                                            self._working_directory,
                                                                            structure_file_path,
                                                                            xml_file_path,
                                                                            impropers_file_path,
                                                                            self._image_x, self._image_y, self._image_z,
                                                                            self._index,
                                                                            self._boxlength_a, self._boxlength_b,
                                                                            self._boxlength_c,
                                                                            self._boxangle_alpha, self._boxangle_beta,
                                                                            self._boxangle_gamma,
                                                                            self._npairs, self._mdengine,
                                                                            self._noh, self._verbose)
                    warning_close_interface.empty()
                    st.success("Job Done!")

                    #   ============================    Getting output files    ============================    #

                    output_file_paths = [os.path.join(output_folder, f) for f in os.listdir(output_folder)]

                    show_info_log_content(output_file_paths)
                    tar_file_path = create_tar_gz(output_folder, output_file_paths)
                    download_link = (f'<a href="data:application/tar+gzip;base64,'
                                     f'{base64.b64encode(open(tar_file_path, "rb").read()).decode()}'
                                     f'" download="replicate_polymer_output_files.tar.gz">'
                                     f'Download Replicate Polymer output files</a>')
                    st.markdown(download_link, unsafe_allow_html=True)

            finally:
                shutil.rmtree(temp_dir)
