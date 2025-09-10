FROM docker.io/library/python:3.13
COPY --from=ghcr.io/astral-sh/uv:0.8.12

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
