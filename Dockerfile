FROM docker.io/library/python:3.13
COPY --from=ghcr.io/astral-sh/uv:0.8.16@sha256:f228383e3aca00ab1a54feaaceb8ea1ba646b96d3ee92dc20f5e8e3dcb159c9f /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
