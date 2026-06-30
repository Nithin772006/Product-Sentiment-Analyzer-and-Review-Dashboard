# Backend — Product Sentiment Analyzer

FastAPI backend providing REST APIs for scraping product reviews from Amazon &
Flipkart, running sentiment analysis, and persisting results in MongoDB.

## Setup

```bash
# 1. Create & activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download NLTK data required by TextBlob
python -c "import nltk; nltk.download('punkt'); nltk.download('averaged_perceptron_tagger')"

# 4. Configure environment
cp .env.example .env
# Edit .env — at minimum set MONGODB_URI and SECRET_KEY

# 5. Start the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/redoc | ReDoc |
| http://localhost:8000/health | Health check |

## Running Tests

```bash
pytest tests/ -v --cov=app --cov-report=html
open htmlcov/index.html   # View coverage report
```

## Code Quality

```bash
# Format code
black app/ tests/
isort app/ tests/

# Lint
flake8 app/ tests/
```

## Project Structure

```
app/
├── api/          # Versioned route handlers
│   └── v1/
├── config/       # Settings (Pydantic BaseSettings)
├── database/     # MongoDB connection & helpers
├── models/       # Pydantic & ODM models
├── scraper/      # Amazon & Flipkart scraper classes
├── sentiment/    # VADER + TextBlob analysis engine
├── services/     # Business logic orchestration
├── utils/        # Logging, helpers, decorators
└── main.py       # Application factory & startup
```
