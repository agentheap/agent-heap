from datetime import datetime, timedelta, timezone
from typing import Any


class CircuitBreaker:
    def __init__(self, max_daily_drawdown: float = 0.05):
        self.max_daily_drawdown = max_daily_drawdown
        self.daily_trades: list[dict[str, Any]] = []

    def record_trade(self, pnl: float) -> None:
        now = datetime.now(timezone.utc)
        self.daily_trades = [
            t
            for t in self.daily_trades
            if t["timestamp"].replace(tzinfo=timezone.utc) > now - timedelta(hours=24)
        ]
        self.daily_trades.append({"timestamp": now, "pnl": pnl})

    def is_tripped(self) -> bool:
        total_pnl = sum(t["pnl"] for t in self.daily_trades)
        return total_pnl < -self.max_daily_drawdown

    def reset(self) -> None:
        self.daily_trades = []
