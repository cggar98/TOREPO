import streamlit as st

from polyanagro_gui_external.torsion_density_maps_gui import run_page_2D_torsion
from polyanagro_gui_external.bonded_distribution_gui import run_page_bonded_distribution
from polyanagro_gui_external.energy_analysis_gui import run_page_energy_analysis
from polyanagro_gui_external.info_trj_gui import run_page_info_trj
from polyanagro_gui_external.neighbor_sphere_gui import run_page_neighbor_sphere
from polyanagro_gui_external.pair_distribution_gui import run_page_pair_distribution
from polyanagro_gui_external.polymer_size_gui import run_page_polymer_size
from polyanagro_gui_external.votca_analysis_gui import run_page_votca_analysis


# =============================================================================

# Mapping de subprogramas a funciones

subprogram_mapping = {
    "2D Torsion Density Maps": run_page_2D_torsion,
    "Bonded Distribution": run_page_bonded_distribution,
    "Energy Analysis": run_page_energy_analysis,
    "Info TRJ": run_page_info_trj,
    "Neighbor Sphere": run_page_neighbor_sphere,
    "Pair Distribution": run_page_pair_distribution,
    "Polymer Size": run_page_polymer_size,
    "VOTCA Analysis": run_page_votca_analysis,
    }
def func_page_polyanagro():
    st.markdown("<h1 style='font-size:24px;'>Polyanagro</h1>", unsafe_allow_html=True)

    # Selección del subprograma
    selected_subprogram = st.selectbox("Select a subprogram", list(subprogram_mapping.keys()))

    # Obtener la función correspondiente al subprograma seleccionado
    selected_func = subprogram_mapping[selected_subprogram]

    # Ejecutar la función del subprograma
    selected_func()

    # Puedes tener una función principal que llame a func_page_polyanagro() para probarlo
def main():
    func_page_polyanagro()

if __name__ == "__main__":
    main()


# =======================================================================================
def run_page_polyanagro():

    func_page_polyanagro()