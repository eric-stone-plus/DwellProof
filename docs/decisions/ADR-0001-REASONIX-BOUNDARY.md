# ADR-0001: Reasonix remains an optional non-authoritative layer

- Status: accepted for architecture; read-only shadow mode implemented 2026-07-19
- Date: 2026-07-13

## Decision

DwellProof should leave a narrow integration seam for Reasonix, but the current
prototype and desktop distribution do not bundle or execute it. The first safe
integration, if pursued, is an isolated shadow path behind the DwellProof
orchestrator:

```text
UI
  -> DwellProof orchestrator
  -> isolated Reasonix ACP
  -> read-only dwellproof MCP
  -> evidence store + deterministic Python core
```

Reasonix may:

- explain evidence gaps and refusal reasons;
- rank already-defined verification tasks;
- answer case questions with claim-level citations; and
- draft prose for a memo from verified facts and signed calculation snapshots.

Reasonix may not:

- mark evidence as verified or resolve a conflict;
- determine title authenticity, disposal authority, or transaction legality;
- supply missing tax rules, bank rates, rents, costs, or comparable sales;
- calculate deed tax, loan schedules, cash flow, NPV, or IRR;
- change readiness, override a hard stop, or issue a buy/sell recommendation; or
- write to the evidence store through a generic tool or shell interface.

The evidence contracts and versioned Python core remain the only authorities for
facts, readiness, rules, and numbers. Every Reasonix statement that depends on a
case fact must cite a stable evidence or calculation-snapshot identifier. Missing
or conflicting support produces a refusal, not a plausible completion.

## Why not bundle it now

The available COFORGE Reasonix work is a fixture-tested runtime spike rather than
a production path. DwellProof first needs a local evidence API, signed calculation
snapshots, a read-only MCP surface, tool-level authorization, persistent audit
records, prompt-injection defenses, case-isolated sessions, and tests proving
that final prose cannot escape its citations.

Housing records can include identity, title, family, borrowing, and financial
details. No case content may be sent to a hosted model without an explicit data
handling decision and user consent. Credentials and transcripts must not be
inherited or persisted by default.

## Consequences

- The current Tauri package contains no Reasonix runtime or credentials.
- UI copy may describe the future responsibility boundary but must not imply an
  active assistant.
- A later integration starts in read-only shadow mode and must pass adversarial,
  cross-case leakage, citation, and deterministic-replay tests before exposure.
- Any proposed write-capable or recommendation-capable integration requires a
  new ADR and a security review.

## Shadow-mode implementation facts (2026-07-19)

The first integration now ships in the desktop package, confined to the
read-only shadow path described above:

- The pinned upstream binary (`esengine/DeepSeek-Reasonix` v1.17.11, commit
  `20a64b4d…`, MIT) is fetched by `scripts/fetch_reasonix_runtime.py`, verified
  against fixed SHA-256 values at fetch time, before every launch
  (`src-tauri/src/reasonix/manifest.rs`), and again inside the signed bundle by
  `desktop/build_macos.sh`. The app never downloads a binary at startup and
  never trusts a PATH-installed Reasonix.
- The ACP v1 host is a Rust client (`src-tauri/src/reasonix/acp.rs`) inside the
  Tauri process — no Node runtime is bundled. The child runs with an isolated
  `REASONIX_HOME` (0700), an emptied workspace, a deny-all config with a
  sentinel tool allowlist, and a filtered environment.
- No MCP servers are registered. The model receives only the demo-case
  snapshot serialized from repository constants plus the user's question. Any
  tool-call update from the runtime is a policy violation that cancels the
  turn; permission requests are always cancelled.
- Responses that cite no known identifier (G01–G07, deed-tax, nbs-index, lpr)
  are not displayed; the UI shows a refusal card instead. Token usage is not
  reported by ACP v1, so the UI honestly marks it unavailable.
- `DEEPSEEK_API_KEY` is read from the host process environment only, bridged
  into `REASONIX_HOME/.env` (0600, exclusive create) for the lifetime of
  session creation, and deleted immediately after. The desktop package stores
  no credential.
- First use requires explicit in-app consent noting that the question and the
  demo snapshot leave the device for api.deepseek.com. Local draft cases and
  uploaded file names are never included. `DWELLPROOF_REASONIX_ENABLED=0`
  disables the integration entirely.
- Audit records (`reasonix-audit.jsonl` in the app data directory) store only
  timestamps, identifiers, outcome codes, and SHA-256 hashes — never content.
- Deterministic replay tests with fixture binaries cover the ACP handshake,
  streamed turns, prompt validation, and the tool-call policy violation path;
  `cargo test --locked` passes without network or model access.

Still deferred and requiring new ADRs: any MCP tool surface, real case
material in prompts, keychain-managed credentials, budget accounting,
recommendation-capable or write-capable behavior, and non-macOS packaging.
