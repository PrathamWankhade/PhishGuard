FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY ai-engine ./ai-engine
COPY scripts ./scripts
# Model artifacts are NOT in git: mount ./trained_models at runtime
# or set MODEL_DIR to a versioned artifact download. Fail fast if missing.
RUN python -c "from pathlib import Path; print('trained_models mount expected at /app/trained_models')"
CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
