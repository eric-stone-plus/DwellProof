# Official-source research - 2026-07-12

## Confirmed national tax rule

Source: Ministry of Finance / State Taxation Administration / Ministry of
Housing and Urban-Rural Development Announcement No. 16 of 2024, reproduced by
the Guangdong tax authority:

https://guangdong.chinatax.gov.cn/gdsw/zjfg/2024-11/14/content_0289c52475614b0c9d89145c43310721.shtml

Effective 2024-12-01:

- A family's only home: area up to and including 140 m2 is taxed at 1%; above
  140 m2 is taxed at 1.5%.
- A family's second home: area up to and including 140 m2 is taxed at 1%; above
  140 m2 is taxed at 2%.
- In Beijing, Shanghai, Guangzhou, and Shenzhen, after removal of the ordinary/
  non-ordinary housing distinction, an individual sale after at least two years
  is exempt from VAT under the confirmed rule.

Local individual income tax, surcharges, property-specific restrictions, and
the actual party bearing each cost still require local official confirmation.

## Loan pricing

Official People's Bank of China LPR index:

https://www.pbc.gov.cn/zhengcehuobisi/125207/125213/125440/3876551/index.html

Direct retrieval from the official index subsequently located the 2026-06-22
announcement. It states 1-year LPR at 3.0% and 5-year-plus LPR at 3.5%, valid
until the next LPR publication. The response hash and extracted values are in
`docs/research/snapshots/pbc-lpr-2026-06-22.json`.

LPR remains a pricing benchmark, not the user's actual mortgage rate;
calculations use the user's dated written bank quote.

## Market statistics

National Bureau of Statistics 2025 statistical communique:

https://www.stats.gov.cn/zt_18555/zthd/lhfw/2026lhzt/2026hgjj/202602/t20260228_1962667.html

The communique states that all 70 surveyed cities had month-on-month declines in
second-hand residential sales prices in 2025-12. This is market context only. A
city index is not a property price, comparable sale, or future return.

## 2026-04 row-level verification

Direct access to the official National Bureau of Statistics page subsequently
allowed a standard-library table parse. Beijing, Shanghai, Guangzhou, Shenzhen,
and Wuhan match the local CSV exactly for both second-hand-home month-on-month
and year-on-year indices. The source hash and selected rows are archived at
`docs/research/snapshots/nbs-70city-2026-04-selected.json`; the check can be
replayed with `scripts/verify_official_70city.py`.

The official headers confirm index notation: previous month or previous-year
month equals 100, so index 100.7 means roughly +0.7%, not +100.7%. Verification
of these five rows improves provenance but does not make a city index a
property-level valuation input.

## Replay commands

Use `python3 scripts/verify_official_page_hashes.py` to refetch the archived tax
and PBC pages and require exact byte-level SHA-256 matches. Use
`python3 scripts/verify_official_70city.py` to refetch and parse the NBS table and
compare the five selected city rows with the local CSV. Any page change, table
shape change, missing city, or value mismatch exits nonzero and must be reviewed;
an old snapshot is not silently promoted to current evidence.
