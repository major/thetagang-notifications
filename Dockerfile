FROM docker.io/library/python:3.14@sha256:788c343877b467e72af452878cb6d2b0ce6a16ffed973e2dc82b57d8d765eb33
COPY --from=ghcr.io/astral-sh/uv:0.11.3@sha256:90bbb3c16635e9627f49eec6539f956d70746c409209041800a0280b93152823 /uv /uvx /bin/

ADD . /app
WORKDIR /app

# Install all dependencies during build (not at runtime)
RUN uv sync --frozen

# Set up environment to use the installed virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Run Python directly (no need for uv at runtime)
CMD ["python", "run_trades.py"]
