# Karnataka payroll demonstration

The CLI consumer example represents an illustrative Bengaluru employee for
November 2026 (tax year 2026–27). It is an executable payroll example, not a
complete tax, eligibility or compliance engine.

## Layers and canonical records

The user clarified that tax-regime selection is an **L2 candidate**. It remains
inside `payroll.employee.settings:<employee_id>:<revision>` in
`payroll_l2_records`, as optional validated data:

```json
{
  "tax": {
    "jurisdiction": "IN",
    "financial_year": "2026-27",
    "regime": "new"
  }
}
```

`old` is the other regime value. The surrounding settings value still carries
employee identity, revision, effective month, policy reference and locale.
This object is not a new L1 record type. The L3 consumer script supplies the
annual projection and computes its illustrative withholding. L1 accepts the
result as a canonical employee instruction; it contains no Indian tax formula.

| Component code | L1 component kind | November amount (INR) |
|---|---|---:|
| BASIC | earning | 75,000 |
| HRA | earning | 30,000 |
| SPECIAL_ALLOWANCE | earning | 45,000 |
| EPF_EMPLOYEE | deduction, authority payable | 1,800 |
| EPF_EMPLOYER | employer contribution | 550 |
| EPS_EMPLOYER | employer contribution | 1,250 |
| PROFESSIONAL_TAX_KA | deduction, authority payable | 200 |
| INCOME_TAX_TDS | deduction, authority payable | Selected projection below |
| LOAN | deduction, not authority payable | 2,000 |
| BONUS | earning, one-time instruction | 5,000 |

Components define meaning. Employee amounts and applicability belong to
employee-scoped earnings/instructions. The loan expires after March 2027.

## Fixture assumptions and calculation

The supplied fixture describes a resident Indian employee under 60, working in
Karnataka for the full year. EPF/EPS membership is already established and EPS
eligibility is supplied; contribution wages are capped at ₹15,000 with no higher
voluntary contribution. Employee EPF is ₹1,800; the ₹1,800 employer share is split
between EPF ₹550 and EPS ₹1,250. This is a member-specific scenario, not a claim
that every employee has the same eligibility. Establishment-level EDLI/admin
charges and other compliance obligations are outside this employee walkthrough.

Annual cash salary is ₹18,00,000 plus one ₹5,000 bonus. No HRA exemption, other
income or additional deduction is claimed. The loan is not a tax deduction.
Employer PF/EPS is included in the domain's payroll gross but is not treated as
cash taxable salary in this capped-contribution example.

The old-regime projection deducts standard deduction ₹50,000, employee EPF
₹21,600 and paid/projected annual profession tax ₹2,500. The new-regime projection
deducts only standard deduction ₹75,000. Neither projection attracts surcharge
or rebate at this income. Cess is 4%. Annual tax ignores paise then rounds to the
nearest ₹10. Prior withholding is an explicit illustrative input: seven monthly
instalments of annual tax / 12, each rounded to paise. November withholding spreads
the remaining projected tax across the five remaining months, rounded to paise.
Later payrolls must reconcile any remaining rounding amount; no past payroll rows
are fabricated to represent these supplied prior-year-to-date facts.

| Projection | New regime | Old regime |
|---|---:|---:|
| Annual cash salary including bonus | ₹18,05,000 | ₹18,05,000 |
| Annual taxable income | ₹17,30,000 | ₹17,30,900 |
| Tax before cess | ₹1,46,000 | ₹3,31,770 |
| Annual tax after cess and rounding | ₹1,51,840 | ₹3,45,040 |
| Supplied prior seven-month TDS | ₹88,573.31 | ₹2,01,273.31 |
| November TDS | ₹12,653.34 | ₹28,753.34 |
| November domain gross, including employer contribution | ₹1,56,800 | ₹1,56,800 |
| November deductions, including employer-contribution balancing | ₹18,453.34 | ₹34,553.34 |
| November net | ₹1,38,346.66 | ₹1,22,246.66 |
| Authority liability outstanding before payment/allocation | ₹16,453.34 | ₹32,553.34 |

## Liability invariant

`authority_payable` is a stable optional component property, orthogonal to the
existing component kind. Employee PF/PT/TDS remain single deduction rows: gross
is not increased and net is reduced once. Employer contributions retain their
expense/liability pair. Ordinary loan deductions are not authority payables.

The generic `payable_entry_ids` commit result includes employer liabilities and
flagged employee deductions. The L3 script creates one obligation per exact posted
entry, with EPFO, Karnataka Commercial Taxes or Income Tax as the supplied
recipient authority. The existing `employer_liability_entry_ids` subset remains
for compatibility. No new monetary ledger or physical table is required.

Default execution leaves all obligations outstanding. `--settle` supplies demo
remittance proofs and explicit allocations; only allocated payments close the
obligations. These are simulated proofs, not actual government payments.

## Commands

```sh
python3 -m sqlite_lab.cli_demo --db /tmp/karnataka-new.sqlite --tax-regime new --step
python3 -m sqlite_lab.cli_demo --db /tmp/karnataka-old.sqlite --tax-regime old --step
python3 -m sqlite_lab.cli_demo --db /tmp/karnataka-settled.sqlite --tax-regime new --settle
```

Use a fresh database path for each independent run. The choices are supplied to
an L3 consumer example; they are not an L1 batch or tax-calculation API.

## Source basis

- [Karnataka Commercial Taxes FAQ](https://ptax.karnataka.gov.in/ptemployer/FAQ): salary threshold/exemptions, February PT ₹300 instead of ₹200, and work-state relevance. The fixture uses November ₹200 and a full-year ₹2,500 projection.
- [Income-tax Act 2025 as amended by Finance Act 2026](https://www.incometaxindia.gov.in/documents/d/guest/income_tax_act_2025_as_amended_by_fa_act_2026-pdf): section 19 salary deductions, section 202 new-regime rates/exclusions, section 516 rounding.
- [Income Tax Department salary guidance](https://www.incometax.gov.in/iec/foportal/help/individual/return-applicable-1): old-regime ordinary slab structure and cess. Its AY 2026–27 label is distinct from this example's tax year 2026–27.
- [Official Budget 2026 memorandum](https://www.indiabudget.gov.in/doc/memo.pdf): tax-year 2026–27 rate context. Do not substitute a budget proposal for final law in a production calculator.
- [EPFO contribution reference](https://www.epfindia.gov.in/site_docs/PDFs/MiscPDFs/ContributionRate.pdf) and [EPFO FAQ](https://www.epfindia.nic.in/site_en/FAQ.php): capped contribution/member applicability reference. Direct PDF retrieval was unavailable during this work; the example takes PF amounts and eligibility as supplied manager facts rather than implementing a statutory eligibility engine.

## Reasonable demo validation — 2026-09-09

Executed the real subprocess walkthrough for new unpaid, old unpaid and new
settled cases. All three produced the literal totals above, five payable entries,
held-commit rejection and identical commit replay. The runs took approximately
2.5–2.9 seconds on this local environment, including Python process startup;
these timings are not a production benchmark.

After adding natural aliases and config, reran the new-regime flow against an
initialized empty database. It retained ₹16,453.34 outstanding. Resetting that
populated database left all five canonical tables empty and preserved the config.
A separate unrelated SQLite database was refused and its existing row remained.
Help without config, natural component definition/read, config selection and the
first interactive settings prompt also passed. The six-month snapshot exporter
and HTML build still complete successfully. No broader regression campaign was run.
