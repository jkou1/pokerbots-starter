# Build from the repository root:
#   docker build -f harness/Dockerfile -t poker-harness .
FROM python:3.12-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.11.21 /uv /bin/

WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=0

COPY harness/pyproject.toml ./
COPY harness/src ./src
RUN uv sync --no-dev --no-editable

FROM python:3.12-slim

WORKDIR /app
COPY --from=build /app/.venv .venv
COPY harness/shard_router.py harness/run_sharded.sh ./
COPY opsd/hint.py ./opsd/hint.py

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 HOST=0.0.0.0 PORT=8765 POKER_HARNESS_RUNS=/tmp/runs

USER 65532:65532
EXPOSE 8765
ENTRYPOINT ["./run_sharded.sh"]
