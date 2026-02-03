FROM docker.io/library/python:3.14@sha256:c951a589819a647ef52c8609a8ecf50a4fa23eab030500e3d106f3644431ff30
COPY --from=ghcr.io/astral-sh/uv:0.9.29@sha256:db9370c2b0b837c74f454bea914343da9f29232035aa7632a1b14dc03add9edb /uv /uvx /bin/

ADD . /app
WORKDIR /app

# Install all dependencies during build (not at runtime)
RUN uv sync --frozen

# Set up environment to use the installed virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Run Python directly (no need for uv at runtime)
CMD ["python", "run_trades.py"]
