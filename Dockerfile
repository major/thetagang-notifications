FROM docker.io/library/python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN pip install -U pip poetry
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root && \
    poetry run playwright install chromium
COPY . .
