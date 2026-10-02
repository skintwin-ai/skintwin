import json
import os
import tempfile
import unittest
from pathlib import Path

from chain_stage import respond


class OutcomeRouteTests(unittest.TestCase):
    def test_accepts_a_skin_outcome(self) -> None:
        body, status = respond(
            {
                "command": "record_outcome",
                "args": {
                    "outcome_id": "outcome-1",
                    "fulfillment_id": "order-treatment",
                    "concern": "pigmentation",
                    "score": 81,
                },
            }
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["artifact"]["score"], 81)

    def test_rejects_a_score_above_100(self) -> None:
        body, status = respond(
            {
                "command": "record_outcome",
                "args": {
                    "outcome_id": "outcome-1",
                    "fulfillment_id": "order-treatment",
                    "concern": "pigmentation",
                    "score": 140,
                },
            }
        )
        self.assertEqual(status, 400)

    def test_outcome_against_an_empty_ledger_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "supply-chain.jsonl"
            previous = os.environ.get("SKINTWIN_CHAIN_LEDGER")
            os.environ["SKINTWIN_CHAIN_LEDGER"] = str(ledger)
            os.environ["SKINTWIN_HUB_ROOT"] = "/agent/repos/skintwin-ecosystem-design"
            try:
                body, status = respond(
                    {
                        "command": "record_outcome",
                        "args": {
                            "outcome_id": "outcome-1",
                            "fulfillment_id": "missing-order",
                            "concern": "dryness",
                            "score": 40,
                        },
                    }
                )
            finally:
                if previous is None:
                    os.environ.pop("SKINTWIN_CHAIN_LEDGER", None)
                else:
                    os.environ["SKINTWIN_CHAIN_LEDGER"] = previous
        self.assertEqual(status, 400)
        self.assertFalse(body["ok"])
        self.assertFalse(ledger.exists())
        self.assertIn("fulfillment", json.dumps(body))


if __name__ == "__main__":
    unittest.main()
