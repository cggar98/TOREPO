import streamlit as st
import os
import json
from tkinter import filedialog
from functions.server_options.server_options_functions import (ensure_json_extension, save_options_to_json,
                                                               check_username_and_name_server, verify_virtualenv_path,
                                                               verify_working_directory, clean_server_options)


class ServerScreen:
    def __init__(self):
        self._name_server = None
        self._name_user = None
        self._ssh_key_options = None
        self._path_virtualenv = None
        self._working_directory = None

        self._json_filename = None
        self._input_placeholder = None

        self._use_queuing_system = None
        self._submit_with = None
        self._check_status = None
        self._add_mpi = None
        self._add_cpus = None
        self._script_before_run = None
        self._script_after_run = None

    def show_screen_sidebar(self):

        #   ============================    Load server options   ============================    #

        st.sidebar.markdown("<h1 style='font-size:22px;'>Load server options </h1>", unsafe_allow_html=True)

        self._input_placeholder = st.sidebar.empty()
        self._input_placeholder.text_input("Load file:", key="json_filepath")
        browse_load_file = st.sidebar.button("Browse", key="browse_load")
        if browse_load_file:
            wkdir = os.getcwd()
            filename = filedialog.askopenfilename(initialdir=wkdir,
                                                  title="Select a file containing a server options",
                                                  filetypes=[("JSON files", "*.json")])
            if filename:
                json_filepath = filename
                self._input_placeholder.text_input("Load file:", key="json_input",
                                                   value=json_filepath)
                if json_filepath:
                    try:
                        with open(json_filepath, "r") as f:
                            server_options = json.load(f)
                        if server_options:
                            self._name_server = server_options.get("Name Server*", "")
                            self._name_user = server_options.get("Username*", "")
                            self._ssh_key_options = server_options.get("Key SSH file path*", "")
                            self._path_virtualenv = server_options.get("Virtual environment path*", "")
                            self._working_directory = server_options.get("Working directory*", "")
                            st.session_state.server_options = {"Name Server*": self._name_server,
                                                               "Username*": self._name_user,
                                                               "Key SSH file path*": self._ssh_key_options,
                                                               "Virtual environment path*":
                                                                   self._path_virtualenv,
                                                               "Working directory*": self._working_directory}
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")

        #   ============================    Server options   ============================    #

        st.sidebar.markdown("<h1 style='font-size:22px;'>Server options</h1>", unsafe_allow_html=True)

        st.sidebar.write("Fields with '*' are required")

        #   ========    Clean button   ========    #
        clean_server_options()  # Only clean if you have loaded it
        #   ========    Clean button   ========    #

        server_options = st.session_state.get("server_options", {
            "Name Server*": "",
            "Username*": "",
            "Key SSH file path*": "",
            "Virtual environment path*": "",
            "Working directory*": ""
        })

        self._name_server = st.sidebar.text_input("Name Server*", server_options.get("Name Server*", ""),
                                                  key="name_server")
        self._name_user = st.sidebar.text_input("Username*", server_options.get("Username*", ""))
        self._ssh_key_options = st.sidebar.text_input("Key SSH file path*",
                                                      server_options.get("Key SSH file path*", ""))
        self._path_virtualenv = st.sidebar.text_input("Virtual environment path*",
                                                      server_options.get("Virtual environment path*", ""))
        self._working_directory = st.sidebar.text_input("Working directory*",
                                                        server_options.get("Working directory*", ""))

        st.session_state["server_options"] = {
            "Name Server*": self._name_server,
            "Username*": self._name_user,
            "Key SSH file path*": self._ssh_key_options,
            "Virtual environment path*": self._path_virtualenv,
            "Working directory*": self._working_directory
        }

        #   ============================    Save server options   ============================    #

        st.sidebar.markdown("<h1 style='font-size:22px;'>Save server options </h1>", unsafe_allow_html=True)

        self._json_filename = st.sidebar.text_input("Filename:", key="json_filename")
        if self._json_filename:
            if self._json_filename.strip() and self._name_server and self._name_user and self._ssh_key_options \
                    and self._path_virtualenv and self._working_directory:
                self._json_filename = ensure_json_extension(self._json_filename.strip())
                server_options = save_options_to_json(self._name_server, self._name_user,
                                                      self._ssh_key_options, self._path_virtualenv,
                                                      self._working_directory, self._json_filename)
                button_download = st.sidebar.download_button(label="Save", data=server_options,
                                                             file_name=self._json_filename,
                                                             mime="application/json")
                if button_download:
                    st.sidebar.success(f"File saved successfully as '{self._json_filename}'")

        #     ============================    Queueing system   ============================    #

        st.sidebar.markdown("<h1 style='font-size:22px;'>Queuing system options </h1>", unsafe_allow_html=True)

        self._use_queuing_system = st.sidebar.checkbox("Use queuing system")
        if self._use_queuing_system:
            self._submit_with = st.sidebar.text_input("Submit with")
            self._check_status = st.sidebar.text_input("Check status")
            st.sidebar.write("automatically:")
            self._add_mpi = st.sidebar.checkbox("add PARA_ARCH=MPI")
            self._add_cpus = st.sidebar.checkbox("add PARNODES=number of CPUs")
            self._script_before_run = st.sidebar.text_area("Script before job execution (without #!/bin/sh)",
                                                           height=400)
            self._script_after_run = st.sidebar.text_area("Script after job execution", height=400)

        #     ============================    Check server options    ============================    #

        valid = True
        if not self._name_server or not self._name_user or not self._ssh_key_options \
                or not self._path_virtualenv or not self._working_directory:
            st.sidebar.error("Please enter all fields with '*'")
            valid = False
            return

        if not os.path.exists(self._ssh_key_options):
            st.sidebar.error(f"Key SSH file path '{self._ssh_key_options}' does not exist")
            valid = False
            return

        if not check_username_and_name_server(self._name_server, self._name_user, self._ssh_key_options):
            st.sidebar.error(
                f"Name server '{self._name_server}' or username '{self._name_user}' do not exist. Please, check them")
            valid = False
            return

        if not verify_virtualenv_path(self._name_server, self._name_user, self._ssh_key_options,
                                      self._path_virtualenv):
            st.sidebar.error(
                f"Virtual environment path '{self._path_virtualenv}' does not exist on the remote server")
            valid = False
            return

        if not verify_working_directory(self._name_server, self._name_user,
                                        self._ssh_key_options, self._working_directory):
            st.sidebar.error(f"Working directory '{self._working_directory}' does not exist")
            valid = False
            return
        return True
