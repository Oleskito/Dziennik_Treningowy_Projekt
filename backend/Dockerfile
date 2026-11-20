FROM python:3.12-slim AS aplikacja

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app
COPY sql/historia_treningow.sql ./sql/historia_treningow.sql

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM aplikacja AS testy

COPY tests/requirements.txt ./tests/requirements.txt
RUN pip install --no-cache-dir -r tests/requirements.txt
COPY tests/ ./tests

CMD ["python", "-m", "pytest", "-q", "tests"]

FROM aplikacja AS produkcja
