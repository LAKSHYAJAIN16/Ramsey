FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend
COPY data /app/data
COPY frontend /app/frontend
COPY homepage /app/homepage
ENV PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
