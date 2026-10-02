import unittest

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


if __name__ == "__main__":
    unittest.main()
