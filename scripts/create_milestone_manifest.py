#!/usr/bin/env python3
"""Hash every non-ignored repository file except the manifest itself."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MILESTONE = "2026-07-13"
MANIFEST = Path(f"docs/manifests/MILESTONE-{MILESTONE}.sha256")
MANIFEST_DIGEST = Path(f"docs/manifests/MILESTONE-{MILESTONE}.manifest.sha256")
ALL_MANIFESTS = {
    path.relative_to(ROOT)
    for path in (ROOT / "docs/manifests").glob("MILESTONE-*.sha256")
}


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def main() -> int:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    paths = sorted(
        Path(item.decode("utf-8"))
        for item in result.stdout.split(b"\0")
        if item
        and Path(item.decode("utf-8")) not in ALL_MANIFESTS | {MANIFEST, MANIFEST_DIGEST}
    )
    if any("\n" in str(path) for path in paths):
        raise RuntimeError("manifest does not support filenames containing newlines")
    payload = "".join(f"{digest(ROOT / path)}  {path}\n" for path in paths)
    target = ROOT / MANIFEST
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(payload, encoding="utf-8")
    digest_target = ROOT / MANIFEST_DIGEST
    digest_target.write_text(
        f"{digest(target)}  {MANIFEST}\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(paths)} entries to {MANIFEST}")
    print(f"Wrote manifest digest to {MANIFEST_DIGEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
