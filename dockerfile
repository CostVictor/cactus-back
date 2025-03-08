FROM python:3.12-slim

WORKDIR /app

# Previne criar arquivos de cache
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=1

# Instala dependências do apt e postgres
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  libpq-dev \
  postgresql-client \
  build-essential \
  musl-dev \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Cria o ambiente virtual e instala as dependências do projeto
RUN python -m venv /venv && \
  /venv/bin/pip install --upgrade pip && \
  /venv/bin/pip install -r requirements.txt

# Cria um usuário para o projeto
RUN adduser --disabled-password --no-create-home django-user

ENV PATH="/venv/bin:$PATH"

USER django-user

COPY . .

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]