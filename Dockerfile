FROM python:3.11-slim

WORKDIR /app

# Instaluj Poetry
RUN pip install poetry

# Ustaw zmienne środowiskowe
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Konfiguruj Poetry
RUN poetry config virtualenvs.create false

# Kopiuj pliki projektu
COPY pyproject.toml poetry.lock* ./

# Instaluj zależności
RUN poetry install --no-dev

# Kopiuj kod aplikacji
COPY . .

# Ustawienie domyślnego polecenia
CMD ["poetry", "run", "dun"]

# Utwórz folder output
RUN mkdir -p /app/output

CMD ["poetry", "run", "python", "run.py"]