"""Command-line entry point for the simulation."""

from __future__ import annotations

import argparse

from .agents import MarketSnapshot
from .simulation import Coordinator, evaluate_returns, generate_prices


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the educational multi-agent market simulation.")
    parser.add_argument("--seed", type=int, default=7, help="Random seed for reproducibility.")
    parser.add_argument("--steps", type=int, default=60, help="Number of synthetic price observations.")
    parser.add_argument("--symbol", default="DEMO", help="Synthetic instrument label.")
    args = parser.parse_args()

    prices = generate_prices(steps=args.steps, seed=args.seed)
    market = MarketSnapshot(symbol=args.symbol, prices=prices)
    result = Coordinator().run(market)
    metrics = evaluate_returns(prices)

    print("Distributed Multi-Agent Market Simulator")
    print("=" * 42)
    print(f"Instrument:       {result.symbol}")
    print(f"Start / end:      {result.start_price:.2f} / {result.end_price:.2f}")
    print(f"Window return:    {result.market_return:+.2%}")
    print(f"Research signal:  {result.signal.action} (heuristic confidence {result.signal.confidence:.2f})")
    print(f"Research rationale: {result.signal.rationale}")
    print(f"Risk decision:    {result.risk.action} | approved={result.risk.approved} | exposure={result.risk.exposure:.2f}")
    print(f"Risk rationale:   {result.risk.reason}")
    print(f"Messages routed:  {len(result.messages)}")
    print("\nDescriptive synthetic-market metrics")
    for name, value in metrics.items():
        print(f"  {name.replace('_', ' '):24s} {value:+.4%}")


if __name__ == "__main__":
    main()
