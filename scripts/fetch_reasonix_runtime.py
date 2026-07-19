#!/usr/bin/env python3
"""Fetch and verify the pinned Reasonix runtime for the DwellProof desktop shell.

Downloads the pinned upstream release asset for the current platform, verifies
both the archive and the extracted binary against the SHA-256 values fixed in
this script, and installs them under desktop/.runtime/ (gitignored).

The runtime is never downloaded at app startup; this script runs at build or
development setup time only. A hash mismatch is a hard failure.
"""

from __future__ import annotations

import hashlib
import json
import platform
import shutil
import stat
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNTIME_ROOT = ROOT / "desktop" / ".runtime"

# Pinned upstream release. Keep in sync with src-tauri/src/reasonix/manifest.rs;
# the Rust side verifies the same values again before every launch.
MANIFEST = {
    "upstream": "esengine/DeepSeek-Reasonix",
    "version": "1.17.11",
    "tag": "v1.17.11",
    "commit": "20a64b4d15687fbddb7ccc658daf909f71d01427",
    "protocolVersion": 1,
    "licenseSha256": "dc024237821ac82056c37f8d82e3be919bd51e39a4529ec12a8ab3e2a346dc4c",
    "assets": {
        "darwin-x64": {
            "archive": "reasonix-darwin-amd64.tar.gz",
            "archiveSha256": "5424abde113f91291d49b775b48ad92b5db0d0d78cf9a6a4577adb8a776bd107",
            "binary": "reasonix",
            "binarySha256": "f839fcc1b85539eb2bd8c921239c72570a02b8f38eec23d51b1987148c349adc",
        },
        "darwin-arm64": {
            "archive": "reasonix-darwin-arm64.tar.gz",
            "archiveSha256": "2d10cf48643441fa854d878f036c62acb0d78eec6f5483f2469f113e2500d857",
            "binary": "reasonix",
            "binarySha256": "a7adba9ee65175e73a4218b2ffb78a3c09e81c5a47b59d6ceb153ba3bdab1ff6",
        },
        "linux-x64": {
            "archive": "reasonix-linux-amd64.tar.gz",
            "archiveSha256": "109b90fb6421b6015614a19dfcdb2f38e825d90e5c658d8a9f25b0e89c58595d",
            "binary": "reasonix",
            "binarySha256": "65b1de073d7c4c6fb4d2a6b009e42987e2f7d3e300ba9a496f57966285d8b0c3",
        },
    },
}

RELEASE_BASE = (
    "https://github.com/esengine/DeepSeek-Reasonix/releases/download/{tag}/{name}"
)
LICENSE_URL = (
    "https://raw.githubusercontent.com/esengine/DeepSeek-Reasonix/{commit}/LICENSE"
)


def fail(message: str) -> "SystemExit":
    print(f"error: {message}", file=sys.stderr)
    return SystemExit(1)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def platform_key() -> str:
    system = platform.system().lower()
    machine = platform.machine().lower()
    arch = {"x86_64": "x64", "amd64": "x64", "arm64": "arm64", "aarch64": "arm64"}.get(
        machine
    )
    key = f"{system}-{arch}"
    if key not in MANIFEST["assets"]:
        raise fail(f"unsupported platform for pinned Reasonix runtime: {key}")
    return key


def download(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "dwellproof-build"})
    with urllib.request.urlopen(request, timeout=120) as response:
        total = 0
        with destination.open("wb") as handle:
            while True:
                chunk = response.read(1024 * 512)
                if not chunk:
                    break
                handle.write(chunk)
                total += len(chunk)
    if total == 0:
        raise fail(f"downloaded empty file from {url}")


def main() -> int:
    key = platform_key()
    asset = MANIFEST["assets"][key]
    target_dir = RUNTIME_ROOT / f"reasonix-v{MANIFEST['version']}-{key}"
    binary_path = target_dir / asset["binary"]
    license_path = target_dir / "LICENSE.reasonix"

    if binary_path.exists() and sha256_file(binary_path) == asset["binarySha256"]:
        print(f"Reasonix runtime already verified: {binary_path}")
    else:
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, mode=0o755)

        with tempfile.TemporaryDirectory(prefix="dwellproof-reasonix-") as tmp:
            archive_path = Path(tmp) / asset["archive"]
            url = RELEASE_BASE.format(tag=MANIFEST["tag"], name=asset["archive"])
            print(f"downloading {url}")
            download(url, archive_path)

            archive_sha = sha256_file(archive_path)
            if archive_sha != asset["archiveSha256"]:
                raise fail(
                    f"archive SHA-256 mismatch: got {archive_sha}, "
                    f"expected {asset['archiveSha256']}"
                )

            with tarfile.open(archive_path) as tar:
                members = [m for m in tar.getmembers() if m.name == asset["binary"]]
                if len(members) != 1:
                    raise fail(
                        f"archive must contain exactly one {asset['binary']} entry"
                    )
                member = members[0]
                if not member.isfile() or member.issym() or member.islnk():
                    raise fail("binary archive entry is not a regular file")
                extracted = tar.extractfile(member)
                if extracted is None:
                    raise fail("failed to read binary from archive")
                with binary_path.open("wb") as handle:
                    shutil.copyfileobj(extracted, handle)

        binary_path.chmod(
            stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP
        )
        binary_sha = sha256_file(binary_path)
        if binary_sha != asset["binarySha256"]:
            binary_path.unlink(missing_ok=True)
            raise fail(
                f"binary SHA-256 mismatch: got {binary_sha}, "
                f"expected {asset['binarySha256']}"
            )

    if not license_path.exists():
        license_url = LICENSE_URL.format(commit=MANIFEST["commit"])
        print(f"downloading {license_url}")
        download(license_url, license_path)
    license_sha = sha256_file(license_path)
    if license_sha != MANIFEST["licenseSha256"]:
        license_path.unlink(missing_ok=True)
        raise fail(
            f"license SHA-256 mismatch: got {license_sha}, "
            f"expected {MANIFEST['licenseSha256']}"
        )

    marker = target_dir / "manifest.json"
    marker.write_text(json.dumps({"platform": key, **MANIFEST}, indent=2) + "\n")
    print(f"verified Reasonix {MANIFEST['version']} ({key}): {binary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
