import os
from datetime import date
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from psycopg.rows import dict_row
from pydantic import BaseModel, StringConstraints

app = FastAPI(title="Dziennik Treningowy API")


class NowyTrening(BaseModel):
    data: date
    nazwa: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


@app.exception_handler(RequestValidationError)
async def obsluz_blad_walidacji(zapytanie: Request, blad: RequestValidationError):
    odpowiedz = await request_validation_exception_handler(zapytanie, blad)

    if zapytanie.method == "POST" and zapytanie.url.path == "/treningi":
        odpowiedz.status_code = 400
    return odpowiedz


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
    try:
        with polacz_z_baza() as polaczenie:
            polaczenie.execute("SELECT 1")
        return {"status_backendu": "ok", "status_bazy": "ok"}
    except Exception as blad:
        raise HTTPException(
            status_code=503, detail=f"Brak połączenia z bazą: {str(blad)}"
        )


@app.get("/treningi")
def pobierz_treningi():
    with polacz_z_baza() as polaczenie:
        return polaczenie.execute(
            "SELECT id, data, nazwa FROM treningi ORDER BY id"
        ).fetchall()


@app.get("/treningi/{id_treningu}")
def pobierz_trening(id_treningu: int):
    with polacz_z_baza() as polaczenie:
        trening = polaczenie.execute(
            "SELECT id, data, nazwa FROM treningi WHERE id = %s",
            (id_treningu,),
        ).fetchone()

        if trening is None:
            raise HTTPException(
                status_code=404,
                detail="Nie znaleziono treningu",
            )
        return trening


@app.post("/treningi", status_code=201)
def dodaj_trening(trening: NowyTrening):
    with polacz_z_baza() as polaczenie:
        return polaczenie.execute(
            "INSERT INTO treningi (data, nazwa) VALUES (%s, %s) RETURNING id, data, nazwa",
            (trening.data, trening.nazwa),
        ).fetchone()


@app.delete("/treningi/{id_treningu}")
def usun_trening(id_treningu: int):
    with polacz_z_baza() as polaczenie:
        trening = polaczenie.execute(
            "DELETE FROM treningi WHERE id = %s RETURNING id",
            (id_treningu,),
        ).fetchone()

        if trening is None:
            raise HTTPException(status_code=404, detail="Nie znaleziono treningu")

        return {"komunikat": "Trening został usunięty", "id": trening["id"]}
