#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOST_ARCH="$(uname -m)"
TARGET_BUNDLE="$ROOT/src-tauri/target/release/bundle/macos/DwellProof.app"
DIST="$ROOT/desktop/dist"
APP="$DIST/DwellProof.app"
STAGE=""

cleanup() {
  if [[ -n "$STAGE" && -d "$STAGE" ]]; then
    rm -rf "$STAGE"
  fi
}
trap cleanup EXIT

case "$HOST_ARCH" in
  x86_64|arm64) ;;
  *)
    echo "Unsupported macOS architecture: $HOST_ARCH" >&2
    exit 1
    ;;
esac

command -v npm >/dev/null 2>&1 || { echo "npm is required" >&2; exit 1; }
command -v cargo >/dev/null 2>&1 || { echo "cargo is required" >&2; exit 1; }
command -v cargo-tauri >/dev/null 2>&1 || { echo "cargo-tauri v2 is required" >&2; exit 1; }

cd "$ROOT"

npm --prefix web run typecheck
npm --prefix web audit
python3 scripts/fetch_reasonix_runtime.py

REASONIX_RUNTIME_DIR="$ROOT/desktop/.runtime/reasonix-v1.17.11-$( [[ "$HOST_ARCH" == "arm64" ]] && echo darwin-arm64 || echo darwin-x64 )"
REASONIX_BIN="$REASONIX_RUNTIME_DIR/reasonix"
REASONIX_LICENSE="$REASONIX_RUNTIME_DIR/LICENSE.reasonix"
for f in "$REASONIX_BIN" "$REASONIX_LICENSE"; do
  if [[ ! -f "$f" || -L "$f" || ! -s "$f" ]]; then
    echo "Missing or invalid Reasonix runtime resource: $f" >&2
    exit 1
  fi
done

cargo tauri build --bundles app -- --locked

test -d "$TARGET_BUNDLE" || { echo "Expected app bundle not found: $TARGET_BUNDLE" >&2; exit 1; }

rm -rf "$DIST"
mkdir -p "$DIST"
ditto "$TARGET_BUNDLE" "$APP"

# Bundle the pinned Reasonix runtime; re-verify its SHA-256 inside the bundle
# before signing so a corrupted copy can never ship.
ditto "$REASONIX_BIN" "$APP/Contents/Resources/reasonix"
ditto "$REASONIX_LICENSE" "$APP/Contents/Resources/LICENSE.reasonix"
REASONIX_EXPECTED_SHA="$(shasum -a 256 "$REASONIX_BIN" | awk '{print $1}')"
REASONIX_BUNDLED_SHA="$(shasum -a 256 "$APP/Contents/Resources/reasonix" | awk '{print $1}')"
if [[ "$REASONIX_EXPECTED_SHA" != "$REASONIX_BUNDLED_SHA" ]]; then
  echo "Bundled Reasonix SHA-256 mismatch" >&2
  exit 1
fi
echo "Bundled Reasonix v1.17.11 (sha256: $REASONIX_BUNDLED_SHA)"

codesign --force --deep --sign - "$APP"
codesign --verify --deep --strict --verbose=2 "$APP"

VERSION="$(plutil -extract CFBundleShortVersionString raw "$APP/Contents/Info.plist")"
case "$HOST_ARCH" in
  x86_64) ARCH_LABEL="x64" ;;
  arm64) ARCH_LABEL="aarch64" ;;
esac
DMG="$DIST/DwellProof_${VERSION}_${ARCH_LABEL}.dmg"

STAGE="$(mktemp -d "${TMPDIR:-/tmp}/dwellproof-dmg.XXXXXX")"
ditto "$APP" "$STAGE/DwellProof.app"
ln -s /Applications "$STAGE/Applications"
hdiutil create -volname DwellProof -srcfolder "$STAGE" -ov -format UDZO "$DMG"

(
  cd "$DIST"
  shasum -a 256 "$(basename "$DMG")"
  shasum -a 256 "DwellProof.app/Contents/MacOS/dwellproof-desktop"
) > "$DIST/SHA256SUMS"

GIT_SHA="$(git -C "$ROOT" rev-parse HEAD)"
if [[ -n "$(git -C "$ROOT" status --porcelain --untracked-files=normal)" ]]; then
  GIT_STATE="dirty"
else
  GIT_STATE="clean"
fi
PACKAGE_LOCK_SHA="$(shasum -a 256 "$ROOT/web/package-lock.json" | awk '{print $1}')"
CARGO_LOCK_SHA="$(shasum -a 256 "$ROOT/src-tauri/Cargo.lock" | awk '{print $1}')"

cat > "$DIST/BUILD-INFO.txt" <<EOF
DwellProof $VERSION
Architecture: $HOST_ARCH
Git commit: $GIT_SHA
Git state: $GIT_STATE
Package lock SHA-256: $PACKAGE_LOCK_SHA
Cargo lock SHA-256: $CARGO_LOCK_SHA
Node: $(node --version)
NPM: $(npm --version)
Rust: $(rustc --version)
Cargo: $(cargo --version)
Tauri CLI: $(cargo tauri --version)
Frontend: static Next.js export
Desktop shell: Tauri 2 / system WebView
WebView IPC permissions: none
Signing: local ad-hoc only
Notarization: not configured
Reasonix: bundled v1.17.11 (pinned, sha256-verified); read-only shadow mode; requires DEEPSEEK_API_KEY at runtime
Python core: not connected in this presentation shell
EOF

echo "Built local macOS test application: $APP"
echo "Built local macOS test disk image: $DMG"
echo "Architecture: $HOST_ARCH"
echo "Distribution status: local test only; Developer ID notarization is not configured."
