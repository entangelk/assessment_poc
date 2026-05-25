FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY schemas ./schemas
COPY config ./config
COPY fixtures ./fixtures
COPY tests ./tests

ENV ASSESSMENT_HARNESS_SCHEMA_DIR=/app/schemas \
    ASSESSMENT_HARNESS_DEFAULT_POLICY=/app/config/policy.yaml

ENTRYPOINT ["assessment-harness"]
CMD ["--help"]
