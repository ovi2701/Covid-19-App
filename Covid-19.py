import streamlit as st

import Prediction
import Statistics

PAGES = {
    "Covid-19 Statistics": Statistics,
    "Covid-19 Prediction": Prediction
}
st.sidebar.title('MENU')
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
page = PAGES[selection]
page.app()


