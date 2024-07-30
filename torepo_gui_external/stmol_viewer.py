import streamlit as st
import py3Dmol
import string
from stmol import showmol


class StmolScreen:
    def __init__(self):
        self._chain_number = None
        self._structure_style = None
        self._residue_name = None
        self._atom_number = None
        self._surf_transp = None
        self._residues_selected_color = None
        self._chains_selected_color = None
        self._atoms_selected_color = None
        self._backbone_color = None
        self._structure_color = None
        self._viewer_background_color = None

    def show_screen(self):

        file_to_see = st.file_uploader('Select a molecule or polymer file', type=["pdb"])

        #   ============================    Viewer options   ============================    #

        st.sidebar.markdown("<h1 style='font-size:22px;'>Viewer options </h1>", unsafe_allow_html=True)

        self._structure_style = st.sidebar.selectbox('Structure style', ['Select a style', 'cartoon', 'line', 'cross',
                                                                         'stick', 'sphere'])
        self._residue_name = st.sidebar.multiselect(label="Residue name", options=list(string.ascii_uppercase))
        self._chain_number = st.sidebar.multiselect(label="Chain number", options=list(range(1, 5000)))
        self._atom_number = st.sidebar.multiselect(label="Atom number", options=list(range(1, 100000)))
        self._surf_transp = st.sidebar.slider("Surface transparency", min_value=0.0, max_value=1.0, value=0.0)
        self._residues_selected_color = st.sidebar.color_picker(label="Residues selected color", value="#FFA500")
        self._chains_selected_color = st.sidebar.color_picker(label="Chains selected color", value="#F90000")
        self._atoms_selected_color = st.sidebar.color_picker(label="Atoms selected color", value="#00FF00")
        self._backbone_color = st.sidebar.color_picker(label="Backbone color", value="#B7B7B7")
        self._structure_color = st.sidebar.color_picker(label="Structure color", value="#FFFFFF")
        self._viewer_background_color = st.sidebar.color_picker('Viewer background color', '#000000')

        #   ============================    Viewer output   ============================    #

        if file_to_see is not None:
            file_data = file_to_see.read().decode("utf-8")

            viewer_width = 700
            viewer_height = 700
            xyzview = py3Dmol.view(width=viewer_width, height=viewer_height)

            xyzview.addModel(file_data, 'pdb')
            xyzview.setStyle({self._structure_style: {'color': 'spectrum'}})
            xyzview.addSurface(py3Dmol.VDW, {"opacity": self._surf_transp, "color": self._backbone_color},
                               {"hetflag": False}, viewer=(0,0))  # Surface transparence does not work

            stick_radius = 0.2

            xyzview.addStyle({"elem": "C", "hetflag": True},
                             {"stick": {"color": self._structure_color, "radius": stick_radius}})

            xyzview.addStyle({"hetflag": True},
                             {"stick": {"radius": stick_radius}})
            

            for resn in self._residue_name:
                xyzview.addStyle({"chain": self._residue_name},
                                 {"stick": {"color": self._residues_selected_color, "radius": stick_radius}})


            for hl_resi in self._chain_number:
                xyzview.addStyle({"chain": self._residue_name, "resi": hl_resi, "elem": "C"},
                                 {"stick": {"color": self._chains_selected_color, "radius": stick_radius}})
                xyzview.addStyle({"chain": self._residue_name, "resi": hl_resi},
                                 {"stick": {"radius": stick_radius}})

            for hl_resi in self._chain_number:
                xyzview.addResLabels({"chain": self._residue_name, "resi": hl_resi},
                                     {"backgroundColor": "lightgreen", "fontColor": "black",
                                      "backgroundOpacity": 0.5})
                #   La posicion del visor se resetea al cambiar los colores

            for hl_atom in self._atom_number:
                xyzview.setStyle({'serial': self._atom_number}, {'stick': {'color': self._atoms_selected_color}})

            for hl_atom in self._atom_number:
                xyzview.addResLabels({"serial": self._atom_number},
                                     {"backgroundColor": "lightgreen", "fontColor": "black",
                                      "backgroundOpacity": 0.5})
            # else:
            #     # Styling and labeling specific atoms
            #     for hl_resi in self._chain_number:
            #         for hl_atom in self._atom_number:
            #             xyzview.addStyle({
            #                 "chain": self._residue_name,
            #                 "resi": hl_resi,
            #                 "serial": hl_atom
            #             }, {"stick": {"color": self._atoms_selected_color, "radius": stick_radius}})
            #
            #             xyzview.addResLabels({
            #                 "chain": self._residue_name,
            #                 "resi": hl_resi,
            #                 "serial": hl_atom
            #             }, {"backgroundColor": "lightgreen", "fontColor": "black", "backgroundOpacity": 0.5})

            xyzview.setBackgroundColor(self._viewer_background_color)
            xyzview.zoomTo()
            showmol(xyzview, width=viewer_width, height=viewer_height)
