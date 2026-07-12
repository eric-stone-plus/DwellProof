# ADR-0001: Reasonix remains an optional non-authoritative layer

- Status: accepted for architecture; runtime integration deferred
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
