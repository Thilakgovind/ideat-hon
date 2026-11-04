FROM node:22-bookworm-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
COPY design/ /app/design/
# Public browser configuration only. Never add service-role or provider secrets here.
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_MAPTILER_KEY
RUN npm run build

FROM python:3.12-slim AS app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000
WORKDIR /app
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt
COPY backend/ ./backend/
COPY data/ ./data/
COPY agents/ ./agents/
COPY --from=frontend /app/frontend/dist ./frontend/dist
RUN useradd --create-home avvai && chown -R avvai:avvai /app
USER avvai
EXPOSE 8000
CMD ["sh", "-c", "exec python -m uvicorn backend.web:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
