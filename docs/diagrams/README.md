# Payroll canonical diagrams

Standalone, editable SVG diagrams for the approved three-ledger model. Both use
vector shapes/text, accessible titles/descriptions and system fonts, with no
external resources or scripts.

- [Canonical storage map](payroll-canonical-storage.svg): three ledger tables,
  the L1/L2 record stores and all 15 required row kinds.
- [Employee payroll journey](payroll-employee-journey.svg): exact sources, fixed
  draft, atomic commit, application/receipt evidence and proof-backed liability
  allocation for the connected E101 example.

Read the [complete canonical row map](../design/canonical-row-map.md) for meanings, references,
query/index requirements and the example amounts. The SVGs describe the target
simulation contracts; they are not production architecture or load-test evidence.

Both were XML-validated and rendered in headless Chrome for visual inspection.
The source SVGs are retained here; temporary PNG review renders are not committed.
