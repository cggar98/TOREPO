import streamlit as st
from PIL import Image


from torepo_gui_external.topology_gui import run_page_topology
from torepo_gui_external.replicate_gui import run_page_replicate
from polyanagro_gui import run_page_polyanagro




# =================================================================================================
def main_page():

    st.title('Welcome to TOREPO')


# =================================================================================================
def main():

    main_page()
    st.sidebar.subheader('Program selection')
    page_selection = st.sidebar.selectbox('Please select a program',
                                          ['Topology', 'Replicate Polymer', 'Polyanagro'])

    # Run selected page
    if page_selection == "Topology":
        run_page_topology()
    elif page_selection == "Replicate Polymer":
        run_page_replicate()
    elif page_selection == "Polyanagro":
        run_page_polyanagro()


# =============================================================================
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
            'Get help': 'https://github.com/jrdcasa?tab=repositories',
            'About': '**BIOPHYM (https://www.biophym.iem.csic.es/)**'
            },
    )


    #####   I CANNNOT FIND A WAY TO CHANGE THE COLORS   #####

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