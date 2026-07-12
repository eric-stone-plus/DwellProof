# Target architecture

## Product flow

```text
Property case
  -> evidence ingestion and source snapshots
  -> typed facts with units, case/property/borrower scope, and timestamps
  -> title / tax / finance / comparable-transaction gates
  -> versioned deterministic calculations
  -> scenario and sensitivity analysis
  -> evidence-quality assessment
  -> auditable investment memo or refusal checklist
```

## Trust boundaries

- The model may help classify questions and explain computed results.
- The model may not invent missing facts, rates, policies, or comparable sales.
- Deterministic code owns rules, calculations, validation, and recommendation
  readiness.
- Source conflicts and expired critical facts stop the recommendation path.
- Cross-case, cross-property, or cross-borrower evidence mixing is rejected.
- A missing borrower identity is not treated as a valid shared scope.
- One evidence ID cannot name different facts across scenario results.
- User housing records stay local and outside the source repository.

## Workbench mapping

The QueryForge visual grammar maps to DwellProof as follows:

| QueryForge concept | DwellProof concept |
|---|---|
| Natural-language analysis | Case intake and evidence questions |
| KPI row | Evidence completeness and calculation readiness |
| Result card | Versioned investment memo |
| SQL / method disclosure | Sources, rule versions, and formulas |
| Saved metric | Saved property case and monitoring item |
| Settings status | Source, policy, and loan-quote health |

The UI must never keep an old successful number visible after its source query
fails without a prominent stale/error state.

## Desktop shell

The local desktop presentation shell uses Tauri 2 with the operating system
WebView and a static Next.js export. It bundles no Chromium, Node.js server,
Python runtime, or localhost listener. The current WebView receives no Tauri IPC
permissions. The Python core will later be connected only through a narrow,
versioned JSON sidecar protocol; the frontend will not receive generic shell or
filesystem access.

## Optional model layer

Reasonix is intentionally deferred and non-authoritative. Its allowed and
forbidden responsibilities, security prerequisites, and proposed read-only data
flow are recorded in `docs/decisions/ADR-0001-REASONIX-BOUNDARY.md`.
