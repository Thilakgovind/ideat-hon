"""Single-origin deployment: API routes first, built React app last.

Build frontend first, then run `python -m uvicorn backend.web:app --port 8000`.
Keep one worker: the existing journey scheduler holds process-local state.
"""
from pathlib import Path

from .spa import FrontendFiles

from .app import app

DIST = Path(__file__).resolve().parent.parent / 'frontend' / 'dist'


if not (DIST / 'index.html').is_file():
    raise RuntimeError('Build the frontend first: npm ci --prefix frontend && npm run build --prefix frontend')

app.mount('/', FrontendFiles(directory=DIST, html=True), name='frontend')
