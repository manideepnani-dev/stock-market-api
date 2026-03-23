"""
Stock Market Data API

A production-ready REST API for fetching stock market data from Yahoo Finance.
Built with FastAPI and yfinance library.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import yfinance as yf
import pandas as pd

app = FastAPI(
    title="Stock Market Data API",
    description="A production-ready API for fetching real-time stock market data from Yahoo Finance. "
                "Provides quotes, historical prices, company info, financials, technical indicators, "
                "news, dividends, earnings, market movers, sectors, crypto, and forex data.",
    version="2.0.0",
)

# Rate limiter setup
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.get("/")
def root():
    return {
        "name": "Stock Market Data API",
        "version": "2.0.0",
        "status": "running",
        "endpoints": [
            "/health",
            "/stock/{ticker}/quote",
            "/stock/{ticker}/history",
            "/stock/{ticker}/info",
            "/stock/{ticker}/recommendations",
            "/stock/{ticker}/financials",
            "/stock/{ticker}/news",
            "/stock/{ticker}/indicators",
            "/stock/{ticker}/dividends",
            "/stock/{ticker}/earnings",
            "/stock/{ticker}/analysts",
            "/stocks/compare",
            "/market/movers",
            "/market/summary",
            "/market/sectors",
            "/crypto/{symbol}/quote",
            "/forex/{pair}/quote",
            "/stock/search",
        ]
    }


# CORS middleware - allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def round_float(value: Optional[float], decimals: int = 4) -> Optional[float]:
    """Round a float value to specified decimal places."""
    if value is None:
        return None
    return round(float(value), decimals)


def validate_ticker(ticker: str) -> str:
    """Convert ticker to uppercase and validate."""
    return ticker.upper().strip()


# ─────────────────────────────────────────────
# HEALTH
# ─────────────────────────────────────────────

@app.get("/health", tags=["Health"], responses={
    200: {
        "description": "API is healthy and running",
        "content": {
            "application/json": {
                "example": {
                    "status": "ok",
                    "timestamp": "2026-03-23T10:30:00+00:00"
                }
            }
        }
    }
})
@limiter.limit("60/minute")
async def health_check(request: Request):
    """
    Health check endpoint.

    Returns the current UTC timestamp and status to verify the API is running.

    Example: /health
    """
    try:
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─────────────────────────────────────────────
# EXISTING STOCK ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/stock/{ticker}/quote", tags=["Stock Data"], responses={
    200: {
        "description": "Real-time stock quote for a given ticker",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "price": 178.52,
                    "open": 177.25,
                    "high": 179.38,
                    "low": 176.80,
                    "volume": 58234500,
                    "market_cap": 2800000000000,
                    "pe_ratio": 28.45,
                    "52_week_high": 199.62,
                    "52_week_low": 164.08,
                    "currency": "USD"
                }
            }
        }
    }
})
@limiter.limit("30/minute")
async def get_stock_quote(request: Request, ticker: str):
    """
    Get real-time stock quote for a given ticker.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Returns price, open, high, low, volume, market_cap, pe_ratio, 52-week high/low, currency.

    Example: /stock/AAPL/quote
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            raise HTTPException(
                status_code=404,
                detail=f"Ticker '{ticker}' not found or no market data available"
            )

        return {
            "ticker": ticker,
            "price": round_float(info.get("regularMarketPrice")),
            "open": round_float(info.get("regularMarketOpen")),
            "high": round_float(info.get("regularMarketDayHigh")),
            "low": round_float(info.get("regularMarketDayLow")),
            "volume": info.get("regularMarketVolume"),
            "market_cap": round_float(info.get("marketCap")),
            "pe_ratio": round_float(info.get("trailingPE")),
            "52_week_high": round_float(info.get("fiftyTwoWeekHigh")),
            "52_week_low": round_float(info.get("fiftyTwoWeekLow")),
            "currency": info.get("currency", "USD"),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching quote: {str(e)}")


@app.get("/stock/{ticker}/history", tags=["Stock Data"], responses={
    200: {
        "description": "Historical OHLCV data for a stock",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "period": "1mo",
                    "interval": "1d",
                    "data": [
                        {
                            "date": "2026-02-23T00:00:00",
                            "open": 175.50,
                            "high": 177.82,
                            "low": 175.10,
                            "close": 177.25,
                            "volume": 45230000
                        },
                        {
                            "date": "2026-02-24T00:00:00",
                            "open": 177.25,
                            "high": 179.38,
                            "low": 176.80,
                            "close": 178.52,
                            "volume": 58234500
                        }
                    ]
                }
            }
        }
    }
})
@limiter.limit("20/minute")
async def get_stock_history(
    request: Request,
    ticker: str,
    period: str = Query(default="1mo", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query(default="1d", description="Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo"),
):
    """
    Get historical OHLCV data for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
        period: Time period for historical data (default: 1mo)
        interval: Data interval (default: 1d)

    Example: /stock/AAPL/history?period=1mo&interval=1d
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)

        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo"]

        if period not in valid_periods:
            raise HTTPException(status_code=400, detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}")
        if interval not in valid_intervals:
            raise HTTPException(status_code=400, detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}")

        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No historical data found for ticker '{ticker}'")

        records = []
        for date, row in hist.iterrows():
            records.append({
                "date": date.isoformat(),
                "open": round_float(row["Open"]),
                "high": round_float(row["High"]),
                "low": round_float(row["Low"]),
                "close": round_float(row["Close"]),
                "volume": int(row["Volume"]) if pd.notna(row["Volume"]) else 0,
            })

        return {"ticker": ticker, "period": period, "interval": interval, "data": records}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@app.get("/stock/{ticker}/info", tags=["Stock Data"], responses={
    200: {
        "description": "Company information and metadata for a stock",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "company_name": "Apple Inc.",
                    "sector": "Technology",
                    "industry": "Consumer Electronics",
                    "country": "United States",
                    "website": "https://www.apple.com",
                    "employees": 164000,
                    "description": "Apple Inc. designs, manufactures, and markets smartphones, personal computers, tablets, wearables, and accessories worldwide...",
                    "exchange": "NASDAQ",
                    "dividend_yield": 0.0052
                }
            }
        }
    }
})
@limiter.limit("30/minute")
async def get_stock_info(request: Request, ticker: str):
    """
    Get company information and metadata for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Example: /stock/AAPL/info
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or not info.get("regularMarketPrice"):
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found or no market data available")

        return {
            "ticker": ticker,
            "company_name": info.get("shortName") or info.get("longName", "N/A"),
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "country": info.get("country", "N/A"),
            "website": info.get("website", "N/A"),
            "employees": info.get("fullTimeEmployees", 0),
            "description": info.get("longBusinessSummary", "N/A")[:500] if info.get("longBusinessSummary") else "N/A",
            "exchange": info.get("exchange", "N/A"),
            "dividend_yield": round_float(info.get("dividendYield")),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching info: {str(e)}")


@app.get("/stock/{ticker}/recommendations", tags=["Stock Data"], responses={
    200: {
        "description": "Latest analyst recommendations for a stock",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "recommendations": [
                        {
                            "date": "2026-03-20T00:00:00",
                            "firm": "Morgan Stanley",
                            "to_grade": "Overweight",
                            "from_grade": "Equal-Weight",
                            "action": "upgrade"
                        },
                        {
                            "date": "2026-03-18T00:00:00",
                            "firm": "Goldman Sachs",
                            "to_grade": "Buy",
                            "from_grade": "Neutral",
                            "action": "main"
                        }
                    ]
                }
            }
        }
    }
})
@limiter.limit("20/minute")
async def get_stock_recommendations(request: Request, ticker: str):
    """
    Get latest analyst recommendations for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Example: /stock/AAPL/recommendations
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations

        if recs is None or recs.empty:
            raise HTTPException(status_code=404, detail=f"No recommendations found for ticker '{ticker}'")

        recs = recs.tail(10)
        records = []
        for _, row in recs.iterrows():
            records.append({
                "date": row["Date"].isoformat() if pd.notna(row.get("Date")) else None,
                "firm": row.get("Firm", "N/A"),
                "to_grade": row.get("ToGrade", "N/A"),
                "from_grade": row.get("FromGrade", "N/A"),
                "action": row.get("Action", "N/A"),
            })

        return {"ticker": ticker, "recommendations": records}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")


@app.get("/stocks/compare", tags=["Stock Data"], responses={
    200: {
        "description": "Side-by-side comparison of multiple stocks",
        "content": {
            "application/json": {
                "example": {
                    "stocks": [
                        {
                            "ticker": "AAPL",
                            "price": 178.52,
                            "market_cap": 2800000000000,
                            "pe_ratio": 28.45,
                            "52_week_high": 199.62,
                            "52_week_low": 164.08,
                            "currency": "USD"
                        },
                        {
                            "ticker": "MSFT",
                            "price": 415.30,
                            "market_cap": 3080000000000,
                            "pe_ratio": 35.20,
                            "52_week_high": 430.82,
                            "52_week_low": 362.90,
                            "currency": "USD"
                        },
                        {
                            "ticker": "TSLA",
                            "price": 175.20,
                            "market_cap": 558000000000,
                            "pe_ratio": 42.80,
                            "52_week_high": 278.98,
                            "52_week_low": 138.80,
                            "currency": "USD"
                        }
                    ]
                }
            }
        }
    }
})
@limiter.limit("10/minute")
async def compare_stocks(
    request: Request,
    tickers: str = Query(..., description="Comma-separated ticker symbols (max 5, e.g. AAPL,MSFT,TSLA)"),
):
    """
    Compare multiple stocks side by side.

    Args:
        tickers: Comma-separated ticker symbols (max 5, e.g., AAPL,MSFT,TSLA)

    Example: /stocks/compare?tickers=AAPL,MSFT,TSLA
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    if len(ticker_list) > 5:
        raise HTTPException(status_code=400, detail="Maximum 5 tickers allowed for comparison")
    if len(ticker_list) < 2:
        raise HTTPException(status_code=400, detail="At least 2 tickers required for comparison")

    results = []
    errors = []

    for ticker in ticker_list:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info

            if not info or info.get("regularMarketPrice") is None:
                errors.append(f"Ticker '{ticker}' not found")
                continue

            results.append({
                "ticker": ticker,
                "price": round_float(info.get("regularMarketPrice")),
                "market_cap": round_float(info.get("marketCap")),
                "pe_ratio": round_float(info.get("trailingPE")),
                "52_week_high": round_float(info.get("fiftyTwoWeekHigh")),
                "52_week_low": round_float(info.get("fiftyTwoWeekLow")),
                "currency": info.get("currency", "USD"),
            })
        except Exception as e:
            errors.append(f"Ticker '{ticker}': {str(e)}")

    if not results:
        raise HTTPException(status_code=404, detail=f"No valid tickers found. Errors: {'; '.join(errors)}")

    response_data = {"stocks": results}
    if errors:
        response_data["errors"] = errors

    return response_data


# ─────────────────────────────────────────────
# NEW ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/stock/{ticker}/financials", tags=["Stock Data"], responses={
    200: {
        "description": "Financial statements for a stock (income, balance sheet, cash flow)",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "income_statement": {
                        "Total Revenue": 394328000000,
                        "Net Income": 97099000000,
                        "Gross Profit": 170882000000,
                        "Operating Income": 119437000000,
                        "EPS": 6.13
                    },
                    "balance_sheet": {
                        "Total Assets": 352583000000,
                        "Total Liabilities": 290437000000,
                        "Total Equity": 62146000000,
                        "Cash": 62699000000,
                        "Long Term Debt": 98959000000
                    },
                    "cash_flow": {
                        "Operating Cash Flow": 110056000000,
                        "Capital Expenditure": -11758000000,
                        "Free Cash Flow": 98298000000,
                        "Dividends Paid": -14876000000
                    }
                }
            }
        }
    }
})
@limiter.limit("10/minute")
async def get_stock_financials(request: Request, ticker: str):
    """
    Get financial statements for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Returns latest annual income statement, balance sheet, and cash flow data.

    Example: /stock/AAPL/financials
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

        def safe_df(df):
            if df is None or df.empty:
                return {}
            col = df.columns[0]
            return {
                str(k): (None if pd.isna(v) else round_float(v))
                for k, v in df[col].items()
            }

        return {
            "ticker": ticker,
            "income_statement": safe_df(stock.financials),
            "balance_sheet": safe_df(stock.balance_sheet),
            "cash_flow": safe_df(stock.cashflow),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching financials: {str(e)}")


@app.get("/stock/{ticker}/news", tags=["Stock Data"], responses={
    200: {
        "description": "Latest news articles for a stock",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "count": 2,
                    "news": [
                        {
                            "title": "Apple Reports Record Q1 Revenue, Services Growth Continues",
                            "publisher": "Bloomberg",
                            "link": "https://example.com/apple-news-1",
                            "published_at": "2026-03-22T14:30:00+00:00",
                            "type": "Article"
                        },
                        {
                            "title": "Apple Announces New AI Features for iPhone",
                            "publisher": "Reuters",
                            "link": "https://example.com/apple-news-2",
                            "published_at": "2026-03-21T09:15:00+00:00",
                            "type": "Article"
                        }
                    ]
                }
            }
        }
    }
})
@limiter.limit("20/minute")
async def get_stock_news(
    request: Request,
    ticker: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of news articles to return (max 50)"),
):
    """
    Get latest news articles for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
        limit: Number of news articles to return (default: 10, max: 50)

    Returns title, publisher, link, and publish time for each article.

    Example: /stock/AAPL/news?limit=5
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        news = stock.news

        if not news:
            raise HTTPException(status_code=404, detail=f"No news found for ticker '{ticker}'")

        articles = []
        for item in news[:limit]:
            articles.append({
                "title": item.get("title", "N/A"),
                "publisher": item.get("publisher", "N/A"),
                "link": item.get("link", "N/A"),
                "published_at": datetime.fromtimestamp(item["providerPublishTime"], tz=timezone.utc).isoformat()
                    if item.get("providerPublishTime") else None,
                "type": item.get("type", "N/A"),
            })

        return {"ticker": ticker, "count": len(articles), "news": articles}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching news: {str(e)}")


@app.get("/stock/{ticker}/indicators", tags=["Stock Data"], responses={
    200: {
        "description": "Technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands)",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "period": "6mo",
                    "current_price": 178.52,
                    "moving_averages": {
                        "sma_20": 175.82,
                        "sma_50": 172.45,
                        "sma_200": 168.30,
                        "ema_12": 178.25,
                        "ema_26": 176.80
                    },
                    "macd": {
                        "macd": 2.45,
                        "signal": 1.82,
                        "histogram": 0.63
                    },
                    "rsi_14": 62.35,
                    "bollinger_bands": {
                        "upper": 182.15,
                        "middle": 175.82,
                        "lower": 169.49
                    }
                }
            }
        }
    }
})
@limiter.limit("10/minute")
async def get_technical_indicators(
    request: Request,
    ticker: str,
    period: str = Query(default="6mo", description="Time period for calculation: 3mo, 6mo, 1y, 2y"),
):
    """
    Get technical indicators for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
        period: Time period for calculation (default: 6mo)

    Returns SMA (20, 50, 200), EMA (12, 26), RSI (14), MACD, and Bollinger Bands.

    Example: /stock/AAPL/indicators?period=6mo
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period, interval="1d")

        if hist.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker '{ticker}'")

        close = hist["Close"]

        # Simple Moving Averages
        sma_20 = close.rolling(window=20).mean().iloc[-1] if len(close) >= 20 else None
        sma_50 = close.rolling(window=50).mean().iloc[-1] if len(close) >= 50 else None
        sma_200 = close.rolling(window=200).mean().iloc[-1] if len(close) >= 200 else None

        # Exponential Moving Averages
        ema_12 = close.ewm(span=12, adjust=False).mean().iloc[-1]
        ema_26 = close.ewm(span=26, adjust=False).mean().iloc[-1]

        # MACD
        macd_line = close.ewm(span=12, adjust=False).mean() - close.ewm(span=26, adjust=False).mean()
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd = round_float(macd_line.iloc[-1])
        macd_signal = round_float(signal_line.iloc[-1])
        macd_histogram = round_float(macd_line.iloc[-1] - signal_line.iloc[-1])

        # RSI (14)
        delta = close.diff()
        gain = delta.clip(lower=0).rolling(window=14).mean()
        loss = (-delta.clip(upper=0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = round_float(100 - (100 / (1 + rs.iloc[-1])))

        # Bollinger Bands (20-day)
        bb_sma = close.rolling(window=20).mean()
        bb_std = close.rolling(window=20).std()
        bb_upper = round_float((bb_sma + 2 * bb_std).iloc[-1]) if len(close) >= 20 else None
        bb_lower = round_float((bb_sma - 2 * bb_std).iloc[-1]) if len(close) >= 20 else None
        bb_mid = round_float(bb_sma.iloc[-1]) if len(close) >= 20 else None

        return {
            "ticker": ticker,
            "period": period,
            "current_price": round_float(close.iloc[-1]),
            "moving_averages": {
                "sma_20": round_float(sma_20),
                "sma_50": round_float(sma_50),
                "sma_200": round_float(sma_200),
                "ema_12": round_float(ema_12),
                "ema_26": round_float(ema_26),
            },
            "macd": {
                "macd": macd,
                "signal": macd_signal,
                "histogram": macd_histogram,
            },
            "rsi_14": rsi,
            "bollinger_bands": {
                "upper": bb_upper,
                "middle": bb_mid,
                "lower": bb_lower,
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating indicators: {str(e)}")


@app.get("/stock/{ticker}/dividends", tags=["Stock Data"], responses={
    200: {
        "description": "Dividend history and yield information",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "dividend_yield": 0.0052,
                    "annual_dividend_rate": 0.96,
                    "ex_dividend_date": "2026-02-14",
                    "payout_ratio": 0.15,
                    "history": [
                        {"date": "2026-02-14", "amount": 0.24},
                        {"date": "2025-11-14", "amount": 0.24},
                        {"date": "2025-08-15", "amount": 0.24},
                        {"date": "2025-05-16", "amount": 0.24}
                    ]
                }
            }
        }
    }
})
@limiter.limit("20/minute")
async def get_stock_dividends(
    request: Request,
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100, description="Number of dividend records to return"),
):
    """
    Get dividend history for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
        limit: Number of dividend records to return (default: 20, max: 100)

    Returns dividend payment dates and amounts, plus current yield and annual rate.

    Example: /stock/AAPL/dividends?limit=10
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        dividends = stock.dividends
        info = stock.info

        if dividends is None or dividends.empty:
            raise HTTPException(status_code=404, detail=f"No dividend data found for ticker '{ticker}'")

        records = []
        for date, amount in dividends.tail(limit).items():
            records.append({
                "date": date.isoformat(),
                "amount": round_float(amount),
            })

        return {
            "ticker": ticker,
            "dividend_yield": round_float(info.get("dividendYield")),
            "annual_dividend_rate": round_float(info.get("dividendRate")),
            "ex_dividend_date": info.get("exDividendDate"),
            "payout_ratio": round_float(info.get("payoutRatio")),
            "history": records,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching dividends: {str(e)}")


@app.get("/stock/{ticker}/earnings", tags=["Stock Data"], responses={
    200: {
        "description": "Earnings data including EPS, revenue, and upcoming earnings dates",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "eps_trailing_12m": 6.13,
                    "eps_forward": 7.25,
                    "pe_trailing": 28.45,
                    "pe_forward": 24.25,
                    "earnings_growth": 0.11,
                    "revenue_growth": 0.04,
                    "annual_earnings": [
                        {"year": "2025", "revenue": 394328000000, "earnings": 97099000000},
                        {"year": "2024", "revenue": 385606000000, "earnings": 97099000000}
                    ],
                    "quarterly_earnings": [
                        {"quarter": "2026-Q1", "revenue": 124300000000, "earnings": 36308000000},
                        {"quarter": "2025-Q4", "revenue": 94930000000, "earnings": 24356000000}
                    ]
                }
            }
        }
    }
})
@limiter.limit("10/minute")
async def get_stock_earnings(request: Request, ticker: str):
    """
    Get earnings data for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Returns annual and quarterly EPS, revenue, and upcoming earnings date.

    Example: /stock/AAPL/earnings
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

        # Quarterly earnings
        quarterly = stock.quarterly_earnings
        quarterly_records = []
        if quarterly is not None and not quarterly.empty:
            for date, row in quarterly.iterrows():
                quarterly_records.append({
                    "quarter": str(date),
                    "revenue": round_float(row.get("Revenue")),
                    "earnings": round_float(row.get("Earnings")),
                })

        # Annual earnings
        annual = stock.earnings
        annual_records = []
        if annual is not None and not annual.empty:
            for year, row in annual.iterrows():
                annual_records.append({
                    "year": str(year),
                    "revenue": round_float(row.get("Revenue")),
                    "earnings": round_float(row.get("Earnings")),
                })

        return {
            "ticker": ticker,
            "eps_trailing_12m": round_float(info.get("trailingEps")),
            "eps_forward": round_float(info.get("forwardEps")),
            "pe_trailing": round_float(info.get("trailingPE")),
            "pe_forward": round_float(info.get("forwardPE")),
            "earnings_growth": round_float(info.get("earningsGrowth")),
            "revenue_growth": round_float(info.get("revenueGrowth")),
            "annual_earnings": annual_records,
            "quarterly_earnings": quarterly_records,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching earnings: {str(e)}")


@app.get("/stock/{ticker}/analysts", tags=["Stock Data"], responses={
    200: {
        "description": "Analyst price targets and ratings summary",
        "content": {
            "application/json": {
                "example": {
                    "ticker": "AAPL",
                    "current_price": 178.52,
                    "target_mean_price": 210.25,
                    "target_low_price": 170.00,
                    "target_high_price": 250.00,
                    "target_median_price": 205.00,
                    "recommendation": "buy",
                    "analyst_count": 42,
                    "ratings": {
                        "strong_buy": 15,
                        "buy": 20,
                        "hold": 6,
                        "sell": 1,
                        "strong_sell": 0
                    }
                }
            }
        }
    }
})
@limiter.limit("20/minute")
async def get_analyst_targets(request: Request, ticker: str):
    """
    Get analyst price targets and ratings summary for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Returns mean/low/high price targets and buy/hold/sell counts.

    Example: /stock/AAPL/analysts
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or info.get("regularMarketPrice") is None:
            raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found")

        return {
            "ticker": ticker,
            "current_price": round_float(info.get("regularMarketPrice")),
            "target_mean_price": round_float(info.get("targetMeanPrice")),
            "target_low_price": round_float(info.get("targetLowPrice")),
            "target_high_price": round_float(info.get("targetHighPrice")),
            "target_median_price": round_float(info.get("targetMedianPrice")),
            "recommendation": info.get("recommendationKey", "N/A"),
            "analyst_count": info.get("numberOfAnalystOpinions"),
            "ratings": {
                "strong_buy": info.get("strongBuy"),
                "buy": info.get("buy"),
                "hold": info.get("hold"),
                "sell": info.get("sell"),
                "strong_sell": info.get("strongSell"),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analyst targets: {str(e)}")


# ─────────────────────────────────────────────
# MARKET ENDPOINTS
# ─────────────────────────────────────────────

@app.get("/market/movers", tags=["Market Data"], responses={
    200: {
        "description": "Top market gainers and losers",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2026-03-23T10:30:00+00:00",
                    "top_gainers": [
                        {"ticker": "NVDA", "price": 875.50, "change_pct": 5.82, "volume": 42500000},
                        {"ticker": "AMD", "price": 185.20, "change_pct": 4.65, "volume": 52100000},
                        {"ticker": "TSLA", "price": 175.20, "change_pct": 3.92, "volume": 98200000},
                        {"ticker": "META", "price": 505.30, "change_pct": 2.85, "volume": 18500000},
                        {"ticker": "NFLX", "price": 685.40, "change_pct": 2.45, "volume": 4200000}
                    ],
                    "top_losers": [
                        {"ticker": "PYPL", "price": 58.20, "change_pct": -4.85, "volume": 22500000},
                        {"ticker": "INTC", "price": 42.30, "change_pct": -3.65, "volume": 38500000},
                        {"ticker": "MRK", "price": 118.50, "change_pct": -2.15, "volume": 8500000},
                        {"ticker": "VZ", "price": 38.40, "change_pct": -1.85, "volume": 18200000},
                        {"ticker": "MA", "price": 485.20, "change_pct": -1.25, "volume": 3200000}
                    ]
                }
            }
        }
    }
})
@limiter.limit("5/minute")
async def get_market_movers(request: Request):
    """
    Get top market movers - gainers and losers of the day.

    Tracks a curated list of large-cap stocks and returns top 5 gainers and losers by % change.

    Example: /market/movers
    """
    # Curated list of large-cap tickers to scan
    watchlist = [
        "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B",
        "JPM", "JNJ", "V", "UNH", "XOM", "PG", "MA", "HD", "CVX", "MRK",
        "ABBV", "PEP", "KO", "LLY", "AVGO", "COST", "TMO", "MCD", "ACN",
        "DHR", "VZ", "ADBE", "NFLX", "CRM", "INTC", "AMD", "PYPL", "QCOM",
    ]
    try:
        results = []
        for ticker in watchlist:
            try:
                info = yf.Ticker(ticker).info
                price = info.get("regularMarketPrice")
                prev_close = info.get("regularMarketPreviousClose")
                if price and prev_close and prev_close != 0:
                    change_pct = round_float(((price - prev_close) / prev_close) * 100, 2)
                    results.append({
                        "ticker": ticker,
                        "price": round_float(price),
                        "change_pct": change_pct,
                        "volume": info.get("regularMarketVolume"),
                    })
            except Exception:
                continue

        results.sort(key=lambda x: x["change_pct"] or 0, reverse=True)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "top_gainers": results[:5],
            "top_losers": results[-5:][::-1],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching movers: {str(e)}")


@app.get("/market/summary", tags=["Market Data"], responses={
    200: {
        "description": "Overall market summary for major indices",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2026-03-23T10:30:00+00:00",
                    "indices": [
                        {"name": "S&P 500", "symbol": "^GSPC", "price": 5428.50, "change_pct": 0.85, "day_high": 5445.20, "day_low": 5398.30},
                        {"name": "NASDAQ", "symbol": "^IXIC", "price": 17892.30, "change_pct": 1.25, "day_high": 17950.80, "day_low": 17820.40},
                        {"name": "Dow Jones", "symbol": "^DJI", "price": 42850.20, "change_pct": 0.45, "day_high": 42980.50, "day_low": 42750.30},
                        {"name": "Russell 2000", "symbol": "^RUT", "price": 2085.40, "change_pct": -0.35, "day_high": 2095.80, "day_low": 2078.20},
                        {"name": "VIX", "symbol": "^VIX", "price": 15.80, "change_pct": -2.85, "day_high": 16.45, "day_low": 15.60}
                    ]
                }
            }
        }
    }
})
@limiter.limit("10/minute")
async def get_market_summary(request: Request):
    """
    Get overall market summary for major indices.

    Returns current price and daily change for S&P 500, NASDAQ, Dow Jones, Russell 2000, and VIX.

    Example: /market/summary
    """
    indices = {
        "S&P 500": "^GSPC",
        "NASDAQ": "^IXIC",
        "Dow Jones": "^DJI",
        "Russell 2000": "^RUT",
        "VIX": "^VIX",
    }
    try:
        results = []
        for name, symbol in indices.items():
            try:
                info = yf.Ticker(symbol).info
                price = info.get("regularMarketPrice")
                prev_close = info.get("regularMarketPreviousClose")
                change_pct = round_float(((price - prev_close) / prev_close) * 100, 2) if price and prev_close else None

                results.append({
                    "name": name,
                    "symbol": symbol,
                    "price": round_float(price),
                    "change_pct": change_pct,
                    "day_high": round_float(info.get("regularMarketDayHigh")),
                    "day_low": round_float(info.get("regularMarketDayLow")),
                })
            except Exception:
                continue

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "indices": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching market summary: {str(e)}")


@app.get("/market/sectors", tags=["Market Data"], responses={
    200: {
        "description": "Performance of major market sectors",
        "content": {
            "application/json": {
                "example": {
                    "timestamp": "2026-03-23T10:30:00+00:00",
                    "sectors": [
                        {"sector": "Technology", "etf": "XLK", "price": 245.80, "change_pct": 1.85},
                        {"sector": "Healthcare", "etf": "XLV", "price": 142.30, "change_pct": 0.92},
                        {"sector": "Financials", "etf": "XLF", "price": 42.50, "change_pct": 0.45},
                        {"sector": "Energy", "etf": "XLE", "price": 88.20, "change_pct": -0.35},
                        {"sector": "Consumer Discretionary", "etf": "XLY", "price": 182.40, "change_pct": 1.25}
                    ]
                }
            }
        }
    }
})
@limiter.limit("10/minute")
async def get_sector_performance(request: Request):
    """
    Get performance of major market sectors.

    Returns daily % change for 11 GICS sectors using sector ETFs.

    Example: /market/sectors
    """
    sectors = {
        "Technology": "XLK",
        "Healthcare": "XLV",
        "Financials": "XLF",
        "Energy": "XLE",
        "Consumer Discretionary": "XLY",
        "Consumer Staples": "XLP",
        "Industrials": "XLI",
        "Utilities": "XLU",
        "Real Estate": "XLRE",
        "Materials": "XLB",
        "Communication Services": "XLC",
    }
    try:
        results = []
        for sector_name, etf in sectors.items():
            try:
                info = yf.Ticker(etf).info
                price = info.get("regularMarketPrice")
                prev_close = info.get("regularMarketPreviousClose")
                change_pct = round_float(((price - prev_close) / prev_close) * 100, 2) if price and prev_close else None

                results.append({
                    "sector": sector_name,
                    "etf": etf,
                    "price": round_float(price),
                    "change_pct": change_pct,
                })
            except Exception:
                continue

        results.sort(key=lambda x: x["change_pct"] or 0, reverse=True)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sectors": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sector performance: {str(e)}")


# ─────────────────────────────────────────────
# CRYPTO & FOREX
# ─────────────────────────────────────────────

@app.get("/crypto/{symbol}/quote", tags=["Crypto & Forex"], responses={
    200: {
        "description": "Real-time cryptocurrency quote",
        "content": {
            "application/json": {
                "example": {
                    "symbol": "BTC",
                    "pair": "BTC-USD",
                    "price_usd": 67542.30,
                    "open": 66850.00,
                    "day_high": 68250.00,
                    "day_low": 66200.00,
                    "volume_24h": 28500000000,
                    "market_cap": 1320000000000,
                    "52_week_high": 108240.00,
                    "52_week_low": 38250.00
                }
            }
        }
    }
})
@limiter.limit("30/minute")
async def get_crypto_quote(request: Request, symbol: str):
    """
    Get real-time cryptocurrency quote.

    Args:
        symbol: Crypto symbol (e.g., BTC, ETH, SOL, BNB)

    Returns price, volume, market cap, and 24h change.

    Example: /crypto/BTC/quote
    """
    symbol = symbol.upper().strip()
    ticker_symbol = f"{symbol}-USD"
    try:
        crypto = yf.Ticker(ticker_symbol)
        info = crypto.info

        if not info or info.get("regularMarketPrice") is None:
            raise HTTPException(status_code=404, detail=f"Crypto '{symbol}' not found")

        return {
            "symbol": symbol,
            "pair": ticker_symbol,
            "price_usd": round_float(info.get("regularMarketPrice")),
            "open": round_float(info.get("regularMarketOpen")),
            "day_high": round_float(info.get("regularMarketDayHigh")),
            "day_low": round_float(info.get("regularMarketDayLow")),
            "volume_24h": info.get("regularMarketVolume"),
            "market_cap": round_float(info.get("marketCap")),
            "52_week_high": round_float(info.get("fiftyTwoWeekHigh")),
            "52_week_low": round_float(info.get("fiftyTwoWeekLow")),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching crypto quote: {str(e)}")


@app.get("/forex/{pair}/quote", tags=["Crypto & Forex"], responses={
    200: {
        "description": "Real-time forex exchange rate",
        "content": {
            "application/json": {
                "example": {
                    "pair": "EURUSD",
                    "base_currency": "EUR",
                    "quote_currency": "USD",
                    "rate": 1.0845,
                    "open": 1.0820,
                    "day_high": 1.0875,
                    "day_low": 1.0810,
                    "previous_close": 1.0825
                }
            }
        }
    }
})
@limiter.limit("30/minute")
async def get_forex_quote(request: Request, pair: str):
    """
    Get real-time forex exchange rate.

    Args:
        pair: Currency pair (e.g., EURUSD, GBPUSD, USDJPY, INRUSD)

    Returns current rate, day high/low, and open.

    Example: /forex/EURUSD/quote
    """
    pair = pair.upper().strip()
    if len(pair) != 6:
        raise HTTPException(status_code=400, detail="Pair must be 6 characters, e.g. EURUSD, GBPUSD")

    base = pair[:3]
    quote = pair[3:]
    ticker_symbol = f"{base}{quote}=X"

    try:
        forex = yf.Ticker(ticker_symbol)
        info = forex.info

        if not info or info.get("regularMarketPrice") is None:
            raise HTTPException(status_code=404, detail=f"Forex pair '{pair}' not found")

        return {
            "pair": pair,
            "base_currency": base,
            "quote_currency": quote,
            "rate": round_float(info.get("regularMarketPrice")),
            "open": round_float(info.get("regularMarketOpen")),
            "day_high": round_float(info.get("regularMarketDayHigh")),
            "day_low": round_float(info.get("regularMarketDayLow")),
            "previous_close": round_float(info.get("regularMarketPreviousClose")),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching forex quote: {str(e)}")


# ─────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────

@app.get("/stock/search", tags=["Stock Data"], responses={
    200: {
        "description": "Search for stocks by ticker or company name",
        "content": {
            "application/json": {
                "example": {
                    "query": "Apple",
                    "results": [
                        {
                            "ticker": "AAPL",
                            "company_name": "Apple Inc.",
                            "price": 178.52,
                            "exchange": "NASDAQ",
                            "sector": "Technology",
                            "currency": "USD"
                        }
                    ]
                }
            }
        }
    }
})
@limiter.limit("20/minute")
async def search_stocks(
    request: Request,
    q: str = Query(..., description="Search query - company name or ticker symbol"),
):
    """
    Search for stocks by ticker or company name.

    Args:
        q: Search query (e.g., 'Apple', 'AAPL', 'Tesla')

    Returns matching stocks with basic quote data.

    Example: /stock/search?q=AAPL
    """
    if len(q.strip()) < 1:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")

    try:
        # Try direct ticker lookup first
        results = []
        candidates = [q.upper().strip()]

        for ticker_str in candidates:
            try:
                stock = yf.Ticker(ticker_str)
                info = stock.info
                if info and info.get("regularMarketPrice"):
                    results.append({
                        "ticker": ticker_str,
                        "company_name": info.get("shortName") or info.get("longName", "N/A"),
                        "price": round_float(info.get("regularMarketPrice")),
                        "exchange": info.get("exchange", "N/A"),
                        "sector": info.get("sector", "N/A"),
                        "currency": info.get("currency", "USD"),
                    })
            except Exception:
                continue

        if not results:
            raise HTTPException(status_code=404, detail=f"No stocks found for query '{q}'")

        return {"query": q, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching stocks: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
