# Distributed Multi-Agent Market Simulator

**Course:** Deep Learning Technologies  
**Project:** Final project

A research prototype for a distributed, multi-agent financial decision system. Specialized agents analyze a market snapshot, propose a position, apply risk limits, and coordinate a simulated portfolio action. The initial implementation uses transparent baseline rules so the workflow can be tested before replacing the analyst with a trained deep-learning model.

> **Safety and scope:** This is an educational simulation. It does not connect to a broker, place live orders, or provide investment advice. All market data in the demo is synthetic.

## What it demonstrates

- **Market data agent** — produces a reproducible synthetic price series and current market snapshot.
- **Research agent** — turns recent price movement into a transparent BUY / SELL / HOLD proposal with a confidence score.
- **Risk agent** — checks the proposal against configurable position and confidence limits.
- **Coordinator** — passes typed messages between agents, records each decision, and returns a final simulated action.
- **Evaluation** — computes basic return, volatility, and drawdown statistics from the generated series.

The current research agent is a rule-based baseline, **not a trained deep-learning model**. This gives the project a reliable end-to-end foundation and a clear comparison point for a future neural model.

## Quick start

Requires Python 3.11 or newer. The starter version uses only the Python standard library.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
python -m pip install -e .
python -m distributed_multiagent
```

Run tests:

```bash
python -m unittest discover -s tests -v
```

## Example workflow

1. Generate deterministic synthetic prices.
2. Ask the research agent for a directional signal.
3. Ask the risk agent to approve, reduce, or reject the proposed exposure.
4. Record the coordinator's decision and print a compact run summary.

## Configuration

The demo exposes a seed and number of time steps, so runs are reproducible:

```bash
python -m distributed_multiagent --seed 7 --steps 120
```

## Architecture

```text
Synthetic Market Data
        |
        v
   Research Agent ---- signal / confidence ----+
                                               v
                                        Risk Agent
                                               |
                                        approved exposure
                                               v
                                         Coordinator
                                               |
                                      Simulated decision
```

See [docs/architecture.md](docs/architecture.md) for design notes and [docs/roadmap.md](docs/roadmap.md) for next steps.

## Limitations and next steps

- Synthetic data is for software validation only; it does not establish trading performance.
- The baseline signal uses recent returns, not a learned representation.
- The current demo is a single-process simulation of agent boundaries, not a networked distributed deployment.
- No broker integration, credentials, or live trading are included.

Planned extensions include a trained time-series model, an independent evaluator agent, message/event logging, and experiments comparing the baseline with the learned model.
