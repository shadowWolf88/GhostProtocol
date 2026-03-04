FROM python:3.12-slim
# cache-bust: v3

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "echo '=== GHOST PROTOCOL BOOT ===' && echo 'PORT='${PORT:-8000} && python -c \"import os; u=os.getenv('DATABASE_URL',''); print('DB_HOST=' + (u.split('@')[-1] if '@' in u else 'NOT_SET'))\" && echo '=== RUNNING ALEMBIC ===' && alembic upgrade head; echo '=== STARTING UVICORN ===' && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
