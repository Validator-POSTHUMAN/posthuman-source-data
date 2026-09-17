#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).with_name("update-monad-decentralize-map.py")
SPEC = importlib.util.spec_from_file_location("monad_map_updater", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def validator(validator_id: int, name: str) -> dict[str, object]:
    return {
        "id": validator_id,
        "name": name,
        "active": True,
        "decommissioned": False,
        "lat": 52.52,
        "lon": 13.405,
        "geo_city": "Berlin",
        "geo_country": "DE",
        "asn": 64500,
        "asn_org": "Example Network",
        "commission": 10,
        "stake": 1234.5,
        "rank": validator_id,
        "website": "https://example.invalid",
    }


class ValidatorRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.rows = [validator(9, "Nine"), validator(3, "Three")]
        self.payload = {"updated": "2026-09-17T12:00:00Z", "validators": self.rows}

    def test_parse_is_complete_and_sorted_by_stable_validator_id(self) -> None:
        rows, updated = MODULE.parse_validator_registry(
            json.dumps(self.payload), "https://example.invalid/validators.json", 2
        )
        self.assertEqual([row["id"] for row in rows], [3, 9])
        self.assertEqual(updated, self.payload["updated"])

    def test_duplicate_id_fails_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["validators"][1]["id"] = 9
        with self.assertRaisesRegex(ValueError, "duplicate validator id 9"):
            MODULE.parse_validator_registry(json.dumps(payload), "source", 2)

    def test_invalid_coordinates_fail_closed(self) -> None:
        payload = copy.deepcopy(self.payload)
        payload["validators"][0]["lat"] = None
        with self.assertRaisesRegex(ValueError, "invalid coordinates"):
            MODULE.parse_validator_registry(json.dumps(payload), "source", 2)

    def test_boolean_coordinates_fail_closed(self) -> None:
        for field in ("lat", "lon"):
            with self.subTest(field=field):
                payload = copy.deepcopy(self.payload)
                payload["validators"][0][field] = True
                with self.assertRaisesRegex(ValueError, "invalid coordinates"):
                    MODULE.parse_validator_registry(json.dumps(payload), "source", 2)

    def test_missing_identity_and_location_fields_fail_closed(self) -> None:
        cases = {
            "name": "has no name",
            "geo_country": "has no country code",
            "asn_org": "has no ASN provider",
            "asn": "has invalid ASN",
        }
        for field, message in cases.items():
            with self.subTest(field=field):
                payload = copy.deepcopy(self.payload)
                payload["validators"][0][field] = None
                with self.assertRaisesRegex(ValueError, message):
                    MODULE.parse_validator_registry(json.dumps(payload), "source", 2)

    def test_truncated_registry_fails_closed(self) -> None:
        with self.assertRaisesRegex(ValueError, "minimum expected is 3"):
            MODULE.parse_validator_registry(json.dumps(self.payload), "source", 3)

    def test_production_floor_rejects_a_195_row_partial_feed(self) -> None:
        payload = {
            "updated": self.payload["updated"],
            "validators": [
                validator(validator_id, f"Validator {validator_id}")
                for validator_id in range(1, 196)
            ],
        }
        minimum = MODULE.NETWORKS["monad"]["validator_registry_min_count"]
        self.assertEqual(minimum, 196)
        with self.assertRaisesRegex(ValueError, "has 195 rows; minimum expected is 196"):
            MODULE.parse_validator_registry(json.dumps(payload), "source", minimum)

    def test_points_include_every_row_without_validator_endpoints(self) -> None:
        cfg = {
            "network_id": "monad-mainnet",
            "validator_registry_url": "https://example.invalid/validators.json",
            "validator_registry_min_count": 2,
        }
        with patch.object(MODULE, "fetch_text", return_value=json.dumps(self.payload)):
            points = MODULE.build_validator_registry_points(cfg, "2026-09-17T12:01:00Z")

        self.assertEqual(len(points), 2)
        self.assertEqual(
            [point["id"] for point in points],
            ["monad-mainnet-validator-3", "monad-mainnet-validator-9"],
        )
        self.assertTrue(all(point["type"] == "validator" for point in points))
        self.assertTrue(all("endpoint" not in point and "ip" not in point for point in points))
        self.assertEqual(points[0]["metadata"]["validator_id"], 3)

    def test_registry_continuity_rejects_any_omitted_existing_id(self) -> None:
        source_url = "https://example.invalid/validators.json"
        cfg = {"validator_registry_url": source_url}
        previous = {
            "points": [
                {
                    "type": "validator",
                    "source": source_url,
                    "metadata": {"validator_id": validator_id},
                }
                for validator_id in (3, 9)
            ]
        }
        current = {
            "points": [
                {
                    "type": "validator",
                    "source": source_url,
                    "metadata": {"validator_id": 3},
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "decentralize-map.json"
            path.write_text(json.dumps(previous))
            before = path.read_bytes()
            with self.assertRaisesRegex(ValueError, "omitted ids: 9"):
                MODULE.validate_validator_registry_continuity(path, current, cfg)
            self.assertEqual(path.read_bytes(), before)

    def test_first_registry_migration_allows_legacy_endpoint_only_map(self) -> None:
        source_url = "https://example.invalid/validators.json"
        cfg = {"validator_registry_url": source_url}
        previous = {
            "points": [
                {
                    "type": "validator",
                    "source": "operator-approved endpoint",
                    "metadata": {"collection": "public validator endpoint"},
                }
            ]
        }
        current = {
            "points": [
                {
                    "type": "validator",
                    "source": source_url,
                    "metadata": {"validator_id": 3},
                }
            ]
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "decentralize-map.json"
            path.write_text(json.dumps(previous))
            MODULE.validate_validator_registry_continuity(path, current, cfg)

    def test_network_privacy_description_matches_each_validator_source(self) -> None:
        mainnet = MODULE.NETWORKS["monad"]
        testnet = MODULE.NETWORKS["monad-testnet"]
        self.assertIn(
            "validator IPs and P2P endpoints are not published",
            MODULE.validator_privacy_description(mainnet),
        )
        self.assertEqual(
            MODULE.validator_privacy_description(testnet),
            "operator-approved public validator P2P endpoints are published",
        )


if __name__ == "__main__":
    unittest.main()
