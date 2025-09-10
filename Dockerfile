FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Instalar dependencias del sistema necesarias para mysqlclient
RUN apt-get update \
   && apt-get install -y --no-install-recommends \
       build-essential \
       default-libmysqlclient-dev \
       pkg-config \
   && rm -rf /var/lib/apt/lists/*

# Instalar Poetry y configurar para no crear virtualenv
RUN pip install poetry
ENV POETRY_VENV_IN_PROJECT=1
ENV POETRY_NO_INTERACTION=1

# Copiar archivos de configuración del proyecto
COPY pyproject.toml poetry.lock ./

# Instalar las dependencias del proyecto usando Poetry
RUN poetry config virtualenvs.create false && poetry install --only main --no-root

# Copiar el resto del código y el script de inicio
COPY . .
RUN chmod +x start.sh

# ... El resto del Dockerfile permanece igual
RUN adduser --disabled-password --gecos '' appuser \
   && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["./start.sh"]