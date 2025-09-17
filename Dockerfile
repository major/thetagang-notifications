FROM docker.io/library/python:3.13
COPY --from=ghcr.io/astral-sh/uv:0.8.18@sha256:62022a082ce1358336b920e9b7746ac7c95b1b11473aa93ab5e4f01232d6712d /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
