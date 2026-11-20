# Dziennik treningowy

Projekt z przedmiotu Metody wirtualizacji. Projekt wykonują Kacper Noweta i Aleksander Ostrycharz.

## Uruchomienie

Do uruchomienia projektu potrzebny jest działający Docker z Docker Compose. Uruchom poniższe polecenie w katalogu repozytorium.

```sh
docker compose up --build -d
```

- Frontend Streamlit działa pod adresem [localhost:8501](http://localhost:8501).
- API FastAPI działa pod adresem [localhost:8000](http://localhost:8000). Interaktywna dokumentacja jest dostępna pod [localhost:8000/docs](http://localhost:8000/docs).

Compose ma domyślne ustawienia do uruchomienia lokalnego. Opcjonalny plik `.env` może je nadpisać. Wzór ustawień jest w `.env.example`.

| Zmienna | Domyślna wartość | Znaczenie |
| --- | --- | --- |
| `POSTGRES_DB` | `baza` | Nazwa bazy danych |
| `POSTGRES_USER` | `uzytkownik` | Użytkownik bazy |
| `POSTGRES_PASSWORD` | `haslo` | Hasło użytkownika bazy |
| `DB_HOST` | `baza` | Adres bazy z perspektywy backendu |
| `BACKEND_URL` | `http://backend:8000` | Adres API z perspektywy frontendu |

Polecenie `docker compose down` zatrzymuje i usuwa kontenery, zachowując dane w nazwanym wolumenie.

## Architektura

- **Frontend** działa w osobnym obrazie Streamlit i korzysta z API. W widoku **Treningi** pokazuje szczegóły treningu z powiązanymi ćwiczeniami oraz umożliwia edycję i archiwizację. Pozostałe widoki służą do dodawania treningów, przeglądania historii i sprawdzania stanu połączenia.
- **Backend** udostępnia API JSON i łączy się z PostgreSQL. Compose uruchamia backend po uzyskaniu gotowości przez bazę, a frontend po udanym sprawdzeniu `/health` backendu.
- **PostgreSQL** korzysta z oficjalnego obrazu `postgres:16-alpine` i wolumenu `wolumen_bazy`. Port bazy jest dostępny dla backendu przez sieć Compose `dziennik`. Skrypt `backend/sql/create_treningi.sql` tworzy tabele i dane startowe przy pierwszym uruchomieniu wolumenu.
- Każde ćwiczenie należy do jednego treningu, a każdy wpis historii wskazuje trening. Przy starcie backend wykonuje migrację `backend/sql/historia_treningow.sql`, która dodaje historię i obsługę archiwum także na istniejącym wolumenie.

## Historia zmian

Przed dodaniem, edycją lub archiwizacją wpisz **Autora zmian** w menu bocznym. Autor jest deklarowany przez użytkownika. Backend zapisuje zmianę treningu oraz wpis historii w jednej transakcji. Trening po usunięciu trafia do archiwum. Jego historię można odczytać w widoku **Historia zmian**, wybierając **Archiwum**.

Historia zawiera operację, autora, czas nadany przez bazę oraz dane przed zmianą i po niej. Zbieranie historii zaczyna się od pierwszej operacji wykonanej przez API po wdrożeniu tej funkcji. Dlatego dane startowe i starsze treningi mogą mieć pustą historię.

## API i format JSON

Żądania z danymi oraz odpowiedzi używają `Content-Type: application/json`. Daty treningów mają format `RRRR-MM-DD`, a czasy wpisów historii są w formacie ISO 8601 ze strefą czasową.

| Metoda | Ścieżka | Zastosowanie | Kody odpowiedzi |
| --- | --- | --- | --- |
| GET | `/` | Informacja o działaniu API | 200 |
| GET | `/health` | Gotowość backendu i połączenia z bazą | 200, 503 |
| GET | `/treningi` | Lista aktywnych treningów. Parametr `archiwalne=true` zwraca treningi w archiwum | 200, 400 |
| GET | `/treningi/{id}` | Jeden aktywny trening z listą ćwiczeń | 200, 400, 404 |
| POST | `/treningi` | Dodanie treningu i wpisu historii | 201, 400 |
| PUT | `/treningi/{id}` | Zmiana danych aktywnego treningu i zapis historii | 200, 400, 404 |
| DELETE | `/treningi/{id}` | Archiwizacja aktywnego treningu i zapis historii | 200, 400, 404 |
| GET | `/treningi/{id}/history` | Historia treningu, również zarchiwizowanego, od najnowszego wpisu | 200, 400, 404 |

Przykładowe żądanie `POST` lub `PUT`. Pola `nazwa` i `autor` muszą zawierać tekst, a `autor` mieści do 100 znaków.

```json
{
  "data": "2026-11-08",
  "nazwa": "Trening klatki i ramion",
  "autor": "Łukasz"
}
```

Każda pozycja listy oraz odpowiedzi na `POST` i `PUT` mają pola `id`, `data` i `nazwa`. Szczegóły treningu zawierają dodatkowo tablicę `cwiczenia`. Poniżej znajduje się przykładowa odpowiedź z `GET /treningi/1`.

```json
{
  "id": 1,
  "data": "2026-11-01",
  "nazwa": "Góra ciała - Siła",
  "cwiczenia": [
    {
      "id": 1,
      "nazwa_cwiczenia": "Wyciskanie na maszynie",
      "serie": 4,
      "powtorzenia": 10,
      "ciezar_kg": 45
    },
    {
      "id": 2,
      "nazwa_cwiczenia": "Rozpiętki Butterfly",
      "serie": 3,
      "powtorzenia": 12,
      "ciezar_kg": 50
    }
  ]
}
```

Żądanie `DELETE` przyjmuje JSON `{"autor": "Łukasz"}`. Po archiwizacji zwraca np. `{"komunikat": "Trening został usunięty", "id": 1}`.

Poniżej znajduje się przykładowa odpowiedź z `GET /treningi/1/history`.

```json
[
  {
    "id": 1,
    "operacja": "usuniecie",
    "autor": "Łukasz",
    "czas": "2026-11-20T13:42:00+00:00",
    "przed": {"data": "2026-11-01", "nazwa": "Góra ciała - Siła"},
    "po": null
  }
]
```

Pole `operacja` ma jedną z wartości `dodanie`, `edycja`, `usuniecie`. Przy dodaniu `przed` ma wartość `null`, a przy usunięciu `po` ma wartość `null`.

Kod `400` oznacza błędne dane, np. pustą nazwę, brak autora lub nieprawidłowe ID. Odpowiedź zawiera tablicę błędów w polu `detail`. Kod `404` zwraca `{"detail": "Nie znaleziono treningu"}`, gdy zasób nie istnieje lub jest w archiwum, a żądanie dotyczy wyłącznie aktywnych treningów. `GET /health` zwraca przy powodzeniu `{"status_backendu": "ok", "status_bazy": "ok"}`, a w razie braku połączenia z bazą kod `503` i opis w polu `detail`.

## Testy

```sh
docker compose -f docker-compose.test.yml up --build --abort-on-container-exit --exit-code-from testy
```

Pytest sprawdza endpointy i błędy walidacji, powiązanie treningów z ćwiczeniami oraz historię dodania, edycji i archiwizacji. Testy korzystają z osobnej, tymczasowej bazy PostgreSQL. Po zakończeniu można posprzątać środowisko poleceniem `docker compose -f docker-compose.test.yml down`.

## AI

Do realizacji KM3 użyto Codex do przeglądu istniejącego projektu, implementacji historii zmian, przygotowania testów i aktualizacji dokumentacji.
