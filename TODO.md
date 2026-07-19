# DwellProof TODO

Ordered by dependency, not by wish. The fail-closed contract in `README.md`
and the boundary in `docs/decisions/ADR-0001-REASONIX-BOUNDARY.md` govern
every item below; nothing here may weaken them.

## Now (unblocked, high value)

- [ ] Live smoke of the Reasonix shadow layer: set `DEEPSEEK_API_KEY` in the
  process environment, launch the desktop app, run the three suggested
  questions, and record whether citation validation passes on real model
  output. File the first citation-rejection example if one appears.
- [ ] Signed calculation snapshot bridge between `core/` (Python) and `web/`:
  versioned JSON with a content hash, produced by the Python core, consumed
  read-only by the workbench. This is the prerequisite for everything below.
- [ ] Commit a reviewed snapshot of the current demo case as the regression
  fixture for that bridge.

## Evidence data (release blockers from README)

- [ ] Comparable-transaction workflow (G07): start with manual archival of
  official 网签/住建 sources (e.g. 广州阳光家缘, 北京住建委存量房网签) under
  the existing snapshot/provenance rules; evaluate the enterprise Beike open
  platform `assessTransactionCase` API only if an organization account is
  realistically obtainable. Note: Beike hides transaction prices in several
  cities since 2025-08, so broker quotes remain a required channel.
- [ ] Title/encumbrance check workflow (G01/G02): document the official
  channel per target city ("互联网+不动产登记" portal, lawyer online-query
  pilots, self-service terminals). No public API exists; keep it
  human-verified by design.
- [ ] Local tax rules (G05): extend the versioned rule snapshots from the
  national deed-tax rule to city-level bases and exemptions.
- [ ] Bank rate quotes (G06): define the written-quote intake format; LPR
  stays benchmark-only (third-party LPR APIs exist but cannot substitute).

## Reasonix follow-ups (each needs its own ADR before implementation)

- [ ] First-party read-only MCP over the evidence store (only after the
  signed snapshot bridge exists); host allowlist `mcp__dwellproof__*`.
- [ ] Keychain-managed `DEEPSEEK_API_KEY` (macOS), replacing the env-only
  bridge; remove the `.env` bridge once upstream supports in-memory
  credential injection.
- [ ] Real case material in prompts: field-level minimization, explicit
  consent, and adversarial prompt-injection tests before any real property
  or borrower data leaves the device.
- [ ] Budget/usage accounting once ACP reports token usage; until then keep
  the honest `usageUnavailable` marking.
- [ ] Adversarial, cross-case leakage, and deterministic-replay test suites
  required by ADR-0001 before any exposure beyond shadow mode.

## Packaging and engineering

- [ ] arm64 desktop build on an arm64 host (pinned `darwin-arm64` asset,
  same SHA-256 flow); Windows/Linux packaging after that.
- [ ] Developer ID signing + notarization for any distribution beyond local
  testing; the current ad-hoc bundle is not a release.
- [ ] CI: run `cargo test --locked`, `npm run typecheck && npm run build`,
  `python3 -m unittest discover -s tests`, and
  `scripts/fetch_reasonix_runtime.py --check`-style verification on push.
- [ ] Reasonix upgrade policy: keep one known-good pinned version for
  rollback; bump only after ACP contract tests pass.
