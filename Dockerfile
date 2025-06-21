FROM python:3.11-slim

WORKDIR /app

# Instaluj Poetry
RUN pip install poetry

# Konfiguruj Poetry
RUN poetry config virtualenvs.create false

# Kopiuj pliki projektu
COPY pyproject.toml poetry.lock* ./

# Instaluj zależności
RUN poetry install --no-dev

# Kopiuj kod aplikacji
COPY . .

# Utwórz folder output
RUN mkdir -p /app/output

CMD ["poetry", "run", "python", "run.py"]