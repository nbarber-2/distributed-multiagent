import unittest

from distributed_multiagent.agents import MarketSnapshot
from distributed_multiagent.simulation import Coordinator, evaluate_returns, generate_prices


class SimulationTests(unittest.TestCase):
    def test_price_generator_is_reproducible(self):
        self.assertEqual(generate_prices(steps=10, seed=21), generate_prices(steps=10, seed=21))

    def test_price_generator_requires_two_steps(self):
        with self.assertRaises(ValueError):
            generate_prices(steps=1)

    def test_coordinator_records_agent_messages(self):
        market = MarketSnapshot("DEMO", (100.0, 101.0, 102.0))
        result = Coordinator().run(market)
        self.assertEqual(len(result.messages), 2)
        self.assertEqual(result.messages[0].message_type, "signal.proposed")
        self.assertEqual(result.messages[1].message_type, "risk.reviewed")

    def test_evaluation_metrics_are_bounded(self):
        metrics = evaluate_returns((100.0, 110.0, 105.0))
        self.assertAlmostEqual(metrics["total_return"], 0.05)
        self.assertGreaterEqual(metrics["max_drawdown"], 0.0)


if __name__ == "__main__":
    unittest.main()
