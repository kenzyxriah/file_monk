import streamlit as st

st.set_page_config(page_title="File Monk", page_icon="📁", layout="wide")

home_page = st.Page(
    page="pages/home.py",
    title="Home",
    icon="🏠",
    default=True
)

converter_page = st.Page(
    page="pages/converter.py",
    title="Converter",
    icon="🔄"
)

annotator_page = st.Page(
    page="pages/annotator.py",
    title="PDF Annotator",
    icon="🖌️"
)

creator_page = st.Page(
    page="pages/creator.py",
    title="File Creation",
    icon="📝"
)

pg = st.navigation(
    {
        "Welcome": [home_page],
        "Tools": [converter_page, annotator_page, creator_page]
    }
)

pg.run()
