Projekt z przedmiotu Metody wirtualizacji.
Projekt jest wykonywany przez Kacpra Nowetę oraz Aleksandra Ostrycharza.
Tematem jest stworzenie dziennika treningowego, który będzie miał poprawną strukturę plików oraz będzie skonteneryzowany

wymagania wstępne - zainstalowany docker oraz docker compose

kroki uruchomienia:
1. przygotowanie zmiennych środowiskowych na podstawie .env.example
2. zbudowanie i uruchomienie kontenerów - docker compose up --build
3. url aplikacji :
-Frontent: http://localhost:8501
-Backend: http://localhost:8000/health
4. zakończenie działania poprzec Ctrl + c lub wpisaniu w osobnym oknie terminala docker compose down