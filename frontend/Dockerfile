# Vienna Transit app image (frontend app + GTFS loader share this image).
# Build context is the REPO ROOT so scripts/, models/ and db/ are available
# (gtfs_manager imports scripts.* at app import time).
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV DATABASE_URL=postgresql://wienerlinien:wienerlinien@db:5432/wienerlinien

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    libpq-dev \
    postgresql-client \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY frontend/requirements.txt requirements.txt
COPY requirements-db.txt requirements-db.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-db.txt

# Copy application code (frontend app + shared scripts/models/db)
COPY frontend/ ./
COPY scripts/ ./scripts/
COPY models/ ./models/
COPY db/init-scripts/ ./db/init-scripts/

# Create logs directory
RUN mkdir -p logs

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 3080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3080/api/status || exit 1

# Run the application with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3080"]
