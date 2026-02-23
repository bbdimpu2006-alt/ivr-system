FROM python:3.11-slim

WORKDIR /app

RUN pip install fastapi uvicorn celery redis psycopg2-binary

COPY app/ ./app/

EXPOSE 8000 4573

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
