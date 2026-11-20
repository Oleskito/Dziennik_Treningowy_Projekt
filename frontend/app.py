import os
from datetime import date

import requests
import streamlit as st


BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")


def wywolaj_api(metoda, sciezka, **opcje):
    try:
        odpowiedz = requests.request(
            metoda, f"{BACKEND_URL}{sciezka}", timeout=5, **opcje
        )
    except requests.RequestException as blad:
        st.error(f"Nie udało się połączyć z backendem. {blad}")
        return None

    try:
        wynik = odpowiedz.json()
    except requests.JSONDecodeError:
        st.error(f"Nieprawidłowa odpowiedź backendu (HTTP {odpowiedz.status_code}).")
        return None

    if not odpowiedz.ok:
        st.error(f"Błąd API (HTTP {odpowiedz.status_code}).")
        st.write(wynik.get("detail", wynik) if isinstance(wynik, dict) else wynik)
        return None

    return wynik


def formularz_treningu(klucz):
    with st.form(klucz, clear_on_submit=True):
        nazwa = st.text_input("Nazwa treningu")
        dzien = st.date_input("Data treningu", value=date.today())
        if st.form_submit_button("Zapisz trening"):
            return {"nazwa": nazwa, "data": str(dzien) if dzien else None}

    return None


def wybierz_trening(treningi, klucz):
    wedlug_id = {trening["id"]: trening for trening in treningi}
    etykiety = {
        identyfikator: f"{trening['nazwa']} · {trening['data']} · #{identyfikator}"
        for identyfikator, trening in wedlug_id.items()
    }

    # Streamlit tworzy nowy widget po zmianie etykiet. Zachowujemy wybrane ID.
    klucz_etykiet = f"{klucz}_etykiety"
    if st.session_state.get(klucz_etykiet) != etykiety:
        poprzedni = st.session_state.get(klucz)
        st.session_state[klucz] = poprzedni if poprzedni in etykiety else next(iter(etykiety))
        st.session_state[klucz_etykiet] = etykiety

    wybrane_id = st.selectbox("Wybierz trening", etykiety, format_func=etykiety.get, key=klucz)
    return wedlug_id[wybrane_id]


def pokaz_treningi():
    st.title("📋 Treningi")
    treningi = wywolaj_api("GET", "/treningi")
    if treningi is None:
        return
    if not treningi:
        st.info("Brak aktywnych treningów.")
        return

    wybrany = wybierz_trening(treningi, "aktywny_trening")
    sciezka = f"/treningi/{wybrany['id']}"
    trening = wywolaj_api("GET", sciezka)
    if trening is None:
        return

    st.subheader("Ćwiczenia w treningu")
    if trening["cwiczenia"]:
        st.table([
            {
                "Ćwiczenie": cwiczenie["nazwa_cwiczenia"],
                "Serie": cwiczenie["serie"],
                "Powtórzenia": cwiczenie["powtorzenia"],
                "Ciężar (kg)": cwiczenie["ciezar_kg"],
            }
            for cwiczenie in trening["cwiczenia"]
        ])
    else:
        st.info("Ten trening nie zawiera ćwiczeń.")

    if st.button("Usuń trening", key=f"usun_{trening['id']}"):
        if wywolaj_api("DELETE", sciezka) is not None:
            st.session_state["komunikat"] = "Usunięto trening."
            st.rerun()


def dodaj_trening():
    st.title("➕ Dodaj trening")
    dane = formularz_treningu("nowy_trening")
    if dane is not None:
        trening = wywolaj_api("POST", "/treningi", json=dane)
        if trening is not None:
            st.success(f"Dodano trening #{trening['id']}.")


def pokaz_status():
    st.title("🩺 Status połączenia")
    if st.button("Sprawdź stan"):
        status = wywolaj_api("GET", "/health")
        if status is not None:
            st.success("Backend i baza danych działają poprawnie.")
            st.json(status)


st.set_page_config(page_title="Dziennik Treningowy", page_icon="🏋️", layout="wide")
st.sidebar.title("🏋️ Dziennik treningowy")
ekran = st.sidebar.radio(
    "Przejdź do", ["Treningi", "Dodaj trening", "Status połączenia"]
)

komunikat = st.session_state.pop("komunikat", None)
if komunikat:
    st.success(komunikat)

if ekran == "Treningi":
    pokaz_treningi()
elif ekran == "Dodaj trening":
    dodaj_trening()
else:
    pokaz_status()
