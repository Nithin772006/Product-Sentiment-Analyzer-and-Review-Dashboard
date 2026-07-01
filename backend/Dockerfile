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
    && pip install --no-cache-dir -r requirements.txt \
    && python -c "import sklearn; print('scikit-learn', sklearn.__version__)"

# Download NLTK data required by TextBlob / VADER / Preprocessor
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger'); nltk.download('averaged_perceptron_tagger_eng'); nltk.download('stopwords'); nltk.download('wordnet'); nltk.download('omw-1.4')"

# Install Playwright browsers and dependencies
RUN playwright install --with-deps chromium

# Copy application source
COPY . .

# Create log directory
RUN mkdir -p logs

# Render injects PORT at runtime. The default keeps local Docker usage simple.
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start Uvicorn. Use a single process so startup/import failures are reported cleanly
# and Render can reliably detect the bound port on free instances.
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"
