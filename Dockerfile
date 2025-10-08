FROM docker.io/library/python:3.14@sha256:5b95b240f2db781f34a5da81e6e2301378495b3ab78d689df325c937be267e1c
COPY --from=ghcr.io/astral-sh/uv:0.8.24@sha256:1d31be550ff927957472b2a491dc3de1ea9b5c2d319a9cea5b6a48021e2990a6 /uv /uvx /bin/

ADD . /app
WORKDIR /app
RUN uv sync --locked

CMD ["uv", "run", "run_trades.py"]
