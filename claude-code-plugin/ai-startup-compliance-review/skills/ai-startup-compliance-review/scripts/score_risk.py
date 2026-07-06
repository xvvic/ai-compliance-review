#!/usr/bin/env python3
"""Score AI startup compliance risks from structured factors."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass

FACTORS = (
    "legal_trigger",
    "severity",
    "likelihood",
    "controllability",
    "affected_population",
    "source_confidence",
)


@dataclass(frozen=True)
class ScoreResult:
    total: int
    level: str
    action: str


def level_for_total(total: int, red_line: bool = False) -> ScoreResult:
    if red_line or total >= 14:
        return ScoreResult(total, "L4 Stop / Red Line", "do not proceed until redesigned or externally verified")
    if total >= 9:
        return ScoreResult(total, "L3 High", "pause or escalate before launch, closing, or signing")
    if total >= 5:
        return ScoreResult(total, "L2 Medium", "proceed only after specified controls")
    return ScoreResult(total, "L1 Low", "proceed with records and monitoring")


def parse_scores(raw: str | None, args: argparse.Namespace) -> dict[str, int]:
    if raw:
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON: {exc}") from exc
    else:
        data = {name: getattr(args, name) for name in FACTORS}

    missing = [name for name in FACTORS if name not in data]
    if missing:
        raise SystemExit(f"Missing factor(s): {', '.join(missing)}")

    scores: dict[str, int] = {}
    for name in FACTORS:
        value = data[name]
        if not isinstance(value, int) or value < 0 or value > 3:
            raise SystemExit(f"{name} must be an integer from 0 to 3")
        scores[name] = value
    return scores


def run_self_test() -> None:
    cases = [
        (dict.fromkeys(FACTORS, 0), False, "L1 Low"),
        ({"legal_trigger": 2, "severity": 1, "likelihood": 1, "controllability": 1, "affected_population": 0, "source_confidence": 0}, False, "L2 Medium"),
        ({"legal_trigger": 2, "severity": 2, "likelihood": 2, "controllability": 1, "affected_population": 1, "source_confidence": 1}, False, "L3 High"),
        (dict.fromkeys(FACTORS, 3), False, "L4 Stop / Red Line"),
        (dict.fromkeys(FACTORS, 0), True, "L4 Stop / Red Line"),
    ]
    for scores, red_line, expected in cases:
        result = level_for_total(sum(scores.values()), red_line)
        assert result.level == expected, (scores, red_line, result)
    print("self-test passed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", help="JSON object containing all six factor scores")
    parser.add_argument("--red-line", action="store_true", help="force L4 due to a red-line trigger")
    parser.add_argument("--self-test", action="store_true", help="run built-in tests")
    for name in FACTORS:
        parser.add_argument(f"--{name.replace('_', '-')}", type=int, default=0)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0

    scores = parse_scores(args.json, args)
    total = sum(scores.values())
    result = level_for_total(total, args.red_line)
    print(json.dumps({"total": result.total, "level": result.level, "action": result.action, "factors": scores}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
