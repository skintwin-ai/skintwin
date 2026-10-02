#!/usr/bin/env python3
"""Skin outcome recording for the Alchemist workbench."""

from __future__ import annotations

import json
import sys


def record_outcome(args: dict) -> dict:
    score = args.get("score")
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("score must be an integer from 0 to 100")
    return {
        "outcome_id": _text(args.get("outcome_id"), "outcome_id"),
        "fulfillment_id": _text(args.get("fulfillment_id"), "fulfillment_id"),
        "concern": _text(args.get("concern"), "concern"),
        "score": score,
    }


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required")
    return value.strip()


def main() -> None:
    request = json.load(sys.stdin)
    if request.get("command") != "record_outcome":
        _fail(f"unknown command {request.get('command')}")
    try:
        artifact = record_outcome(request.get("args") or {})
    except ValueError as exc:
        _fail(str(exc))
    json.dump({"ok": True, "artifact": artifact}, sys.stdout)


def _fail(message: str) -> None:
    json.dump({"ok": False, "error": message}, sys.stdout)
    raise SystemExit(1)


if __name__ == "__main__":
    main()
