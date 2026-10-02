import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from chain_stage import _locate_script, respond


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

    def test_a_score_named_by_a_numeric_string_records_that_outcome_once(self) -> None:
        body, status = respond(
            {
                "command": "record_outcome",
                "args": {
                    "outcome_id": "outcome-1",
                    "fulfillment_id": "order-treatment",
                    "concern": "pigmentation",
                    "score": " 81 ",
                },
            }
        )
        self.assertEqual(status, 200)
        self.assertEqual(body["artifact"]["score"], 81)
        zero, zero_status = respond(
            {
                "command": "record_outcome",
                "args": {
                    "outcome_id": "outcome-0",
                    "fulfillment_id": "order-treatment",
                    "concern": "dryness",
                    "score": "0",
                },
            }
        )
        self.assertEqual(zero_status, 200)
        self.assertEqual(zero["artifact"]["score"], 0)
        rejected, rejected_status = respond(
            {
                "command": "record_outcome",
                "args": {
                    "outcome_id": "outcome-word",
                    "fulfillment_id": "order-treatment",
                    "concern": "pigmentation",
                    "score": "high",
                },
            }
        )
        self.assertEqual(rejected_status, 400)
        self.assertFalse(rejected["ok"])
        script = _locate_script()
        self.assertIsNotNone(script)
        hub = script.parent.parent
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "supply-chain.jsonl"
            previous_ledger = os.environ.get("SKINTWIN_CHAIN_LEDGER")
            previous_hub = os.environ.get("SKINTWIN_HUB_ROOT")
            os.environ["SKINTWIN_CHAIN_LEDGER"] = str(ledger)
            os.environ["SKINTWIN_HUB_ROOT"] = str(hub)
            try:
                seeded = subprocess.run(
                    ["python3", "-m", "domain.ledger"],
                    cwd=hub,
                    input=json.dumps(
                        {
                            "commands": [
                                {
                                    "command": "specify_ingredient",
                                    "args": {"ingredient_id": "glycerin", "inci": "Glycerin", "cas": "56-81-5"},
                                },
                                {
                                    "command": "qualify_supplier",
                                    "args": {
                                        "qualification_id": "qual-glycerin",
                                        "supplier_name": "Inland Humectants",
                                        "ingredient_id": "glycerin",
                                    },
                                },
                                {
                                    "command": "receive_lot",
                                    "args": {
                                        "lot_id": "lot-glycerin",
                                        "ingredient_id": "glycerin",
                                        "qualification_id": "qual-glycerin",
                                        "milligrams": 5000,
                                    },
                                },
                                {
                                    "command": "define_formula",
                                    "args": {
                                        "formula_id": "cleanser",
                                        "name": "Gentle cleanser",
                                        "lines": [["glycerin", 5000]],
                                    },
                                },
                                {
                                    "command": "catalog_sku",
                                    "args": {
                                        "sku_id": "sku-cleanser",
                                        "formula_id": "cleanser",
                                        "name": "Gentle cleanser",
                                    },
                                },
                                {
                                    "command": "manufacture",
                                    "args": {
                                        "batch_id": "batch-cleanser",
                                        "sku_id": "sku-cleanser",
                                        "units": 1,
                                        "allocations": [["glycerin", "lot-glycerin", 5000]],
                                    },
                                },
                                {
                                    "command": "transfer",
                                    "args": {
                                        "transfer_id": "xfer-cape-town",
                                        "sku_id": "sku-cleanser",
                                        "batch_id": "batch-cleanser",
                                        "source": "plant",
                                        "destination": "cape-town",
                                        "milligrams": 2000,
                                    },
                                },
                                {
                                    "command": "fulfill",
                                    "args": {
                                        "fulfillment_id": "order-treatment",
                                        "sku_id": "sku-cleanser",
                                        "location": "cape-town",
                                        "milligrams": 2000,
                                        "kind": "retail",
                                    },
                                },
                            ]
                        }
                    ),
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(seeded.returncode, 0, seeded.stderr or seeded.stdout)
                seeded_text = ledger.read_text(encoding="utf-8")
                missing, missing_status = respond(
                    {
                        "command": "record_outcome",
                        "args": {
                            "outcome_id": "outcome-missing",
                            "fulfillment_id": "",
                            "concern": "pigmentation",
                            "score": "81",
                        },
                    }
                )
                self.assertEqual(missing_status, 400)
                self.assertFalse(missing["ok"])
                self.assertEqual(ledger.read_text(encoding="utf-8"), seeded_text)
                word, word_status = respond(
                    {
                        "command": "record_outcome",
                        "args": {
                            "outcome_id": "outcome-word",
                            "fulfillment_id": "order-treatment",
                            "concern": "pigmentation",
                            "score": "high",
                        },
                    }
                )
                self.assertEqual(word_status, 400)
                self.assertEqual(ledger.read_text(encoding="utf-8"), seeded_text)
                recorded, recorded_status = respond(
                    {
                        "command": "record_outcome",
                        "args": {
                            "outcome_id": "outcome-text",
                            "fulfillment_id": "order-treatment",
                            "concern": "pigmentation",
                            "score": "81",
                        },
                    }
                )
                self.assertEqual(recorded_status, 200, recorded)
                self.assertTrue(recorded["ok"])
                written = ledger.read_text(encoding="utf-8")
                self.assertIn('"score": 81', written)
                self.assertIn("outcome-text", written)
                again, again_status = respond(
                    {
                        "command": "record_outcome",
                        "args": {
                            "outcome_id": "outcome-text",
                            "fulfillment_id": "order-treatment",
                            "concern": "pigmentation",
                            "score": "81",
                        },
                    }
                )
                self.assertEqual(again_status, 400)
                self.assertEqual(ledger.read_text(encoding="utf-8"), written)
            finally:
                if previous_ledger is None:
                    os.environ.pop("SKINTWIN_CHAIN_LEDGER", None)
                else:
                    os.environ["SKINTWIN_CHAIN_LEDGER"] = previous_ledger
                if previous_hub is None:
                    os.environ.pop("SKINTWIN_HUB_ROOT", None)
                else:
                    os.environ["SKINTWIN_HUB_ROOT"] = previous_hub


if __name__ == "__main__":
    unittest.main()
