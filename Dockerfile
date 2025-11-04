FROM docker.io/library/python:3.14@sha256:a8053dece0fb59fd31e0eb615302e1d3936191655bc8ec74db128107fa415a08
COPY --from=ghcr.io/astral-sh/uv:0.9.7@sha256:ba4857bf2a068e9bc0e64eed8563b065908a4cd6bfb66b531a9c424c8e25e142 /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
