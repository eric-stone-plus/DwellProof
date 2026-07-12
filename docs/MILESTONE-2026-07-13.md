# DwellProof workbench and desktop milestone

## Scope

This milestone records the professional workbench redesign, the local Tauri 2
presentation package, and the Reasonix authority boundary. It extends, but does
not weaken, the fail-closed controlled-prototype baseline from 2026-07-12.

## Accepted outcomes

- COFORGE's complete dark/light design tokens and brand gradient are used by the
  Web workbench, favicon, and generated desktop icons.
- The main user flow is evidence-first rather than chat-first or KPI-first.
- All seven property gates remain unverified in the demo. Missing evidence is
  visible and no property value, return, or directional recommendation is
  produced.
- The static frontend is packaged in Tauri 2 with the system WebView. No Node,
  Chromium, localhost service, Python runtime, or Reasonix runtime is included.
- The current WebView has no Tauri IPC permissions.
- Reasonix is deferred to a future read-only, cited explanation layer and cannot
  own facts, calculations, readiness, or advice.
- DwellProof-authored software and associated documentation use the MIT License.
  QueryForge/COFORGE-derived design material retains its original Apache-2.0
  and MIT copyright and permission notices in `THIRD_PARTY_NOTICES.md`.

## Verification matrix

| Check | Result |
|---|---|
| Core unit tests | 77 / 77 passed |
| Legacy safety regressions | 46 / 46 passed |
| Python compilation | passed |
| Tax and PBC official-page hash replay | both matched |
| NBS selected city replay | five cities matched |
| `npm audit` | 0 vulnerabilities |
| TypeScript and Next.js static export | passed |
| Browser desktop/mobile, themes, workspaces, search, drawers | passed |
| Browser console | 0 errors, 0 warnings |
| `cargo check --locked` and Rust formatting | passed |
| Complete Tauri/macOS build script | passed |
| Ad-hoc code-signature structure and DMG verification | passed |

## Local desktop artifact

- Version: 0.1.0
- Architecture: x86_64
- Static frontend: approximately 1.0 MB
- `.app`: approximately 3.4 MB
- DMG: approximately 2.1 MB
- Signing: ad-hoc local test only
- Public distribution: not approved

Generated files live under ignored `desktop/dist/`. `BUILD-INFO.txt` records the
source commit, dirty state, lock-file hashes, and toolchain versions;
`SHA256SUMS` uses portable relative paths.

The candidate source tree is anchored by
`docs/manifests/MILESTONE-2026-07-13.sha256`; its checksum sidecar is
`docs/manifests/MILESTONE-2026-07-13.manifest.sha256`. This is a drift detector,
not a signed trust root.

## Remaining release blockers

- connect the Python core through a tested, versioned sidecar protocol;
- add an authoritative local evidence store and signed calculation snapshots;
- implement property-level evidence intake and human verification without
  leaking identity or financial records;
- decide and test a domain-allowlisted external-link policy for the desktop app;
- add arm64 or universal builds, Developer ID signing, hardened runtime,
  notarization, and stapling; and
- complete a Rust advisory scan when `cargo-audit` is available.

Until the property gates and integration blockers are satisfied, the durable
decision state remains `INSUFFICIENT_EVIDENCE`.
