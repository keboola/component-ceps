FROM python:3.11-slim
ENV PYTHONIOENCODING utf-8

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY /src /code/src/
COPY /tests /code/tests/
COPY /scripts /code/scripts/
COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock
COPY deploy.sh /code/deploy.sh

WORKDIR /code/

ENV UV_PROJECT_ENVIRONMENT="/usr/local/"

RUN uv sync --frozen

CMD ["python", "-u", "/code/src/component.py"]
