from datetime import datetime

import psycopg
import pytest
from fastapi.testclient import TestClient

from app import main


DANE_TRENINGU = {"data": "2026-11-20", "nazwa": "Trening testowy", "autor": "Ola"}
DANE_EDYCJI = {"data": "2026-11-21", "nazwa": "Trening po edycji", "autor": "Iga"}
BRAK_TRENINGU = "/treningi/2147483647"


@pytest.fixture(scope="session")
def klient():
    with TestClient(main.app) as klient_testowy:
        yield klient_testowy


@pytest.fixture
def adres_treningu(klient):
    odpowiedz = klient.post("/treningi", json=DANE_TRENINGU)
    assert odpowiedz.status_code == 201
    return f"/treningi/{odpowiedz.json()['id']}"


def test_health(klient, monkeypatch):
    odpowiedz = klient.get("/health")
    assert odpowiedz.status_code == 200
    assert odpowiedz.json() == {"status_backendu": "ok", "status_bazy": "ok"}

    def brak_polaczenia():
        raise psycopg.OperationalError("Brak połączenia")

    monkeypatch.setattr(main, "polacz_z_baza", brak_polaczenia)
    assert klient.get("/health").status_code == 503


def test_lista_treningow(klient):
    odpowiedz = klient.get("/treningi")
    assert odpowiedz.status_code == 200
    assert {trening["id"] for trening in odpowiedz.json()} >= {1, 2}
    assert klient.get("/treningi", params={"archiwalne": "abc"}).status_code == 400


def test_szczegoly_treningu(klient):
    odpowiedz = klient.get("/treningi/1")
    assert odpowiedz.status_code == 200
    trening = odpowiedz.json()
    assert trening["id"] == 1
    assert len(trening["cwiczenia"]) == 2
    assert trening["cwiczenia"][0]["nazwa_cwiczenia"] == "Wyciskanie na maszynie"

    assert klient.get("/treningi/abc").status_code == 400
    assert klient.get(BRAK_TRENINGU).status_code == 404


def test_dodanie_treningu(klient):
    odpowiedz = klient.post("/treningi", json=DANE_TRENINGU)
    assert odpowiedz.status_code == 201
    assert odpowiedz.json()["nazwa"] == DANE_TRENINGU["nazwa"]

    bledne_dane = {**DANE_TRENINGU, "nazwa": " "}
    assert klient.post("/treningi", json=bledne_dane).status_code == 400


def test_edycja_treningu(klient, adres_treningu):
    odpowiedz = klient.put(adres_treningu, json=DANE_EDYCJI)
    assert odpowiedz.status_code == 200
    assert odpowiedz.json()["nazwa"] == DANE_EDYCJI["nazwa"]

    assert klient.put(adres_treningu, json={}).status_code == 400
    assert klient.put(BRAK_TRENINGU, json=DANE_EDYCJI).status_code == 404


def test_archiwizacja_treningu(klient, adres_treningu):
    assert klient.request("DELETE", adres_treningu, json={}).status_code == 400
    assert klient.request("DELETE", BRAK_TRENINGU, json={"autor": "Jan"}).status_code == 404

    odpowiedz = klient.request("DELETE", adres_treningu, json={"autor": "Jan"})
    assert odpowiedz.status_code == 200
    trening_id = odpowiedz.json()["id"]
    assert klient.get(adres_treningu).status_code == 404

    archiwum = klient.get("/treningi", params={"archiwalne": "true"})
    assert archiwum.status_code == 200
    assert trening_id in {trening["id"] for trening in archiwum.json()}


def test_historia_zmian(klient, adres_treningu):
    assert klient.put(adres_treningu, json=DANE_EDYCJI).status_code == 200
    assert klient.request("DELETE", adres_treningu, json={"autor": "Jan"}).status_code == 200

    odpowiedz = klient.get(f"{adres_treningu}/history")
    assert odpowiedz.status_code == 200
    historia = odpowiedz.json()
    assert [(wpis["operacja"], wpis["autor"]) for wpis in historia] == [
        ("usuniecie", "Jan"),
        ("edycja", "Iga"),
        ("dodanie", "Ola"),
    ]
    assert all(datetime.fromisoformat(wpis["czas"]).utcoffset() is not None for wpis in historia)
    assert historia[1]["przed"]["nazwa"] == DANE_TRENINGU["nazwa"]
    assert historia[1]["po"]["nazwa"] == DANE_EDYCJI["nazwa"]

    assert klient.get("/treningi/abc/history").status_code == 400
    assert klient.get(f"{BRAK_TRENINGU}/history").status_code == 404
