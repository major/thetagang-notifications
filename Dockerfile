FROM docker.io/library/python:3.14@sha256:ffebef43892dd36262fa2b042eddd3320d5510a21f8440dce0a650a3c124b51d
COPY --from=ghcr.io/astral-sh/uv:0.11.0@sha256:e49fde5daf002023f0a2e2643861ce9ca8a8da5b73d0e6db83ef82ff99969baf /uv /uvx /bin/

ADD . /app
WORKDIR /app

# Install all dependencies during build (not at runtime)
RUN uv sync --frozen

# Set up environment to use the installed virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Run Python directly (no need for uv at runtime)
CMD ["python", "run_trades.py"]
