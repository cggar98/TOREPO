import py3Dmol

def test_surface_transparency():
    viewer_width = 700
    viewer_height = 700
    xyzview = py3Dmol.view(width=viewer_width, height=viewer_height)

    # Sample PDB data for testing
    pdb_data = """
    ATOM      1  N   MET A   1      20.154  34.425  27.337  1.00 20.00           N
    ATOM      2  CA  MET A   1      19.183  33.414  26.683  1.00 20.00           C
    ATOM      3  C   MET A   1      19.982  33.076  25.306  1.00 20.00           C
    ATOM      4  O   MET A   1      19.847  32.086  24.695  1.00 20.00           O
    """

    xyzview.addModel(pdb_data, 'pdb')

    # Set styles
    xyzview.setStyle({'stick': {'color': 'spectrum'}})

    # Add surface with transparency
    xyzview.addSurface(py3Dmol.SAS, {"opacity": 0.5, "color": "blue"}, {"hetflag": False})

    # Set background color
    xyzview.setBackgroundColor('white')

    # Zoom and show
    xyzview.zoomTo()
    xyzview.show()
