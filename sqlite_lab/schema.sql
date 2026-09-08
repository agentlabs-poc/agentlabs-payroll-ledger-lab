PRAGMA foreign_keys = ON;

CREATE TABLE payroll_l1_records (
 tenant TEXT NOT NULL, key TEXT NOT NULL,
 value TEXT NOT NULL CHECK(json_valid(value) AND json_type(value)='object'),
 ts TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('enabled','disabled','deleted')),
 PRIMARY KEY(tenant,key)
);
CREATE TABLE payroll_l2_records (
 tenant TEXT NOT NULL, key TEXT NOT NULL,
 value TEXT NOT NULL CHECK(json_valid(value) AND json_type(value)='object'),
 ts TEXT NOT NULL, state TEXT NOT NULL CHECK(state IN ('enabled','disabled','deleted')),
 PRIMARY KEY(tenant,key)
);

CREATE INDEX l1_component_revision ON payroll_l1_records(tenant,json_extract(value,'$.component_id'),CAST(json_extract(value,'$.revision') AS INTEGER) DESC) WHERE key LIKE 'payroll.component:%';
CREATE INDEX l1_earning_effective ON payroll_l1_records(tenant,json_extract(value,'$.employee_id'),json_extract(value,'$.earning_id'),CAST(json_extract(value,'$.revision') AS INTEGER) DESC,json_extract(value,'$.effective_from')) WHERE key LIKE 'payroll.earning:%';
CREATE UNIQUE INDEX l1_instruction_version ON payroll_l1_records(tenant,json_extract(value,'$.employee_id'),json_extract(value,'$.version_id')) WHERE key LIKE 'payroll.instruction:%';
CREATE INDEX l1_instruction_effective ON payroll_l1_records(tenant,json_extract(value,'$.employee_id'),json_extract(value,'$.instruction_id'),CAST(json_extract(value,'$.revision') AS INTEGER) DESC,json_extract(value,'$.effective_from')) WHERE key LIKE 'payroll.instruction:%';
CREATE INDEX l1_draft_employee_month ON payroll_l1_records(tenant,json_extract(value,'$.employee_id'),json_extract(value,'$.payroll_month')) WHERE key LIKE 'payroll.draft:%';
CREATE INDEX l1_receipt_replay ON payroll_l1_records(tenant,json_extract(value,'$.employee_id'),json_extract(value,'$.executor'),json_extract(value,'$.operation'),json_extract(value,'$.subject_id'),json_extract(value,'$.idempotency_key')) WHERE key LIKE 'payroll.operation.receipt:%';
CREATE UNIQUE INDEX l1_monthly_application_once ON payroll_l1_records(tenant,json_extract(value,'$.instruction_id'),json_extract(value,'$.employee_id'),json_extract(value,'$.payroll_month')) WHERE key LIKE 'payroll.instruction.application:%' AND json_extract(value,'$.cadence')='monthly';
CREATE UNIQUE INDEX l1_one_time_application_once ON payroll_l1_records(tenant,json_extract(value,'$.instruction_id'),json_extract(value,'$.employee_id')) WHERE key LIKE 'payroll.instruction.application:%' AND json_extract(value,'$.cadence')='one_time';
CREATE INDEX l1_application_reverse ON payroll_l1_records(tenant,json_extract(value,'$.instruction_id'),json_extract(value,'$.employee_id'),json_extract(value,'$.payroll_month')) WHERE key LIKE 'payroll.instruction.application:%';
CREATE INDEX l2_settings_effective ON payroll_l2_records(tenant,json_extract(value,'$.employee_id'),json_extract(value,'$.effective_from') DESC,CAST(json_extract(value,'$.revision') AS INTEGER) DESC) WHERE key LIKE 'payroll.employee.settings:%';

CREATE TRIGGER component_code_scope BEFORE INSERT ON payroll_l1_records
WHEN NEW.key LIKE 'payroll.component:%' AND EXISTS(SELECT 1 FROM payroll_l1_records old WHERE old.tenant=NEW.tenant AND old.key LIKE 'payroll.component:%' AND json_extract(old.value,'$.country_code')=json_extract(NEW.value,'$.country_code') AND json_extract(old.value,'$.code')=json_extract(NEW.value,'$.code') AND json_extract(old.value,'$.component_id')<>json_extract(NEW.value,'$.component_id'))
BEGIN SELECT RAISE(ABORT,'component code conflicts in tenant/country scope'); END;
CREATE TRIGGER component_identity_stable BEFORE INSERT ON payroll_l1_records
WHEN NEW.key LIKE 'payroll.component:%' AND EXISTS(SELECT 1 FROM payroll_l1_records old WHERE old.tenant=NEW.tenant AND old.key LIKE 'payroll.component:%' AND json_extract(old.value,'$.component_id')=json_extract(NEW.value,'$.component_id') AND (json_extract(old.value,'$.code')<>json_extract(NEW.value,'$.code') OR json_extract(old.value,'$.kind')<>json_extract(NEW.value,'$.kind') OR json_extract(old.value,'$.country_code')<>json_extract(NEW.value,'$.country_code') OR CASE WHEN json_extract(old.value,'$.kind')='employer_contribution' THEN 1 ELSE COALESCE(json_extract(old.value,'$.authority_payable'),0) END<>CASE WHEN json_extract(NEW.value,'$.kind')='employer_contribution' THEN 1 ELSE COALESCE(json_extract(NEW.value,'$.authority_payable'),0) END))
BEGIN SELECT RAISE(ABORT,'component identity fields changed'); END;
CREATE TRIGGER l1_immutable_update BEFORE UPDATE ON payroll_l1_records BEGIN SELECT RAISE(ABORT,'L1 records are immutable'); END;
CREATE TRIGGER l1_immutable_delete BEFORE DELETE ON payroll_l1_records BEGIN SELECT RAISE(ABORT,'L1 records are immutable'); END;

CREATE TABLE payroll_draft_ledger (
 tenant TEXT NOT NULL, draft_key TEXT NOT NULL, entry_id TEXT NOT NULL,
 employee_id TEXT NOT NULL, payroll_month TEXT NOT NULL, source_key TEXT NOT NULL,
 component_key TEXT NOT NULL, direction TEXT NOT NULL CHECK(direction IN ('earning','deduction','employer_expense','employer_liability')),
 amount_minor INTEGER NOT NULL CHECK(typeof(amount_minor)='integer' AND amount_minor>0), currency TEXT NOT NULL CHECK(currency='INR'),
 row_kind TEXT NOT NULL DEFAULT 'draft' CHECK(row_kind='draft'), PRIMARY KEY(tenant,draft_key,entry_id),
 FOREIGN KEY(tenant,draft_key) REFERENCES payroll_l1_records(tenant,key),
 FOREIGN KEY(tenant,source_key) REFERENCES payroll_l1_records(tenant,key),
 FOREIGN KEY(tenant,component_key) REFERENCES payroll_l1_records(tenant,key)
);
CREATE TRIGGER draft_refs_typed BEFORE INSERT ON payroll_draft_ledger
WHEN NEW.draft_key NOT LIKE 'payroll.draft:%' OR NEW.component_key NOT LIKE 'payroll.component:%' OR (NEW.source_key NOT LIKE 'payroll.earning:%' AND NEW.source_key NOT LIKE 'payroll.instruction:%')
BEGIN SELECT RAISE(ABORT,'draft reference type mismatch'); END;
CREATE TRIGGER draft_refs_exact BEFORE INSERT ON payroll_draft_ledger
WHEN NOT EXISTS(
 SELECT 1 FROM payroll_l1_records d
 JOIN payroll_l1_records s ON s.tenant=d.tenant AND s.key=NEW.source_key
 JOIN payroll_l1_records c ON c.tenant=d.tenant AND c.key=NEW.component_key
 WHERE d.tenant=NEW.tenant AND d.key=NEW.draft_key
 AND json_extract(d.value,'$.employee_id')=NEW.employee_id
 AND json_extract(d.value,'$.payroll_month')=NEW.payroll_month
 AND (EXISTS(SELECT 1 FROM json_each(d.value,'$.earning_keys') WHERE value=NEW.source_key)
      OR EXISTS(SELECT 1 FROM json_each(d.value,'$.instruction_keys') WHERE value=NEW.source_key))
 AND json_extract(s.value,'$.employee_id')=NEW.employee_id
 AND json_extract(s.value,'$.component_key')=NEW.component_key
 AND json_extract(s.value,'$.amount_minor')=NEW.amount_minor
 AND ((json_extract(c.value,'$.kind')='earning' AND NEW.direction='earning')
      OR (json_extract(c.value,'$.kind')='deduction' AND NEW.direction='deduction')
      OR (json_extract(c.value,'$.kind')='employer_contribution' AND NEW.direction IN ('employer_expense','employer_liability')))
)
BEGIN SELECT RAISE(ABORT,'draft row must match exact draft and source'); END;
CREATE INDEX draft_employee_month ON payroll_draft_ledger(tenant,employee_id,payroll_month,draft_key);
CREATE TRIGGER draft_immutable_update BEFORE UPDATE ON payroll_draft_ledger BEGIN SELECT RAISE(ABORT,'draft ledger is immutable'); END;
CREATE TRIGGER draft_immutable_delete BEFORE DELETE ON payroll_draft_ledger BEGIN SELECT RAISE(ABORT,'draft ledger is immutable'); END;

CREATE TABLE payroll_ledger (
 tenant TEXT NOT NULL, ledger_entry_id TEXT NOT NULL, draft_key TEXT NOT NULL, draft_entry_id TEXT NOT NULL,
 employee_id TEXT NOT NULL, payroll_month TEXT NOT NULL, source_key TEXT NOT NULL, component_key TEXT NOT NULL,
 direction TEXT NOT NULL CHECK(direction IN ('earning','deduction','employer_expense','employer_liability')),
 amount_minor INTEGER NOT NULL CHECK(typeof(amount_minor)='integer' AND amount_minor>0), currency TEXT NOT NULL CHECK(currency='INR'),
 row_kind TEXT NOT NULL DEFAULT 'posted' CHECK(row_kind='posted'), PRIMARY KEY(tenant,ledger_entry_id),
 FOREIGN KEY(tenant,draft_key,draft_entry_id) REFERENCES payroll_draft_ledger(tenant,draft_key,entry_id),
 FOREIGN KEY(tenant,draft_key) REFERENCES payroll_l1_records(tenant,key),
 FOREIGN KEY(tenant,source_key) REFERENCES payroll_l1_records(tenant,key),
 FOREIGN KEY(tenant,component_key) REFERENCES payroll_l1_records(tenant,key)
);
CREATE INDEX posted_employee_month ON payroll_ledger(tenant,employee_id,payroll_month,draft_key);
CREATE TRIGGER posted_matches_draft BEFORE INSERT ON payroll_ledger
WHEN NOT EXISTS(
 SELECT 1 FROM payroll_draft_ledger d
 WHERE d.tenant=NEW.tenant AND d.draft_key=NEW.draft_key AND d.entry_id=NEW.draft_entry_id
 AND d.employee_id=NEW.employee_id AND d.payroll_month=NEW.payroll_month
 AND d.source_key=NEW.source_key AND d.component_key=NEW.component_key
 AND d.direction=NEW.direction AND d.amount_minor=NEW.amount_minor AND d.currency=NEW.currency
)
BEGIN SELECT RAISE(ABORT,'posted row must exactly match draft row'); END;
CREATE TRIGGER posted_immutable_update BEFORE UPDATE ON payroll_ledger BEGIN SELECT RAISE(ABORT,'payroll ledger is immutable'); END;
CREATE TRIGGER posted_immutable_delete BEFORE DELETE ON payroll_ledger BEGIN SELECT RAISE(ABORT,'payroll ledger is immutable'); END;

CREATE TABLE payroll_employer_liability_ledger (
 tenant TEXT NOT NULL, entry_id TEXT NOT NULL, row_kind TEXT NOT NULL CHECK(row_kind IN ('obligation','remittance','allocation')),
 amount_minor INTEGER NOT NULL CHECK(typeof(amount_minor)='integer' AND amount_minor>0),
 employer_id TEXT NOT NULL, authority_id TEXT NOT NULL, currency TEXT NOT NULL,
 reporting_period TEXT, posted_liability_entry_id TEXT, obligation_entry_id TEXT, remittance_entry_id TEXT, proof_ref TEXT,
 PRIMARY KEY(tenant,entry_id), FOREIGN KEY(tenant,posted_liability_entry_id) REFERENCES payroll_ledger(tenant,ledger_entry_id),
 FOREIGN KEY(tenant,obligation_entry_id) REFERENCES payroll_employer_liability_ledger(tenant,entry_id),
 FOREIGN KEY(tenant,remittance_entry_id) REFERENCES payroll_employer_liability_ledger(tenant,entry_id),
 CHECK((row_kind='obligation' AND posted_liability_entry_id IS NOT NULL AND obligation_entry_id IS NULL AND remittance_entry_id IS NULL AND proof_ref IS NULL)
 OR (row_kind='remittance' AND posted_liability_entry_id IS NULL AND obligation_entry_id IS NULL AND remittance_entry_id IS NULL AND typeof(proof_ref)='text' AND length(trim(proof_ref))>0)
 OR (row_kind='allocation' AND posted_liability_entry_id IS NULL AND obligation_entry_id IS NOT NULL AND remittance_entry_id IS NOT NULL AND proof_ref IS NULL))
);
CREATE UNIQUE INDEX one_obligation_per_liability ON payroll_employer_liability_ledger(tenant,posted_liability_entry_id) WHERE row_kind='obligation';
CREATE INDEX liability_allocations ON payroll_employer_liability_ledger(tenant,obligation_entry_id) WHERE row_kind='allocation';
CREATE TRIGGER obligation_matches_posted BEFORE INSERT ON payroll_employer_liability_ledger
WHEN NEW.row_kind='obligation' AND NOT EXISTS(SELECT 1 FROM payroll_ledger p JOIN payroll_l1_records c ON c.tenant=p.tenant AND c.key=p.component_key WHERE p.tenant=NEW.tenant AND p.ledger_entry_id=NEW.posted_liability_entry_id AND (p.direction='employer_liability' OR (p.direction='deduction' AND json_extract(c.value,'$.authority_payable')=1)) AND p.amount_minor=NEW.amount_minor)
BEGIN SELECT RAISE(ABORT,'obligation must match posted payable'); END;
CREATE TRIGGER allocation_refs_typed BEFORE INSERT ON payroll_employer_liability_ledger
WHEN NEW.row_kind='allocation' AND (NOT EXISTS(SELECT 1 FROM payroll_employer_liability_ledger o WHERE o.tenant=NEW.tenant AND o.entry_id=NEW.obligation_entry_id AND o.row_kind='obligation') OR NOT EXISTS(SELECT 1 FROM payroll_employer_liability_ledger r WHERE r.tenant=NEW.tenant AND r.entry_id=NEW.remittance_entry_id AND r.row_kind='remittance'))
BEGIN SELECT RAISE(ABORT,'allocation reference type mismatch'); END;
CREATE TRIGGER liability_immutable_update BEFORE UPDATE ON payroll_employer_liability_ledger BEGIN SELECT RAISE(ABORT,'employer liability ledger is immutable'); END;
CREATE TRIGGER liability_immutable_delete BEFORE DELETE ON payroll_employer_liability_ledger BEGIN SELECT RAISE(ABORT,'employer liability ledger is immutable'); END;
