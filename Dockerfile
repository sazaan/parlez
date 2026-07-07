# Hardened production image (Task 3.2).
# - Non-root user (S17)
# - HEALTHCHECK for orchestrators
# - .dockerignore keeps tests/, data/, books/, caches, dev tooling out of the image
# - Single-worker note: app uses SQLite + in-memory rate limiter; do NOT
#   run with --workers > 1 (db.py + main.py:60-68). See main.py comment near
#   uvicorn.run for the full rationale.

FROM python:3.12-slim

WORKDIR /app

# Create non-root user up-front so the final chown doesn't have to recurse
# over large COPY layers.
RUN adduser --disabled-password --gecos "" appuser

# Install deps as root (needed for pip), then drop privileges for runtime.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code.
COPY . .

# Hand ownership to the non-root user and switch to it.
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health', timeout=3).status==200 else 1)"

CMD ["python", "main.py"]
