import unittest

from distributed_multiagent.agents import MarketSnapshot, ResearchAgent, RiskAgent, Signal


class AgentTests(unittest.TestCase):
    def test_snapshot_rejects_nonpositive_prices(self):
        with self.assertRaises(ValueError):
            MarketSnapshot("DEMO", (100.0, 0.0))

    def test_research_detects_positive_momentum(self):
        signal = ResearchAgent().analyze(MarketSnapshot("DEMO", (100.0, 101.0, 102.0)))
        self.assertEqual(signal.action, "BUY")
        self.assertGreaterEqual(signal.confidence, 0.0)
        self.assertLessEqual(signal.confidence, 1.0)

    def test_research_detects_negative_momentum(self):
        signal = ResearchAgent().analyze(MarketSnapshot("DEMO", (100.0, 99.0, 98.0)))
        self.assertEqual(signal.action, "SELL")

    def test_risk_rejects_low_confidence_signal(self):
        signal = Signal("BUY", 0.1, "weak signal")
        decision = RiskAgent(min_confidence=0.2).review(signal)
        self.assertFalse(decision.approved)
        self.assertEqual(decision.action, "HOLD")
        self.assertEqual(decision.exposure, 0.0)

    def test_risk_caps_exposure(self):
        signal = Signal("BUY", 1.0, "strong signal")
        decision = RiskAgent(max_exposure=0.4).review(signal)
        self.assertTrue(decision.approved)
        self.assertEqual(decision.exposure, 0.4)


if __name__ == "__main__":
    unittest.main()
