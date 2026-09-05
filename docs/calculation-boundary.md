# Calculation and the payroll core

**PAY-ARCH-001 / PAY-Q-011 — agreed. User approved the explained boundary.** This begins the
horizontal pass through high-impact areas requested under PAY-PROCESS-006.
It draws on the existing lab's separation of ledger operations from its
higher-order preparation code; it does not select a new service architecture.

PAY-CORE-008/009/010 clarify this boundary: the producing layer determines
business source intent; payroll uses applicable facts at run time; source
tracing is not mandatory in payroll core. Existing application guards and
protected reconciliation remain distinct controls.

## Responsibility split

| Responsibility | Agreed owner |
|---|---|
| Preserve source records and identity, with the agreed applicability and instruction-use semantics | Payroll core |
| Apply business calculation rules to those sources and produce proposed earning/deduction amounts | Higher-order calculation logic |
| Create a complete fixed draft with sufficient basis for the agreed reconciliation | Payroll core, accepting the calculation result through its governed boundary |
| Review and accept the proposed result | Authorized review/approval workflow; exact role separation remains a later horizontal topic |
| Enforce lifecycle, reconcile the draft's basis, prevent duplicate applications, and commit monetary entries | Payroll core |
| Preserve posted history and expose entries and their summaries for downstream use | Payroll core |

Higher-order calculation logic can be a module in the same application. The
logical boundary does not require a network service, plugin system, particular
language, or a separate deployment.

The core can calculate sums, check amount representation, and enforce ledger
invariants. Those operations are different from deciding a business formula
such as how salary is prorated or how a particular statutory deduction is
calculated. The agreement keeps the latter rules in calculation logic while
retaining core control over the creation and posting of monetary records.

## Rationale

The five core stores describe sources and monetary lifecycle independently of
the particular formula producing an earning or deduction. Keeping business
calculation separate lets the same ledger model accommodate different rules
and instructions without adding a new ledger primitive for every use case.

The user's loan example fits this boundary: higher-order logic determines the
repayment arrangement and produces an appropriate finite standing instruction.
The core represents its lifetime, monthly application, draft effect, and posted
history. It need not become a loan-servicing subsystem to do so.

At the same time, calculation output is a proposal. It cannot bypass the core's
approval, reconciliation, application, or commit rules merely because it came
from trusted software. Source consistency and duplicate prevention also do not
by themselves prove a business formula is correct. Calculation correctness and
the evidence needed to review it remain responsibilities to make explicit.

## Existing code and an example

Source: lab revision `737465d5e27888518018e9b1f28f75fcfcac0139`,
[main.ts](../src/main.ts), particularly `preparePayrollReport`,
`fireDraftPayroll`, `appendDraft`, and `commitDraft`.

`preparePayrollReport` reads salary and instruction sources, copies some amounts,
and derives another deduction using a hardcoded demo rule. It produces a query
preview. `fireDraftPayroll` materializes its rows into a draft; ledger operations
then seal, approve, and commit. The demo formula is source evidence, not a
statutory recommendation. The mutable open draft and incomplete validation are
already recorded implementation gaps against later agreements.

Illustrative case: calculation logic derives a deduction amount from the
applicable inputs. The core receives that proposed amount; PAY-CORE-010 does not require
source/evidence links on the monetary entry. It holds it in the fixed draft, subjects it to the
approval flow, and reconciles before posting. A replacement calculator must
use the same monetary lifecycle even if its formula differs.

Counterexample: calculation logic directly inserts a posted deduction and marks
an instruction used, skipping draft approval or source reconciliation. Another
counterexample: the core silently recalculates with a changed business rule
during commit and posts amounts different from the reviewed draft.

## Scope of this decision

This decision establishes responsibilities. It does not settle calculator
interfaces, rule languages, policy-version encoding, execution evidence format,
algorithm validation, or the list of payroll formulas. Dependency capture and
validation must eventually satisfy PAY-CORE-006-C; those details stay parked
until the major boundaries are covered.

**PAY-Q-011 — approved:** Calculation logic produces business amounts; the core
owns source/ledger integrity, draft/approval lifecycle, reconciliation, and
commit for every producer.

---

The following horizontal branch, [ledger ownership and the unit of work](ledger-ownership.md),
is now agreed under PAY-Q-012. See the [roadmap](handbook-roadmap.md) for the current proposal.
