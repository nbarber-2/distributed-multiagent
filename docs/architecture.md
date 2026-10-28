# Architecture and Message Flow

## Current design

The project models a small multi-agent system through explicit interfaces and typed messages. The first version runs in one Python process so the message contract and decision trail are easy to inspect.

1. **Market snapshot**: immutable symbol and price window.
2. **Research agent**: emits an action, a bounded heuristic confidence score, and a rationale.
3. **Risk agent**: applies a minimum-confidence gate and a maximum exposure limit.
4. **Coordinator**: routes the proposal and review, then returns the complete decision trace.
5. **Evaluator**: reports descriptive metrics for the synthetic price path.

## Message contracts

| Message | Sender | Recipient | Purpose |
|---|---|---|---|
| `signal.proposed` | research | risk | Proposed action and rationale |
| `risk.reviewed` | risk | coordinator | Approved/rejected action and exposure |

## Deep-learning extension point

Replace `ResearchAgent.analyze` with an inference adapter that accepts a feature tensor and returns a calibrated score. Keep risk controls separate from the model so a learned signal cannot override exposure limits. Evaluate the trained model against the current momentum baseline using chronological train/validation/test splits and metrics chosen before testing.

## Distributed extension point

For a networked implementation, serialize each message as JSON and send it over a message broker or HTTP interface. Add message IDs, timestamps, schema versions, retries, idempotency, timeouts, and audit logging before introducing asynchronous agents.

## Design boundaries

- Synthetic prices are not market data.
- The confidence value is a heuristic score, not a calibrated probability.
- The reported metrics describe the synthetic path only.
- No live trading or brokerage API is implemented.
