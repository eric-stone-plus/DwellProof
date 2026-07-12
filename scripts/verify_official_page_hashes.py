#!/usr/bin/env python3
"""Replay byte-level hashes for archived official tax and LPR pages."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen


SNAPSHOTS = Path(__file__).resolve().parents[1] / "docs" / "research" / "snapshots"
FILES = ("tax-cn-2024-12-01.json", "pbc-lpr-2026-06-22.json")


def main() -> int:
    results = []
    for filename in FILES:
        snapshot = json.loads((SNAPSHOTS / filename).read_text(encoding="utf-8"))
        request = Request(
            snapshot["source_url"],
            headers={"User-Agent": "DwellProof official-source verifier/0.1"},
        )
        with urlopen(request, timeout=30) as response:
            if response.status != 200:
                raise RuntimeError(
                    f"{filename}: official page returned HTTP {response.status}"
                )
            actual = hashlib.sha256(response.read()).hexdigest()
        expected = snapshot["source_sha256"]
        results.append(
            {
                "snapshot": filename,
                "source_url": snapshot["source_url"],
                "expected_sha256": expected,
                "actual_sha256": actual,
                "matches": actual == expected,
            }
        )

    payload = {"schema_version": "official-page-hash-replay.v1", "checks": results}
    payload["all_match"] = all(item["matches"] for item in results)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["all_match"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
