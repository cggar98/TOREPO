import streamlit as st
from PIL import Image
from torepo_gui_external.topology_gui import run_page_topology
from torepo_gui_external.replicate_gui_updated import run_page_replicate
from polyanagro_gui import run_page_polyanagro

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

#   ============================    Programs mapping   ============================    #


def main():

    main_page()
    st.sidebar.subheader('Program selection')
    page_selection = st.sidebar.selectbox('Please select a program',
                                          ['Select a program', 'Topology', 'Replicate Polymer', 'Polyanagro'])

    # Run selected page
    if page_selection == "Topology":
        run_page_topology()
    elif page_selection == "Replicate Polymer":
        run_page_replicate()
    elif page_selection == "Polyanagro":
        run_page_polyanagro()

#   ============================    Logo configuration   ============================    #


if __name__ == '__main__':

    # Tab thumbnail
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

    # Configuring the page woth the custom style
    st.markdown(page_bg_img, unsafe_allow_html=True)

    main()
