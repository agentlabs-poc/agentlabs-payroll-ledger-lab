# Handbook review and remaining work

Review date: 2026-09-06. This records an editorial and conceptual consistency
review of the current working edition. It is not a production conformance test,
statutory certification, or a new set of approved payroll rules.

## Incorporated coverage

| Area | Current coverage | Evidence or rationale |
|---|---|---|
| Five employee payroll stores | Definitions, relationships, and agreed core flow incorporated | [Core concepts](core-concepts.md#agreed-core-model) |
| Intake and calculation | Manager/API handoff; business calculation and source intent outside the core ledger responsibility | [Handbook flow](handbook.md#from-manager-inputs-to-generated-payroll) |
| Source changes and draft finality | Immutable source history, fixed draft, protected reconciliation, cancel/rebuild/fresh review | [Reconciliation model](source-reconciliation.md) |
| Instruction lifetime/application | Expiry, once-per-period monthly applications, one-time consumption on commit, and late processing | [Instruction rules](handbook.md#instruction-lifetime-and-application) |
| Ownership and authority | Employee-month association without a canonical ID generator, employee-period draft/commit unit, batch outcomes, and distinct scoped capabilities | [Ownership](ledger-ownership.md), [authority](authority-and-review.md) |
| Changes and exceptions | Salary change, expiry, abandoned/stale drafts, batch exception, and subsequent-month adjustment examples | [Scenarios](payroll-scenarios.md) |
| Joining, partial periods, and exit | Supplied calculation amounts use the governed flow; after-exit corrections excluded to accounting | [Extended journeys](employee-and-annual-journeys.md) |
| Employer contribution and liability | CTC contribution earning/deduction pair precedes employer register; remittance/proof closes the corresponding liability | [Contribution flow](payroll-outputs.md#pay-core-014--employer-contributions-through-payroll) |
| Annual information and reporting | Data flow, preparation/review sequence, allocation examples, and distinction from issuance | [Reporting and reconciliation](reporting-and-reconciliation.md) |
| Full illustrative monthly cycle | Seven payroll components, commit/application, employer liabilities, proof-backed closure, later correction, and annual use | [Continuous walkthrough](payroll-scenarios.md#end-to-end-payroll-and-liability-walkthrough) |
| Decision rationale/history | Current agreements and source facts distinguished from rejected or parked proposals | [Decision log](decision-log.md) |
| Code comparison | Current agreement groups mapped to inspected support and gaps; source revisions and limits retained | [Evidence coverage](implementation-gaps.md#agreement-to-evidence-coverage) |

The major conceptual coverage is incorporated. This does not imply every
formula, API, operational policy, or issuance integration is specified.

## Consistency points reviewed

- All payroll for an employee/month is tied together. No canonical ID-generation
  method is selected; grouping does not transfer exact-draft approval or permit
  duplicate applications.
- Employer contributions increase gross and deductions equally, leaving net
  unchanged by the pair. They enter committed payroll before the employer
  register and represent one corresponding obligation.
- The employer-liability register is inside payroll. General accounting and
  corrections arising after employee exit are outside payroll.
- Generated payroll is final. Corresponding government remittance and proof
  close the employer obligation; these are distinct finality events.
- Relevant source changes require rebuilding the fixed draft before commit.
  Historical source tracing and business overlap inference are not mandatory
  payroll-core responsibilities.
- Monthly application, one-time consumption, and expiry remain distinct. The
  examples do not silently restore instructions or extend repayment schedules.
- Old freeze and direct-contribution alternatives remain history, rather than
  active requirements. The separate-sealing proposal remains explicitly parked.
- Annual readiness is not issuance; a global TDS total plus one payslip does
  not establish a complete employee/year result. Code limitations are recorded.

## What remains, and where it belongs

| Remaining item | Why it remains | Next treatment |
|---|---|---|
| PAY-Q-009: separate sealing | The lab exposes a seal step, while the agreed draft is fixed from complete creation | Revisit when specifying the draft API/UI; keep the current semantic rule without inventing a selected operation |
| Expiry and validation representation | Dates/period encoding, immutable-source lifecycle metadata, and validation evidence are not selected | Implementation specification; no reopening of applicability or source-tracing decisions |
| Exceptional installment/application behavior | Automatic extension, splitting, and restoration have not been adopted | Apply the supplied policy where it fits existing rules; ask if a core behavior change is proposed |
| Concurrency, retries, and recovery | Durable storage and coordination are not implemented in the demo | Implement against the already stated invariants when authorized |
| Detailed role assignments and integrations | Capabilities and system boundaries are settled, concrete mappings are not | Deployment/operating specification rather than invented job-title rules |
| Complete annual issuance | The information flow is explained; applicable form/period mapping and integrated issuance are not delivered | Scope-specific statutory/integration work, using authoritative material for the applicable period |
| Detailed business calculations | Proration, contribution amounts, and annual tax formulas belong to higher-order policy | Do not turn them into new core ledger primitives or infer policy from demo arithmetic |

These items should not all be presented as unanswered foundational questions.
Some are implementation choices, some belong to the producing/consuming layer,
and the named proposal remains parked. If a future scenario exposes a material
choice within payroll scope, identify that choice and ask before adopting it.

## Review checks

This pass checks local Markdown links and heading anchors, fence balance,
consistency of recorded decision status, example arithmetic, preservation of the
pinned charter, and separation of runtime code from documentation changes.
The walkthrough covers gross/deductions/net and liability amounts explicitly.
Source-inspected implementation gaps remain open; no runtime execution or
completed software behavior is claimed by this review.

The handbook is a reviewable conceptual working edition. Full deployment and
period-specific compliance procedures remain outside what this review proves.
