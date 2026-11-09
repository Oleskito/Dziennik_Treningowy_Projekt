import os
from datetime import date

import requests
import streamlit as st

st.set_page_config(page_title="Dziennik Treningowy", page_icon="🏋️", layout="wide")

BACKEND_URL = os.getenv("BACKEND_URL")

# Menu nawigacyjne
st.sidebar.title("🏋️ Menu Aplikacji")
wybrany_ekran = st.sidebar.radio(
    "Przejdź do:",
    [
        "📋 Lista treningów i usuwanie",
        "➕ Dodaj nowy trening",
        "🩺 Status połączenia (/health)",
    ],
)

st.sidebar.markdown("---")
st.sidebar.caption(f"Połączono z: `{BACKEND_URL}`")


# PRZEGLĄD TRENINGÓW I USUWANIE (GET /treningi, DELETE /treningi/{id})

if wybrany_ekran == "📋 Lista treningów i usuwanie":
    st.title("📋 Twoje Treningi")
    st.write("Podgląd zapisanych jednostek treningowych oraz zarządzanie wpisami.")

    naglowek_lewy, naglowek_prawy = st.columns([5, 1])
    with naglowek_prawy:
        if st.button("🔄 Odśwież", use_container_width=True):
            st.rerun()

    try:
        odpowiedz = requests.get(f"{BACKEND_URL}/treningi", timeout=5)

        if odpowiedz.status_code == 200:
            lista_treningow = odpowiedz.json()

            if not lista_treningow:
                st.info("Brak treningów. Dodaj swój pierwszy trening w innym ekranie.")
            else:
                for t in lista_treningow:
                    with st.container(border=True):
                        kol_id, kol_opis, kol_akcja = st.columns([1, 6, 2])

                        with kol_id:
                            st.metric(label="ID", value=t["id"])

                        with kol_opis:
                            st.subheader(t["nazwa"])
                            st.write(f"📅 **Data:** `{t['data']}`")

                        with kol_akcja:
                            st.write("")
                            if st.button(
                                "🗑️ Usuń",
                                key=f"usun_{t['id']}",
                                use_container_width=True,
                            ):
                                del_res = requests.delete(
                                    f"{BACKEND_URL}/treningi/{t['id']}", timeout=5
                                )
                                if del_res.status_code == 200:
                                    st.success(f"Pomyślnie usunięto trening #{t['id']}")
                                    st.rerun()
                                elif del_res.status_code == 404:
                                    st.warning("Trening już nie istnieje w bazie.")
                                    st.rerun()
                                else:
                                    st.error(
                                        f"Błąd podczas usuwania: {del_res.status_code}"
                                    )
        else:
            st.error(f"Backend zwrócił kod błędu: {odpowiedz.status_code}")

    except requests.exceptions.RequestException as e:
        st.error(f"Nie udało się połączyć z backendem: {e}")


# FORMULARZ DODAWANIA NOWEGO TRENINGU (POST /treningi)

elif wybrany_ekran == "➕ Dodaj nowy trening":
    st.title("➕ Dodaj Nowy Trening")
    st.write(
        "Wprowadź dane sesji treningowej. Backend dokona walidacji przesłanych pól."
    )

    with st.form("formularz_nowy_trening", clear_on_submit=True):
        nazwa_treningu = st.text_input(
            "Nazwa treningu:", placeholder="np. Góra ciała - Siła / Sesja Boulderingowa"
        )
        data_treningu = st.date_input("Data sesji:", value=date.today())

        przycisk_zapisz = st.form_submit_button(
            "💾 Zapisz w bazie", use_container_width=True
        )

        # Przygotowanie JSON
        if przycisk_zapisz:
            dane_treningu = {"data": str(data_treningu), "nazwa": nazwa_treningu}

            try:
                odpowiedz = requests.post(
                    f"{BACKEND_URL}/treningi", json=dane_treningu, timeout=5
                )

                if odpowiedz.status_code == 201:
                    wynik = odpowiedz.json()
                    st.success(
                        f"✅ Dodano trening: **{wynik['nazwa']}** (ID: {wynik['id']}) na dzień {wynik['data']}"
                    )
                elif odpowiedz.status_code == 400:
                    st.error("❌ Błąd walidacji danych (400 Bad Request)")
                    st.json(odpowiedz.json())
                else:
                    st.error(f"Błąd serwera: {odpowiedz.status_code}")

            except requests.exceptions.RequestException as e:
                st.error(f"Błąd połączenia z backendem: {e}")

# TODO
# EKRAN ĆWICZEŃ (DODAWANIE I WYŚWIETLANIE), OPCJONALNIE SORTOWANIE I FILTRACJA


# DIAGNOSTYKA SYSTEMU (/health)

elif wybrany_ekran == "🩺 Status połączenia (/health)":
    st.title("🩺 Status Infrastruktury")
    st.write("Weryfikacja dostępności backendu oraz połączenia backendu z PostgreSQL.")

    if st.button("Sprawdź stan /health", use_container_width=True):
        try:
            odpowiedz = requests.get(f"{BACKEND_URL}/health", timeout=5)
            if odpowiedz.status_code == 200:
                st.success("Wszystkie usługi działają poprawnie (kod 200 OK)")
                st.json(odpowiedz.json())
            else:
                st.error(f"Awaria backendu/bazy (kod {odpowiedz.status_code})")
                st.json(odpowiedz.json())
        except requests.exceptions.RequestException as e:
            st.error(f"Brak łączności z backendem: {e}")
