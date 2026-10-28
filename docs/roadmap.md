# Roadmap

## Milestone 1 — Working baseline
- [x] Synthetic, seeded price generator
- [x] Research agent with transparent momentum rule
- [x] Independent risk gate
- [x] Coordinator and message trace
- [x] Unit tests and command-line demo

## Milestone 2 — Deep-learning model
- [ ] Select and document a time-series dataset with appropriate usage rights
- [ ] Define a naive baseline and evaluation metrics before training
- [ ] Build chronological train, validation, and test splits
- [ ] Train a compact model and save its configuration and weights
- [ ] Compare against the momentum baseline without data leakage

## Milestone 3 — Stronger multi-agent evaluation
- [ ] Add an evaluator agent that critiques the research rationale
- [ ] Record decisions, risk rejections, and agent latencies
- [ ] Test disagreements between research and evaluator agents
- [ ] Add ablation experiments to measure the value of each agent

## Milestone 4 — Distributed execution
- [ ] Define versioned JSON message schemas
- [ ] Add a transport adapter and correlation IDs
- [ ] Add retries, timeouts, and idempotency
- [ ] Keep risk checks fail-closed when dependencies fail

## Evaluation principles
- Keep all test data chronologically separate from training.
- Compare against simple baselines.
- Report transaction costs and turnover if a backtest is added.
- Do not describe synthetic-data results as evidence of real-world trading performance.
