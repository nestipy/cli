FROM python:3.12-slim-buster

WORKDIR /app

# Install uv
RUN apt-get update && apt-get install -y curl \
    && curl -Ls https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && apt-get clean

# Copy project files
COPY pyproject.toml ./

# Install deps (fast, deterministic)
RUN uv sync --no-dev

# Copy app
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
