# What was incorporated into the handbook

This is an editorial change record, not a new domain decision. It implements
the user's request to incorporate established material first and show what was
incorporated. The discussion snapshot was committed and pushed first as
`6a30db5ced58dff013bb2caa436b15733d832d87`.

## Change in the reading experience

Previously, the handbook's resume section mostly listed approvals in discussion
order and sent the reader to separate chapters. The revised
[handbook](handbook.md#reading-path) explains the model in subject order:
ledgers, manager handoff, payroll generation, instruction application, a monthly
example and correction, ownership/authority, and existing-code evidence.

The pinned charter and completion criteria are retained. The decision log,
specialist chapters, rationale, alternatives, and superseded history remain
available; the narrative does not replace their evidence.

## Incorporated from agreements and user clarifications

| Material | Existing basis | Where the reader finds it |
|---|---|---|
| Five ledgers and their different meanings | PAY-CORE-001/002 and the reviewed model | [The five ledgers](handbook.md#the-five-ledgers) |
| Manager/API handoff, applicable facts, calculation/core split, fixed draft, and protected commit | PAY-INTAKE-001, PAY-CORE-006-C/008/009/010, PAY-ARCH-001 | [From manager inputs to generated payroll](handbook.md#from-manager-inputs-to-generated-payroll) |
| Expiry, one-time consumption, monthly application, and payroll-period applicability | PAY-CORE-002/003/004/005 | [Instruction lifetime and application](handbook.md#instruction-lifetime-and-application) |
| Ordinary payroll and subsequent-month correction, with generated payroll treated as final | PAY-CORE-001/003/004/011; existing illustrative amounts | [One monthly payroll, then a correction](handbook.md#one-monthly-payroll-then-a-correction) |
| Employee-period unit, batch outcomes, and scoped capabilities | PAY-ARCH-002/003 | [Ownership, batches, and authority](handbook.md#ownership-batches-and-authority) |

These sections state the agreed outcomes and rationale directly. They do not
ask for the same approval again. The examples apply existing rules rather than
selecting new exception, calculation, or recovery policies.

## Incorporated as existing-code descriptions only

The [existing lab section](handbook.md#what-the-existing-lab-additionally-describes)
incorporates seven already described concepts: preparation preview,
component/head, proof attachment, payroll reference, payslip snapshot/PDF,
employer-liability records, and the incomplete annual readiness package.

Evidence: lab revision `737465d5e27888518018e9b1f28f75fcfcac0139`,
[main.ts](../src/main.ts), as recorded in [the baseline](operating-baseline.md)
and [core-concept chapter](core-concepts.md). Each row includes its limitation.
Code descriptions do not become approved requirements merely by being included.

## What remained undecided at this incorporation

- PAY-Q-014 / PAY-ARCH-004: the proposed downstream responsibility boundary.
- PAY-Q-009 / PAY-CORE-007: the parked separate-sealing question.
- Detailed exceptions, source/validation representations, role assignments,
  wider journeys, and integration policies identified in the roadmap.

No new payroll rules, source-tracing requirement, automatic instruction reuse,
or same-month correction policy is introduced. No runtime code is changed.
The handbook's coverage estimate is not automatically increased by reorganizing
existing content; complete scenario coverage and publication review remain work.

Later update: the user subsequently answered PAY-Q-014 with a corrected
boundary: employer liabilities inside payroll, accounting outside. See the
[updated chapter](payroll-outputs.md). This was a separate user clarification,
not an approval inferred during the incorporation pass.

## Scenario incorporation — 2026-09-06

After confirming the liability lifecycle, the next pass added
[payroll scenarios](payroll-scenarios.md): nine outcome cases derived from prior
agreements, a three-month salary/expiry illustration, and an explanation of the
two reconciliation purposes. Each case identifies its established decision
basis; none introduces a new domain decision.

The grouped-challan example is explicitly source-described behavior from
`payAndReconcileChallans` and `matchReconciliation`, not adoption of production
allocation rules. Joining/exit, partial-period calculation, and full annual
issuance remain incomplete. This adds worked scenario coverage but is not an
implementation test or a claim that all handbook journeys are now complete.

## Extended journeys — 2026-09-06

[Joining, partial periods, exit, and annual reporting](employee-and-annual-journeys.md)
now describe how supplied facts and calculation outputs use the agreed payroll
lifecycle. Examples assume component amounts rather than choosing new formulas.
The settlement source description is pinned to the previously inspected HRMS
Core revision; the annual description retains the lab's incomplete status.

PAY-Q-015 raised one new material question about a former employee’s later
adjustment. The user answered during this pass: handle it in external accounting,
outside payroll. PAY-CORE-013 records the boundary and withdraws the proposed
payroll exception. This is a user decision, not inferred from incorporation.
Complete annual issuance and exception/calculation policies remain further work.

## Reconciliation and consistency pass — 2026-09-06

[Reporting and reconciliation](reporting-and-reconciliation.md) now distinguishes
employee payroll finality, liability closure, annual readiness, and issuance.
It adds supplied-allocation and annual-data examples, while GAP-007/008 record
missing matching validation and annual aggregation in the inspected code.

The consistency pass updates earlier wording in the source-input, calculation,
core-concept, ownership, and operating-baseline chapters to reflect later
agreements. The gap register now maps agreement groups to inspected support.
Historical alternatives remain reconstructable; settled concepts are not
reopened because code enforcement is missing.

PAY-Q-016 initially asked about employer-only contributions with no effect on
gross. The user subsequently corrected that premise: CTC contribution earning
and matching deduction enter payroll first, followed by employer liability.
PAY-CORE-014 now records that flow, with gross increasing and net unchanged by
the pair. The earlier proposal is withdrawn; the revised material derives from
the user’s clarification, not from the reporting examples.

## Integrated walkthrough and review — 2026-09-06

The [continuous payroll/liability walkthrough](payroll-scenarios.md#end-to-end-payroll-and-liability-walkthrough)
combines the established contribution earning/deduction pair with salary,
monthly/one-time instructions, commit, and corresponding remittances with proof.
The [review record](handbook-review.md) maps coverage and classifies remaining
implementation details separately from policy questions. This consolidates
existing concepts; it does not claim runtime implementation or complete statutory
issuance procedures.

During this pass, the user clarified PAY-CORE-015: all payroll for an employee
and month is tied together, and no canonical ID-generation method is established.
The ownership chapter and handbook now state this association without inventing
an identifier format, new ledger, or automatic transfer of draft approval.

## Lifecycle consolidation — 2026-09-06

The [lifecycle chapter](payroll-lifecycle.md) consolidates preparation, complete
fixed drafts, exact approval, protected reconciliation, cancellation/rebuild,
commit, retry guarantees, and subsequent-month correction. These derive from
existing decisions rather than newly proposed core responsibilities.

Source inspection identifies an explicit PAY-GAP-005 case: `abandonDraft`
rejects approved drafts, so the lab cannot cancel an approved stale draft
through that operation. The implementation gap is recorded without selecting
a new authorization policy.

PAY-Q-009 was returned to the user after horizontal coverage. Its separate-seal
proposal remains unapproved; the historical source freeze remains superseded.
Navigation and current-status tables now distinguish the pending answer from
the agreed fixed-draft invariant. No runtime code is changed.

## Sealing decision recorded — 2026-09-06

The user answered “agreed” to PAY-Q-009. PAY-CORE-007 now includes sealing in
complete draft creation, leaving create → approve → commit as the visible
operations, with cancellation before commit. The lifecycle chapter records
the rationale and alternative; the decision log moves this from proposal to
agreement. Current navigation, core concepts, and gap coverage reflect approval.
The earlier pending status above is retained as the history of the previous pass.
Runtime changes remain outside this documentation update.

## Final walkthrough and edition checkpoints — 2026-09-06

Following the user’s direction to continue through the remaining checkpoints,
the [review record](handbook-review.md#edition-checkpoints) now records four
explicit checkpoint results and closes conceptual edition 1 with named deferrals.
The final walkthrough follows the existing seven-component example through
approval, unchanged/changed-basis alternatives, commit, liabilities, correction,
and annual use. It introduces no additional core decision.

The main flow now explicitly includes sealing during creation, and its rebuild
arrow returns through calculation. The README distinguishes the conceptual
handbook from the original browser demo. Employer-specific operations and wider
exception policies are explicitly deferred alongside implementation and issuance
work; the original pinned charter remains intact.

## Gap-resolution audit and association confirmation — 2026-09-06

The user requested an audit of whether every gap was discussed and resolved,
and reiterated the employee-month association without a canonical ID generator.
The [audit](gap-resolution-audit.md) maps all eight numbered gaps and additional
coverage findings to conceptual, deferred, and implementation status. PAY-CORE-015
remains resolved; generator selection is not a further core question.

Current checkpoint wording now says no named proposal awaits an answer, rather
than suggesting all remaining decisions or gaps are closed. The prior edition
closure remains an editorial checkpoint with explicit deferrals. Seven active
numbered gaps/limitations remain; none was implemented during documentation work.
No implementation handoff or runtime change was made in the interrupted turn.

## Gap-closure acceptance cases — 2026-09-06

Following the user’s direction to work on the gaps, the
[worksheet](gap-closure-work.md) consolidates twelve acceptance cases from
existing agreements. These give later implementation reviews concrete outcomes
without claiming tests ran or code gaps closed. ID generation and mandatory
source tracing are not reopened.

PAY-Q-017 / proposed PAY-CORE-016 asks how to represent a partial employer
remittance, using INR 10,000 owed and INR 6,000 remitted with proof. This is a
material refinement of the previously deferred partial-payment mechanics. It
remains awaiting the user’s answer; navigation and proposal status reflect that.

## Partial-remittance rule approved — 2026-09-06

The user approved PAY-Q-017 and emphasized that the remainder stays a liability.
PAY-CORE-016 moves from proposal to agreement. The output chapter records
INR 10,000 owed, INR 6,000 settled with proof, INR 4,000 still owed, and full
closure after the remaining INR 4,000 is settled with proof. Rationale and the
unselected alternative are retained. AC-13 provides the corresponding
acceptance case; the main diagram now distinguishes partial from full settlement.

Current navigation reflects approval. Historical audit/proposal records remain
labeled in time. GAP-007 stays open for implementation and further allocation/
interface detail; approving this balance rule does not claim a delivered fix.

## Operation contracts — 2026-09-06

The user directed continued work until all gaps are complete. The
[operation contracts](payroll-operation-contracts.md) develop the agreed rules
into inputs, preconditions, outcomes, failure/recovery behavior, and review
cases. They include an explicit supplied split of a INR 9,000 remittance across
two obligations and correctly scoped annual data-selection examples. These
specifications do not introduce an allocation order, ID generator, or business
source-tracing requirement.

PAY-Q-018 asks whether annual coverage means the payroll package/handoff or
complete issuance for a specified jurisdiction/year. At this pass it awaits
an answer; the following entry records its approval. The operation contracts
specify behavior without claiming that runtime gaps are fixed.

## Annual package scope approved — 2026-09-06

The user answered “yes” to PAY-Q-018. PAY-ARCH-005 selects the payroll annual
package and issuance handoff, with detailed statutory procedures in a separate
jurisdiction/year chapter. The [package specification](annual-payroll-package.md)
now records contents, coverage, selection, balances, missing inputs, handoff,
rationale, and acceptance evidence.

GAP-008 retains its implementation finding but now has an approved output scope
and concrete package closure criteria. A INR 12,000 liability with INR 10,000
settled shows INR 2,000 outstanding, independent of the illustrative
INR 600,000 payroll gross. Scope isolation and exact-once entry aggregation are
explicit.

## Remaining-item classification and database review — 2026-09-06

The [classification](gap-closure-work.md#remaining-item-classification) distinguishes
engineering choices, upstream repayment policy, integration work, and unresolved
payroll behavior. PAY-Q-020 / proposed PAY-CORE-017 asks whether approval may be
withdrawn from an unchanged draft while retaining its fixed content for fresh
approval. This remains unapproved.

The user also requested review of actual database tables. The
[database review](database-table-review.md) examines HRMS Core migrations and
consuming code at fetched main `3a87931ea536c8b617e6e391c14affd03ade9f65`;
the reviewed payroll files are unchanged from the local checkout. Six PAY-DB
findings distinguish confirmed schema inconsistencies, model mismatches, index
duplication, and a constraint-coverage question. The source review does not
inspect a deployed database or claim measured performance. No schema/runtime
changes were made.

## Local HRMS Core implementation candidate — 2026-09-06

The later request to fix the database findings was implemented in HRMS Core on
an isolated local branch, `fix/payroll-ledger-schema`. New migrations 92–95 and
their Go consumers address all six PAY-DB findings. The
[database review](database-table-review.md#implementation-candidate--2026-09-06)
now records outcomes, rationale, historical compatibility and test evidence.
No shared branch or deployed database was changed. This handbook update changes
documentation only; the browser lab runtime and its separate gap list remain
unchanged. PAY-Q-020 remains unapproved.

## Consolidated handbook correction — 2026-09-06

The user required handbook completion before more implementation. This pass
pauses code work, preserves the local Core candidate, and corrects the use of
historical conceptual-edition closure as current readiness. The current review
and navigation agree that PAY-Q-020 is unanswered; no proposed rule is adopted.

The new [baseline reconciliation](baseline-reconciliation.md) compares later
user decisions with the hub's layered architecture, merged Core main `3a87931`,
browser-lab revision `737465d`, and local Core candidate `5bc0b1a`. It records
retained public API/CLI acceptance requirements, later employee commit and
liability rules, existing Core approval separation, and future work boundaries.
The historical eight-gap audit is labeled as such rather than rewritten to
claim current Core lacks its already merged payroll controls.

Stale decision-row notes about source replacement, corrections and consumption
are aligned with subsequent approvals. Four acceptance cases make already
agreed batch, association, contribution and capability outcomes explicit.
Rationale: decisions govern implementation; local code and passed tests are
evidence to assess, not a way to settle an unanswered handbook question.

Only handbook Markdown is changed in this pass. No Core/runtime, hub ticket,
PR, deployment or remote branch is changed. The documentation check covered
all 27 Markdown files and 253 local links/anchors, fence balance and the worked
payroll, contribution, settlement and annual arithmetic. All passed; the pending
PAY-Q-020 answer remains a closure dependency.

## PAY-Q-020 closed as superseded — 2026-09-06

The user explained that approval withdrawal, reconciliation and selection of
held drafts belong to the upper layer and vary by organization, then instructed
“add the rationale and close the ticket as superseded”. PAY-Q-020 and proposed
PAY-CORE-017 are now closed/superseded as core decisions, not approved as a
mandatory withdrawal workflow. Earlier paragraphs describing them as unanswered
are historical and are superseded by this entry.

[PAY-ARCH-006](payroll-policy-boundary.md) records the rationale: Layer 1
protects records and monetary operations; Layer 2 chooses organizational policy.
One policy may reconcile current sources; another may treat the fixed draft as
final. Holding one draft can exclude it while other selected drafts proceed,
without reporting the held draft as committed. Separate approval evidence and
hold state are recorded as a suggested representation, not an adopted schema.

Current navigation and status records no longer list PAY-Q-020 as a blocker.
The universal Layer-1 placement of the earlier freshness/rebuild requirement is
superseded; its history remains as a Layer-2 policy example. Further handbook
alignment remains work. Only Markdown changes; no Core or runtime change is
made and implementation remains paused.

## Layer-1 handbook and HRMS payroll policy — 2026-09-06

The user additionally approved expressing the handbook as Layer 1 plus separate
policy and directed continuation. The [Layer-1 chapter](layer-1-contracts.md)
now states records, capabilities and monetary guarantees; the
[HRMS payroll policy](hrms-payroll-policy.md) states organizational ground rules,
reconciliation and draft-authority variants, hold/release and batch examples.

Current operation contracts, lifecycle, diagrams, authority, ownership and source
chapters now distinguish conditional policy from universal ledger integrity.
The review walks the same changed-bonus facts through both policies and checks
that a held employee remains outstanding while the other selected drafts proceed.
Original decisions and earlier examples remain traceable as policy or history;
PAY-Q-020 remains closed as superseded rather than approved as a universal rule.

The conceptual documentation pass is closed with explicit employer-policy,
statutory and implementation limits. Runtime and Core are unchanged; the local
candidate requires later assessment against the clarified layer boundary. Validation passed across
30 Markdown files and 304 local links/anchors, code-fence balance and the worked
arithmetic. A semantic reread checked both policy outcomes, hold exclusion,
approval history and retained application/commit guarantees; no runtime tests
are claimed for these documentation changes.

## Verification

Review this change against the discussion snapshot above. Verify all local
Markdown links and heading anchors, fence balance, the example's arithmetic,
and that agreement, historical proposal, and deferred-work statuses stay distinct. Runtime tests do not
validate this editorial change; no software behavior is modified.
