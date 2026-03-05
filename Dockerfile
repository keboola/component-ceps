FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /code/

COPY /src src/
COPY /tests tests/
COPY /scripts scripts/
COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock
COPY deploy.sh deploy.sh

RUN apt-get update \
    && apt-get install -y --no-install-recommends git libjemalloc2 \
    && rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

RUN uv sync --frozen

CMD ["python", "-u", "src/component.py"]
