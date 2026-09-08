PRAGMA foreign_keys = ON;

CREATE TABLE payroll_l1_records (
    tenant TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL CHECK (json_valid(value) AND json_type(value) = 'object'),
    ts TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('enabled', 'disabled', 'deleted')),
    PRIMARY KEY (tenant, key)
);

CREATE TABLE payroll_l2_records (
    tenant TEXT NOT NULL,
    key TEXT NOT NULL,
    value TEXT NOT NULL CHECK (json_valid(value) AND json_type(value) = 'object'),
    ts TEXT NOT NULL,
    state TEXT NOT NULL CHECK (state IN ('enabled', 'disabled', 'deleted')),
    PRIMARY KEY (tenant, key)
);

CREATE INDEX l1_subject_revision
ON payroll_l1_records (
    tenant,
    json_extract(value, '$.component_id'),
    CAST(json_extract(value, '$.revision') AS INTEGER) DESC
)
WHERE key LIKE 'payroll.component:%';

CREATE INDEX l1_receipt_replay
ON payroll_l1_records (
    tenant,
    json_extract(value, '$.executor'),
    json_extract(value, '$.operation'),
    json_extract(value, '$.subject_id'),
    json_extract(value, '$.idempotency_key')
)
WHERE key LIKE 'payroll.operation.receipt:%';

CREATE UNIQUE INDEX l1_monthly_application_once
ON payroll_l1_records (
    tenant,
    json_extract(value, '$.instruction_id'),
    json_extract(value, '$.employee_id'),
    json_extract(value, '$.payroll_month')
)
WHERE key LIKE 'payroll.instruction.application:%'
  AND json_extract(value, '$.cadence') = 'monthly';

CREATE UNIQUE INDEX l1_one_time_application_once
ON payroll_l1_records (
    tenant,
    json_extract(value, '$.instruction_id'),
    json_extract(value, '$.employee_id')
)
WHERE key LIKE 'payroll.instruction.application:%'
  AND json_extract(value, '$.cadence') = 'one_time';

CREATE INDEX l1_application_reverse
ON payroll_l1_records (
    tenant,
    json_extract(value, '$.instruction_id'),
    json_extract(value, '$.employee_id'),
    json_extract(value, '$.payroll_month')
)
WHERE key LIKE 'payroll.instruction.application:%';

CREATE INDEX l2_settings_effective
ON payroll_l2_records (
    tenant,
    json_extract(value, '$.employee_id'),
    json_extract(value, '$.effective_from') DESC,
    CAST(json_extract(value, '$.revision') AS INTEGER) DESC
)
WHERE key LIKE 'payroll.employee.settings:%';

CREATE TRIGGER l1_immutable_update BEFORE UPDATE ON payroll_l1_records
BEGIN SELECT RAISE(ABORT, 'L1 records are immutable'); END;
CREATE TRIGGER l1_immutable_delete BEFORE DELETE ON payroll_l1_records
BEGIN SELECT RAISE(ABORT, 'L1 records are immutable'); END;

CREATE TABLE payroll_instructions (
    tenant TEXT NOT NULL,
    instruction_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    cadence TEXT NOT NULL CHECK (cadence IN ('monthly', 'one_time')),
    start_month TEXT NOT NULL,
    end_month TEXT,
    PRIMARY KEY (tenant, instruction_id)
);

CREATE TABLE payroll_instruction_versions (
    tenant TEXT NOT NULL,
    instruction_version_id TEXT NOT NULL,
    instruction_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    component_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
    PRIMARY KEY (tenant, instruction_version_id),
    UNIQUE (tenant, instruction_id, revision),
    FOREIGN KEY (tenant, instruction_id)
      REFERENCES payroll_instructions(tenant, instruction_id)
);

CREATE TABLE payroll_calculations (
    tenant TEXT NOT NULL,
    calculation_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    payroll_month TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('draft', 'committed')),
    PRIMARY KEY (tenant, calculation_id)
);

CREATE TABLE payroll_calculation_revisions (
    tenant TEXT NOT NULL,
    calculation_id TEXT NOT NULL,
    revision INTEGER NOT NULL CHECK (revision > 0),
    draft_id TEXT NOT NULL,
    candidate_identity TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    gross_minor INTEGER NOT NULL CHECK (gross_minor >= 0),
    deductions_minor INTEGER NOT NULL CHECK (deductions_minor >= 0),
    net_minor INTEGER NOT NULL CHECK (net_minor = gross_minor - deductions_minor),
    PRIMARY KEY (tenant, calculation_id, revision),
    UNIQUE (tenant, draft_id),
    FOREIGN KEY (tenant, calculation_id)
      REFERENCES payroll_calculations(tenant, calculation_id)
);

CREATE TABLE payroll_draft_entries (
    tenant TEXT NOT NULL,
    draft_id TEXT NOT NULL,
    entry_id TEXT NOT NULL,
    component_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('earning', 'deduction', 'employer_expense', 'employer_liability')),
    amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
    instruction_version_id TEXT,
    PRIMARY KEY (tenant, draft_id, entry_id),
    FOREIGN KEY (tenant, draft_id)
      REFERENCES payroll_calculation_revisions(tenant, draft_id),
    FOREIGN KEY (tenant, instruction_version_id)
      REFERENCES payroll_instruction_versions(tenant, instruction_version_id)
);

CREATE TABLE payroll_ledger_entries (
    tenant TEXT NOT NULL,
    ledger_entry_id TEXT NOT NULL,
    draft_id TEXT NOT NULL,
    employee_id TEXT NOT NULL,
    payroll_month TEXT NOT NULL,
    component_id TEXT NOT NULL,
    direction TEXT NOT NULL CHECK (direction IN ('earning', 'deduction', 'employer_contribution')),
    amount_minor INTEGER NOT NULL CHECK (amount_minor >= 0),
    PRIMARY KEY (tenant, ledger_entry_id),
    FOREIGN KEY (tenant, draft_id)
      REFERENCES payroll_calculation_revisions(tenant, draft_id)
);

CREATE TABLE payroll_statutory_obligations (
    tenant TEXT NOT NULL,
    obligation_id TEXT NOT NULL,
    ledger_entry_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    PRIMARY KEY (tenant, obligation_id),
    FOREIGN KEY (tenant, ledger_entry_id)
      REFERENCES payroll_ledger_entries(tenant, ledger_entry_id)
);

CREATE TABLE payroll_statutory_remittances (
    tenant TEXT NOT NULL,
    remittance_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    PRIMARY KEY (tenant, remittance_id)
);

CREATE TABLE payroll_statutory_allocations (
    tenant TEXT NOT NULL,
    allocation_id TEXT NOT NULL,
    obligation_id TEXT NOT NULL,
    remittance_id TEXT NOT NULL,
    amount_minor INTEGER NOT NULL CHECK (amount_minor > 0),
    PRIMARY KEY (tenant, allocation_id),
    FOREIGN KEY (tenant, obligation_id)
      REFERENCES payroll_statutory_obligations(tenant, obligation_id),
    FOREIGN KEY (tenant, remittance_id)
      REFERENCES payroll_statutory_remittances(tenant, remittance_id)
);

CREATE TRIGGER ledger_entries_immutable_update BEFORE UPDATE ON payroll_ledger_entries
BEGIN SELECT RAISE(ABORT, 'posted entries are immutable'); END;
CREATE TRIGGER ledger_entries_immutable_delete BEFORE DELETE ON payroll_ledger_entries
BEGIN SELECT RAISE(ABORT, 'posted entries are immutable'); END;
CREATE TRIGGER calculation_revisions_immutable_update BEFORE UPDATE ON payroll_calculation_revisions
BEGIN SELECT RAISE(ABORT, 'draft revisions are immutable'); END;
CREATE TRIGGER calculation_revisions_immutable_delete BEFORE DELETE ON payroll_calculation_revisions
BEGIN SELECT RAISE(ABORT, 'draft revisions are immutable'); END;
CREATE TRIGGER draft_entries_immutable_update BEFORE UPDATE ON payroll_draft_entries
BEGIN SELECT RAISE(ABORT, 'draft entries are immutable'); END;
CREATE TRIGGER draft_entries_immutable_delete BEFORE DELETE ON payroll_draft_entries
BEGIN SELECT RAISE(ABORT, 'draft entries are immutable'); END;
CREATE TRIGGER instructions_immutable_update BEFORE UPDATE ON payroll_instructions
BEGIN SELECT RAISE(ABORT, 'instructions are immutable'); END;
CREATE TRIGGER instructions_immutable_delete BEFORE DELETE ON payroll_instructions
BEGIN SELECT RAISE(ABORT, 'instructions are immutable'); END;
CREATE TRIGGER instruction_versions_immutable_update BEFORE UPDATE ON payroll_instruction_versions
BEGIN SELECT RAISE(ABORT, 'instruction versions are immutable'); END;
CREATE TRIGGER instruction_versions_immutable_delete BEFORE DELETE ON payroll_instruction_versions
BEGIN SELECT RAISE(ABORT, 'instruction versions are immutable'); END;
CREATE TRIGGER obligations_immutable_update BEFORE UPDATE ON payroll_statutory_obligations
BEGIN SELECT RAISE(ABORT, 'obligations are immutable'); END;
CREATE TRIGGER obligations_immutable_delete BEFORE DELETE ON payroll_statutory_obligations
BEGIN SELECT RAISE(ABORT, 'obligations are immutable'); END;
CREATE TRIGGER remittances_immutable_update BEFORE UPDATE ON payroll_statutory_remittances
BEGIN SELECT RAISE(ABORT, 'remittances are immutable'); END;
CREATE TRIGGER remittances_immutable_delete BEFORE DELETE ON payroll_statutory_remittances
BEGIN SELECT RAISE(ABORT, 'remittances are immutable'); END;
CREATE TRIGGER allocations_immutable_update BEFORE UPDATE ON payroll_statutory_allocations
BEGIN SELECT RAISE(ABORT, 'allocations are immutable'); END;
CREATE TRIGGER allocations_immutable_delete BEFORE DELETE ON payroll_statutory_allocations
BEGIN SELECT RAISE(ABORT, 'allocations are immutable'); END;
