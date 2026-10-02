#!/usr/bin/env python3
"""Skin outcome commands for the workbench and the hub ledger."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


class StageRejection(ValueError):
    pass


def record_outcome(args: dict) -> dict:
    score = args.get("score")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise StageRejection("score must be an integer from 0 to 100")
    return {
        "outcome_id": _text(args.get("outcome_id"), "outcome_id"),
        "fulfillment_id": _text(args.get("fulfillment_id"), "fulfillment_id"),
        "concern": _text(args.get("concern"), "concern"),
        "score": score,
    }


def respond(body: dict) -> tuple[dict, int]:
    if body.get("command") != "record_outcome":
        return {"ok": False, "error": f"unknown command {body.get('command')}"}, 400
    try:
        artifact = record_outcome(body.get("args") or {})
    except StageRejection as exc:
        return {"ok": False, "error": str(exc)}, 400
    return _commit(body, ({"ok": True, "artifact": artifact}, 200))


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageRejection(f"{label} is required")
    return value.strip()


def _commit(request: dict, result: tuple[dict, int]) -> tuple[dict, int]:
    if result[1] != 200 or os.environ.get("SKINTWIN_CHAIN_SKIP_DISPATCH") == "1":
        return result
    ledger = os.environ.get("SKINTWIN_CHAIN_LEDGER")
    if not ledger:
        return result
    hub = _hub_root()
    if hub is None:
        return {"ok": False, "error": "supply-chain hub is not present"}, 400
    completed = subprocess.run(
        [sys.executable, "-m", "domain.ledger"],
        input=json.dumps(request),
        text=True,
        capture_output=True,
        cwd=hub,
        check=False,
    )
    if completed.returncode != 0:
        try:
            message = json.loads(completed.stdout or "{}").get("error")
        except json.JSONDecodeError:
            message = None
        return {"ok": False, "error": message or completed.stderr or "ledger rejected the command"}, 400
    return result


def _hub_root() -> Path | None:
    override = os.environ.get("SKINTWIN_HUB_ROOT")
    candidates = [Path(override)] if override else []
    candidates.extend(
        [
            Path("/agent/repos/skintwin-ecosystem-design"),
            Path("/workspace/repos/skintwin-ecosystem-design"),
        ]
    )
    for candidate in candidates:
        if (candidate / "domain" / "ledger.py").is_file():
            return candidate
    return None


def main() -> None:
    body, status = respond(json.load(sys.stdin))
    json.dump(body, sys.stdout)
    if status != 200:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
