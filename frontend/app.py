import os

import requests
import streamlit as st

st.set_page_config(page_title="Dziennik Treningowy")

st.title("Projekt - Dziennik Treningowy")
st.write("Panel testowy KM1")
BACKEND_URL = os.getenv("BACKEND_URL")

if st.button("Sprawdź status"):
    try:
        odpowiedz = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if odpowiedz.status_code == 200:
            dane = odpowiedz.json()
            st.success("Połączono z backendem!")
            st.json(dane)
        else:
            st.error(f"Backend - kod błędu: {odpowiedz.status_code}")
    except requests.exceptions.RequestException as blad:
        st.error(f"Nie udało się nawiązać połączenia z backendem: {blad}")
