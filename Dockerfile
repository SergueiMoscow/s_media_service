FROM python:3.12
WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN python -m pip install --upgrade pip && \
    pip install poetry --no-cache-dir && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-root --no-cache --no-interaction

COPY alembic ./alembic
COPY api ./api
COPY common ./common
COPY db ./db
COPY images ./images
COPY repositories ./repositories
COPY schemas ./schemas
COPY services ./services
COPY alembic.ini entrypoint.sh .env ./

CMD ["sh", "./entrypoint.sh"]
