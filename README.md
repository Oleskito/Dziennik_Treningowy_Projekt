# Projekt z przedmiotu Metody wirtualizacji.
Projekt jest wykonywany przez Kacpra Nowetę oraz Aleksandra Ostrycharza.
Tematem jest stworzenie dziennika treningowego, który będzie miał poprawną strukturę plików oraz będzie skonteneryzowany

# Wymagania wstępne:
- zainstalowany docker oraz docker compose

# Kroki uruchomienia:
1. przygotowanie zmiennych środowiskowych na podstawie .env.example
2. zbudowanie i uruchomienie kontenerów - docker compose up --build
3. url aplikacji :
-Frontent: http://localhost:8501
-Backend: http://localhost:8000/health
4. zakończenie działania poprzec Ctrl + c lub wpisaniu w osobnym oknie terminala docker compose down

# Dokumentacja API i formaty wymiany danych (JSON)

Wszystkie żądania przesyłające dane do serwera oraz odpowiedzi zwracane przez serwer korzystają z formatu JSON (`Content-Type: application/json`).

#  1. Pobranie listy treningów
- **Metoda:** `GET`
- **Ścieżka:** `/treningi`
- **Kod sukcesu:** `200 OK`
- **Przykładowa odpowiedź:**
```json
[
  {
    "id": 1,
    "data": "2026-11-01",
    "nazwa": "Góra ciała - Siła"
  },
  {
    "id": 2,
    "data": "2026-11-03",
    "nazwa": "Trening Obwodowy"
  }
]
```
#  2. Pobranie jednego treningów
- **Metoda:** `GET`
- **Ścieżka:** `/treningi/{id_treningu}`
- **Kody odpowiedzi:** 
`200 OK`
`404 Not Found` – brak treningu o danym ID
- **Przykładowa odpowiedź(200):**
```json
{
  "id": 1,
  "data": "2026-11-01",
  "nazwa": "Góra ciała - Siła"
}
```
- **Przykładowa odpowiedź(404):**
```json
{
  "detail": "Nie znaleziono treningu"
}
```
#  3. Utworzenie nowego treningu
- **Metoda:** `POST`
- **Ścieżka:** `/treningi`
- **Body żądania (JSON):** 
```json
{
  "data": "2026-11-08",
  "nazwa": "Trening klatki i ramion"
}
```
- **Kody odpowiedzi:** 
`201 Created` – pomyślnie dodano trening
`400 Bad Request` – błąd walidacji

- **Przykładowa odpowiedź(201):**
```json
{
  "id": 3,
  "data": "2026-11-08",
  "nazwa": "Trening klatki i ramion"
}
```
- **Przykładowa odpowiedź(400):**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "nazwa"],
      "msg": "String should have at least 1 characters",
      "input": ""
    }
  ]
}
```
#  4. Usunięcie treningu
- **Metoda:** `DELETE`
- **Ścieżka:** `/treningi/{id_treningu}`
- **Kody odpowiedzi:** 
`200 OK` – pomyślnie usunięto
`404 Not Found` – trening o podanym ID nie istnieje

- **Przykładowa odpowiedź(200):**
```json
{
  "komunikat": "Trening został usunięty",
  "id": 1
}
```
- **Przykładowa odpowiedź(404):**
```json
{
  "detail": "Nie znaleziono treningu"
}
```
#  5. Status systemu (Healthcheck)
- **Metoda:** `GET`
- **Ścieżka:** `/health`
- **Kody odpowiedzi:** 
  - `200 OK` – backend i baza działają poprawnie
  - `503 Service Unavailable` – brak połączenia z bazą
- **Przykładowa odpowiedź (200):**
```json
{
  "status_backendu": "ok",
  "status_bazy": "ok"
}