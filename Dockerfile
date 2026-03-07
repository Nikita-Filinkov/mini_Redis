FROM python:3.11-slim

RUN pip install uv

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --home /home/appuser appuser

WORKDIR /app
RUN chown appuser:appgroup /app

COPY --chown=appuser:appgroup pyproject.toml uv.lock* ./

USER appuser

RUN uv sync --frozen
COPY --chown=appuser:appgroup . .

EXPOSE 50051

CMD ["uv", "run", "python", "mini_redis/server.py"]