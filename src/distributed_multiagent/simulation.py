"""Coordinator and deterministic synthetic market generator."""

from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from statistics import mean, pstdev

from .agents import MarketSnapshot, ResearchAgent, RiskAgent, RiskDecision, Signal


@dataclass(frozen=True)
class AgentMessage:
    sender: str
    recipient: str
    message_type: str
    payload: dict[str, object]


@dataclass(frozen=True)
class SimulationResult:
    symbol: str
    start_price: float
    end_price: float
    market_return: float
    signal: Signal
    risk: RiskDecision
    messages: tuple[AgentMessage, ...]
    prices: tuple[float, ...]


class Coordinator:
    """Routes information between agents and records the decision trail."""

    def __init__(
        self,
        research_agent: ResearchAgent | None = None,
        risk_agent: RiskAgent | None = None,
    ) -> None:
        self.research_agent = research_agent or ResearchAgent()
        self.risk_agent = risk_agent or RiskAgent()

    def run(self, market: MarketSnapshot) -> SimulationResult:
        signal = self.research_agent.analyze(market)
        message_to_risk = AgentMessage(
            sender="research",
            recipient="risk",
            message_type="signal.proposed",
            payload=asdict(signal),
        )
        decision = self.risk_agent.review(signal)
        message_to_coordinator = AgentMessage(
            sender="risk",
            recipient="coordinator",
            message_type="risk.reviewed",
            payload=asdict(decision),
        )
        return SimulationResult(
            symbol=market.symbol,
            start_price=market.prices[0],
            end_price=market.prices[-1],
            market_return=market.window_return,
            signal=signal,
            risk=decision,
            messages=(message_to_risk, message_to_coordinator),
            prices=market.prices,
        )


def generate_prices(
    steps: int = 60,
    seed: int = 7,
    start_price: float = 100.0,
    drift: float = 0.0005,
    volatility: float = 0.01,
) -> tuple[float, ...]:
    """Generate a repeatable geometric random walk for demonstration only."""
    if steps < 2:
        raise ValueError("steps must be at least 2")
    if start_price <= 0:
        raise ValueError("start_price must be positive")
    if volatility < 0:
        raise ValueError("volatility must be non-negative")

    rng = random.Random(seed)
    prices = [float(start_price)]
    for _ in range(steps - 1):
        daily_return = drift + rng.gauss(0.0, volatility)
        prices.append(max(0.01, prices[-1] * (1.0 + daily_return)))
    return tuple(round(price, 4) for price in prices)


def evaluate_returns(prices: tuple[float, ...]) -> dict[str, float]:
    """Compute descriptive statistics; no claim of predictive performance."""
    if len(prices) < 2 or any(p <= 0 for p in prices):
        raise ValueError("at least two positive prices are required")
    returns = [prices[i] / prices[i - 1] - 1.0 for i in range(1, len(prices))]
    peak = prices[0]
    max_drawdown = 0.0
    for price in prices:
        peak = max(peak, price)
        max_drawdown = max(max_drawdown, (peak - price) / peak)
    return {
        "total_return": prices[-1] / prices[0] - 1.0,
        "mean_step_return": mean(returns),
        "step_return_volatility": pstdev(returns),
        "max_drawdown": max_drawdown,
    }
