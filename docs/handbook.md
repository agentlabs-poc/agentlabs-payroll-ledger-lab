# HRMS Payroll Handbook — working edition

## Pinned goal and intended outcome

Established: 2026-09-05. The user requested a payroll handbook following the
permission-scope handbook approach, directed us to understand ground realities
first, and asked to pin the overall goal and outcome.

Current direction (PAY-PROCESS-004): begin with the concepts already expressed
in code—salary earnings, monthly and one-time instructions, the draft ledger,
and the Payroll Ledger. Understand and confirm their relationships, then refine
them. The earlier interpretation that an employer interview must precede core
concept work is superseded; see the [decision history](decision-log.md).

PAY-PROCESS-006 adds the discussion order: cover high-impact boundaries across
the model first, then return to detailed mechanics. The
[horizontal coverage map](handbook-roadmap.md#horizontal-coverage-map) records
the sequence and parked questions. PAY-PROCESS-008 clarifies that this breadth
must first close the high-impact core semantics; see the
[core-concept coverage checkpoint](core-coverage.md).

**Overall goal:** Develop a shared understanding of HRMS payroll, grounded in
actual operations, and turn that understanding into a handbook that guides
product design, implementation, and review.

Develop the handbook through focused discussion. Preserve reasoning, examples,
decisions, alternatives, and unresolved questions as the understanding evolves.
This charter sets the direction; it does not settle individual payroll rules.

## What the handbook should explain

| Area | Intended coverage |
|---|---|
| Operating reality | Who does what, where information comes from, deadlines, manual work, and common exceptions. |
| Core concepts | Salary entitlement, payroll inputs, calculations, approvals, monetary records, payments, and supporting evidence. |
| Complete journeys | Employee joining, monthly payroll, salary changes, corrections, exit settlement, statutory obligations, and year-end work. |
| Responsibilities and controls | What employees, HR, payroll, finance, software, and external services each own. |
| Expected behavior | What happens when information is missing, changes arrive late, approvals are withdrawn, or payments fail. |

Jurisdictions, employer types, workforce types, and the actual operating process
still need to be established. Inclusion here is a topic to investigate, not a
claim that the lab supports it or that one rule applies to every employer.

## Concrete outcome

A coherent working HRMS Payroll Handbook in this repository, supported by:

- Workflow diagrams showing people, inputs, decisions, records, and handoffs.
- Worked examples and counterexamples, including exceptions and corrections.
- A decision log preserving rationale, alternatives, and agreement status.
- A discussion roadmap with open questions, dependencies, and return points.
- An implementation gap register relating agreed requirements to verified
  software behavior.

## Completion criteria

We can walk through representative payroll scenarios and explain the inputs,
responsible people, decisions, resulting records, and exception handling without
relying on hidden assumptions. Terminology, rules, diagrams, and examples agree.
Remaining questions are explicitly deferred or tracked with their implications.
Implementation gaps are visible rather than presented as delivered behavior.

The handbook is not complete merely because these files exist or the ordinary
monthly payroll example is documented.

## Working sequence

1. Reconstruct the existing core model from code: identify the ledgers,
   instructions, operations, and relationships that produce the payroll flow.
2. Confirm and refine concepts: explain each boundary and lifecycle, test it
   with examples, and distinguish intended semantics from demo shortcuts.
3. Trace the resulting workflows and exceptions: preparation, drafting,
   approval, posting, correction, payslips, liabilities, and downstream outputs.
4. Agree rules and responsibilities: preserve rationale and alternatives;
   examine operational details when needed to settle a core concept.
5. Reconcile and publish: align chapters, examples, code evidence, open
   questions, and the implementation gap register.

Documentation grows through these stages; reconciliation does not require
waiting until the end to inspect source evidence.

## Evidence and decision discipline

Keep observed operating practice, verified repository behavior, illustrative
examples, proposed requirements, and agreed decisions distinguishable. Record
the repository revision for implementation findings. Code inspection alone
does not establish deployed behavior or an employer's operating process.

Existing lab behavior is evidence to examine. Proposed rules become agreements
through discussion; silence does not constitute agreement. Retain superseded
reasoning as labeled history. Statutory claims require applicable jurisdiction,
period, and authoritative sources when that branch is examined.

Creating this handbook does not itself authorize payroll implementation changes.

## Resume here

Supporting material:

- [Agreed core model](core-concepts.md#agreed-core-model): the consolidated
  concepts, flow, and ordinary-payroll example.
- [Calculation and the payroll core](calculation-boundary.md): the agreed
  responsibility boundary, with its rationale and examples.
- [Committed payroll and downstream records](payroll-outputs.md): the current
  unapproved boundary for payslips, reports, liabilities, and accounting.
- [Core concepts — start here](core-concepts.md): the existing ledger model,
  complete conceptual flow, supporting concepts, and refinement candidates.
- [Payroll inputs](payroll-input-flow.md): the user-confirmed source-to-manager
  handoff and submission into payroll through APIs.
- [Operating baseline](operating-baseline.md): inspected source behavior, a
  demo workflow and worked example, and the limits of that evidence.
- [Discussion roadmap](handbook-roadmap.md): coverage, dependencies, and the
  current return point.
- [Decision log](decision-log.md): user directions, open questions, and history.
- [Implementation gaps](implementation-gaps.md): source-backed differences
  from agreed concepts, starting with standing-instruction expiry.

**Current stage:** Horizontal pass through major core concepts and responsibilities.

**Agreed: PAY-Q-003 / PAY-CORE-001.** Draft entries hold proposed payroll money;
commit fixes the recorded result; later corrections add linked entries while
preserving the original. The
[worked example](core-concepts.md#pay-core-001--draft-and-posted-payroll-boundary)
preserves the rationale. PAY-CORE-011 settles subsequent-month corrections;
detailed draft and implementation mechanics remain open.

**Agreed with expiry amendment: PAY-Q-004 / PAY-CORE-002.** Salary earnings
record entitlement; monthly instructions express recurring payroll directions
with an effective lifetime and expiry. The user's five-month loan example,
rationale, and remaining mechanics are preserved in
[salary earnings and monthly instructions](core-concepts.md#pay-core-002--salary-earnings-and-monthly-instructions).
Loan servicing remains outside the core. Expiry enforcement is an open code gap.

**Agreed: PAY-Q-005 / PAY-CORE-003.** A one-time instruction is consumed at
commit, remains available after an abandoned draft, and cannot be reused in
another ordinary payroll once consumed. The
[rationale and example](core-concepts.md#pay-core-003--when-a-one-time-instruction-is-consumed)
are preserved; cross-draft enforcement is tracked as PAY-GAP-002.

**Agreed: PAY-Q-006 / PAY-CORE-004.** A monthly instruction has one ordinary
committed application per employee and applicable payroll month, retaining
eligibility for later months until expiry. The
[rationale and example](core-concepts.md#pay-core-004--monthly-application-versus-instruction-lifetime)
are preserved; enforcement is tracked as PAY-GAP-003.

**Agreed: PAY-Q-007 / PAY-CORE-005.** Evaluate expiry against the payroll period
being processed, subject to the other payroll controls. A processing delay
alone does not change an earlier period's applicability. The
[rationale and examples](core-concepts.md#pay-core-005--applicability-period-and-processing-time)
are preserved; PAY-GAP-001 includes this requirement.

**Historical checkpoint: PAY-Q-008 / PAY-CORE-006-B.** The long-lived source
freeze is superseded by PAY-CORE-006-C. [The freeze chapter](draft-source-freeze.md)
preserves its rationale and earlier approval. Draft monetary immutability and
cancel/rebuild remain part of the current model. PAY-GAP-004 is historical.

**Source clarification: PAY-SOURCE-001.** Source records are immutable; changes
expire old records and create replacements. Their history remains available
even when the applicable source set changes. Full code conformance is unverified.

**Agreed: PAY-Q-010 / PAY-CORE-006-C.**
[Immutable sources and reconciliation before commit](source-reconciliation.md)
replace the long-lived source freeze. A fixed draft captures its basis; protected
reconciliation checks the full applicable input set and instruction use before
posting. Relevant changes require rebuilding and fresh review. PAY-GAP-005
records the current implementation gap.

**Agreed: PAY-Q-011 / PAY-ARCH-001.**
[Calculation logic produces business amounts; the payroll core governs their
monetary lifecycle](calculation-boundary.md). Rationale and examples are recorded;
calculator interfaces and rule details remain parked.

**Agreed: PAY-Q-012 / PAY-ARCH-002.**
[Employee-period drafts are the approval and commit units](ledger-ownership.md).
Batches coordinate exact drafts and retain individual outcomes, including
partial completion. Rationale and the batch-wide alternative are preserved.

**Agreed: PAY-Q-013 / PAY-ARCH-003.**
[Input maintenance, preparation, draft approval, and commit have distinct
scoped authority](authority-and-review.md); policy determines role composition.

---

**Core consolidation recorded.** The [agreed model](core-concepts.md#agreed-core-model)
incorporates PAY-CORE-008/009/010/011: source intent belongs upstream, payroll
uses applicable facts, source tracing is not required, and finalized payroll
is adjusted only in a subsequent month. Prior rationale and alternatives remain
in the [checkpoint](core-coverage.md) and decision log.

**Current proposal: PAY-Q-014 / PAY-ARCH-004.**
[Committed payroll and downstream records](payroll-outputs.md): payslips and
reports present committed payroll; employer-liability/accounting processes
consume it and maintain their own records. This boundary is not yet approved.

**Parked: PAY-Q-009 / PAY-CORE-007.** The proposal to include sealing in complete
draft creation remains unapproved. Return after the horizontal pass under
PAY-PROCESS-006, together with other detailed mechanics.

**PAY-Q-001 is answered at handoff level:** source information, potentially
including attendance, goes to an HR/payroll manager, who consolidates it and
submits payroll inputs through APIs. A role will normally support this work;
exact permissions remain open. The user described no automatic internal
source-service transition into payroll (PAY-INTAKE-001).

**PAY-Q-002 — withdrawn from the current sequence:** The attendance-payload
question was premature. The user directed us to start with the core model that
already produces the flow (PAY-PROCESS-004).

Start at the five stores in [core concepts](core-concepts.md): salary earnings,
monthly standing instructions, one-time inputs, draft transactions, and posted
payroll. Explain how preparation, references, approval, commit, snapshots, and
corrections connect them before proposing refinements. Further employer-specific
operating details are not a prerequisite for this work.
