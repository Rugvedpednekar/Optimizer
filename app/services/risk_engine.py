def calculate_risk_levels(price: float, atr: float, signal: str, rr_ratio: float = 2.0):
    if signal == "BUY":
        stop_loss = price - (1.5 * atr)
        take_profit = price + (atr * 1.5 * rr_ratio)
    elif signal == "SELL":
        stop_loss = price + (1.5 * atr)
        take_profit = price - (atr * 1.5 * rr_ratio)
    else:
        stop_loss = None
        take_profit = None

    return {
        "stop_loss": round(stop_loss, 2) if stop_loss else None,
        "take_profit": round(take_profit, 2) if take_profit else None,
        "risk_reward": rr_ratio
    }
