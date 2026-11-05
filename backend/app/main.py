import os

import psycopg
from fastapi import FastAPI

app = FastAPI(title="Dziennik Treningowy API")


def sprawdz_polaczenie_z_baza():
    try:
        polaczenie = psycopg.connect(
            host=os.getenv("DB_HOST"),
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            port=5432,
        )
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
