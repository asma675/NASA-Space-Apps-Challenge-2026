FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend /app/backend
COPY frontend /app/frontend
COPY scripts /app/scripts
RUN mkdir -p /app/data
ENV PYTHONPATH=/app/backend BLINDSPOT_DB_PATH=/app/data/blindspot.sqlite3
EXPOSE 8000
CMD ["sh","-c","python /app/scripts/seed_demo.py && exec uvicorn app.main:app --app-dir /app/backend --host 0.0.0.0 --port 8000"]
