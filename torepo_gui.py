import streamlit as st
from PIL import Image
from torepo_gui_external.topology_gui import TopologyScreen
from torepo_gui_external.replicate_gui import ReplicateScreen
from torepo_gui_external.polyanagro_gui import run_page_polyanagro
from torepo_gui_external.stmol_viewer import StmolScreen


#   ============================    Title configuration   ============================    #


def main_page():
    st.markdown("""
    <style>
    @keyframes move {
        0% { transform: translateX(-100%); }
        100% { transform: translateX(100%); }
    }

    .moving-title {
        width: 100%;
        overflow: hidden;
        white-space: nowrap;
        box-sizing: border-box;
        animation: move 15s linear infinite;
    }
    </style>
    <div class="moving-title">
        <h1>Welcome to TOREPO</h1>
    </div>
    """, unsafe_allow_html=True)


#   ============================    Program selection   ============================    #


def main():

    main_page()
    st.sidebar.markdown("<h1 style='font-size:32px;'>Program selection</h1>", unsafe_allow_html=True)
    page_selection = st.sidebar.selectbox('Please select a program',
                                          ['Select a program', 'Topology', 'Replicate Polymer', 'Polyanagro'])

    # Run selected page
    if page_selection == "Topology":
        topology_obj = TopologyScreen()
        topology_obj.show_screen()
    elif page_selection == "Replicate Polymer":
        # run_page_replicate()
        replicate_obj = ReplicateScreen()
        replicate_obj.show_screen()
    elif page_selection == "Polyanagro":
        run_page_polyanagro()

    stmol_viewer = st.sidebar.toggle("Display Stmol Viewer")
    if stmol_viewer:
        stmol_obj = StmolScreen()
        stmol_obj.show_screen()

#   ============================    Logo configuration   ============================    #


if __name__ == '__main__':

    icon = Image.open('biophym_logo.ico')

    st.set_page_config(
        page_title='TOREPO',
        page_icon=icon,
        layout='centered',
        initial_sidebar_state='auto',
        # Items to redirect to other pages
        menu_items={
            'Get help': 'https://github.com/cggar98/TOREPO',
            'About': '**BIOPHYM (https://www.biophym.iem.csic.es/)**'
            }
    )

    #   ============================    Colours program (CANNOT CHANGE COLOURS)   ============================    #

    # Settings custom colors
    body_bg_color = "#0091FF"  # Light blue background
    text_color = "#FFFFFF"  # White text

    # Applying styles with HTML and CSS
    page_bg_img = f"""
            <style>
                body {{
                    background-color: {body_bg_color};
                    color: {text_color};
                }}
                .sidebar {{
                    background-color: {body_bg_color};  /* Color de fondo del sidebar */
                    color: {text_color};  /* Color del texto del sidebar */
                }}
            </style>
            """

    # Configuring the page with the custom style
    st.markdown(page_bg_img, unsafe_allow_html=True)

    main()
