# Payroll Ledger Lab

Throwaway, in-memory browser experiment for discovering the smallest useful
Layer-1 payroll ledger primitives.

This repository is **not** a canonical HRMS design, production dependency,
API commitment, release candidate, or source of changes to HRMS Design PR #44.

```bash
npm install
npm run dev
```

Open the displayed URL, then play levels 1 through 7. Refreshing the page
deletes all state. The green controls call ledger primitives; the amber
external calculator deliberately represents higher-order code outside Layer 1.

The terminal is a simulator, not a production CLI. Each normal command maps
to one in-memory primitive. `demo-calculate` is intentionally higher order and
exists only to prove that an external player can compose the primitives.
