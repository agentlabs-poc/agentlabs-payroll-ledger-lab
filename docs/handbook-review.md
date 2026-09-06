# Handbook review and remaining work

Review date: 2026-09-06. This records the consolidated conceptual and editorial
review. It does not certify a deployed system or adopt new payroll rules.

## Current consolidated review

**Layered conceptual handbook reviewed and closed for this documentation pass.
PAY-Q-020 is closed as superseded. Implementation is authorized through the draft Core hub and checkpoint PRs.** This closure
covers the stated Layer-1 contract and organizational policy distinction; it is
not employer-policy selection, production conformance or release approval.

| Review area | Current result | Evidence or remaining boundary |
|---|---|---|
| Core concepts and responsibility boundaries | Reviewed under PAY-ARCH-006 | [Layer-1 contracts](layer-1-contracts.md) separate records/integrity from the [HRMS payroll policy](hrms-payroll-policy.md); existing source, instruction, employee-month, liability and accounting distinctions remain explicit |
| High-impact scenarios and arithmetic | Reviewed | Ordinary payroll, replacement before commit, retries, employee batch exceptions, contribution pairs, subsequent-month correction and partial/full remittance have determinate outcomes; annual package cases isolate employee/employer/year |
| Hub and current Core main | Reconciled | [Baseline reconciliation](baseline-reconciliation.md) distinguishes the merged Layer-1 delivery from later handbook refinements and the unmerged local code candidate |
| Agreement, deferral and code evidence | Reconciled | PAY-GAP findings remain browser-lab findings; PAY-DB findings describe Core. Neither local test success nor historical hub closure language establishes handbook approval |
| Approval withdrawn from an unchanged draft | Closed as superseded | PAY-ARCH-006 places this choice in organizational Layer-2 policy. Neither alternative is mandated by Layer 1; [rationale](payroll-policy-boundary.md) |
| Layer-2 policy variants and hold | Reviewed | Same changed-bonus facts lead to rebuild under policy A or fixed-draft commit under policy B; both preserve exact money and application guards. A held draft remains outstanding while other selected drafts commit |
| Local implementation reconciliation | Reviewed; changes remain pending | [Six-finding disposition](implementation-reconciliation.md): three fixes retained directly; three require reshaping. Protected hold, policy support and public API/CLI evidence remain gaps |
| Implementation readiness | In progress | [Hub PR #172](https://github.com/agentlabs-poc/agentlabs-hrms-core/pull/172) coordinates checkpoint PRs; existing code is not declared compatible until the recorded acceptance gates pass |

The previously recorded unanswered lifecycle proposal is now superseded, not
answered by selecting one workflow. Organizational policies remain variable;
this does not claim every employer policy or future exception has been decided.
The [remaining-item classification](gap-closure-work.md#remaining-item-classification)
separates those extensions from the current ordinary payroll contract. No generic
operating questionnaire is introduced as a prerequisite to core clarity.

## Edition checkpoints

**Historical conceptual edition 1, closed 2026-09-06.** The earlier pass reviewed
CP-01 core concepts, CP-02 responsibility boundaries, CP-03 the representative
walkthrough and CP-04 documentation consistency for that edition. At that point
no named proposal awaited an answer. Later discussion approved partial settlement
(PAY-CORE-016) and annual package/handoff scope (PAY-ARCH-005), then opened
PAY-Q-020. The current review above supersedes the older readiness statement;
the agreed concepts and their rationale remain valid.

## Final walkthrough results

The walkthrough below was reviewed under the reconcile-before-commit policy.
[PAY-ARCH-006](payroll-policy-boundary.md) now classifies that workflow as Layer 2;
it is not a universal Layer-1 freshness or approval requirement.

Basis: the [continuous example](payroll-scenarios.md#end-to-end-payroll-and-liability-walkthrough),
[lifecycle](payroll-lifecycle.md), [source reconciliation](source-reconciliation.md),
[authority](authority-and-review.md), and [extended journeys](employee-and-annual-journeys.md).
This is a review of handbook semantics and arithmetic, not an executed payroll.
Amounts are supplied calculation outputs; no contribution or tax formula is
inferred from the example.

| Step or branch | Responsibility and event | Determinate result from existing decisions |
|---|---|---|
| Intake and preparation | HR/payroll manager consolidates applicable facts through APIs; higher-order calculation supplies seven components | September gross INR 57,500, deductions INR 4,000, net INR 53,500; employer contribution is an earning/deduction pair |
| Creation and approval | Preparation capability creates the complete draft including sealing; approval capability accepts that exact proposal | Monetary content is fixed; neither preparation nor approval consumes instructions or generates final payroll |
| Unchanged basis | Commit capability invokes protected reconciliation and posting | Seven final rows; one-time bonus consumed and monthly applications recorded for September; net INR 53,500 is final |
| Changed-basis alternative before commit | The applicable bonus changes from INR 5,000 to INR 6,000 after approval; calculation supplies the other six amounts unchanged for this illustration | Old draft stays INR 53,500 net and cannot commit. Cancel/rebuild with fresh approval: new gross INR 58,500, deductions INR 4,000, net INR 54,500. Only the replacement commits |
| Retry or abandoned draft | Recovery establishes whether a commit occurred; an uncommitted cancellation produces no payroll | No duplicate result/application from retry; no consumption by cancellation. Recovery mechanics and role mapping remain implementation work |
| Employer liabilities | Payroll records obligations following committed payroll; employer remits to the respective authorities and records proof | Contribution liability INR 1,000 and tax liability INR 2,000 each close against corresponding remittance/proof. The ordinary recovery is not a government liability in this example |
| Later correction within scope | Manager supplies a subsequent-month INR 500 recovery through the governed payroll flow | September remains unchanged; the later month includes INR -500. No automatic undo of earlier instruction applications |
| Correction after exit | The correction arises after the employee has exited | External accounting handles it; payroll history stays final |
| Annual information | Annual workflow uses relevant committed payroll, employer obligations/remittances, and required calculation/official records | September is one contribution to annual information. Neither this example nor liability closure alone constitutes certificate issuance |

The unchanged and changed-basis rows are alternative branches, not two ordinary
commits of the same instructions. All payroll within either employee-month is
associated; approval still belongs to the exact draft. Identifier generation
remains unspecified. Rebuilding includes calculation from the applicable basis.

Additional cases already incorporated cover joining, supplied partial-period
amounts, supplied exit components, future salary changes, finite expiry, late
processing of an eligible period, and a stale employee draft within a batch.
They use the same core operations. The reviewed scenarios expose no additional
core decision; they do not select broader exception policies.

Rationale for closure: the existing decisions explain the selected records,
responsibilities, and outcomes. The remaining uncertainties can be named and
deferred without changing those illustrative outcomes. The browser lab still lacks
several required controls, including approved-stale-draft cancellation and
protected reconciliation; the gap register preserves those findings.

## Layered walkthrough results

| Case | Policy result | Layer-1 guarantee retained |
|---|---|---|
| Bonus changes from 5,000 to 6,000 before commit, policy A | Block/hold old draft and review a replacement; in the seven-entry example net changes from 53,500 to 54,500 only in the replacement | No silent edit or approval transfer; no posting of the blocked draft |
| Same change, policy B | Fixed 5,000 bonus can commit if other controls pass; original seven-entry net stays 53,500 | Exact money, holds, required approval and application constraints still apply; any later adjustment is a new result |
| One of 100 employee drafts held | Select and commit the other 99 if eligible | Held employee stays uncommitted and outstanding; batch evidence does not imply 100 completed payrolls |
| Approval exists before a hold | Retain approval history and apply the hold; release/reapproval behavior is policy | Hold cannot edit money or erase history; changed money is a different draft |
| Draft authority but one-time instruction already consumed | Reject a duplicate application | A freshness policy does not bypass atomic application integrity |

These outcomes follow PAY-ARCH-006 and the retained ledger/application decisions.
They are conceptual walkthroughs, not claims of new executed API behavior.

## Incorporated coverage

| Area | Current coverage | Evidence or rationale |
|---|---|---|
| Five employee payroll stores | Definitions, relationships, and agreed core flow incorporated | [Core concepts](core-concepts.md#agreed-core-model) |
| Intake and calculation | Manager/API handoff; business calculation and source intent outside the core ledger responsibility | [Handbook flow](handbook.md#from-manager-inputs-to-generated-payroll) |
| Lifecycle operations and outcomes | Preparation, fixed draft, exact approval, stale-draft cancellation, commit, and retry guarantees consolidated | [Lifecycle](payroll-lifecycle.md) |
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
  active requirements. PAY-CORE-007 now includes sealing in complete draft creation.
- Annual readiness is not issuance; a global TDS total plus one payslip does
  not establish a complete employee/year result. Code limitations are recorded.

The [database-table review](database-table-review.md) records six HRMS Core
source findings and their subsequent local implementation candidate: settlement
records, contribution pairs, key/index integrity, monthly consumption and
employee finalization. Individual and final combined reviews passed, along with the complete
PostgreSQL payroll suite, short tests and builds. This is separate from the seven
active browser-lab code gaps and does not claim deployed-schema verification.

## What remains, and where it belongs

| Remaining item | Why it remains | Next treatment |
|---|---|---|
| Employer-specific operating procedures | Actual employer/jurisdiction/workforce context, calendars, cutoffs, manual work, and escalation/revocation procedures have not been established | A later operating edition; retain the pinned charter and avoid presenting illustrative practices as observed reality |
| Additional exception policies | Supplemental-run eligibility, partial instruction application, automatic remittance allocation and wider payment-failure procedures are not selected | Later scope only; supplied valid allocations and partial settlement are already specified. These extensions do not reopen ordinary rules |
| Expiry and validation representation | Dates/period encoding, immutable-source lifecycle metadata, and validation evidence are not selected | Implementation specification; no reopening of applicability or source-tracing decisions |
| Exceptional installment/application behavior | Automatic extension, splitting, and restoration have not been adopted | Apply the supplied policy where it fits existing rules; ask if a core behavior change is proposed |
| Concurrency, retries, and recovery | Observable outcomes are specified; the browser demo lacks durable enforcement | Later Core conformance review uses current main and the local candidate separately; choose mechanisms against the existing contracts |
| Detailed role assignments and integrations | Capabilities and system boundaries are settled, concrete mappings are not | Deployment/operating specification rather than invented job-title rules |
| Complete annual issuance | PAY-ARCH-005 selects the payroll annual package/handoff for this handbook; complete issuance is a separate chapter | Develop the statutory procedure for the applicable jurisdiction/year when that chapter is scoped; it does not block the approved package specification |
| Detailed business calculations | Proration, contribution amounts, and annual tax formulas belong to higher-order policy | Do not turn them into new core ledger primitives or infer policy from demo arithmetic |

These items should not all be presented as unanswered foundational questions.
Some are implementation choices; others belong to the producing/consuming layer.
PAY-Q-009 is now settled as PAY-CORE-007. If a future scenario exposes a material
choice within payroll scope, identify that choice and ask before adopting it.

## Review checks

This pass checks local Markdown links and heading anchors, fence balance,
consistency of recorded decision status, example arithmetic, preservation of the
pinned charter, and separation of runtime code from documentation changes.
The walkthrough covers gross/deductions/net and liability amounts explicitly.
Source-inspected implementation gaps remain open; no runtime execution or
completed software behavior is claimed by this review.

Verification for this correction: all 30 Markdown files passed relative-link,
heading-anchor and fence checks (304 local links/anchors). The seven-entry
walkthrough, changed bonus, contribution pair, successive/split remittances and
annual examples were recalculated successfully. `git diff --check` passed.
The checked remote Core main is `3a87931`; the separate local Core branch remains
at `01268e5`. No runtime tests were run for these Markdown-only changes.

The earlier conceptual closure is preserved as history. This layered edition
records PAY-Q-020 as closed/superseded and completes the requested separation
of core contracts from organizational payroll policy. Employer-specific choices,
detailed statutory issuance and verified implementation remain separate work.
No named universal Layer-1 decision awaits an answer in this review; this is not
a claim that every future payroll policy has been specified. Code remains paused.
