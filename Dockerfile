FROM python:3.11-slim
ENV PYTHONIOENCODING utf-8

COPY /src /code/src/
COPY /tests /code/tests/
COPY /scripts /code/scripts/
COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock
COPY deploy.sh /code/deploy.sh

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /code/

RUN uv sync --frozen

CMD ["uv", "run", "python", "-u", "/code/src/component.py"]
