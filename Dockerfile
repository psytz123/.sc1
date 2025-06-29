# Use Python 3.12 for better library compatibility
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements-dashboard.txt /app/
RUN pip install --no-cache-dir -r requirements-dashboard.txt

# Copy application code
COPY automation/ /app/automation/
COPY utils/ /app/utils/
COPY config/ /app/config/
COPY .env* /app/

# Create necessary directories
RUN mkdir -p /app/logs /app/reports

# Expose port (if adding web interface later)
EXPOSE 8080

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash dashboard
RUN chown -R dashboard:dashboard /app
USER dashboard

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import json, pathlib; print('healthy' if pathlib.Path('/app/logs/automation_metrics.json').exists() else exit(1))"

# Default command
CMD ["python", "automation/dashboard.py"]
