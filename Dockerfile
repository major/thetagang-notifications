FROM docker.io/library/python:3.14@sha256:52794854b26e18a67c9cde61b8137e95851772e5cf7460540063074253450dac
COPY --from=ghcr.io/astral-sh/uv:0.9.20@sha256:81f1a183fbdd9cec1498b066a32f0da043d4a9dda12b8372c7bfd183665e485d /uv /uvx /bin/

ADD . /app
WORKDIR /app

# Install all dependencies during build (not at runtime)
RUN uv sync --frozen

# Set up environment to use the installed virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Run Python directly (no need for uv at runtime)
CMD ["python", "run_trades.py"]
