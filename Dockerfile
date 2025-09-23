FROM docker.io/library/python:3.13
COPY --from=ghcr.io/astral-sh/uv:0.8.20@sha256:4e3bde91035d8d11cc1d5e4d1c273b895bb293575b8d23c3e5c6058eed2f1bb9 /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
