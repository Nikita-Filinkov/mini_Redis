FROM python:3.11-slim

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock* ./

RUN uv sync --frozen

COPY . .

EXPOSE 50051

CMD ["uv", "run", "python", "mini_redis/server.py"]