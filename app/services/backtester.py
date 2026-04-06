import pandas as pd
import numpy as np
import yfinance as yf
from app.services.indicators import add_bollinger_bands, add_macd, add_rsi, add_sma

def run_backtest(
    ticker: str,
    strategy: str,
    initial_capital: float = 100000.0,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    if not start_date or not end_date:
        return {"error": "Start date and end date are required"}

    try:
        df = yf.download(
            ticker,
            start=start_date,
            end=end_date,
            interval="1d",
            auto_adjust=True,
            progress=False
        )
    except Exception as e:
        return {"error": f"Could not fetch data for {ticker}: {e}"}

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

    if df is None or df.empty or len(df) < 20:
        return {
            "error": (
                f"Not enough data for {ticker} between {start_date} and {end_date}. "
                f"Try a shorter date range or a different ticker."
            )
        }

    if isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.tz_localize(None)

    df = df.copy()
    required_columns = []
    if strategy == "sma_crossover":
        df = add_sma(df, 20)
        df = add_sma(df, 50)
        required_columns = ["SMA_20", "SMA_50"]
    elif strategy == "rsi_reversal":
        df = add_rsi(df, 14)
        required_columns = ["RSI"]
    elif strategy == "macd_crossover":
        df = add_macd(df)
        required_columns = ["MACD", "MACD_Signal"]
    elif strategy == "bollinger_bounce":
        df = add_bollinger_bands(df)
        required_columns = ["BB_Upper", "BB_Lower"]
    else:
        df = add_sma(df, 20)
        df = add_sma(df, 50)
        df = add_rsi(df, 14)
        required_columns = ["SMA_20", "SMA_50", "RSI"]

    df = df.dropna(subset=required_columns)
    if df.empty or len(df) < 20:
        return {
            "error": (
                f"Not enough data for {ticker} between {start_date} and {end_date}. "
                f"Try a shorter date range or a different ticker."
            )
        }
    
    # Generate Signals (-1 = Sell, 0 = Hold, 1 = Buy)
    signals = pd.Series(0, index=df.index)

    if strategy == "sma_crossover":
        signals = np.where(df["SMA_20"] > df["SMA_50"], 1, -1)
    elif strategy == "rsi_reversal":
        signals = np.where(df["RSI"] < 30, 1, np.where(df["RSI"] > 70, -1, 0))
    elif strategy == "macd_crossover":
        signals = np.where(df["MACD"] > df["MACD_Signal"], 1, -1)
    elif strategy == "bollinger_bounce":
        signals = np.where(df["Close"] < df["BB_Lower"], 1, np.where(df["Close"] > df["BB_Upper"], -1, 0))
    else:
        # Default or 'combined' fallback
        sma_sig = np.where(df["SMA_20"] > df["SMA_50"], 1, -1)
        rsi_sig = np.where(df["RSI"] < 30, 1, np.where(df["RSI"] > 70, -1, 0))
        signals = np.where((sma_sig == 1) & (rsi_sig == 1), 1, np.where((sma_sig == -1) & (rsi_sig == -1), -1, 0))

    # Shift signals to avoid look-ahead bias
    df["Signal"] = pd.Series(signals, index=df.index).shift(1).fillna(0)
    
    # Calculate returns
    df["Market_Return"] = df["Close"].pct_change()
    df["Strategy_Return"] = df["Market_Return"] * df["Signal"]
    
    df["Equity_Curve"] = initial_capital * (1 + df["Strategy_Return"]).cumprod()
    
    final_capital = df["Equity_Curve"].iloc[-1]
    total_return_pct = ((final_capital - initial_capital) / initial_capital) * 100
    
    wins = len(df[df["Strategy_Return"] > 0])
    losses = len(df[df["Strategy_Return"] < 0])
    win_rate = (wins / (wins + losses)) * 100 if (wins + losses) > 0 else 0

    running_max = df["Equity_Curve"].cummax()
    drawdown = (df["Equity_Curve"] - running_max) / running_max
    max_drawdown = drawdown.min() * 100

    sharpe_ratio = (df["Strategy_Return"].mean() / df["Strategy_Return"].std()) * np.sqrt(252) if df["Strategy_Return"].std() != 0 else 0

    # Format equity curve for charting
    equity_points = [{"date": str(idx.date()), "value": float(val)} for idx, val in df["Equity_Curve"].items() if not pd.isna(val)]
    price_points = [{"date": str(idx.date()), "value": float(val)} for idx, val in df["Close"].items() if not pd.isna(val)]

    return {
        "final_capital": round(final_capital, 2),
        "total_return_pct": round(total_return_pct, 2),
        "win_rate": round(win_rate, 2),
        "max_drawdown_pct": round(max_drawdown, 2),
        "sharpe_ratio": round(sharpe_ratio, 2),
        "data_start": str(df.index[0].date()),
        "data_end": str(df.index[-1].date()),
        "equity_curve": equity_points[::5], # Sample every 5 days for payload size
        "price_curve": price_points[::5],
    }
