import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

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

    @unittest.skipUnless(_locate_script(), "requires a registered supply-chain hub")
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

    def test_numeric_score_strings_are_normalized(self) -> None:
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

    @unittest.skipUnless(_locate_script(), "requires a registered supply-chain hub")
    def test_numeric_outcome_is_committed_once_by_the_hub(self) -> None:
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


class OutcomeBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environment = patch.dict(
            os.environ,
            {"SKINTWIN_CHAIN_LEDGER": "", "SKINTWIN_CHAIN_SKIP_DISPATCH": ""},
        )
        self.environment.start()
        self.addCleanup(self.environment.stop)
        self.args = {
            "outcome_id": "outcome-1",
            "fulfillment_id": "order-treatment",
            "concern": "pigmentation",
            "score": 81,
        }

    def test_invalid_requests_never_dispatch_or_change_the_ledger(self) -> None:
        invalid = [None, [], "request", 1, True]
        invalid += [
            {"command": "record_outcome", "args": value}
            for value in [[], [self.args], "args", 0, False]
        ]
        invalid += [
            {"command": "record_outcome", "args": {**self.args, "score": value}}
            for value in [True, False, -1, 101, 81.0, None, "high", "-1", "²", "9" * 5000]
        ]
        invalid += [
            {"command": "record_outcome", "args": {**self.args, field: value}}
            for field in ["outcome_id", "fulfillment_id", "concern"]
            for value in [None, "", "  ", 1, []]
        ]
        invalid += [
            {"command": "record_outcome"},
            {"command": "record_outcome", "args": None},
            {"command": "unknown", "args": self.args},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.jsonl"
            original = '{"existing":"record"}\n'
            ledger.write_text(original, encoding="utf-8")
            with patch.dict(os.environ, {"SKINTWIN_CHAIN_LEDGER": str(ledger)}):
                with patch("chain_stage._locator") as locator:
                    for request in invalid:
                        with self.subTest(request=str(request)[:160]):
                            body, status = respond(request)
                            self.assertEqual(status, 400)
                            self.assertFalse(body["ok"])
                            self.assertIsInstance(body["error"], str)
                    locator.assert_not_called()
            self.assertEqual(ledger.read_text(encoding="utf-8"), original)

    def test_valid_scores_and_trimmed_text_keep_the_artifact_contract(self) -> None:
        for value, expected in [(0, 0), (100, 100), (" 81 ", 81), ("٠", 0), ("１００", 100)]:
            with self.subTest(score=value):
                args = {**self.args, "score": value, "concern": " pigmentation ", "extra": 1}
                body, status = respond({"command": "record_outcome", "args": args})
                self.assertEqual(status, 200)
                self.assertEqual(body["artifact"], {**self.args, "score": expected})
                self.assertEqual(args["score"], value)

    def test_normalized_artifact_is_dispatched_exactly_once(self) -> None:
        hub = Mock()
        hub.commit_command.return_value = None
        args = {key: f" {value} " for key, value in self.args.items()}
        with patch.dict(os.environ, {"SKINTWIN_CHAIN_LEDGER": "ledger.jsonl"}):
            with patch("chain_stage._locator", return_value=hub):
                body, status = respond({"command": "record_outcome", "args": args})
        self.assertEqual(status, 200)
        self.assertEqual(body["artifact"], self.args)
        hub.commit_command.assert_called_once_with(
            {"command": "record_outcome", "args": self.args}
        )

    def test_hub_rejection_is_returned_to_the_caller(self) -> None:
        hub = Mock()
        hub.commit_command.return_value = "fulfillment does not exist"
        with patch.dict(os.environ, {"SKINTWIN_CHAIN_LEDGER": "ledger.jsonl"}):
            with patch("chain_stage._locator", return_value=hub):
                body, status = respond({"command": "record_outcome", "args": self.args})
        self.assertEqual(status, 400)
        self.assertEqual(body, {"ok": False, "error": "fulfillment does not exist"})

    def test_configured_ledger_requires_a_hub(self) -> None:
        with patch.dict(os.environ, {"SKINTWIN_CHAIN_LEDGER": "ledger.jsonl"}):
            with patch("chain_stage._locator", return_value=None):
                body, status = respond({"command": "record_outcome", "args": self.args})
        self.assertEqual(status, 400)
        self.assertEqual(body, {"ok": False, "error": "supply-chain hub is not present"})

    def test_local_modes_do_not_load_the_hub(self) -> None:
        for config in [
            {"SKINTWIN_CHAIN_LEDGER": ""},
            {"SKINTWIN_CHAIN_LEDGER": "ledger.jsonl", "SKINTWIN_CHAIN_SKIP_DISPATCH": "1"},
        ]:
            with self.subTest(config=config), patch.dict(os.environ, config):
                with patch("chain_stage._locator") as locator:
                    body, status = respond({"command": "record_outcome", "args": self.args})
                    self.assertEqual(status, 200)
                    self.assertTrue(body["ok"])
                    locator.assert_not_called()

    def test_cli_reports_json_errors_without_a_traceback(self) -> None:
        script = Path(__file__).with_name("chain_stage.py")
        requests = ["", "{", "null", "[]", "9" * 5000, '{"command":"record_outcome","args":false}']
        requests += [json.dumps({"command": "record_outcome", "args": {**self.args, "score": "²"}})]
        for request in requests:
            with self.subTest(request=request):
                result = subprocess.run(
                    [sys.executable, str(script)],
                    input=request,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stderr, "")
                self.assertFalse(json.loads(result.stdout)["ok"])

    def test_cli_returns_a_normalized_artifact(self) -> None:
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("chain_stage.py"))],
            input=json.dumps({"command": "record_outcome", "args": {**self.args, "score": "81"}}),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stderr, "")
        self.assertEqual(json.loads(result.stdout), {"ok": True, "artifact": self.args})


if __name__ == "__main__":
    unittest.main()
