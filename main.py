"""
Stock Market Data API

A production-ready REST API for fetching stock market data from Yahoo Finance.
Built with FastAPI and yfinance library.
"""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import yfinance as yf
import pandas as pd

app = FastAPI(
    title="Stock Market Data API",
    description="A production-ready API for fetching real-time stock market data from Yahoo Finance. "
                "Provides quotes, historical prices, company info, and analyst recommendations.",
    version="1.0.0",
)

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


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the current UTC timestamp and status to verify the API is running.

    Returns:
        JSON with status and current UTC timestamp
    """
    try:
        return {
            "status": "ok",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stock/{ticker}/quote", tags=["Stock Data"])
async def get_stock_quote(ticker: str, response: Response):
    """
    Get real-time stock quote for a given ticker.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Returns:
        Real-time price data including:
        - price, open, high, low, volume
        - market_cap, pe_ratio
        - 52_week_high, 52_week_low
        - currency
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


@app.get("/stock/{ticker}/history", tags=["Stock Data"])
async def get_stock_history(
    ticker: str,
    period: str = Query(default="1mo", description="Time period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max"),
    interval: str = Query(default="1d", description="Data interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo"),
    response: Response = None
):
    """
    Get historical OHLCV (Open, High, Low, Close, Volume) data for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)
        period: Time period for historical data (default: 1mo)
        interval: Data interval/frequency (default: 1d)

    Returns:
        List of OHLCV records with date, open, high, low, close, volume
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)

        # Validate period and interval
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo"]

        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )

        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
            )

        hist = stock.history(period=period, interval=interval)

        if hist.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No historical data found for ticker '{ticker}'"
            )

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

        return {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "data": records,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


@app.get("/stock/{ticker}/info", tags=["Stock Data"])
async def get_stock_info(ticker: str, response: Response):
    """
    Get company information and metadata for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Returns:
        Company details including:
        - company_name, sector, industry
        - country, website, employees
        - description, exchange
        - dividend_yield
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or not info.get("regularMarketPrice"):
            raise HTTPException(
                status_code=404,
                detail=f"Ticker '{ticker}' not found or no market data available"
            )

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


@app.get("/stock/{ticker}/recommendations", tags=["Stock Data"])
async def get_stock_recommendations(ticker: str, response: Response):
    """
    Get latest analyst recommendations for a stock.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT, TSLA)

    Returns:
        List of latest analyst recommendations with:
        - date, firm, to_grade, from_grade, action
    """
    ticker = validate_ticker(ticker)
    try:
        stock = yf.Ticker(ticker)
        recs = stock.recommendations

        if recs is None or recs.empty:
            raise HTTPException(
                status_code=404,
                detail=f"No recommendations found for ticker '{ticker}'"
            )

        # Get latest 10 recommendations
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

        return {
            "ticker": ticker,
            "recommendations": records,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching recommendations: {str(e)}")


@app.get("/stocks/compare", tags=["Stock Data"])
async def compare_stocks(
    tickers: str = Query(..., description="Comma-separated ticker symbols (max 5, e.g. AAPL,MSFT,TSLA)"),
    response: Response = None
):
    """
    Compare multiple stocks side by side.

    Args:
        tickers: Comma-separated list of ticker symbols (max 5)

    Returns:
        Price, market cap, PE ratio, and 52-week high/low for each ticker
    """
    ticker_list = [t.strip().upper() for t in tickers.split(",")]

    if len(ticker_list) > 5:
        raise HTTPException(
            status_code=400,
            detail="Maximum 5 tickers allowed for comparison"
        )

    if len(ticker_list) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 tickers required for comparison"
        )

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
        raise HTTPException(
            status_code=404,
            detail=f"No valid tickers found. Errors: {'; '.join(errors)}"
        )

    response_data = {"stocks": results}
    if errors:
        response_data["errors"] = errors

    return response_data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
