FROM docker.io/library/python:3.14@sha256:3c737d592b9e137029b9f3fd3bfc50d0de7f41c3334f4212db563ff9eaa1f856
COPY --from=ghcr.io/astral-sh/uv:0.11.15@sha256:e590846f4776907b254ac0f44b5b380347af5d90d668138ca7938d1b0c2f98d3 /uv /uvx /bin/

ADD . /app
WORKDIR /app

# Install all dependencies during build (not at runtime)
RUN uv sync --frozen

# Set up environment to use the installed virtualenv
ENV PATH="/app/.venv/bin:$PATH"

# Run Python directly (no need for uv at runtime)
CMD ["python", "run_trades.py"]
