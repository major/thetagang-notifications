FROM docker.io/library/python:3.14@sha256:6d58c1a9444bc2664f0fa20c43a592fcdb2698eb9a9c32257516538a2746c19a
COPY --from=ghcr.io/astral-sh/uv:0.9.23@sha256:22f6ca040d3f5484d9d792b8de122bb8846760cd997edc73443bc03815cf0a01 /uv /uvx /bin/

ADD . /app
WORKDIR /app

# Install all dependencies during build (not at runtime)
RUN uv sync --frozen

# Set up environment to use the installed virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Run Python directly (no need for uv at runtime)
CMD ["python", "run_trades.py"]
