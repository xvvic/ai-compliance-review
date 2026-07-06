#!/usr/bin/env python3
"""Search a local legal corpus and emit source-tagged snippets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def source_tag(path: Path) -> str:
    parts = set(path.parts)
    if "官方文件" in parts:
        return "[本地法规库]"
    if "案例" in parts:
        return "[本地案例]"
    if "论文" in parts or "书籍" in parts:
        return "[本地论文/报告]"
    return "[待核验: 未知来源类别]"


def iter_text_files(root: Path):
    for path in root.rglob("*.txt"):
        if path.is_file():
            yield path


def search(root: Path, queries: list[str], limit: int) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []
    lowered = [query.lower() for query in queries]
    for path in iter_text_files(root):
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for index, line in enumerate(lines, start=1):
            haystack = line.lower()
            if all(query in haystack for query in lowered):
                snippet = line.strip()
                if len(snippet) > 260:
                    snippet = snippet[:257] + "..."
                results.append({"tag": source_tag(path), "path": str(path), "line": index, "snippet": snippet})
                if len(results) >= limit:
                    return results
    return results


def run_self_test() -> None:
    assert source_tag(Path("legal_preference_txt/官方文件/a.txt")) == "[本地法规库]"
    assert source_tag(Path("legal_preference_txt/案例/a.txt")) == "[本地案例]"
    assert source_tag(Path("legal_preference_txt/论文/a.txt")) == "[本地论文/报告]"
    print("self-test passed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", default="legal_preference_txt", help="corpus root")
    parser.add_argument("--query", action="append", default=[], help="required query term; repeat for AND search")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument("--self-test", action="store_true", help="run built-in tests")
    args = parser.parse_args(argv)

    if args.self_test:
        run_self_test()
        return 0
    if not args.query:
        parser.error("at least one --query is required")

    root = Path(args.root)
    if not root.exists():
        print(f"[ERROR] corpus root not found: {root}", file=sys.stderr)
        return 1

    results = search(root, args.query, args.limit)
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    for item in results:
        print(f"{item['tag']} {item['path']}:{item['line']}: {item['snippet']}")
    if not results:
        print("[待核验: 缺少本地来源] no matches")
    return 0


if __name__ == "__main__":
    sys.exit(main())
