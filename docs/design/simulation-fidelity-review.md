# Simulation fidelity review

Status: read-only study requested after the user identified employee-less earning
keys in the HTML. Implementation is paused. The executable baseline is Lab
`2d2203b`; the uncommitted earning-key correction notes are a target, not delivered
behavior. Two independent traces and disposable SQLite probes support this review.
No production code, API, schema, browser fixture or simulation code was changed
by the study.

## What “near the agreed model” means

The simulation must demonstrate the agreed canonical meanings, identities,
responsibility boundaries and lifecycle with actual stored rows. A complete list
of record types is not complete workflow coverage. A warning about a known wrong
key does not satisfy the employee-ownership requirement.

Keep exactly three canonical monetary ledgers, one payroll L1 record store and
one L2 store. Consumers own L3. Canonical JSON remains the representation; decoded
key columns are a storage projection. Business formulas and organizational policy
remain outside L1. No production-like service stack or new bulk-write API is
needed to make the SQLite walkthrough faithful.

## Findings and evidence

| Priority | Finding | Evidence and consequence |
|---|---|---|
| 1 | Employee identity is absent from earning keys and history scope. | [Earning creation](../../sqlite_lab/payroll.py) lines 58–63 builds a tenant-global earning key. [Record history](../../sqlite_lab/records.py) lines 284–301 selects by earning ID without employee. Two employees using `BASIC-PAY`, revision 1 collide. Fix identity, history, validation, draft references and JSON snapshots together. |
| 1 | Other employee-owned key families need the same ownership audit. | Instruction, draft, control, review, resolution, application and employee-operation receipts omit the employee; settings already includes it. Exact slots require a coherent contract, not isolated display edits. Shared components remain tenant-owned. |
| 1 | Future-effective versions can leave no usable source for an earlier month. | `_source` in [payroll.py](../../sqlite_lab/payroll.py) selects newest authority before checking effective month. After adding a December revision, November rejects the earlier version as non-current and the future version as inapplicable. Reconcile effective-period selection with explicit replacement/disable semantics; do not revive a disabled source accidentally. |
| 1 | Cancellation is reversible and committed drafts still accept controls. | `set_draft_control` in [payroll.py](../../sqlite_lab/payroll.py) lines 149–154 lacks terminal-state checks. A disposable probe cancelled a draft, released it and committed it; a later hold on that posted draft was also accepted. The agreed operation contract makes cancellation terminal and restricts these controls to uncommitted drafts. |
| 2 | The connected HTML scenario omits later-month corrections and source evolution. | [demo.py](../../sqlite_lab/demo.py) follows one employee through one month and settlement. Closed record payloads do not express a correction's prior-result relationship. A new ordinary instruction alone does not demonstrate a linked subsequent-month adjustment. Earlier committed money must remain unchanged; after-exit correction stays in external accounting. |
| 2 | Organizational policy alternatives are not both demonstrated. | Commit supports fixed-draft authority and optional exact approval. There is no protected current-source reconciliation journey. Every hold/release increments control revision and therefore requires another matching approval when approval is required. Retaining approval versus requiring a fresh one is an upper-layer choice, not a universal L1 rule. |
| 2 | ELR arithmetic is demonstrated more completely than correspondence. | Obligations and allocations have exact references and balance caps. Authority/reporting compatibility is not represented. Commit's convenience outcome retains only one employer-liability entry even when several post. Show the full posted-liability set and supplied correspondence; do not invent an automatic allocation policy or tax rule. |
| 2 | Instruction-version replay fails before receipt lookup. | `add_instruction_version` in [payroll.py](../../sqlite_lab/payroll.py) lines 80–94 checks next revision before checking its existing receipt. An identical retry of revision 2 returns `instruction revision is not next`. This is a concrete replay inconsistency to cover when the instruction lifecycle is reconciled. |

The relevant accepted boundaries are in Core's
[operation contracts](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/eb22521/docs/payroll/handbook/payroll-operation-contracts.md),
[payroll policy](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/eb22521/docs/payroll/handbook/hrms-payroll-policy.md),
[calculation boundary](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/eb22521/docs/payroll/handbook/calculation-boundary.md),
and [worked scenarios](https://github.com/agentlabs-poc/agentlabs-hrms-core/blob/eb22521/docs/payroll/handbook/payroll-scenarios.md).
Those chapters retain some older terminology; the current three-ledger and 123
Architecture decisions supersede that terminology. Neither mandatory origin tracing
nor mandatory reconciliation for every commit is reinstated by this review.

## Executed probes

These ran through named operations in temporary SQLite databases, without editing
source or retained evidence:

| Probe | Observed outcome |
|---|---|
| E101 and E102 use the same earning ID and revision | `UNIQUE constraint failed: payroll_l1_records.tenant, payroll_l1_records.key` |
| November draft uses revision 1 after December-effective revision 2 exists | `source is not current authority` |
| November draft uses that December-effective revision 2 | `earning outside effective period` |
| Cancel draft, release cancellation, commit | `committed` |
| Put committed draft on hold | Accepted |
| Repeat the same instruction revision-2 request | `instruction revision is not next` |

## What already aligns

The current code preserves immutable source, draft and posted rows; binds posted
money to exact draft fields; records commit, instruction applications and receipt
atomically; distinguishes monthly and one-time consumption; associates payroll by
employee/month without imposing an ID-generation algorithm; includes employer
contribution in both gross and deductions; and retains obligations, remittance
proof and partial-allocation balances. These strengths must survive corrections.
The existing tests prove specific cases of these properties, not the whole handbook.

## Proposed finite simulation checkpoints

1. **Canonical contract:** one table/record/owner/key-slot map for every displayed
   kind. Employee keys, revision identity, payload agreement and references must
   be explicit. Preserve existing earning IDs unless a separate decision removes
   them. Settle future-effective replacement semantics before changing selection.
2. **Sources and ownership:** two employees, reusing a local earning ID to expose
   accidental tenant-global identity. Basic/HRA remain shared definitions with
   different employee amounts. The manager supplies a monthly allowance, a
   finite loan, a one-time earning and a one-time deduction. Calculation inputs
   are illustrative supplied amounts, not hardcoded statutory formulas.
3. **Draft and commit:** show unchanged snapshot acceptance and the optional
   reconcile/rebuild branch, hold/exclude/release, terminal cancellation, retry
   and exact employee commit. Keep organizational sequencing in the consuming
   layer. Do not create a Layer-1 batch operation.
4. **Across months:** show a replacement earning, the five-month loan from
   October through February and exclusion in March, one-time consumption, and a
   linked correction in a subsequent payroll month. Old payroll and references
   remain stable throughout. Do not add catch-up or installment-extension policy.
5. **Employer liability:** enumerate all liability-bearing posted lines, retain
   supplied authority/correspondence information, and show outstanding, partial
   settlement, one remittance allocated across obligations, and final closure.
   General accounting and annual certificate issuance remain outside this demo.
6. **Storage projection and evidence:** keep canonical JSON intact; demonstrate
   its decoded slots, then prove the SQLite physical projection separately.
   Verify duplicate rejection, escaped identities, references and relevant query
   plans before measuring speed. Regenerate snapshots, mind map and diagrams from
   the corrected actual flow; do not hand-edit displayed monetary history.

These checkpoints are a proposed execution sequence, not blanket acceptance of
new schemas or organizational rules. The immediate outcome of this study is a
coherent correction scope. Implementation remains paused for review of this picture.
