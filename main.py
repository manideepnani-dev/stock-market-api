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
                "Provides quotes, historical prices, company info, financials, technical indicators, "
                "news, dividends, earnings, market movers, sectors, crypto, and forex data.",
    version="2.0.0",
)

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

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns the current UTC timestamp and status to verify the API is running.
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

@app.get("/stock/{ticker}/quote", tags=["Stock Data"])
async def get_stock_quote(ticker: str, response: Response):
    """
    Get real-time stock quote for a given ticker.

    Returns price, open, high, low, volume, market_cap, pe_ratio, 52-week high/low, currency.
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
    Get historical OHLCV data for a stock.
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


@app.get("/stock/{ticker}/info", tags=["Stock Data"])
async def get_stock_info(ticker: str, response: Response):
    """
    Get company information and metadata for a stock.
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


@app.get("/stock/{ticker}/recommendations", tags=["Stock Data"])
async def get_stock_recommendations(ticker: str, response: Response):
    """
    Get latest analyst recommendations for a stock.
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


@app.get("/stocks/compare", tags=["Stock Data"])
async def compare_stocks(
    tickers: str = Query(..., description="Comma-separated ticker symbols (max 5, e.g. AAPL,MSFT,TSLA)"),
    response: Response = None
):
    """
    Compare multiple stocks side by side.
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

@app.get("/stock/{ticker}/financials", tags=["Stock Data"])
async def get_stock_financials(ticker: str, response: Response):
    """
    Get financial statements for a stock.

    Returns latest annual income statement, balance sheet, and cash flow data.
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


@app.get("/stock/{ticker}/news", tags=["Stock Data"])
async def get_stock_news(
    ticker: str,
    limit: int = Query(default=10, ge=1, le=50, description="Number of news articles to return (max 50)"),
    response: Response = None
):
    """
    Get latest news articles for a stock.

    Returns title, publisher, link, and publish time for each article.
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


@app.get("/stock/{ticker}/indicators", tags=["Stock Data"])
async def get_technical_indicators(
    ticker: str,
    period: str = Query(default="6mo", description="Time period for calculation: 3mo, 6mo, 1y, 2y"),
    response: Response = None
):
    """
    Get technical indicators for a stock.

    Returns SMA (20, 50, 200), EMA (12, 26), RSI (14), MACD, and Bollinger Bands.
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


@app.get("/stock/{ticker}/dividends", tags=["Stock Data"])
async def get_stock_dividends(
    ticker: str,
    limit: int = Query(default=20, ge=1, le=100, description="Number of dividend records to return"),
    response: Response = None
):
    """
    Get dividend history for a stock.

    Returns dividend payment dates and amounts, plus current yield and annual rate.
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


@app.get("/stock/{ticker}/earnings", tags=["Stock Data"])
async def get_stock_earnings(ticker: str, response: Response):
    """
    Get earnings data for a stock.

    Returns annual and quarterly EPS, revenue, and upcoming earnings date.
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


@app.get("/stock/{ticker}/analysts", tags=["Stock Data"])
async def get_analyst_targets(ticker: str, response: Response):
    """
    Get analyst price targets and ratings summary for a stock.

    Returns mean/low/high price targets and buy/hold/sell counts.
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

@app.get("/market/movers", tags=["Market Data"])
async def get_market_movers(response: Response = None):
    """
    Get top market movers - gainers and losers of the day.

    Tracks a curated list of large-cap stocks and returns top 5 gainers and losers by % change.
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


@app.get("/market/summary", tags=["Market Data"])
async def get_market_summary(response: Response = None):
    """
    Get overall market summary for major indices.

    Returns current price and daily change for S&P 500, NASDAQ, Dow Jones, Russell 2000, and VIX.
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


@app.get("/market/sectors", tags=["Market Data"])
async def get_sector_performance(response: Response = None):
    """
    Get performance of major market sectors.

    Returns daily % change for 11 GICS sectors using sector ETFs.
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

@app.get("/crypto/{symbol}/quote", tags=["Crypto & Forex"])
async def get_crypto_quote(symbol: str, response: Response = None):
    """
    Get real-time cryptocurrency quote.

    Args:
        symbol: Crypto symbol (e.g., BTC, ETH, SOL, BNB)

    Returns price, volume, market cap, and 24h change.
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


@app.get("/forex/{pair}/quote", tags=["Crypto & Forex"])
async def get_forex_quote(pair: str, response: Response = None):
    """
    Get real-time forex exchange rate.

    Args:
        pair: Currency pair (e.g., EURUSD, GBPUSD, USDJPY, INRUSD)

    Returns current rate, day high/low, and open.
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

@app.get("/stock/search", tags=["Stock Data"])
async def search_stocks(
    q: str = Query(..., description="Search query - company name or ticker symbol"),
    response: Response = None
):
    """
    Search for stocks by ticker or company name.

    Args:
        q: Search query (e.g., 'Apple', 'AAPL', 'Tesla')

    Returns matching stocks with basic quote data.
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
