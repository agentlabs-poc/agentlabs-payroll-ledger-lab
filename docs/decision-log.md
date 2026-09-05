# HRMS Payroll Handbook — decision log

This log records the discussion behind the [handbook](handbook.md).
The [roadmap](handbook-roadmap.md) identifies the current question and return
point. Process directions and user-confirmed operating facts are recorded
separately below.

| ID | Status | Direction | Evidence and consequence |
|---|---|---|---|
| PAY-PROCESS-001 | User direction | Create an HRMS payroll handbook following the permission-scope lab example. | User: "like agentlabs-permission-scope-lab we need to create handbook for hrms payroll". Use the existing handbook as a process reference; its authorization decisions do not become payroll decisions. |
| PAY-PROCESS-002 | User direction; interpretation corrected by PAY-PROCESS-004 | Understand ground realities first. | User: "understand the ground realities first". The assistant initially interpreted this as requiring an operating interview before core concepts; the user subsequently corrected that order. |
| PAY-PROCESS-003 | User direction | Establish and pin the overall goal and outcome. | User: "before we start setup over all goal and the outcome", followed by "pin it" after the goal was presented. The charter is saved in the handbook and linked from the README. |
| PAY-PROCESS-004 | User direction; current | Start with code concepts, understand the existing model completely, then confirm and refine it. | The user identified the Payroll Ledger, draft ledger, earnings, monthly instructions, and one-time instructions as the core concepts from which the flow was formulated. The attendance question was outside the current conceptual discussion. [Core concepts](core-concepts.md) is now the starting chapter. |
| PAY-PROCESS-005 | User direction | Preserve rationale with decisions. | User: "just make sure you record rationale as well". Keep definitions, reasons, worked examples, counterexamples, consequences, and unresolved details in the chapter, with the log linking to them. |
| PAY-PROCESS-006 | User direction; current sequencing | Move horizontally through high-impact areas first. | User: "you should move horizontally with high impact areas first". Establish major concepts and responsibility boundaries before revisiting detailed lifecycle, schema, concurrency, and recovery questions. The user reiterated this direction after approving PAY-ARCH-001. Preserve parked details and return points in the roadmap. |
| PAY-PROCESS-007 | User direction | Separate recorded agreements from the next proposal with a visible transition. | User requested a separator between committed decisions and next items. Agreement status is distinct from payroll commit or Git commit. |
| PAY-PROCESS-008 | User direction; current sequencing clarification | Establish core-concept clarity before further broader architecture and operating questions. | User approved PAY-ARCH-003 but said those questions are relevant once core concepts are clear. Apply horizontal breadth to unresolved core semantics first. [Coverage checkpoint and rationale](core-coverage.md); prior approvals remain valid. |
| PAY-PROCESS-009 | User direction; current editorial rule | Incorporate established material first; ask only where there is a material ambiguity or decision. Commit and push the existing work before incorporation. | User clarified the question standard, then requested incorporation and a visible account of what was incorporated. The existing snapshot was pushed as `6a30db5`. [Incorporation record](incorporation-record.md) separates agreements from code descriptions and retains pending decisions. |

## Discussion questions

| ID | Status | Question | Dependency |
|---|---|---|---|
| PAY-Q-001 | Answered at handoff level | How does the payroll preparer receive that month's employee changes and payment inputs in the operation being examined? | The user described source information going to an HR/payroll manager, who consolidates inputs into payroll through APIs. Source-to-manager delivery details remain open. |
| PAY-Q-002 | Withdrawn from current sequence by PAY-PROCESS-004 | For an attendance example, what exactly does the manager submit to payroll, and what does payroll then do with that input? | The question was premature. Core concept work proceeds from code; return to source payloads only if a later concept requires it. |
| PAY-Q-003 | Approved | Should the draft hold proposed payroll entries, commit fix the recorded result, and later corrections add linked entries without rewriting the original result? | User answered "approved". PAY-CORE-001 is agreed; PAY-CORE-011 later settles subsequent-month correction timing and finality. Detailed enforcement remains open. |
| PAY-Q-004 | Approved with expiry amendment | Does salary earning entitlement versus recurring payroll directions explain why salary earnings and monthly instructions are separate sources? | User required expiry for standing instructions, gave a loan repaid over five months as an example, and said "rest is approved". PAY-CORE-002 includes the amendment and rationale. |
| PAY-Q-005 | Approved | Should one-time instructions be consumed only on commit, remain available after an abandoned draft, and be unavailable for another ordinary payroll once consumed? | User answered "approved" after the bonus example was explained again. Reversals, reservations, and partial application remain separate questions. |
| PAY-Q-006 | Approved | Should a monthly standing instruction have one ordinary committed application per employee and applicable payroll month, while remaining available in later eligible months until expiry? | User answered "approved". PAY-CORE-004 separates period-specific application from overall lifetime; no implementation schema is adopted. |
| PAY-Q-007 | Approved | Should expiry be evaluated against the payroll period being processed, allowing an eligible earlier period to be processed later subject to the other payroll controls? | User answered "approved". PAY-CORE-005 separates applicability from processing time without adopting reopening, catch-up, or automatic extension rules. |
| PAY-Q-008 | Approved as PAY-CORE-006-B | How should sources and draft values remain stable through review and commit? | User answered "approved" to the source-freeze shape and explicit question freezing draft monetary entries from creation. Corrections require cancellation and rebuilding. PAY-CORE-006 is superseded; exact implementation and recovery mechanics remain open. |
| PAY-Q-009 | Parked during horizontal pass; not approved | Should complete draft creation include sealing, leaving approval and commit as the subsequent distinct operations? | Return after high-impact boundaries under PAY-PROCESS-006. |
| PAY-Q-010 | Approved | Should immutable source history and protected reconciliation at commit replace the long-lived source freeze? | User answered "approved". PAY-CORE-006-C replaces source freezing throughout review while retaining fixed draft monetary content. |
| PAY-Q-011 | Approved | Should higher-order calculation logic produce business amounts while the payroll core governs source/ledger integrity, draft/approval lifecycle, reconciliation, and commit? | User answered "approved". PAY-ARCH-001 is agreed; interfaces and rule details remain parked. |
| PAY-Q-012 | Approved | Should one employee’s draft for a payroll period be the unit of approval and protected commit, with batches coordinating those drafts and retaining individual outcomes? | User answered "approved". PAY-ARCH-002 is agreed; batch-wide all-or-nothing posting was not selected. |
| PAY-Q-013 | Approved | Should input maintenance, preparation, draft approval, and commit be distinct scoped capabilities, with policy deciding which may be held by the same person or role? | User answered "approved", then required core clarity before further broader questions. PAY-ARCH-003 is agreed; exact roles and separation-of-duty policy remain open. |
| PAY-Q-014 | Answered with ownership clarification | Where do employer-liability and accounting records belong relative to payroll? | User clarified that accounting is outside and the employer-liability register is inside payroll. PAY-ARCH-004 replaces the earlier grouping; the Form 16 connection is supported with the qualifications in the chapter. |
| PAY-Q-015 | Answered with scope exclusion | Should an exited employee remain eligible for a subsequent-month adjustment payroll without reactivating employment? | User directed that this is out of payroll scope and should be corrected in accounting. PAY-CORE-013 excludes the proposed after-exit adjustment payroll. |
| PAY-Q-016 | Answered by correcting the premise | How do employer contributions enter payroll and the employer-liability register? | User clarified that the offer-letter CTC contribution is a payroll earning plus matching deduction. Gross includes it; net is unchanged by the pair. Payroll entries precede the corresponding liability. |

## Domain decisions

| ID | Status | Operating account | Evidence and boundaries |
|---|---|---|---|
| PAY-INTAKE-001 | User-confirmed operating account | Source information, potentially including attendance, goes to an HR/payroll manager, who consolidates it and submits inputs to payroll through APIs. A role will normally support this responsibility. | User: "it goes to payroll manager and the to payroll" and "it does not internally transition from service". See [the input-flow chapter](payroll-input-flow.md) for the full explanation. Exact permissions, input representation, and separate approvals remain open. API implementation and deployment conformance are unverified. |
| PAY-CORE-001 | Agreed under PAY-Q-003 | Draft entries are proposed payroll money; commit establishes the recorded result; later corrections preserve it through linked additional entries. | User answered "approved". [Definition, rationale, example, and counterexample](core-concepts.md#pay-core-001--draft-and-posted-payroll-boundary). PAY-CORE-011 later settles subsequent-month correction timing and finality; detailed enforcement remains open. |
| PAY-CORE-002 | Agreed with expiry amendment under PAY-Q-004 | Salary earnings record earning entitlement; monthly standing instructions record recurring payroll directions with an effective lifetime and expiry, producing earnings or deductions while applicable. | User's five-month loan example establishes finite applicability while loan business logic remains outside the payroll core. [Rationale, examples, counterexamples, and open mechanics](core-concepts.md#pay-core-002--salary-earnings-and-monthly-instructions). Expiry representation, skipped periods, overlap, and replacement remain open. Implementation gap PAY-GAP-001 is recorded. |
| PAY-CORE-003 | Agreed under PAY-Q-005 | Consume one-time instructions at commit, retaining the committed reference; abandoned drafts do not consume them, and later ordinary payrolls cannot reuse consumed instructions. | User answered "approved" after clarification. [Rationale and example](core-concepts.md#pay-core-003--when-a-one-time-instruction-is-consumed): avoid losing an instruction through an abandoned draft or applying its effect twice. Partial application, reservations, and reversal effects remain open. PAY-GAP-002 records missing cross-draft enforcement. |
| PAY-CORE-004 | Agreed under PAY-Q-006 | A monthly standing instruction has one ordinary committed application per employee and applicable payroll month, retaining eligibility in later months until expiry. | User answered "approved". [Rationale and example](core-concepts.md#pay-core-004--monthly-application-versus-instruction-lifetime): avoid duplicate monthly effects without exhausting the whole recurring instruction. Version changes, split applications, skipped months, and corrections remain open. PAY-GAP-003 records missing enforcement. |
| PAY-CORE-005 | Agreed under PAY-Q-007 | Evaluate instruction expiry against the payroll period, separately from preparation/commit time. | User answered "approved". [Rationale and examples](core-concepts.md#pay-core-005--applicability-period-and-processing-time): a delay alone must not change an eligible period's source applicability. Other controls, expiry representation, catch-up, and correction rules remain separate. PAY-GAP-001 includes this requirement. |
| PAY-CORE-006-B | Historical approval; superseded by PAY-CORE-006-C | Freeze relevant sources and draft monetary content from complete draft creation through commit or cancellation. | Earlier approval and [rationale](draft-source-freeze.md) are retained. PAY-Q-010 approved reconciliation in place of the long-lived source freeze; draft monetary immutability remains current. PAY-GAP-004 is historical. |
| PAY-SOURCE-001 | User-confirmed model clarification | Source records are immutable; old records expire and new records are created instead of overwriting their monetary content. | User: "source ledgers are immuatble, meaning they are expired and new one is created". Preserve historical content and distinguish it from changing applicability. Physical expiry metadata and full implementation conformance are not established. |
| PAY-CORE-006-C | Agreed under PAY-Q-010 | Fix the draft and retain sufficient basis for validation; reconcile the full target-period input set and instruction applications as part of a protected commit; block and rebuild when the basis changes. | User answered "approved". [Rationale, examples, and tradeoff](source-reconciliation.md). Immutable history preserves the basis; protected reconciliation validates applicability without a day-long source freeze. Relevant additions and competing applications must be detected. PAY-CORE-010 removes mandatory business source tracing; validation representation remains open. |
| PAY-ARCH-001 | Agreed under PAY-Q-011 | Higher-order calculation logic produces business amounts; payroll core governs source/ledger integrity and the complete monetary lifecycle for every producer. | User answered "approved". [Rationale, example, and scope](calculation-boundary.md). Separate variable business formulas from stable ledger rules without granting calculation code a posting bypass. Deployment and interfaces are not selected. |
| PAY-ARCH-002 | Agreed under PAY-Q-012 | Employee-owned payroll drafts remain individual approval/commit units; batches group exact drafts and expose individual outcomes. | User answered "approved". [Source evidence, rationale, example, and tradeoff](ledger-ownership.md). Identity representation and bulk-action mechanics remain open. |
| PAY-ARCH-003 | Agreed under PAY-Q-013 | Distinguish scoped input-maintenance, preparation, draft-approval, and commit authority; role composition follows policy. | User answered "approved". [Evidence, rationale, examples, and alternatives](authority-and-review.md). Input acceptance is not payroll approval; commit authority cannot bypass approval or reconciliation. |
| PAY-CORE-008 | User-confirmed boundary | Business overlap, replacement intent, and duplicate detection across sources belong to the producing layer, not payroll core. | User: "we cannot detect this, nor we should its a differnt layer problem". [Rationale and distinction from application guards](core-coverage.md). |
| PAY-CORE-009 | User-confirmed principle | Payroll uses the applicable reality/facts when it runs. | User: "what matters is the reality/fact when your run payroll". [Scope and retained agreements](core-coverage.md). No new cross-version business-intent inference or automatic reuse policy is adopted. |
| PAY-CORE-010 | User-confirmed simplification; amends earlier provenance requirements | Source tracing is not a mandatory payroll-core responsibility. | User: "we dont even need to trace the source". [Rationale and reconciliation distinction](core-coverage.md). Earlier mandatory monetary-entry-to-source lineage wording is superseded; demo reference fields remain source evidence. |
| PAY-CORE-011 | User-confirmed clarification of PAY-CORE-001 | Generated/committed payroll is as good as paid for core finality; corrections are adjustments in a subsequent payroll month. | User: "we should adjust it in subsequent month, once payroll is generated its as good as paid". [Rationale, terminology, and example](core-coverage.md#pay-core-011--generated-payroll-is-final-adjust-a-subsequent-month). Preserve the earlier result; do not reopen it based on payment status. |
| PAY-ARCH-004 | User-clarified ownership under PAY-Q-014 | Employer-liability register belongs inside payroll; general accounting is outside. | User explicitly corrected the earlier grouping. [Rationale, code evidence, and verified Form 16 relationship](payroll-outputs.md). The TDS register supports deduction/deposit reporting; complete Form 16 also needs annual salary/tax and official statement/certificate records. No complete issuance design is approved. |
| PAY-CORE-012 | User-confirmed liability lifecycle | Track outstanding employer liability; record remittance to the government authority with proof such as the challan number; close the corresponding settled liability. | User explicitly described remittance and proof as the closure basis and subsequently confirmed "yes" on 2026-09-06. [Lifecycle, rationale, and example](payroll-outputs.md#pay-core-012--liability-remittance-proof-and-closure). Retain the liability/settlement history; allocation and proof interfaces remain later details. |
| PAY-CORE-013 | User-confirmed scope under PAY-Q-015 | Corrections after employee exit are handled in external accounting, outside payroll; the generated payroll remains unchanged. | User: "this should be out of scope and should be currented in accounting". [Example, rationale, and withdrawn alternative](employee-and-annual-journeys.md#pay-core-013--a-correction-after-employment-has-ended). Narrows PAY-CORE-011 at the after-exit boundary; does not prescribe accounting mechanics. |
| PAY-CORE-014 | User-confirmed contribution flow under PAY-Q-016 | Employer contribution in CTC enters payroll as an earning and matching deduction, then the employer-liability register; gross includes it while the pair leaves net unchanged. | [Rationale, worked amounts, code comparison, and withdrawn alternative](payroll-outputs.md#pay-core-014--employer-contributions-through-payroll). The earlier direct-to-liability/no-gross-effect proposal was incorrect. |

The user identified the existing ledger and instruction concepts as the model
to confirm and refine. The reconstruction in core-concepts.md preserves this
starting point without treating every demo shortcut, lifecycle detail, or
statutory example as an adopted rule.

## Proposals awaiting confirmation

| ID | Status | Proposal | Rationale and remaining details |
|---|---|---|---|
| PAY-CORE-007 | Proposed under PAY-Q-009; parked | Complete and seal monetary content during draft creation; retain approval and commit as separate operations without a distinct user-visible seal step. | [Rationale and alternative](draft-source-freeze.md#pay-core-007--does-sealing-remain-a-separate-operation). Return after the horizontal pass. |

## Alternatives and history

An initial clarification offered a design foundation, an operator guide, or
both as possible handbook orientations. The user redirected the work to
understanding ground realities first. No orientation was selected through that
question. Revisit audience and organization after the operating context is known.

The assistant's initial sequence was operating interview, then concepts,
workflows, rules, and reconciliation. Its PAY-Q-002 attendance question treated
operating payload details as a prerequisite. The user corrected this: the
existing code concepts already formulate the flow and must be understood,
confirmed, and refined first. PAY-PROCESS-004 supersedes that sequencing.
PAY-INTAKE-001 remains valid supporting context; it does not determine the
current discussion agenda.

PAY-CORE-002 was initially proposed without an explicit expiry requirement.
The user approved the distinction with an expiry amendment. The current chapter
preserves why a finite loan-recovery instruction belongs in the model without
making loan servicing a core payroll concept.

Under PAY-Q-008, the user challenged the earlier source-change/revision proposal
with a draft-to-commit mutation freeze, then approved the explained shape and
freezing draft monetary entries from creation. **PAY-CORE-006 is superseded by
PAY-CORE-006-B.** The [earlier rationale](core-concepts.md#pay-core-006--source-changes-and-an-existing-draft)
is preserved as history, not an active proposal. Exact implementation and
recovery authority remain open; PAY-CORE-007 is a subsequent unapproved proposal.

The user then clarified immutable source records with expiry/replacement and
asked whether reconciliation before commit would be simpler. PAY-Q-010 reopened
the freeze decision, and the user approved PAY-CORE-006-C. It supersedes the
long-lived source freeze while retaining draft immutability and cancel/rebuild
on a changed basis. The user then directed horizontal high-impact coverage;
sealing and other mechanics remain parked rather than becoming the next topic.

After approving PAY-ARCH-003, the user asked whether the core concepts had
actually been reviewed and made clear. The source review exists, but known
composition, application-identity, monetary, and correction semantics remain
open. PAY-PROCESS-008 corrects the move into broader responsibilities before
closing those conceptual gaps; it does not withdraw earlier approvals.

The user then rejected business overlap detection as a core task, emphasized
applicable facts at payroll run time, and removed mandatory source tracing.
PAY-CORE-008/009/010 narrow the earlier checklist and provenance assumptions.
At that point, the fourth item required explanation and had no new decision.
The user subsequently clarified that corrections belong in a subsequent month
and generated payroll is as good as paid. PAY-CORE-011 records this finality
rule and closes that question. No automatic instruction restoration is adopted.

PAY-Q-014 was answered by clarifying that accounting is external but the
employer-liability register belongs in payroll. The user asked whether its Form
16 role supports this shape. Official material supports a TDS deduction/deposit
basis alongside annual salary/tax and processed statement/certificate records.
The assistant’s earlier external-liability framing is superseded; detailed
issuance and accounting interfaces remain open.

During incorporation of joining/exit scenarios, PAY-Q-015 asked whether a
former employee could receive subsequent-month adjustment payroll without
employment reactivation. The user placed this case outside payroll and in
accounting. PAY-CORE-013 records that exclusion; the proposed payroll eligibility
exception is withdrawn. Existing generated payroll remains final.

PAY-Q-016 incorrectly assumed an employer-only contribution would bypass
payroll earnings and leave gross unchanged. The user clarified the offer-letter
CTC model: an employer-contribution earning and matching deduction enter the
Payroll Ledger first; the corresponding obligation then enters the employer
register. PAY-CORE-014 records that flow; the prior proposal is withdrawn.
