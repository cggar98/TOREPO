import streamlit as st
import py3Dmol
import string
from stmol import showmol


class StmolScreen:
    def __init__(self):
        self._file_to_see = None
        self._chain_number = None
        self._structure_style = None
        self._residue_name = None
        self._atom_number = None
        self._residues_selected_color = None
        self._chains_selected_color = None
        self._atoms_selected_color = None
        self._backbone_color = None
        self._add_simulation_box = None
        self._simulation_box_color = None
        self._viewer_background_color = None
        self._surf_transp = None

    def show_screen(self):

        self._file_to_see = st.file_uploader('Select a molecule or polymer file', type=["pdb"])

        #   ============================    Viewer options   ============================    #

        st.sidebar.markdown("<h1 style='font-size:22px;'>Viewer options </h1>", unsafe_allow_html=True)

        self._structure_style = st.sidebar.selectbox('Structure style', ['Select a style', 'cartoon', 'line', 'cross',
                                                                         'stick', 'sphere'])
        self._residue_name = st.sidebar.multiselect(label="Residue name", options=list(string.ascii_uppercase))
        self._chain_number = st.sidebar.multiselect(label="Chain number", options=list(range(1, 5000)))
        self._atom_number = st.sidebar.multiselect(label="Atom number", options=list(range(1, 100000)))
        self._residues_selected_color = st.sidebar.color_picker(label="Residues selected color", value="#FFA500")
        self._chains_selected_color = st.sidebar.color_picker(label="Chains selected color", value="#F90000")
        self._atoms_selected_color = st.sidebar.color_picker(label="Atoms selected color", value="#00FF00")
        self._backbone_color = st.sidebar.color_picker(label="Backbone color (NO FUNCIONA)", value="#B7B7B7")
        self._viewer_background_color = st.sidebar.color_picker('Viewer background color', '#000000')
        self._surf_transp = st.sidebar.slider("Surface Transparency", min_value=0.0, max_value=1.0, value=0.0)

        #   ============================    Viewer output   ============================    #

        if self._file_to_see is not None:
            file_data = self._file_to_see.read().decode("utf-8")

            viewer_width = 700
            viewer_height = 700
            stick_radius = 0.4

            xyzview = py3Dmol.view(width=viewer_width, height=viewer_height)
            xyzview.addModel(file_data, 'pdb')
            xyzview.setStyle({self._structure_style: {'color': 'spectrum'}})
            xyzview.addSurface(py3Dmol.VDW, {"opacity": self._surf_transp, "color": self._backbone_color},
                               {"hetflag": False}, viewer=(0, 0))
            # xyzview.addStyle({"hetflag": True},
            #                  {"stick": {"radius": stick_radius}})

            if self._residue_name:
                xyzview.setStyle({}, {'hide': True})
                for resn in self._residue_name:
                    xyzview.addStyle({"chain": self._residue_name},
                                     {f"{self._structure_style}": {"color": self._residues_selected_color,
                                                                   "radius": stick_radius}})

            if self._chain_number:
                xyzview.setStyle({}, {'hide': True})
                for hl_resi in self._chain_number:
                    xyzview.addStyle({"chain": self._residue_name, "resi": hl_resi, "elem": "C"},
                                     {f"{self._structure_style}": {"color": self._chains_selected_color,
                                                                   "radius": stick_radius}})
                for hl_resi in self._chain_number:
                    xyzview.addResLabels({"chain": self._residue_name, "resi": hl_resi},
                                         {"backgroundColor": "lightgreen", "fontColor": "black",
                                          "backgroundOpacity": 0.5})

            if self._atom_number:
                # Hide all atoms first
                xyzview.setStyle({}, {'hide': True})
                # Show only the selected atoms
                for atom in self._atom_number:
                    xyzview.addStyle({"serial": self._atom_number},
                                     {f"{self._structure_style}": {"color": self._atoms_selected_color,
                                                                   "radius": stick_radius}})

            box_dimensions = None
            for line in file_data.splitlines():
                if line.startswith("CRYST1"):
                    parts = line.split()
                    x_dim = float(parts[1])
                    y_dim = float(parts[2])
                    z_dim = float(parts[3])
                    box_dimensions = (x_dim, y_dim, z_dim)
                    break

            # Add simulation box if dimensions were found
            if box_dimensions:
                #   TEST
                self._add_simulation_box = st.toggle("Add simulation box")
                if self._add_simulation_box:
                    self._simulation_box_color = st.color_picker('Simulation box color', '#FFFFFF')
                    center = {'x': box_dimensions[0] / 2, 'y': box_dimensions[1] / 2, 'z': box_dimensions[2] / 2}
                    dimensions = {'w': box_dimensions[0], 'h': box_dimensions[1], 'd': box_dimensions[2]}

                    xyzview.addBox({
                        'center': center,
                        'dimensions': dimensions,
                        'color': f'{self._simulation_box_color}',
                        'opacity': 0.5
                    })

            xyzview.setBackgroundColor(self._viewer_background_color)
            xyzview.zoomTo()
            showmol(xyzview, width=viewer_width, height=viewer_height)
