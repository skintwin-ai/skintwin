"""Integrity checks for the supplied pattern topology and SkinTwin decisions."""

import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CATALOG = ROOT / "docs" / "cog253" / "catalog.json"
APPLICATION = ROOT / "docs" / "cog253" / "application.json"


class Cog253Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.application = json.loads(APPLICATION.read_text(encoding="utf-8"))

    def test_catalog_preserves_the_supplied_source(self) -> None:
        self.assertEqual(
            hashlib.sha256(CATALOG.read_bytes()).hexdigest(),
            self.application["source"]["catalog_sha256"],
        )
        self.assertEqual(self.catalog["version"], "1.0.0")
        self.assertEqual(self.catalog["total_patterns"], 253)

    def test_all_patterns_and_category_ranges_are_present(self) -> None:
        patterns = self.catalog["patterns"]
        expected = {f"cog{i:03}" for i in range(1, 254)}
        self.assertEqual(len(patterns), 253)
        self.assertEqual({pattern["id"] for pattern in patterns}, expected)
        categories = {
            "cat1_cognitive_ecosystems": (1, 94),
            "cat2_cognitive_subsystems": (95, 204),
            "cat3_cognitive_primitives": (205, 253),
        }
        self.assertEqual(set(self.catalog["categories"]), set(categories))
        for category, (start, end) in categories.items():
            with self.subTest(category=category):
                self.assertEqual(
                    self.catalog["categories"][category],
                    {"range": f"cog{start:03}-cog{end:03}", "count": end - start + 1},
                )

    def test_source_fields_and_related_patterns_are_valid(self) -> None:
        ids = {pattern["id"] for pattern in self.catalog["patterns"]}
        for pattern in self.catalog["patterns"]:
            with self.subTest(pattern=pattern["id"]):
                for field in ["name", "gh", "interpretation"]:
                    self.assertIsInstance(pattern[field], str)
                    self.assertTrue(pattern[field].strip())
                self.assertIsInstance(pattern["components"], list)
                self.assertTrue(pattern["components"])
                for component in pattern["components"]:
                    self.assertIsInstance(component, str)
                    self.assertTrue(component.strip())
                self.assertIsInstance(pattern["related"], list)
                self.assertTrue(set(pattern["related"]) <= ids)

    def test_application_covers_each_pattern_once_with_local_evidence(self) -> None:
        assigned = []
        groups = self.application["groups"]
        self.assertEqual(len({group["id"] for group in groups}), len(groups))
        self.assertEqual(set(self.application["statuses"]), {"applied", "existing", "design", "deferred"})
        for group in groups:
            with self.subTest(group=group["id"]):
                self.assertIn(group["status"], self.application["statuses"])
                self.assertTrue(group["name"].strip())
                self.assertTrue(group["decision"].strip())
                self.assertTrue(group["patterns"])
                self.assertTrue(group["evidence"])
                for evidence in group["evidence"]:
                    path = (ROOT / evidence).resolve()
                    self.assertTrue(path.is_relative_to(ROOT))
                    self.assertTrue(path.is_file(), evidence)
                assigned.extend(group["patterns"])
        self.assertEqual(len(assigned), 253)
        self.assertEqual(set(assigned), {pattern["id"] for pattern in self.catalog["patterns"]})


if __name__ == "__main__":
    unittest.main()
