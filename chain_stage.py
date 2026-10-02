#!/usr/bin/env python3
"""Skin outcome commands for the workbench and the hub ledger."""

from __future__ import annotations

import json
import sys


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
    return {"ok": True, "artifact": artifact}, 200


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageRejection(f"{label} is required")
    return value.strip()


def main() -> None:
    body, status = respond(json.load(sys.stdin))
    json.dump(body, sys.stdout)
    if status != 200:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
