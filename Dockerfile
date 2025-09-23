FROM docker.io/library/python:3.13
COPY --from=ghcr.io/astral-sh/uv:0.8.21@sha256:ca74b4b463d7dfc1176cbe82a02b6e143fd03a144dcb1a87c3c3e81ac16c6f6d /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
