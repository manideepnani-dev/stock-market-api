# Stock Market Data API

A production-ready REST API for fetching real-time stock market data from Yahoo Finance. Built with FastAPI and yfinance library.

## Features

- Real-time stock quotes
- Historical OHLCV data
- Company information
- Analyst recommendations
- Multi-stock comparison
- Health check endpoint

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd stock-market-api
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running Locally

Start the API server:

```bash
uvicorn main:app --reload
```

Or run directly:

```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the API is running.

**Example:**
```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-03-23T12:00:00.000000+00:00"
}
```

---

### 2. Stock Quote

**GET** `/stock/{ticker}/quote`

Get real-time stock quote data.

**Example:**
```bash
curl http://localhost:8000/stock/AAPL/quote
```

**Response:**
```json
{
  "ticker": "AAPL",
  "price": 174.55,
  "open": 173.50,
  "high": 175.20,
  "low": 173.25,
  "volume": 45678900,
  "market_cap": 2750000000000.0,
  "pe_ratio": 28.5,
  "52_week_high": 198.23,
  "52_week_low": 142.00,
  "currency": "USD"
}
```

---

### 3. Historical Data

**GET** `/stock/{ticker}/history`

Get historical OHLCV (Open, High, Low, Close, Volume) data.

**Query Parameters:**
- `period` (default: 1mo) - Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max
- `interval` (default: 1d) - Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo

**Example:**
```bash
curl "http://localhost:8000/stock/AAPL/history?period=1mo&interval=1d"
```

**Response:**
```json
{
  "ticker": "AAPL",
  "period": "1mo",
  "interval": "1d",
  "data": [
    {
      "date": "2026-02-23T00:00:00",
      "open": 173.50,
      "high": 175.20,
      "low": 173.25,
      "close": 174.55,
      "volume": 45678900
    }
  ]
}
```

---

### 4. Company Info

**GET** `/stock/{ticker}/info`

Get company information and metadata.

**Example:**
```bash
curl http://localhost:8000/stock/AAPL/info
```

**Response:**
```json
{
  "ticker": "AAPL",
  "company_name": "Apple Inc.",
  "sector": "Technology",
  "industry": "Consumer Electronics",
  "country": "United States",
  "website": "https://www.apple.com",
  "employees": 164000,
  "description": "Apple Inc. designs, manufactures, and markets smartphones...",
  "exchange": "NASDAQ",
  "dividend_yield": 0.0055
}
```

---

### 5. Analyst Recommendations

**GET** `/stock/{ticker}/recommendations`

Get latest analyst recommendations.

**Example:**
```bash
curl http://localhost:8000/stock/AAPL/recommendations
```

**Response:**
```json
{
  "ticker": "AAPL",
  "recommendations": [
    {
      "date": "2026-03-20",
      "firm": "Morgan Stanley",
      "to_grade": "Overweight",
      "from_grade": "Equal-Weight",
      "action": "upgrade"
    }
  ]
}
```

---

### 6. Compare Stocks

**GET** `/stocks/compare`

Compare multiple stocks side by side.

**Query Parameters:**
- `tickers` - Comma-separated ticker symbols (max 5)

**Example:**
```bash
curl "http://localhost:8000/stocks/compare?tickers=AAPL,MSFT,TSLA"
```

**Response:**
```json
{
  "stocks": [
    {
      "ticker": "AAPL",
      "price": 174.55,
      "market_cap": 2750000000000.0,
      "pe_ratio": 28.5,
      "52_week_high": 198.23,
      "52_week_low": 142.00,
      "currency": "USD"
    },
    {
      "ticker": "MSFT",
      "price": 415.20,
      "market_cap": 3100000000000.0,
      "pe_ratio": 35.2,
      "52_week_high": 468.35,
      "52_week_low": 362.90,
      "currency": "USD"
    },
    {
      "ticker": "TSLA",
      "price": 175.10,
      "market_cap": 560000000000.0,
      "pe_ratio": 42.8,
      "52_week_high": 299.29,
      "52_week_low": 138.80,
      "currency": "USD"
    }
  ]
}
```

---

## Vercel Deployment

### Prerequisites
- A GitHub account with the code pushed
- A Vercel account (sign up at vercel.com)

### Deploy Steps

1. **Push code to GitHub:**
```bash
git init
git add .
git commit -m "Initial commit - Stock Market API"
git branch -M main
git remote add origin https://github.com/yourusername/stock-market-api.git
git push -u origin main
```

2. **Deploy on Vercel:**
   - Go to [vercel.com](https://vercel.com) and sign in with GitHub
   - Click "New Project"
   - Import your GitHub repository
   - Leave the settings as default (Framework Preset: Python)
   - Click "Deploy"

3. **Your API will be live at:**
   `https://your-project-name.vercel.app`

### Testing the Deployed API

```bash
curl https://your-project-name.vercel.app/health
curl https://your-project-name.vercel.app/stock/AAPL/quote
```

---

## Environment

- Python 3.8+
- FastAPI
- uvicorn
- yfinance
- pandas

## License

MIT License
