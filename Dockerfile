FROM python:3.11-slim

RUN mkdir /app && \
    addgroup --system --gid 1000 appuser && \
    adduser --system --uid 1000 --ingroup appuser appuser && \
    chown -R appuser:appuser /aggregator

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen

COPY . .

USER appuser

EXPOSE 50051

CMD ["uv", "run", "python", "mini_redis/server.py"]