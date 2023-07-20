FROM docker.io/library/python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app

RUN pip install -U pip poetry
COPY pyproject.toml poetry.lock ./

RUN poetry config virtualenvs.create false
RUN poetry install --only main --no-root

COPY . .
CMD ["/app/run_trades.py"]
