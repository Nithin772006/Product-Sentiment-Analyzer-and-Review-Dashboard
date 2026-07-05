# Product Sentiment Analyzer and Review Dashboard

A production-ready full-stack application that scrapes product reviews from Amazon and Flipkart, processes sentiments using a consensus double-engine NLP model (VADER + TextBlob), archives metrics inside MongoDB Atlas, and visualizes interactive dashboards via a React 18 dashboard interface.

---

## 🛠️ Technology Stack

* **Backend**: Python 3.12, FastAPI, Motor (Async MongoDB), BeautifulSoup4, Playwright (Headless Chromium), Selenium (fallback), Pydantic v2, Loguru.
* **Frontend**: React 18, Vite, React Router DOM, TailwindCSS, Axios, Recharts, React Icons.
* **Database**: MongoDB Atlas Cluster.

---

## 📂 Project Architecture

```text
product-sentiment-analyzer/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/         # FastAPI endpoint route controllers
│   │   ├── config/             # System config & environment settings
│   │   ├── database/           # MongoDB connect and setup layer
│   │   ├── models/             # Pydantic schemas
│   │   ├── repositories/       # MongoDB collections operations layer
│   │   ├── scraper/            # Amazon & Flipkart crawling engines
│   │   │   ├── playwright_driver.py   # Playwright Chromium helper
│   │   │   ├── review_extractor.py    # 5-strategy full review extractor
│   │   │   ├── amazon_scraper.py      # Amazon scraper (Playwright + Selenium)
│   │   │   └── flipkart_scraper.py    # Flipkart scraper
│   │   ├── sentiment/          # NLP evaluation engines & batch processor
│   │   ├── utils/              # Custom helper models and loggers
│   │   └── main.py             # App entrypoint & middleware configuration
│   ├── tests/                  # Backend pytest & unit test suites
│   ├── .env                    # Local backend environment keys
│   └── requirements.txt        # Backend dependencies list
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API request clients
│   │   ├── charts/             # Recharts components (Pie, Line, Bars)
│   │   ├── components/         # Reusable layouts (Navbar, Footer, Feed)
│   │   ├── pages/              # Routing views (Home, Dashboard, Details)
│   │   ├── styles/             # Tailwind base & theme design tokens CSS
│   │   ├── App.jsx             # Main routing registry
│   │   └── main.jsx            # Entry point
│   ├── tailwind.config.js      # Styling design configurations
│   ├── package.json            # Frontend script registry & packages
│   └── vite.config.js          # Vite build configuration files
└── README.md                   # This master documentation file
```

---

## ⚙️ Environment Variables Configuration

### Backend (`backend/.env`)

Configure these keys in your `backend/.env` file:
```env
APP_NAME="Product Sentiment Analyzer"
APP_ENV="development"
APP_VERSION="1.0.0"

# MongoDB connection settings (Replace with your connection string)
MONGODB_URI="mongodb+srv://<user>:<password>@cluster.mongodb.net/?appName=Cluster"
MONGODB_DB_NAME="product_sentiment_db"

# Scraper settings
SCRAPER_HEADLESS=true
SCRAPER_TIMEOUT=30
SCRAPER_DELAY_MIN=2
SCRAPER_DELAY_MAX=5
SCRAPER_MAX_RETRIES=3

# Sentiment evaluation thresholds
SENTIMENT_AGREEMENT_THRESHOLD=0.1
```

### Frontend (`frontend/.env`)

Configure this key in your `frontend/.env` file (or let it fall back to localhost defaults):
```env
VITE_API_BASE_URL="http://localhost:8000/api"
```

---

## 📦 Installation

### Backend Setup

```bash
# 1. Navigate to the backend directory
cd backend

# 2. Create a virtual environment (first time only)
python -m venv .venv

# 3. Activate the virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# 4. Install all Python dependencies
pip install -r requirements.txt

# 5. Install Playwright Chromium browser binaries (one-time setup, ~300 MB)
playwright install chromium
```

### Frontend Setup

```bash
# 1. Navigate to the frontend directory
cd frontend

# 2. Install Node.js dependencies
npm install
```

---

## 🚀 Running Locally

### Step 1: Start the Backend Server

1. Open a terminal and navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Activate your virtual environment:
   ```bash
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1

   # macOS / Linux
   source .venv/bin/activate
   ```
3. Run the development server with live reload:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
4. Access interactive API documentation at:
   * **Swagger**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   * **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Step 2: Start the React Frontend

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Start the Vite dev server:
   ```bash
   npm run dev
   ```
3. Open your browser and navigate to the dashboard portal:
   * **Local Address**: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Running Tests

All tests are located in `backend/tests/`. Run them with the venv activated:

```bash
# Run all tests with verbose output
pytest tests/ -v

# Run only scraper tests
pytest tests/test_scraper.py -v

# Run only sentiment tests
pytest tests/test_sentiment.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=term-missing
```

---

## 🕷️ Scraper Quick Reference

The Amazon scraper uses **Playwright (Chromium)** as the primary engine with **Selenium as fallback**.

| Task | Command |
|------|---------|
| Install all backend dependencies | `pip install -r requirements.txt` |
| Install Playwright browser binaries | `playwright install chromium` |
| Reinstall Playwright from scratch | `pip install playwright && playwright install chromium` |
| Check Playwright version | `python -m playwright --version` |
| Run scraper in headed (visible) mode | Set `SCRAPER_HEADLESS=false` in `backend/.env` |

> Debug screenshots on scraping errors are saved to: `backend/static/screenshots/`

---

## 🔍 API Endpoints Documentation

All endpoints return a standardized JSON structure with `status`, `message`, and `data` objects:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/health` | Returns API services status and MongoDB ping details. |
| **GET** | `/api/products` | Paginated and sortable list of products. |
| **GET** | `/api/products/{id}` | Get details of a single tracked product. |
| **POST**| `/api/products/search` | Search product URL. Runs scraper & NLP if uncached. |
| **PUT** | `/api/products/{id}` | Update product information metadata. |
| **DELETE**| `/api/products/{id}`| Cascade deletes product metadata, reviews, and NLP records. |
| **GET** | `/api/reviews/product/{id}`| Paginated, filtered, and sorted review feed for a product. |
| **GET** | `/api/sentiments/product/{id}`| List parsed sentiment classifications for a product. |
| **GET** | `/api/analytics/product/{id}`| Highly compiled statistics, star distributions, and keywords. |
| **GET** | `/api/search?q={query}` | Database search by product title, categories, or brand. |
