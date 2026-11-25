FROM ghcr.io/astral-sh/uv:0.11.15-python3.12-bookworm-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH"

RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-install-project --python 3.12
COPY src ./src
COPY configs ./configs
COPY datasets ./datasets
COPY examples ./examples
COPY README.md README.zh-CN.md LICENSE ./
RUN uv sync --locked --no-dev --python 3.12 \
    && useradd --create-home --uid 10001 rag \
    && chown -R rag:rag /app

USER rag
EXPOSE 8000 8501
CMD ["uvicorn", "rag_toolkit.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
