import os

import psycopg
from fastapi import FastAPI
from psycopg.rows import dict_row

app = FastAPI(title="Dziennik Treningowy API")


def polacz_z_baza():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=5432,
        row_factory=dict_row,
    )


def sprawdz_polaczenie_z_baza():
    try:
        polaczenie = polacz_z_baza()
        polaczenie.close()
        return "Połaczono z bazą postgres"
    except Exception as blad:
        return f"Błąd połączenia z bazą: {str(blad)}"


@app.get("/")
def strona_glowna():
    return {"komunikat": "Dziennik Treningowy - Backend działa poprawnie!"}


@app.get("/health")
def status_systemu():
    # Endpoint sprawdzający połączenie frontendu z backendem i backendu z bazą
    stan_bazy = sprawdz_polaczenie_z_baza()
    return {"status_backendu": "ok", "status_bazy": stan_bazy}


@app.get("/treningi")
def pobierz_treningi():
    with polacz_z_baza() as polaczenie:
        return polaczenie.execute("SELECT id, data, nazwa FROM treningi ORDER BY id").fetchall()