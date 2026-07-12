# Auditable accuracy core

This package is the fail-closed calculation layer for a personal second-hand
housing investment tool. It uses only the Python standard library and keeps
source provenance attached to every numeric input and result.

## Modules

- `contracts.py`: immutable evidence contracts. A numeric value requires its
  unit, observation period, publication/retrieval timestamps, source URL,
  geography, case/property/borrower scope, semantic role, and verification
  status. Calculation functions reject non-verified status, unit mismatches, and
  wrong-role evidence even when the broad kind and unit happen to match.
- `readiness.py`: a minimum due-diligence gate. Title, mortgage/seizure or other
  encumbrances, property nature, tenancy, tax, loan, and comparable transactions
  must all be present, verified, and clear before downstream recommendation
  analysis may begin. A separate deterministic policy must still justify any
  directional label.
- `tax.py`: versioned implementation of the national preferential deed-tax rule
  effective 2024-12-01. Only a family's sole or second home is implemented. The
  140 m2 boundary is inclusive; unsupported dates and other/unknown home counts
  are refused.
- `loan.py`: fixed-rate equal principal-and-interest and equal-principal monthly
  schedules. There is deliberately no built-in LPR; a verified annual contract
  rate or bank quote is mandatory. Reconstructed schedules are checked row by
  row against that rate and the declared repayment method. The equal-payment
  formula uses an isolated high-precision context; nonzero annual rates below
  `1e-12` are explicitly outside the supported numeric contract.
- `cashflow.py`: complete monthly holding-period cash flow for three explicit
  scenarios, including acquisition outflow, effective rent, operating cost,
  debt service, sale costs, loan payoff, net rental yield, NPV, IRR when a root
  can be safely bracketed, and maximum cash shortfall. Financing must reconcile:
  initial equity plus loan principal must equal the purchase price.
  Net rental yield uses purchase price plus acquisition costs as its denominator
  and annualizes actual NOI from the first `min(holding_months, 12)` months.
  Every readiness, transaction, scenario, and loan reference must share one case,
  property, and non-empty borrower scope. Across the standard three scenarios,
  one evidence ID may recur only when its complete reference is identical.

## Policy source and version

`CN-DEED-TAX-2024-12-01-v1` implements Ministry of Finance, State Taxation
Administration, and Ministry of Housing and Urban-Rural Development Announcement
No. 16 of 2024. The source URL embedded in each result is the official Guangdong
Provincial Tax Service publication:

<https://guangdong.chinatax.gov.cn/gdsw/zjfg/2024-11/14/content_0289c52475614b0c9d89145c43310721.shtml>

Any future policy must be added as a new rule version; do not alter historical
semantics in place.

## Important limitations

This is a deterministic calculator and evidence gate, not legal, tax, lending,
valuation, or investment advice. `verified` means the calling workflow verified
the evidence under its own documented procedure; the package does not fetch or
authenticate sources. Passing readiness does not mean a property is safe or
profitable. It only confirms the minimum evidence set is explicitly clear.

The deed-tax module does not calculate VAT, individual income tax, stamp duty,
local fees, subsidies, exemptions, or tax-base adjustments, and refuses home
counts outside its implemented preferential cases. Cash-flow outputs depend
entirely on assumptions and omit any cost not supplied by the caller. The IRR
solver returns `None` for cash-flow patterns without a bracketed practical root;
NPV remains available. Interest-rate resets, prepayments, penalties, provident
fund rules, floating-rate repricing, and day-count conventions are not modeled.
The prototype also has no business-level maximum holding period; an API boundary
must add a documented resource limit before accepting untrusted public input.

Run all tests from the repository root:

```sh
python3 -m unittest discover -s tests -v
```
