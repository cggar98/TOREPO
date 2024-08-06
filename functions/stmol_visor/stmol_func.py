import streamlit as st
import os
from tkinter import filedialog


def handle_button_click(option, input_key, action):
    if action == "browse":
        file_selection_options(option, input_key)
    elif action == "remove":
        st.session_state["input_options"][input_key] = ""
        st.experimental_rerun()


def file_selection_options(option, input_key):
    wkdir = os.getcwd()
    if option == "Select a molecule or polymer file":
        filetypes = [("PDB files", "*.pdb")]

    input_filename = filedialog.askopenfilename(
        initialdir=wkdir,
        title="Select a file",
        filetypes=filetypes
    )

    if input_filename:
        st.session_state["input_options"][input_key] = input_filename
        st.experimental_rerun()
