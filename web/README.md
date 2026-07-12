# DwellProof evidence workbench

This is the frontend shell for DwellProof. It borrows QueryForge's dense local
analysis-workbench pattern while changing the product contract: a stale or
incomplete case is visibly locked instead of retaining a previous recommendation.

The initial screen uses an explicitly labelled demonstration case. It is not
connected to live market data and does not issue a buy/sell recommendation.

```bash
npm install
npm run dev
npm run typecheck
npm run build
```

`npm run build` produces a static export in `web/out/`. The Tauri desktop shell
embeds that directory directly; it does not start or bundle a Node.js server.

The next integration step is to consume a signed calculation snapshot generated
by the Python core. The frontend must not reimplement tax, loan, or cash-flow
rules independently.
