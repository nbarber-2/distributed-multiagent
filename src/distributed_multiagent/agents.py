"""Small, explicit agents used by the educational simulation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

Action = Literal["BUY", "SELL", "HOLD"]


@dataclass(frozen=True)
class MarketSnapshot:
    """A point-in-time market view. Prices must be positive."""

    symbol: str
    prices: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("symbol must not be empty")
        if len(self.prices) < 2:
            raise ValueError("at least two prices are required")
        if any(price <= 0 for price in self.prices):
            raise ValueError("prices must all be positive")

    @property
    def recent_return(self) -> float:
        """Return over the most recent observation interval."""
        return self.prices[-1] / self.prices[-2] - 1.0

    @property
    def window_return(self) -> float:
        """Return over the full supplied window."""
        return self.prices[-1] / self.prices[0] - 1.0


@dataclass(frozen=True)
class Signal:
    action: Action
    confidence: float
    rationale: str
    agent: str = "research"

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    action: Action
    exposure: float
    reason: str
    agent: str = "risk"


class ResearchAgent:
    """Transparent momentum baseline; replace with a trained model later."""

    def __init__(self, threshold: float = 0.002) -> None:
        if threshold < 0:
            raise ValueError("threshold must be non-negative")
        self.threshold = threshold

    def analyze(self, market: MarketSnapshot) -> Signal:
        movement = market.window_return
        if movement > self.threshold:
            action: Action = "BUY"
            rationale = "The supplied window has positive momentum."
        elif movement < -self.threshold:
            action = "SELL"
            rationale = "The supplied window has negative momentum."
        else:
            action = "HOLD"
            rationale = "The supplied window is inside the neutral band."

        # Confidence is a bounded, interpretable heuristic, not a probability.
        confidence = min(1.0, abs(movement) / max(self.threshold * 5, 0.01))
        if action == "HOLD":
            confidence = 1.0 - confidence
        return Signal(action=action, confidence=confidence, rationale=rationale)


class RiskAgent:
    """Applies hard exposure and confidence limits to a proposed signal."""

    def __init__(
        self,
        max_exposure: float = 1.0,
        min_confidence: float = 0.2,
    ) -> None:
        if not 0.0 <= max_exposure <= 1.0:
            raise ValueError("max_exposure must be between 0 and 1")
        if not 0.0 <= min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")
        self.max_exposure = max_exposure
        self.min_confidence = min_confidence

    def review(self, signal: Signal) -> RiskDecision:
        if signal.action == "HOLD":
            return RiskDecision(True, "HOLD", 0.0, "No position requested.")
        if signal.confidence < self.min_confidence:
            return RiskDecision(False, "HOLD", 0.0, "Signal confidence is below the risk threshold.")
        # Exposure is scaled by confidence and cannot exceed the configured cap.
        exposure = self.max_exposure * signal.confidence
        return RiskDecision(True, signal.action, exposure, "Signal passed the configured risk checks.")
