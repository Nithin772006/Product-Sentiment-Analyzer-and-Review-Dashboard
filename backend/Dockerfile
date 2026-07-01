# syntax=docker/dockerfile:1
FROM python:3.12-slim

# Install system dependencies for Chrome / Selenium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    curl \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Download NLTK data required by TextBlob / VADER
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

# Install Playwright browsers and dependencies
RUN playwright install --with-deps chromium

# Copy application source
COPY . .

# Create log directory
RUN mkdir -p logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
