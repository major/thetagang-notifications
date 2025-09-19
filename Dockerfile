FROM docker.io/library/python:3.13
COPY --from=ghcr.io/astral-sh/uv:0.8.19@sha256:0ca07117081b2c6a8dd813d2badacf76dceecaf8b8a41d51b5d715024ffef7d8 /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
