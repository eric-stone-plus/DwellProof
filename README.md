# DwellProof

DwellProof is a local-first evidence workbench for evaluating a specific second-hand
home transaction in China. Its intended output is an auditable investment memo,
not a black-box buy/sell signal.

## Status on 2026-07-12

The repository has been reorganized around a fail-closed accuracy core and a new
QueryForge-inspired workbench. It is a controlled prototype, not yet an
actionable investment-advice system.

- `core/` implements typed evidence contracts, a seven-check readiness gate,
  versioned deed-tax rules, loan schedules, and acquisition/holding/exit cash
  flows. Its 77 tests pass.
- `web/` is a responsive Next.js workbench shell. Dependency audit, TypeScript
  checking, and the production build pass, but it is not yet connected to the
  Python core or live property evidence.
- `legacy/` retains the former prototype as a non-actionable archive. Its paths fail
  closed and its 46 regression tests pass. All 101 top-level Markdown reports
  and four HTML dashboards carry a visible non-actionable archive warning.
- `docs/research/snapshots/` stores reviewed official-source evidence; the NBS
  selected-row check is replayable with `scripts/verify_official_70city.py`.

The current user-facing conclusion is therefore `INSUFFICIENT_EVIDENCE` until a
specific property passes all required evidence checks. See `docs/PROGRESS.md`
for the durable verification record and outstanding limitations. The accepted
controlled-prototype baseline is frozen in `docs/MILESTONE-2026-07-12.md`.

## Accuracy contract

DwellProof must fail closed. It does not issue a directional recommendation when a
critical fact is missing, stale, contradictory, or unsupported by a source.

Every decision-relevant value must retain:

- its value, unit, observation period, and geographic scope;
- its case, property, and borrower scope where applicable;
- its strongly typed semantic role, so same-unit facts cannot be swapped;
- publication and retrieval timestamps;
- source authority and URL;
- verification/freshness status;
- the exact rule and formula version that consumed it.

City-level price indices are market context only. They are not a substitute for
comparable transactions, title checks, local taxes, a written loan quote, or the
property's own cash-flow assumptions.

The model may explain deterministic results, but it may not create missing
rates, taxes, title facts, comparable transactions, or evidence. LPR is a market
benchmark only; mortgage calculations require a dated, verified bank execution
rate.

Readiness results revalidate seven unique, clear evidence references. Loan
schedules recompute every row from the evidenced bank rate and repayment method;
cash-flow analysis rejects evidence mixed across cases, properties, or borrowers.
Missing borrower identity, conflicting reuse of an evidence ID across scenarios,
and nonzero rates below the supported numerical precision fail closed.

## Verified official-source baseline

The 2026-07-12 review archived official page URLs, retrieval metadata, and source
response hashes for:

- the national preferential deed-tax rule effective 2024-12-01;
- the PBC LPR announcement published 2026-06-22 (1-year 3.0% and 5-year-plus
  3.5%), explicitly classified as benchmark-only; and
- the NBS 2026-04 second-hand-home table. Beijing, Shanghai, Guangzhou,
  Shenzhen, and Wuhan match the local CSV for both month-on-month and
  year-on-year indices.

These checks confirm only the archived facts. They do not verify a particular
home's value, legal status, taxes, or financing.

Firecrawl credits reached `0 / 5,000` after the initial research pass. Known
official government pages were then retrieved directly and archived under the
same provenance and fail-closed rules. This fallback does not justify filling
discovery gaps or assuming that an old snapshot is still current.

## Remaining release blockers

DwellProof cannot produce a trustworthy property-level recommendation until it has:

- recent, attributable comparable transactions for the specific property;
- versioned local taxes, fees, exemptions, and transaction restrictions;
- an authoritative title, disposal-authority, and encumbrance-check workflow;
- a dated written bank mortgage execution-rate quote; and
- a tested API or signed-snapshot integration between `web/` and `core/`.

## Development

The legacy Python scripts and the new core use Python 3.10+. The new workbench is
a separate Next.js application under `web/`; see its README for commands.

From the repository root:

```sh
python3 -m unittest discover -s tests -v
python3 legacy/legacy_test.py
python3 -m compileall -q core tests scripts legacy
python3 scripts/verify_official_page_hashes.py
python3 scripts/verify_official_70city.py
```

For the frontend:

```sh
cd web
npm audit
npm run typecheck
npm run build
```

## Repository and attribution

- Public repository: `https://github.com/eric-stone-plus/DwellProof`
- Maintainer: `@eric-stone-plus`
- AI development collaborator: Codex (OpenAI)

See `CONTRIBUTORS.md` for the contribution record and `CONTRIBUTING.md` for
the evidence, privacy, and verification requirements applied to changes.

## Rights and public-use boundary

This repository is public for inspection and reproducibility, but it does not
currently grant an open-source license. Public visibility is not permission to
copy, redistribute, or reuse its contents. The retired `legacy/` tree and
research material may also contain third-party data or quotations whose rights
remain with their respective owners. See `RIGHTS.md` for the repository-wide
boundary and `SECURITY.md` before reporting a problem involving real property
or personal financial data.
