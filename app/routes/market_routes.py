from fastapi import APIRouter, HTTPException, Query
import pandas as pd
import yfinance as yf

router = APIRouter(prefix="/api/v1/market", tags=["market"])


def _normalize_history(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
    if isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = df.index.tz_localize(None)
        except TypeError:
            pass
    return df


def _safe_float(value, default=None):
    try:
        val = float(value)
        return val if val == val else default
    except (TypeError, ValueError):
        return default


def _fetch_quote_history(ticker: str, period: str = "5d", interval: str = "1d") -> pd.DataFrame:
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    df = _normalize_history(df)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail="No market data found for ticker")
    return df


@router.get("/{ticker}/ohlcv")
def get_ohlcv(
    ticker: str,
    period: str = Query("3mo"),
    interval: str = Query("1d"),
):
    df = _fetch_quote_history(ticker.upper(), period=period, interval=interval)
    candles = []
    for idx, row in df.iterrows():
        candles.append(
            {
                "time": str(idx.date()),
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if _safe_float(row["Volume"], 0) is not None else 0,
            }
        )
    return candles


@router.get("/{ticker}/info")
def get_market_info(ticker: str):
    symbol = ticker.upper()
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception as exc:
        raise HTTPException(status_code=404, detail=f"Could not load company info for {symbol}: {exc}") from exc

    summary = (info.get("longBusinessSummary") or "").strip()
    return {
        "name": info.get("longName", symbol),
        "sector": info.get("sector", "Equity"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": info.get("trailingPE"),
        "52w_high": info.get("fiftyTwoWeekHigh"),
        "52w_low": info.get("fiftyTwoWeekLow"),
        "avg_volume": info.get("averageVolume"),
        "dividend": info.get("dividendYield"),
        "beta": info.get("beta"),
        "description": summary[:300],
        "description_full": summary[:1200],
    }


@router.get("/{ticker}")
def get_market_snapshot(ticker: str):
    symbol = ticker.upper()
    df = _fetch_quote_history(symbol, period="5d", interval="1d")
    try:
        info = yf.Ticker(symbol).info or {}
    except Exception:
        info = {}

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else latest
    current_price = _safe_float(latest.get("Close"), 0.0) or 0.0
    previous_close = _safe_float(previous.get("Close"), current_price) or current_price
    change = current_price - previous_close
    change_pct = (change / previous_close * 100) if previous_close else 0.0

    return {
        "ticker": symbol,
        "name": info.get("longName", info.get("shortName", symbol)),
        "sector": info.get("sector", "Equity"),
        "current_price": round(current_price, 2),
        "previous_close": round(previous_close, 2),
        "change": round(change, 2),
        "change_pct": round(change_pct, 2),
        "volume": int(_safe_float(latest.get("Volume"), 0) or 0),
    }
