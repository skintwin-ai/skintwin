#!/usr/bin/env python3
"""Skin outcome commands for the workbench and the hub ledger."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


class StageRejection(ValueError):
    pass


def _whole_score(value: object) -> object:
    """A digit string is that integer. A word is left as written."""
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return value


def record_outcome(args: dict) -> dict:
    score = _whole_score(args.get("score"))
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
    recorded = {"command": "record_outcome", "args": artifact}
    return _commit(recorded, ({"ok": True, "artifact": artifact}, 200))


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StageRejection(f"{label} is required")
    return value.strip()


def _commit(request: dict, result: tuple[dict, int]) -> tuple[dict, int]:
    if result[1] != 200 or os.environ.get("SKINTWIN_CHAIN_SKIP_DISPATCH") == "1":
        return result
    if not os.environ.get("SKINTWIN_CHAIN_LEDGER"):
        return result
    locator = _locator()
    if locator is None:
        return {"ok": False, "error": "supply-chain hub is not present"}, 400
    error = locator.commit_command(request)
    if error:
        return {"ok": False, "error": error}, 400
    return result


_LOCATOR = None


def _locator():
    global _LOCATOR
    if _LOCATOR is False:
        return None
    if _LOCATOR is not None:
        return _LOCATOR
    import importlib.util

    script = _locate_script()
    if script is None:
        _LOCATOR = False
        return None
    spec = importlib.util.spec_from_file_location("skintwin_chain_locate", script)
    if spec is None or spec.loader is None:
        _LOCATOR = False
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _LOCATOR = module
    return module


def _recorded_hub(directory: Path, file_name: str) -> Path | None:
    directory = directory.resolve()
    registry_path = directory / "domain" / "org-ecosystem.json"
    script = directory / "domain" / file_name
    if not registry_path.is_file() or not (directory / "domain" / "supply-chain.json").is_file():
        return None
    if not script.is_file():
        return None
    try:
        data = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    hub = data.get("hub") if isinstance(data, dict) else None
    name = hub.get("name") if isinstance(hub, dict) else None
    if name != directory.name:
        return None
    return script


def _locate_script() -> Path | None:
    override = os.environ.get("SKINTWIN_HUB_ROOT")
    if override:
        found = _recorded_hub(Path(override), "locate.py")
        if found is not None:
            return found
    start = Path(__file__).resolve()
    for parent in [start, *start.parents]:
        if not (parent / ".git").exists():
            continue
        try:
            children = list(parent.parent.iterdir())
        except OSError:
            return None
        for child in children:
            found = _recorded_hub(child, "locate.py")
            if found is not None:
                return found
        return None
    return None


def main() -> None:
    body, status = respond(json.load(sys.stdin))
    json.dump(body, sys.stdout)
    if status != 200:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
