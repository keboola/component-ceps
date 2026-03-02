FROM python:3.11-slim
ENV PYTHONIOENCODING utf-8

COPY /src /code/src/
COPY /scripts /code/scripts/
COPY /tests /code/tests/
COPY pyproject.toml /code/pyproject.toml
COPY uv.lock /code/uv.lock
COPY flake8.cfg /code/flake8.cfg
COPY deploy.sh /code/deploy.sh

# install gcc and git — gcc for building native extensions, git for VCS dependencies
RUN apt-get update && apt-get install -y build-essential git curl && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /code/

RUN uv sync --frozen

CMD ["uv", "run", "python", "-u", "/code/src/component.py"]
