FROM docker.io/library/python:3.14@sha256:78ad0471881f0232093c9e6edf58addade7bf106377732e0790c0f0c914b3b7b
COPY --from=ghcr.io/astral-sh/uv:0.9.4@sha256:c4089b0085cf4d38e38d5cdaa5e57752c1878a6f41f2e3a3a234dc5f23942cb4 /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
