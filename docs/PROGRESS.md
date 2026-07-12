# DwellProof progress log

This file is the durable hand-off for work completed in the repository. Entries
record outcomes and verification, not just intended tasks.

## 2026-07-13 - Public repository preparation

- Approved publication target: `https://github.com/eric-stone-plus/DwellProof`,
  with public visibility and `main` as the default branch.
- Recorded Codex (OpenAI) in `CONTRIBUTORS.md`; release commits use a matching
  `Co-authored-by` trailer so attribution is present in both the files and Git
  history.
- Added contribution, sensitive-data reporting, and rights boundaries. No
  open-source license is implied: public visibility permits inspection but does
  not grant reuse, and archival or third-party-source material retains its own
  rights.
- Removed workstation paths and unnecessary authentication/billing metadata
  from the public hand-off while preserving the material research limitation.
- Scanned the exact candidate publication set with Gitleaks, TruffleHog, and
  common credential/privacy patterns. No credential, private key, password,
  personal case record, build output, or oversized file was found. Generated
  Next.js secrets existed only under ignored `.next/` build output.
- Re-ran 77 core tests, 46 legacy regressions, Python compilation, shell syntax,
  both official-source checks, `npm audit`, TypeScript checking, and the
  production build. All passed; the milestone manifest also verified before
  publication metadata was added and was then regenerated.
- Created the public repository at
  `https://github.com/eric-stone-plus/DwellProof` and pushed `main`. The initial
  controlled-prototype baseline is commit
  `86fbd93ef059890cb3a8ff9130296922763e873f`; the local branch, remote-tracking
  branch, and GitHub `main` reference all resolved to that object after push.
- Verified through GitHub's commit-author graph that the initial commit records
  both `eric-stone-plus` and `Codex` (`@codex`) as authors. The repository also
  retains the human-readable contribution record in `CONTRIBUTORS.md`.

## 2026-07-12 - DwellProof milestone freeze

- Renamed the active product from the placeholder `HOUSE` to `DwellProof` after
  an authenticated GitHub exact-name collision check.
- Moved the former HouseAlice prototype from `housealice/` to `legacy/`, renamed
  active compatibility modules and reports to neutral `legacy_*` names, and
  retained the old name only as clearly marked historical provenance.
- Frozen acceptance, safety invariants, verification results, remaining scope,
  and integrity anchors in `docs/MILESTONE-2026-07-12.md`.
- Re-ran desktop and 390 px mobile browser QA after the rename: DwellProof fits
  the header, all three mobile tabs and both themes work, the old `house-theme`
  preference migrates to `dwellproof-theme`, and the console has no errors or
  warnings.

## 2026-07-12 - Local rebuild baseline

### Completed discovery

- Inventoried the local prototype: research reports, 47 CSV files, 29 Python
  scripts, and four static HTML dashboards. There was no Git repository,
  dependency manifest, or live frontend application.
- Confirmed authenticated GitHub access to the intended owner,
  `eric-stone-plus`, using HTTPS Git operations.
- Confirmed local QueryForge matches `eric-stone-plus/QueryForge` `main` at
  `ce663ac8d7ab432d0923c2f077bae02ae2b34a8e`.
- Compared the former HouseAlice static dashboard with QueryForge in a local browser.
  The reusable part is the workbench shell and interaction grammar, not the
  static KPI snapshot or generic chart inference.
- Completed an independent code/model audit and official-source research. The
  detailed findings are archived in `docs/AUDIT-2026-07-12.md` and
  `docs/research/OFFICIAL-SOURCES-2026-07-12.md`.

### Repository governance and organization

- Initialized a local Git repository on `main`. No commit or remote push was
  created during this rebuild.
- Added root project documentation and ignored browser/research caches, build
  output, Python caches, local environments, secrets, and personal housing
  account state.
- Migrated the former prototype to `legacy/` as traceable research rather than
  deleting or silently rewriting the historical material.
- Defined `core/` as the deterministic accuracy boundary, `web/` as the new
  presentation layer, and `docs/` as the durable audit and source record.

### Safety decision

The legacy green/yellow/red recommendations are not valid investment advice.
They mixed city-level indices, estimated rents, handwritten valuation
coefficients, stale policy rules, and incompatible backtests. Until the new
seven-item readiness gate passes for a specific property, the product displays
`INSUFFICIENT_EVIDENCE` instead of `BUY`, `SELL`, or `BEST_INVESTMENT`.

City indices remain market context only. LPR remains a benchmark only. Neither
may be substituted for property-level comparable transactions or a dated bank
execution-rate quote. A language model may explain verified deterministic
results, but may not supply missing evidence or factual inputs.

### Accuracy core completed

- Added immutable evidence contracts with units, geographic and observation
  scope, case/property/borrower identifiers, publication/retrieval timestamps,
  source URL, validity windows, broad evidence purpose, strongly typed formula
  role, and verification state.
- Added a seven-check gate covering title/disposal authority, mortgage/seizure
  and other encumbrances, property nature, tenancy, tax, loan, and comparable
  transactions. A missing, unclear, adverse, stale, or unverified critical item
  closes the recommendation path.
- Bound every open readiness result to seven unique `clear` references from one
  case, property, and non-empty borrower identity; tampered adverse results,
  missing borrower scope, and cross-scope mixes are rejected before cash-flow
  analysis.
- Bound every tax, loan, transaction, rent, cost, and scenario parameter to a
  distinct `EvidenceRole`; same-unit verified facts such as rent/fixed cost or
  occupancy/sale cost cannot be swapped into the wrong formula slot.
- Reject duplicate evidence identities across formula slots, sub-cent currency
  inputs, unsupported numeric magnitudes, and malformed public API containers
  with explicit `ContractError` results.
- Added `CN-DEED-TAX-2024-12-01-v1`, with the inclusive 140 m2 boundary and
  explicit refusal for dates and household-home counts outside the implemented
  rule.
- Added fixed-rate equal-payment and equal-principal loan schedules without an
  embedded LPR assumption. Every payment row is revalidated against the verified
  bank execution rate, borrower scope, and declared repayment method. The
  equal-payment formula uses a shared high-precision implementation and rejects
  unsupported tiny nonzero rates instead of silently miscalculating them.
- Added monthly acquisition, holding, financing, and exit cash flows with rent,
  operating costs, debt service, sale costs, loan payoff, NPV, bracketed IRR,
  net rental yield, and maximum cash shortfall. Results retain all seven gate
  references plus every numeric and loan reference; the three-scenario batch
  rejects an evidence ID that maps to conflicting facts. Net rental yield uses
  actual NOI over the available first-year period before annualization.

### Legacy safety repairs completed

- Replaced removed absolute runtime paths with project-relative paths and made
  the update orchestrator stop on the first failed step without reporting a
  false success or creating a success backup.
- Added full-coverage validation and atomic replacement to data refresh paths;
  unavailable or incomplete downloads leave the existing data untouched.
- Fixed the lead/lag correlation sentinel, city/date merge duplication, latest
  PMI observation selection, the 140 m2 tax-demo boundary, and idempotent UHA
  observation updates.
- Disabled legacy directional backtests and made decision, MCP, ranking, and
  valuation entry points fail closed. Known heuristic valuations are explicitly
  `illustrative_only` and non-actionable; unknown inputs are refused.
- Disabled 17 directly executable legacy entry points covering forecasts,
  risk scores, macro narratives, timing, city rankings, sell guides, and
  synthetic-account/alert demos. The retained monitor now publishes only a
  validated descriptive city-index cross-section without `Regime` or alert
  labels.
- Quarantined the old synthetic personal-account values, rents, counts, costs,
  and watchlist as `PERSONAL_STATE_UNVERIFIED`; default and direct summary paths
  no longer display those details.
- Added a canonical `LEGACY_ARCHIVE_UNVERIFIED` first-screen warning to all 101
  top-level legacy Markdown files and all four HTML dashboards. A regression
  test enumerates the directory so future or regenerated files cannot omit it.

### Official sources verified

- Archived the national preferential deed-tax rule effective 2024-12-01 from
  the Guangdong Provincial Tax Service publication. The retrieved official page
  SHA-256 is
  `33c8ebe85c7bac9b88a3de253b60cdd93956042e285884cd5dc36e88962b15e1`.
- Archived the PBC announcement published 2026-06-22: 1-year LPR is 3.0% and
  5-year-plus LPR is 3.5%, valid until the next publication. The page SHA-256 is
  `e7d55c20b77a779d72c0ff6cbbdf46d2930ccc961138f24ea54a6f8d0295816e`;
  the product metadata marks both values as benchmark-only.
- Parsed the official NBS 2026-04 second-hand-home table and confirmed the
  official bases `上月=100` and `上年同月=100`. Beijing, Shanghai, Guangzhou,
  Shenzhen, and Wuhan match the local CSV exactly for both month-on-month and
  year-on-year indices. The official response SHA-256 is
  `1b3ea998c4f4f4364e23c016053dc1512050941185f16da986af7931c903c608`.
- Stored reviewed snapshots in `docs/research/snapshots/` and added the
  fail-closed online replay script `scripts/verify_official_70city.py`.

These source checks verify the recorded national rules, benchmark, and selected
city-index rows only. They do not establish property value, title status, local
tax treatment, mortgage eligibility, or investment return.

### New workbench completed

- Added a Next.js 15 / React / TypeScript / Tailwind workbench under `web/`,
  borrowing QueryForge's dense analysis-shell pattern while replacing generic
  KPI output with evidence readiness, source state, method disclosure, and a
  locked calculation workflow.
- Added desktop and mobile layouts, light/dark themes, an explicit controlled-
  prototype banner, and a default `INSUFFICIENT_EVIDENCE` conclusion.
- Kept scenarios locked until property-level evidence and a verified bank quote
  are available. The current screen is demonstration data and is not connected
  to the Python core or live property sources.
- Completed Playwright interaction and visual QA at 1440 px desktop and 390 x
  844 mobile in dark and light themes. All three mobile tabs and formula
  disclosure worked, the scenario caption layout was corrected, and the browser
  console reported zero errors and zero warnings.

### Verification record

The following commands passed locally on 2026-07-12:

| Check | Result |
|---|---|
| `python3 -m unittest discover -s tests -v` | 77/77 passed |
| `python3 legacy/legacy_test.py` | 46/46 passed |
| `python3 -m compileall -q core tests scripts legacy` | passed |
| `python3 scripts/verify_official_70city.py` | `all_match: true` for the five selected cities |
| `python3 scripts/verify_official_page_hashes.py` | both archived SHA-256 values still match |
| `npm audit` in `web/` | 0 vulnerabilities |
| `npm run typecheck` in `web/` | passed |
| `npm run build` in `web/` | production build passed |

The desktop and mobile prototype passed final browser interaction, theme, tab,
layout, and console QA. This does not imply that the frontend is wired to live
evidence.

### Remaining release blockers

- No property-level comparable-sale acquisition and provenance workflow exists.
- Only the confirmed national deed-tax preference is implemented; local income
  tax, VAT details, surcharges, fees, exemptions, and restrictions remain to be
  versioned and verified for the transaction location.
- No authoritative title, disposal-authority, mortgage, seizure, objection,
  residence-right, or transaction-restriction lookup is integrated.
- No dated written bank mortgage execution-rate quote is captured or verified.
- The frontend is not connected to the Python core through a tested API or
  signed calculation snapshot.
- Automated source freshness monitoring and end-to-end property-case tests are
  not yet implemented.
- No business-level maximum holding period is defined; the future public API
  must impose a documented resource bound before accepting untrusted input.

These blockers keep the project at controlled-prototype status. Passing the
current tests proves the implemented contracts and regressions; it does not
make any historical dashboard or demonstration case actionable advice.

### External research limitation

Firecrawl credits reached `0 / 5,000` after the first official-source pass. The
project then used direct retrieval from known official government domains. That
fallback produced the archived tax, LPR, and NBS evidence above, including a
successful five-city 2026-04 row-level replay, repeated at final verification
with the same official response SHA-256. It does not provide broad web
discovery, and no missing policy, locality, or property fact may be inferred
from the exhausted search budget. Any future refresh must preserve source URL,
authority, timestamps, response hash, rule version, and fail-closed behavior.
Final status on 2026-07-12: the external search quota remained `0 / 5,000`; no
exhausted-quota request was represented as a successful search.
