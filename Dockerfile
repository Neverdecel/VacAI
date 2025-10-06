# VacAI - AI-Powered Job Search Automation
# Optimized Docker image for GHCR deployment

FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    cron \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY main.py .
COPY setup.py .
COPY README.md .

# Install the package
RUN pip install --no-cache-dir -e .

# Create necessary directories
RUN mkdir -p /app/config /app/data /app/reports /app/logs /app/resume

# Create non-root user for security
RUN useradd -m -u 1000 vacai && \
    chown -R vacai:vacai /app

# Switch to non-root user
USER vacai

# Environment variables (can be overridden at runtime)
ENV PYTHONUNBUFFERED=1 \
    OPENAI_API_KEY="" \
    DATABASE_PATH="/app/data/vacai.db"

# Volume mounts for persistent data
VOLUME ["/app/config", "/app/data", "/app/reports", "/app/resume"]

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; from src.database.manager import DatabaseManager; db = DatabaseManager(); sys.exit(0 if db else 1)"

# Default command - can be overridden
CMD ["python", "main.py", "--help"]
