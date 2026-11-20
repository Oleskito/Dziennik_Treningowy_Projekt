import os
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated

import psycopg
from fastapi import FastAPI, HTTPException, Path as PathParam, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb
from pydantic import BaseModel, StringConstraints

IdTreningu = Annotated[int, PathParam(ge=1, le=2_147_483_647)]
MIGRACJA_HISTORII = Path(__file__).resolve().parents[1] / "sql" / "historia_treningow.sql"


class ZmianaTreningu(BaseModel):
    autor: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100, pattern=r"^[^\x00]+$")]


class DaneTreningu(ZmianaTreningu):
    data: date
    nazwa: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, pattern=r"^[^\x00]+$")]


def polacz_z_baza():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        port=os.getenv("DB_PORT", "5432"),
        row_factory=dict_row,
    )


@asynccontextmanager
async def cykl_zycia_aplikacji(_app: FastAPI):
    with polacz_z_baza() as polaczenie:
        polaczenie.execute(MIGRACJA_HISTORII.read_text(encoding="utf-8"))
    yield


app = FastAPI(title="Dziennik Treningowy API", lifespan=cykl_zycia_aplikacji)


@app.exception_handler(RequestValidationError)
async def obsluz_blad_walidacji(zapytanie: Request, blad: RequestValidationError):
    odpowiedz = await request_validation_exception_handler(zapytanie, blad)
    odpowiedz.status_code = 400
    return odpowiedz


def pobierz_trening_do_zmiany(polaczenie, id_treningu):
    trening = polaczenie.execute(
        """
        SELECT id, data, nazwa FROM treningi
        WHERE id = %s AND usunieto_o IS NULL FOR UPDATE
        """,
        (id_treningu,),
    ).fetchone()
    if trening is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono treningu")
    return trening


def dane_json(trening):
    if trening is None:
        return None
    return Jsonb({"data": trening["data"].isoformat(), "nazwa": trening["nazwa"]})


def zapisz_historie(polaczenie, id_treningu, operacja, autor, *, przed=None, po=None):
    polaczenie.execute(
        """
        INSERT INTO historia_treningow (trening_id, operacja, autor, przed, po)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (id_treningu, operacja, autor, dane_json(przed), dane_json(po)),
    )


@app.get("/")
def strona_glowna():
    return {"komunikat": "Dziennik Treningowy - Backend działa poprawnie!"}


@app.get("/health")
def status_systemu():
    try:
        with polacz_z_baza() as polaczenie:
            polaczenie.execute("SELECT 1")
        return {"status_backendu": "ok", "status_bazy": "ok"}
    except psycopg.Error as blad:
        raise HTTPException(status_code=503, detail="Brak połączenia z bazą") from blad


@app.get("/treningi")
def pobierz_treningi(archiwalne: bool = False):
    with polacz_z_baza() as polaczenie:
        return polaczenie.execute(
            """
            SELECT id, data, nazwa FROM treningi
            WHERE (usunieto_o IS NOT NULL) = %s ORDER BY id
            """,
            (archiwalne,),
        ).fetchall()


@app.get("/treningi/{id_treningu}")
def pobierz_trening(id_treningu: IdTreningu):
    with polacz_z_baza() as polaczenie:
        trening = polaczenie.execute(
            "SELECT id, data, nazwa FROM treningi WHERE id = %s AND usunieto_o IS NULL",
            (id_treningu,),
        ).fetchone()
        if trening is None:
            raise HTTPException(status_code=404, detail="Nie znaleziono treningu")

        trening["cwiczenia"] = polaczenie.execute(
            """
            SELECT id, nazwa_cwiczenia, serie, powtorzenia, ciezar_kg
            FROM cwiczenia WHERE trening_id = %s ORDER BY id
            """,
            (id_treningu,),
        ).fetchall()
        return trening


@app.post("/treningi", status_code=201)
def dodaj_trening(trening: DaneTreningu):
    with polacz_z_baza() as polaczenie:
        nowy = polaczenie.execute(
            "INSERT INTO treningi (data, nazwa) VALUES (%s, %s) RETURNING id, data, nazwa",
            (trening.data, trening.nazwa),
        ).fetchone()
        zapisz_historie(polaczenie, nowy["id"], "dodanie", trening.autor, po=nowy)
        return nowy


@app.put("/treningi/{id_treningu}")
def edytuj_trening(id_treningu: IdTreningu, trening: DaneTreningu):
    with polacz_z_baza() as polaczenie:
        poprzedni = pobierz_trening_do_zmiany(polaczenie, id_treningu)
        zmieniony = polaczenie.execute(
            "UPDATE treningi SET data = %s, nazwa = %s WHERE id = %s RETURNING id, data, nazwa",
            (trening.data, trening.nazwa, id_treningu),
        ).fetchone()
        zapisz_historie(
            polaczenie, id_treningu, "edycja", trening.autor, przed=poprzedni, po=zmieniony
        )
        return zmieniony


@app.delete("/treningi/{id_treningu}")
def usun_trening(id_treningu: IdTreningu, zmiana: ZmianaTreningu):
    with polacz_z_baza() as polaczenie:
        trening = pobierz_trening_do_zmiany(polaczenie, id_treningu)
        polaczenie.execute(
            "UPDATE treningi SET usunieto_o = clock_timestamp() WHERE id = %s",
            (id_treningu,),
        )
        zapisz_historie(polaczenie, id_treningu, "usuniecie", zmiana.autor, przed=trening)
        return {"komunikat": "Trening został usunięty", "id": id_treningu}


@app.get("/treningi/{id_treningu}/history")
def pobierz_historie(id_treningu: IdTreningu):
    with polacz_z_baza() as polaczenie:
        istnieje = polaczenie.execute("SELECT 1 FROM treningi WHERE id = %s", (id_treningu,))
        if istnieje.fetchone() is None:
            raise HTTPException(status_code=404, detail="Nie znaleziono treningu")

        return polaczenie.execute(
            """
            SELECT id, operacja, autor, czas, przed, po FROM historia_treningow
            WHERE trening_id = %s ORDER BY id DESC
            """,
            (id_treningu,),
        ).fetchall()
