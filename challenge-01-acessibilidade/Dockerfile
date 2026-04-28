FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir pip-tools

COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"

COPY . .

RUN mkdir -p /app/data

EXPOSE 8009

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8009", "--reload"]
