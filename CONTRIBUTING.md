# Contributing

DwellProof is an accuracy-sensitive controlled prototype. Discuss substantial
changes with the maintainer before investing significant work.

## Non-negotiable boundaries

- Preserve fail-closed behavior: missing, stale, conflicting, or wrong-scope
  evidence must not produce directional investment advice.
- Give every decision-relevant fact an authoritative source, observation scope,
  retrieval date, semantic role, and freshness state.
- Do not infer property value from city-level indices or use LPR as a mortgage
  execution quote.
- Never commit real addresses, identity documents, title records, loan files,
  account data, API credentials, or other personal financial information.
- Keep retired material visibly isolated under `legacy/`; do not present it as
  verified DwellProof output.

## Verification

Run the repository checks before proposing a change:

```sh
python3 -m unittest discover -s tests -v
python3 legacy/legacy_test.py
python3 -m compileall -q core tests scripts legacy
python3 scripts/verify_official_page_hashes.py
python3 scripts/verify_official_70city.py
cd web && npm audit && npm run typecheck && npm run build
```

Explain any changed formula or policy rule and add regression coverage for its
boundaries. Do not refresh an official snapshot without retaining its source
URL, timestamps, response hash, and review notes.

## License

Only submit material you authored or have the right to submit. By contributing,
you agree that your contribution is licensed under the repository's MIT
License. Third-party data, quotations, and archival material remain subject to
the boundaries in `RIGHTS.md`.
