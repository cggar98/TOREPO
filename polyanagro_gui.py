import streamlit as st
from polyanagro_gui_external.torsion_density_maps_gui import run_page_2d_torsion
from polyanagro_gui_external.bonded_distribution_gui import run_page_bonded_distribution
from polyanagro_gui_external.energy_analysis_gui import run_page_energy_analysis
from polyanagro_gui_external.info_trj_gui import run_page_info_trj
from polyanagro_gui_external.neighbor_sphere_gui import run_page_neighbor_sphere
from polyanagro_gui_external.pair_distribution_gui import run_page_pair_distribution
from polyanagro_gui_external.polymer_size_gui import run_page_polymer_size
from polyanagro_gui_external.votca_analysis_gui import run_page_votca_analysis


#   ============================    Subprograms mapping   ============================    #


def func_page_polyanagro():
    st.markdown("<h1 style='font-size:32px;'>Polyanagro</h1>", unsafe_allow_html=True)

    page_selection = st.selectbox('Select a subprogram',
                                  ['Select a subprogram', '2D Torsion Density Maps', 'Bonded Distribution',
                                   'Energy Analysis', 'Info TRJ', 'Neighbor Sphere',
                                   'Pair Distribution', 'Polymer Size', 'VOTCA Analysis'])

    # Run selected page
    if page_selection == "2D Torsion Density Maps":
        run_page_2d_torsion()
    elif page_selection == "Bonded Distribution":
        run_page_bonded_distribution()
    elif page_selection == "Energy Analysis":
        run_page_energy_analysis()
    elif page_selection == "Info TRJ":
        run_page_info_trj()
    elif page_selection == "Neighbor Sphere":
        run_page_neighbor_sphere()
    elif page_selection == "Pair Distribution":
        run_page_pair_distribution()
    elif page_selection == "Polymer Size":
        run_page_polymer_size()
    elif page_selection == "VOTCA Analysis":
        run_page_votca_analysis()


def main():
    func_page_polyanagro()


if __name__ == "__main__":
    main()


def run_page_polyanagro():
    func_page_polyanagro()
