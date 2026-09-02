import './styles.css';
import { jsPDF } from 'jspdf';

type HeadKind = 'earning' | 'deduction';
type DraftStatus = 'open' | 'sealed' | 'approved' | 'committed' | 'abandoned';
type ReferenceKind = 'salary' | 'exception' | 'payroll' | 'correction';
type ReferenceStatus = 'proposed' | 'draft' | 'sealed' | 'approved' | 'committed' | 'abandoned';
type InputMode = 'monthly_standing' | 'one_time';

interface LedgerReference {
  number: string;
  kind: ReferenceKind;
  status: ReferenceStatus;
  ledgerOwnerId: string;
  ledgerDate: string;
  period: string;
  root: string;
  corrects?: string;
}

interface Head {
  key: string;
  label: string;
  kind: HeadKind;
  effect: 'add' | 'subtract' | 'input';
  statutoryTag?: string;
}

interface Employee {
  id: string;
  name: string;
  ledgerOwnerId: string;
  ledgerDate: string;
  joinedOn: string;
  status: 'active';
}

interface SalaryEntry {
  id: string;
  reference: string;
  ledgerOwnerId: string;
  ledgerDate: string;
  head: string;
  amount: bigint;
  effectiveFrom: string;
  source: string;
}

interface Evidence {
  name: string;
  type: string;
  size: number;
  file: File;
}

interface PayrollInputEntry {
  id: string;
  reference: string;
  ledgerOwnerId: string;
  ledgerDate: string;
  type: string;
  key: string;
  value: string;
  amount?: bigint;
  period: string;
  approved: boolean;
  inputMode: InputMode;
  payrollHead?: string;
  effectiveFrom?: string;
  effectiveUntil?: string;
  applicablePeriod?: string;
  consumedBy?: string;
  sourceReference?: string;
}

interface ProofAttachment {
  id: string;
  ledgerOwnerId: string;
  uploadedAt: string;
  category: string;
  fiscalYear: string;
  status: 'submitted' | 'accepted';
  reviewedBy?: string;
  file: Evidence;
}

interface DraftEntry {
  id: string;
  head: string;
  amount: bigint;
  source: string;
  sourceReference: string;
  ledgerOwnerId: string;
  ledgerDate: string;
}

interface PreparationReport {
  queryId: string;
  ledgerOwnerId: string;
  asOf: string;
  period: string;
  reviewed: boolean;
  materialised: boolean;
  entries: DraftEntry[];
  checksum: string;
}

interface Draft {
  id: string;
  reference: string;
  revision: number;
  ledgerOwnerId: string;
  ledgerDate: string;
  period: string;
  status: DraftStatus;
  entries: DraftEntry[];
  hash: string;
}

interface PostedEntry extends DraftEntry {
  postedId: string;
  draftId: string;
  ledgerReference: string;
  adjustmentFor?: string;
}

interface PayslipSnapshot {
  id: string;
  ledgerReference: string;
  ledgerOwnerId: string;
  ledgerDate: string;
  entryIds: string[];
  ledgerHash: string;
  gross: bigint;
  deductions: bigint;
  net: bigint;
}

interface StatutoryLiabilityEntry {
  id: string;
  ledgerOwnerId: string;
  ledgerDate: string;
  statutoryTag: string;
  period: string;
  debit: bigint;
  credit: bigint;
  employeeId?: string;
  canonicalReference: string;
  payrollEntryId?: string;
  authorityReference?: string;
  bankReference?: string;
  attachmentReference?: string;
}

interface ReconciliationMatch {
  id: string;
  ledgerOwnerId: string;
  ledgerDate: string;
  statutoryTag: string;
  period: string;
  payrollCreditEntryId: string;
  challanDebitEntryId: string;
  amount: bigint;
}

interface Form16Snapshot {
  id: string;
  ledgerOwnerId: string;
  ledgerDate: string;
  fiscalYear: string;
  payrollReference: string;
  challanReferences: string[];
  grossSalary: bigint;
  taxDeducted: bigint;
  hash: string;
  status: 'incomplete';
  missingRequirements: string[];
}

const state = {
  employees: [] as Employee[],
  references: [] as LedgerReference[],
  heads: [] as Head[],
  salary: [] as SalaryEntry[],
  standingInputs: [] as PayrollInputEntry[],
  oneTimeInputs: [] as PayrollInputEntry[],
  proofAttachments: [] as ProofAttachment[],
  preparations: [] as PreparationReport[],
  drafts: [] as Draft[],
  posted: [] as PostedEntry[],
  payslips: [] as PayslipSnapshot[],
  statutoryLiabilities: [] as StatutoryLiabilityEntry[],
  reconciliationMatches: [] as ReconciliationMatch[],
  form16s: [] as Form16Snapshot[],
  log: [] as string[],
  counter: 1,
  referenceCounter: 1,
};

const app = document.querySelector<HTMLDivElement>('#app')!;

function next(prefix: string): string {
  return `${prefix}${state.counter++}`;
}

function createReference(kind: ReferenceKind, ledgerOwnerId: string, period: string, ledgerDate: string, corrects?: string): LedgerReference {
  const prefix = kind === 'salary' ? 'SAL' : kind === 'exception' ? 'EXC' : 'PAY';
  const number = `${prefix}-${String(state.referenceCounter++).padStart(6, '0')}`;
  const corrected = corrects ? state.references.find((reference) => reference.number === corrects) : undefined;
  const reference: LedgerReference = {
    number,
    kind,
    status: kind === 'payroll' || kind === 'correction' ? 'draft' : 'proposed',
    ledgerOwnerId,
    ledgerDate,
    period,
    root: corrected?.root || number,
  };
  if (corrects) reference.corrects = corrects;
  state.references.push(reference);
  return reference;
}

function reference(number: string): LedgerReference {
  const found = state.references.find((item) => item.number === number);
  if (!found) throw new Error(`ledger reference not found: ${number}`);
  return found;
}

function money(text: string): bigint {
  if (!/^-?(0|[1-9][0-9]*)\.[0-9]{2}$/.test(text)) {
    throw new Error(`money must be an exact decimal string: ${text}`);
  }
  const negative = text.startsWith('-');
  const raw = negative ? text.slice(1) : text;
  const [whole, fraction] = raw.split('.');
  const cents = BigInt(whole) * 100n + BigInt(fraction);
  return negative ? -cents : cents;
}

function formatMoney(cents: bigint): string {
  const negative = cents < 0n;
  const value = negative ? -cents : cents;
  return `${negative ? '-' : ''}${value / 100n}.${String(value % 100n).padStart(2, '0')}`;
}

function log(message: string): void {
  state.log.push(message);
  render();
  requestAnimationFrame(() => {
    const output = document.querySelector('.terminal-output');
    if (output) output.scrollTop = output.scrollHeight;
  });
}

function defineHead(key: string, label: string, kind: HeadKind, effect: Head['effect'], statutoryTag?: string): void {
  if (state.heads.some((head) => head.key === key)) throw new Error(`head already exists: ${key}`);
  state.heads.push({ key, label, kind, effect, statutoryTag });
}

function appendSalary(employee: string, head: string, amount: string, ledgerReference?: string): SalaryEntry {
  requireHead(head, 'earning');
  const assignedReference = ledgerReference || createReference('salary', employee, 'effective:2026-04-01', '2026-04-01').number;
  const entry = { id: next('S'), reference: assignedReference, ledgerOwnerId: employee, ledgerDate: '2026-04-01', head, amount: money(amount), effectiveFrom: '2026-04-01', source: 'offer-letter-demo' };
  state.salary.push(entry);
  return entry;
}

function appendPayrollInput(employee: string, type: string, key: string, value: string, amount: string, inputMode: InputMode, payrollHead: string, sourceReference?: string): PayrollInputEntry {
  const period = inputMode === 'monthly_standing' ? 'effective:2026-09' : '2026-09';
  const assignedReference = createReference('exception', employee, period, '2026-09-01');
  const entry: PayrollInputEntry = {
    id: next('X'), reference: assignedReference.number, ledgerOwnerId: employee, ledgerDate: assignedReference.ledgerDate,
    type, key, value, period: assignedReference.period, approved: false, inputMode, payrollHead, sourceReference,
  };
  if (inputMode === 'monthly_standing') entry.effectiveFrom = '2026-09';
  else entry.applicablePeriod = '2026-09';
  entry.amount = money(amount);
  (inputMode === 'monthly_standing' ? state.standingInputs : state.oneTimeInputs).push(entry);
  return entry;
}

function approveInput(id: string): void {
  const entry = [...state.standingInputs, ...state.oneTimeInputs].find((item) => item.id === id);
  if (!entry) throw new Error(`payroll input not found: ${id}`);
  entry.approved = true;
  reference(entry.reference).status = 'approved';
}

function submitProofAttachment(employee: string, file: File): ProofAttachment {
  const attachment: ProofAttachment = {
    id: next('ATT'), ledgerOwnerId: employee, uploadedAt: '2026-09-10', category: 'rent-proof', fiscalYear: '2026-27',
    status: 'submitted', file: { name: file.name, type: file.type || 'application/octet-stream', size: file.size, file },
  };
  state.proofAttachments.push(attachment);
  return attachment;
}

function createDraft(employee: string, period: string): Draft {
  const ledgerDate = monthEnd(period);
  const ledgerReference = createReference('payroll', employee, period, ledgerDate);
  const draft: Draft = { id: next('D'), reference: ledgerReference.number, revision: 1, ledgerOwnerId: employee, ledgerDate, period, status: 'open', entries: [], hash: '' };
  state.drafts.push(draft);
  refreshHash(draft);
  return draft;
}

function appendDraft(draftId: string, head: string, amount: string, source: string, sourceReference = 'manual'): DraftEntry {
  const draft = getDraft(draftId);
  if (draft.status !== 'open') throw new Error(`draft ${draftId} is ${draft.status}`);
  requireHead(head);
  const entry = { id: next('L'), head, amount: money(amount), source, sourceReference, ledgerOwnerId: draft.ledgerOwnerId, ledgerDate: draft.ledgerDate };
  draft.entries.push(entry);
  refreshHash(draft);
  return entry;
}

function sealDraft(id: string): void {
  const draft = getDraft(id);
  if (draft.status !== 'open' || draft.entries.length === 0) throw new Error('only a non-empty open draft can be sealed');
  draft.status = 'sealed';
  reference(draft.reference).status = 'sealed';
  refreshHash(draft);
}

function approveDraft(id: string): void {
  const draft = getDraft(id);
  if (draft.status !== 'sealed') throw new Error('only a sealed draft can be approved');
  draft.status = 'approved';
  reference(draft.reference).status = 'approved';
}

function commitDraft(id: string): void {
  const draft = getDraft(id);
  if (draft.status === 'committed') return;
  if (draft.status !== 'approved') throw new Error('only an approved draft can be committed');
  for (const entry of draft.entries) {
    state.posted.push({ ...entry, postedId: next('P'), draftId: draft.id, ledgerReference: draft.reference });
  }
  draft.status = 'committed';
  reference(draft.reference).status = 'committed';
  for (const input of state.oneTimeInputs) {
    if (draft.entries.some((entry) => entry.sourceReference === input.reference)) input.consumedBy = draft.reference;
  }
  createPayslipSnapshot(draft.reference);
  createStatutoryLiabilities(draft.reference);
}

function abandonDraft(id: string): void {
  const draft = getDraft(id);
  if (draft.status !== 'open' && draft.status !== 'sealed') throw new Error('only an uncommitted draft can be abandoned');
  draft.status = 'abandoned';
  reference(draft.reference).status = 'abandoned';
}

function carryAdjustmentToNextMonth(id: string, amount: string, ledgerDate = '2026-10-31'): void {
  const original = state.posted.find((entry) => entry.postedId === id);
  if (!original) throw new Error(`posted entry not found: ${id}`);
  if (state.posted.some((entry) => entry.adjustmentFor === id)) throw new Error(`next-month adjustment already exists for: ${id}`);
  const originalReference = reference(original.ledgerReference);
  const period = ledgerDate.slice(0, 7);
  const correctionRef = createReference('correction', original.ledgerOwnerId, period, ledgerDate, originalReference.number);
  correctionRef.status = 'committed';
  state.posted.push({
    id: next('L'), postedId: next('P'), draftId: 'next-month-adjustment', head: 'prior_period_recovery',
    amount: money(amount), source: `prior-period:${id}`, sourceReference: original.ledgerReference,
    ledgerReference: correctionRef.number, ledgerOwnerId: original.ledgerOwnerId, ledgerDate, adjustmentFor: id,
  });
  createPayslipSnapshot(correctionRef.number);
}

function monthEnd(period: string): string {
  if (!/^\d{4}-\d{2}$/.test(period)) throw new Error(`period must be YYYY-MM: ${period}`);
  const [year, month] = period.split('-').map(Number);
  return new Date(Date.UTC(year, month, 0)).toISOString().slice(0, 10);
}

function createPayslipSnapshot(ledgerReference: string): PayslipSnapshot {
  const existing = state.payslips.find((snapshot) => snapshot.ledgerReference === ledgerReference);
  if (existing) return existing;
  const entries = state.posted.filter((entry) => entry.ledgerReference === ledgerReference);
  if (!entries.length) throw new Error(`cannot snapshot empty ledger reference: ${ledgerReference}`);
  const summary = totals(entries);
  const ledgerHash = hashText(entries.map((entry) => `${entry.postedId}:${entry.head}:${entry.amount}:${entry.ledgerOwnerId}:${entry.ledgerDate}`).join('|'));
  const snapshot: PayslipSnapshot = {
    id: next('PS'), ledgerReference, ledgerOwnerId: entries[0].ledgerOwnerId, ledgerDate: entries[0].ledgerDate,
    entryIds: entries.map((entry) => entry.postedId), ledgerHash, ...summary,
  };
  state.payslips.push(snapshot);
  return snapshot;
}

function downloadPayslip(snapshotId: string): void {
  const snapshot = state.payslips.find((item) => item.id === snapshotId);
  if (!snapshot) throw new Error(`payslip snapshot not found: ${snapshotId}`);
  const entries = snapshot.entryIds.map((id) => state.posted.find((entry) => entry.postedId === id)).filter((entry): entry is PostedEntry => Boolean(entry));
  if (entries.length !== snapshot.entryIds.length) throw new Error(`payslip snapshot ${snapshotId} no longer resolves exactly`);

  const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
  pdf.setProperties({
    title: `Payslip ${snapshot.ledgerReference}`,
    subject: `Immutable payroll ledger snapshot ${snapshot.ledgerHash}`,
    author: 'Payroll Ledger Lab',
  });
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(20);
  pdf.text('PAYSLIP', 18, 22);
  pdf.setFontSize(10);
  pdf.setFont('helvetica', 'normal');
  pdf.text(`Payroll reference: ${snapshot.ledgerReference}`, 18, 32);
  pdf.text(`Ledger owner ID: ${snapshot.ledgerOwnerId}`, 18, 38);
  pdf.text(`Ledger date: ${snapshot.ledgerDate}`, 18, 44);
  pdf.text(`Snapshot ID: ${snapshot.id}`, 118, 32);
  pdf.text(`Snapshot hash: ${snapshot.ledgerHash}`, 118, 38);

  pdf.setDrawColor(90, 110, 100);
  pdf.line(18, 51, 192, 51);
  pdf.setFont('helvetica', 'bold');
  pdf.text('Entry', 18, 59);
  pdf.text('Component', 40, 59);
  pdf.text('Source', 98, 59);
  pdf.text('Amount (INR)', 192, 59, { align: 'right' });
  pdf.setFont('helvetica', 'normal');

  let y = 67;
  for (const entry of entries) {
    pdf.text(entry.postedId, 18, y);
    pdf.text(requireHead(entry.head).label, 40, y);
    pdf.text(entry.source.slice(0, 40), 98, y);
    pdf.text(formatMoney(entry.amount), 192, y, { align: 'right' });
    y += 7;
  }

  y += 3;
  pdf.line(118, y, 192, y);
  y += 8;
  pdf.text(`Gross earnings: INR ${formatMoney(snapshot.gross)}`, 192, y, { align: 'right' });
  y += 7;
  pdf.text(`Deductions: INR ${formatMoney(snapshot.deductions)}`, 192, y, { align: 'right' });
  y += 7;
  pdf.setFont('helvetica', 'bold');
  pdf.text(`Net: INR ${formatMoney(snapshot.net)}`, 192, y, { align: 'right' });

  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(8);
  pdf.text('This PDF is a rendering of the immutable ledger snapshot identified above.', 18, 278);
  pdf.text('The ledger reference, entry IDs and snapshot hash are the authoritative linkage.', 18, 283);
  pdf.save(`payslip-${snapshot.ledgerOwnerId}-${snapshot.ledgerDate}-${snapshot.ledgerReference}.pdf`);
}

function businessReference(prefix: string): string {
  return `${prefix}-${String(state.referenceCounter++).padStart(6, '0')}`;
}

function createStatutoryLiabilities(payrollReference: string): void {
  if (state.statutoryLiabilities.some((entry) => entry.canonicalReference === payrollReference && entry.credit > 0n)) return;
  const payroll = reference(payrollReference);
  const entries = state.posted.filter((entry) => entry.ledgerReference === payrollReference);
  for (const entry of entries.filter((item) => requireHead(item.head).kind === 'deduction')) {
    const statutoryTag = requireHead(entry.head).statutoryTag;
    if (!statutoryTag) continue;
    state.statutoryLiabilities.push({
      id: next('SL'), ledgerOwnerId: 'LEGAL-ENTITY-01', ledgerDate: payroll.ledgerDate, statutoryTag,
      period: payroll.period, debit: 0n, credit: -entry.amount, employeeId: entry.ledgerOwnerId,
      canonicalReference: payrollReference, payrollEntryId: entry.postedId,
    });
  }
}

function matchReconciliation(payrollCredit: StatutoryLiabilityEntry, challanDebit: StatutoryLiabilityEntry, amount: bigint): ReconciliationMatch {
  if (payrollCredit.credit === 0n || challanDebit.debit === 0n) throw new Error('reconciliation must connect a liability credit to a settlement debit');
  const alreadyMatched = state.reconciliationMatches.filter((match) => match.payrollCreditEntryId === payrollCredit.id).reduce((sum, match) => sum + match.amount, 0n);
  if (alreadyMatched + amount > payrollCredit.credit) throw new Error(`match exceeds payroll liability ${payrollCredit.id}`);
  const match: ReconciliationMatch = {
    id: next('M'), ledgerOwnerId: challanDebit.ledgerOwnerId, ledgerDate: challanDebit.ledgerDate,
    statutoryTag: payrollCredit.statutoryTag, period: payrollCredit.period,
    payrollCreditEntryId: payrollCredit.id, challanDebitEntryId: challanDebit.id, amount,
  };
  state.reconciliationMatches.push(match);
  return match;
}

function payAndReconcileChallans(): void {
  const payrollCredits = state.statutoryLiabilities.filter((entry) => entry.credit > 0n);
  if (!payrollCredits.length) throw new Error('commit payroll first');
  if (state.statutoryLiabilities.some((entry) => entry.debit > 0n)) throw new Error('demo challans already created');

  for (const statutoryTag of [...new Set(payrollCredits.map((entry) => entry.statutoryTag))]) {
    const credits = payrollCredits.filter((entry) => entry.statutoryTag === statutoryTag);
    const amount = credits.reduce((sum, entry) => sum + entry.credit, 0n);
    if (amount === 0n) continue;
    const debit: StatutoryLiabilityEntry = {
      id: next('SL'), ledgerOwnerId: 'LEGAL-ENTITY-01', ledgerDate: '2026-10-12', statutoryTag,
      period: credits[0].period, debit: amount, credit: 0n, canonicalReference: businessReference('CHL'),
      authorityReference: `${statutoryTag.toUpperCase().replace(/[^A-Z0-9]+/g, '-')}-202609-${String(state.counter).padStart(4, '0')}`,
      bankReference: `UTR-HDFC-${String(state.counter).padStart(6, '0')}`,
      attachmentReference: `ATTACHMENT:${statutoryTag}:2026-09`,
    };
    state.statutoryLiabilities.push(debit);
    credits.forEach((credit) => matchReconciliation(credit, debit, credit.credit));
  }
  log('appended PF/TDS challan debits and matched each settlement to its employee deduction credits');
}

function createForm16(): Form16Snapshot {
  if (state.form16s.length) return state.form16s[0];
  const tdsCredits = state.statutoryLiabilities.filter((entry) => entry.statutoryTag === 'authority:income-tax' && entry.credit > 0n);
  if (!tdsCredits.length) throw new Error('commit payroll first');
  const taxDeducted = tdsCredits.reduce((sum, entry) => sum + entry.credit, 0n);
  const matched = state.reconciliationMatches.filter((match) => match.statutoryTag === 'authority:income-tax').reduce((sum, match) => sum + match.amount, 0n);
  if (taxDeducted === 0n || matched !== taxDeducted) throw new Error('Form 16 requires fully reconciled TDS challans');
  const challanReferences = [...new Set(state.reconciliationMatches.filter((match) => match.statutoryTag === 'authority:income-tax').map((match) => {
    return state.statutoryLiabilities.find((entry) => entry.id === match.challanDebitEntryId)!.canonicalReference;
  }))];
  const payrollReference = tdsCredits[0].canonicalReference;
  const payslip = state.payslips.find((snapshot) => snapshot.ledgerReference === payrollReference)!;
  const form16: Form16Snapshot = {
    id: next('F16'), ledgerOwnerId: tdsCredits[0].employeeId!, ledgerDate: '2027-05-31', fiscalYear: '2026-27',
    payrollReference, challanReferences, grossSalary: payslip.gross, taxDeducted,
    hash: hashText(`${payrollReference}|${challanReferences.join('|')}|${payslip.gross}|${taxDeducted}`),
    status: 'incomplete',
    missingRequirements: [
      'TRACES-generated Part A PDF and certificate number',
      'valid employer PAN and TAN plus employee PAN',
      'all quarterly Form 24Q receipt numbers and Q4 Annexure II',
      'complete annual payroll and Part B tax-computation values',
      'authorised signatory identity and authentication',
    ],
  };
  state.form16s.push(form16);
  log(`built Form 16 readiness package ${form16.id}; issuance blocked by ${form16.missingRequirements.length} mandatory requirements`);
  return form16;
}

function downloadForm16PackageDocument(form16: Form16Snapshot): void {
  const pdf = new jsPDF({ unit: 'mm', format: 'a4' });
  pdf.setProperties({ title: `Form 16 readiness ${form16.fiscalYear}`, subject: `Incomplete issuance package ${form16.hash}` });
  const pageFrame = (): void => {
    pdf.setDrawColor(70, 70, 70);
    pdf.rect(12, 10, 186, 277);
  };
  pageFrame();
  pdf.setFont('helvetica', 'bold');
  pdf.setFontSize(16);
  pdf.text('FORM 16 ISSUANCE READINESS PACKAGE', 105, 22, { align: 'center' });
  pdf.setTextColor(180, 35, 35);
  pdf.setFontSize(10);
  pdf.text('INCOMPLETE - THIS IS NOT FORM NO. 16', 105, 31, { align: 'center' });
  pdf.setTextColor(0, 0, 0);
  pdf.setFont('helvetica', 'normal');
  pdf.setFontSize(8.5);
  pdf.text('Part A must be generated by TRACES from processed TDS statements; this application must import it, not fabricate it.', 18, 43);
  pdf.text(`Employee: ${form16.ledgerOwnerId}    Financial year: ${form16.fiscalYear}    Payroll source: ${form16.payrollReference}`, 18, 53);
  pdf.text(`Reconciled tax in demonstrated period: INR ${formatMoney(form16.taxDeducted)}`, 18, 60);
  pdf.text(`Canonical settlement references: ${form16.challanReferences.join(', ')}`, 18, 67);
  pdf.text(`Package checksum: ${form16.hash}`, 18, 74);
  pdf.setFont('helvetica', 'bold');
  pdf.text('Mandatory requirements still missing', 18, 88);
  pdf.setFont('helvetica', 'normal');
  let missingY = 98;
  form16.missingRequirements.forEach((requirement, index) => {
    pdf.text(`${index + 1}. ${requirement}`, 22, missingY);
    missingY += 9;
  });
  pdf.setFont('helvetica', 'bold');
  pdf.text('Correct issuance flow', 18, 154);
  pdf.setFont('helvetica', 'normal');
  pdf.text([
    '1. Complete annual payroll and employee declarations.',
    '2. File quarterly Form 24Q and Q4 Annexure II; reconcile challans and statement receipts.',
    '3. Request and download non-editable Part A from TRACES.',
    '4. Produce complete employer Part B (Annexure-I) from annual tax computation.',
    '5. Authenticate, retain certificate control/log, and furnish the combined package to the employee.',
  ], 22, 164);

  const partBRows: Array<[string, string]> = [
    ['A. Whether opting out of taxation u/s 115BAC(1A)', 'MISSING'],
    ['1(a). Salary under section 17(1)', `PARTIAL PERIOD ONLY: INR ${formatMoney(form16.grossSalary)}`],
    ['1(b). Value of perquisites under section 17(2) / Form 12BA', 'MISSING'],
    ['1(c). Profits in lieu of salary under section 17(3)', 'MISSING'],
    ['1(d). Total gross salary', 'INCOMPLETE ANNUAL DATA'],
    ['1(e). Salary received from other employer(s)', 'MISSING'],
    ['2(a). Travel concession under section 10(5)', 'MISSING'],
    ['2(b). Death-cum-retirement gratuity under section 10(10)', 'MISSING'],
    ['2(c). Commuted pension under section 10(10A)', 'MISSING'],
    ['2(d). Leave encashment under section 10(10AA)', 'MISSING'],
    ['2(e). House rent allowance under section 10(13A)', 'MISSING'],
    ['2(f). Other special allowances under section 10(14)', 'MISSING'],
    ['2(g-h). Other exemptions and their total under section 10', 'MISSING'],
    ['2(i). Total exemptions under section 10', 'MISSING'],
    ['3. Salary received from current employer [1(d)-2(i)]', 'MISSING'],
    ['4(a). Standard deduction under section 16(ia)', 'MISSING'],
    ['4(b). Entertainment allowance under section 16(ii)', 'MISSING'],
    ['4(c). Tax on employment under section 16(iii)', 'MISSING'],
    ['5. Total deductions under section 16', 'MISSING'],
    ['6. Income chargeable under the head Salaries', 'MISSING'],
    ['7(a). Income/loss from house property reported under section 192(2B)', 'MISSING'],
    ['7(b). Income from other sources offered for TDS', 'MISSING'],
    ['8. Total other income reported by employee', 'MISSING'],
    ['9. Gross total income', 'MISSING'],
    ['10(a-d). Sections 80C, 80CCC and 80CCD(1)', 'MISSING'],
    ['10(e). Section 80CCD(1B)', 'MISSING'],
    ['10(f). Employer contribution under section 80CCD(2)', 'MISSING'],
    ['10(g). Health insurance under section 80D', 'MISSING'],
    ['10(h). Higher-education loan interest under section 80E', 'MISSING'],
    ['10(i-j). Employee/Government Agnipath contributions under section 80CCH', 'MISSING'],
    ['10(k). Donations under section 80G', 'MISSING'],
    ['10(l). Savings interest under section 80TTA', 'MISSING'],
    ['10(m-n). Other Chapter VI-A deductions and total', 'MISSING'],
    ['11. Aggregate Chapter VI-A deductible amount', 'MISSING'],
    ['12. Total taxable income', 'MISSING'],
    ['13. Tax on total income', 'MISSING'],
    ['14. Rebate under section 87A', 'MISSING'],
    ['15. Surcharge', 'MISSING'],
    ['16. Health and education cess at 4%', 'MISSING'],
    ['17. Tax payable', 'MISSING'],
    ['18. Relief under section 89', 'MISSING'],
    ['19. TDS per Form 12BAA under section 192(2B)', 'MISSING'],
    ['20. TCS per Form 12BAA under section 192(2B)', 'MISSING'],
    ['21. Net tax payable', 'MISSING'],
  ];

  let y = 0;
  const startPartBPage = (): void => {
    pdf.addPage(); pageFrame();
    pdf.setFont('helvetica', 'bold'); pdf.setFontSize(13);
    pdf.text('FORM NO. 16 - PART B (ANNEXURE-I) WORKING DRAFT', 105, 20, { align: 'center' });
    pdf.setTextColor(180, 35, 35); pdf.setFontSize(8);
    pdf.text('INCOMPLETE ANNUAL DATA - NOT FOR ISSUANCE', 105, 28, { align: 'center' });
    pdf.setTextColor(0, 0, 0); y = 39;
  };
  startPartBPage();
  for (const [label, value] of partBRows) {
    const labelLines = pdf.splitTextToSize(label, 118) as string[];
    const height = Math.max(9, labelLines.length * 4 + 4);
    if (y + height > 276) startPartBPage();
    pdf.rect(18, y, 174, height); pdf.line(142, y, 142, y + height);
    pdf.setFont('helvetica', 'normal'); pdf.setFontSize(7.5);
    pdf.text(labelLines, 21, y + 5);
    pdf.setFont('helvetica', value === 'MISSING' || value.startsWith('INCOMPLETE') ? 'bold' : 'normal');
    pdf.text(value, 189, y + 5, { align: 'right', maxWidth: 44 });
    y += height;
  }
  pdf.save(`form16-readiness-${form16.ledgerOwnerId}-${form16.fiscalYear}.pdf`);
}

function downloadForm16(id: string): void {
  const form16 = state.form16s.find((item) => item.id === id);
  if (!form16) throw new Error(`Form 16 readiness package not found: ${id}`);
  downloadForm16PackageDocument(form16);
}

function hashText(input: string): string {
  let hash = 2166136261;
  for (const character of input) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  return Math.abs(hash >>> 0).toString(16).padStart(8, '0');
}

function getDraft(id: string): Draft {
  const draft = state.drafts.find((item) => item.id === id);
  if (!draft) throw new Error(`draft not found: ${id}`);
  return draft;
}

function requireHead(key: string, kind?: HeadKind): Head {
  const head = state.heads.find((item) => item.key === key);
  if (!head) throw new Error(`head not found: ${key}`);
  if (kind && head.kind !== kind) throw new Error(`${key} is not ${kind}`);
  return head;
}

function refreshHash(draft: Draft): void {
  const input = draft.entries.map((entry) => `${entry.head}:${entry.amount}:${entry.source}`).join('|');
  draft.hash = hashText(input);
}

function reset(): void {
  state.employees.length = 0;
  state.references.length = 0;
  state.heads.length = 0;
  state.salary.length = 0;
  state.standingInputs.length = 0;
  state.oneTimeInputs.length = 0;
  state.proofAttachments.length = 0;
  state.preparations.length = 0;
  state.drafts.length = 0;
  state.posted.length = 0;
  state.payslips.length = 0;
  state.statutoryLiabilities.length = 0;
  state.reconciliationMatches.length = 0;
  state.form16s.length = 0;
  state.log.length = 0;
  state.counter = 1;
  state.referenceCounter = 1;
}

function joinDemoEmployee(): void {
  reset();
  state.employees.push({ id: 'vinay', name: 'Vinay', ledgerOwnerId: 'vinay', ledgerDate: '2026-04-01', joinedOn: '2026-04-01', status: 'active' });
  state.log.push('Vinay joined as an active employee on 2026-04-01');
  render();
}

function createDemoPayroll(): void {
  if (!state.employees.some((employee) => employee.id === 'vinay')) throw new Error('join the employee first');
  if (state.heads.length) throw new Error('payroll is already created');
  defineHead('basic', 'Basic', 'earning', 'add');
  defineHead('hra', 'HRA', 'earning', 'add');
  defineHead('special', 'Special Allowance', 'earning', 'add');
  defineHead('bonus', 'Performance Bonus', 'earning', 'add');
  defineHead('internet_allowance', 'Internet Allowance', 'earning', 'add');
  defineHead('pf', 'Provident Fund', 'deduction', 'subtract', 'authority:epfo');
  defineHead('vpf', 'Voluntary PF', 'deduction', 'subtract', 'authority:epfo');
  defineHead('unpaid_leave', 'Unpaid Leave', 'deduction', 'subtract');
  defineHead('income_tax', 'Income Tax', 'deduction', 'subtract', 'authority:income-tax');
  defineHead('prior_period_recovery', 'Prior-period Recovery', 'deduction', 'subtract');
  const salaryReference = createReference('salary', 'vinay', 'effective:2026-04-01', '2026-04-01');
  salaryReference.status = 'approved';
  appendSalary('vinay', 'basic', '50000.00', salaryReference.number);
  appendSalary('vinay', 'hra', '20000.00', salaryReference.number);
  appendSalary('vinay', 'special', '10000.00', salaryReference.number);
  appendPayrollInput('vinay', 'other_earning', 'internet_allowance', 'monthly standing allowance', '1500.00', 'monthly_standing', 'internet_allowance');
  appendPayrollInput('vinay', 'deduction_instruction', 'voluntary_pf', 'monthly standing instruction', '1000.00', 'monthly_standing', 'vpf');
  appendPayrollInput('vinay', 'other_earning', 'performance_bonus', 'approved bonus', '5000.00', 'one_time', 'bonus');
  appendPayrollInput('vinay', 'deduction_instruction', 'unpaid_leave', '1 day', '2000.00', 'one_time', 'unpaid_leave');
  state.log.push('created Vinay payroll: component catalog, salary entitlement and monthly inputs');
  render();
}

function attachDemoProof(): void {
  if (!state.salary.length) throw new Error('create payroll first');
  if (state.proofAttachments.length) throw new Error('proof is already attached');
  const attachment = submitProofAttachment('vinay', new File(['synthetic rent receipt'], 'rent-receipt-demo.txt', { type: 'text/plain' }));
  log(`Vinay submitted proof attachment ${attachment.id}; it created no monetary instruction`);
}

function approveDemoInputs(): void {
  if (!state.standingInputs.length && !state.oneTimeInputs.length) throw new Error('create payroll first');
  const proof = state.proofAttachments[0];
  if (!proof) throw new Error('employee must submit proof first');
  proof.status = 'accepted';
  proof.reviewedBy = 'hr-admin';
  if (!state.standingInputs.some((entry) => entry.key === 'income_tax_instruction')) {
    appendPayrollInput('vinay', 'deduction_instruction', 'income_tax_instruction', 'HR-tuned monthly TDS after proof review', '4500.00', 'monthly_standing', 'income_tax', proof.id);
  }
  [...state.standingInputs, ...state.oneTimeInputs].forEach((entry) => approveInput(entry.id));
  log(`HR accepted ${proof.id}, created monthly TDS instruction and approved payroll inputs`);
}

// This is deliberately higher-order demo code. It reads primitives and produces a report, not ledger rows.
function preparePayrollReport(): void {
  if (!state.salary.length || [...state.standingInputs, ...state.oneTimeInputs].some((entry) => !entry.approved)) {
    throw new Error('approved salary and payroll inputs are required');
  }
  if (state.preparations.length) throw new Error('a preparation report already exists');
  const report: PreparationReport = {
    queryId: next('QUERY'), ledgerOwnerId: 'vinay', asOf: '2026-09-30',
    period: '2026-09', reviewed: false, materialised: false, entries: [], checksum: '',
  };
  const add = (head: string, amount: bigint, source: string, sourceReference: string): void => {
    report.entries.push({ id: next('R'), head, amount, source, sourceReference, ledgerOwnerId: report.ledgerOwnerId, ledgerDate: report.asOf });
  };
  for (const salary of state.salary) add(salary.head, salary.amount, `salary:${salary.id}`, salary.reference);
  const monthlyEarning = state.standingInputs.find((entry) => entry.key === 'internet_allowance')!;
  const monthlyDeduction = state.standingInputs.find((entry) => entry.key === 'voluntary_pf')!;
  const bonus = state.oneTimeInputs.find((entry) => entry.key === 'performance_bonus')!;
  const leave = state.oneTimeInputs.find((entry) => entry.key === 'unpaid_leave')!;
  const taxInstruction = state.standingInputs.find((entry) => entry.key === 'income_tax_instruction')!;
  add(monthlyEarning.payrollHead!, monthlyEarning.amount!, `monthly-input:${monthlyEarning.id}`, monthlyEarning.reference);
  add(monthlyDeduction.payrollHead!, -monthlyDeduction.amount!, `monthly-input:${monthlyDeduction.id}`, monthlyDeduction.reference);
  add(bonus.payrollHead!, bonus.amount!, `one-time-input:${bonus.id}`, bonus.reference);
  add(leave.payrollHead!, -leave.amount!, `one-time-input:${leave.id}`, leave.reference);
  const basic = state.salary.find((entry) => entry.head === 'basic')!;
  add('pf', -(basic.amount * 12n / 100n), `demo-rule:12%-basic|salary:${basic.id}`, basic.reference);
  add('income_tax', -taxInstruction.amount!, `monthly-input:${taxInstruction.id}|proof:${taxInstruction.sourceReference}`, taxInstruction.reference);
  report.checksum = hashText(report.entries.map((entry) => `${entry.head}:${entry.amount}:${entry.source}`).join('|'));
  state.preparations.push(report);
  log(`queried non-canonical payroll preview ${report.queryId} @ checksum ${report.checksum}; no ledger object exists yet`);
}

function reviewPreparationReport(): void {
  const report = state.preparations[state.preparations.length - 1];
  if (!report || report.reviewed) throw new Error('prepare an unreviewed report first');
  report.reviewed = true;
  log(`payroll manager reviewed displayed query ${report.queryId}; this is local workflow state, not a canonical approval`);
}

function fireDraftPayroll(): void {
  const report = state.preparations[state.preparations.length - 1];
  if (!report || !report.reviewed || report.materialised) throw new Error('review an unmaterialised preparation query first');
  const draft = createDraft(report.ledgerOwnerId, report.period);
  for (const entry of report.entries) appendDraft(draft.id, entry.head, formatMoney(entry.amount), entry.source, entry.sourceReference);
  if (draft.hash !== report.checksum) throw new Error('draft does not exactly match the displayed query result');
  report.materialised = true;
  log(`created first canonical object: draft ${draft.reference}/${draft.id} @ ${draft.hash}, matching query checksum ${report.checksum}`);
}

function sealAndApproveDemo(): void {
  const draft = activeDraft();
  sealDraft(draft.id);
  approveDraft(draft.id);
  log(`sealed and approved exact draft ${draft.id} @ ${draft.hash}`);
}

function commitDemo(): void {
  const draft = activeDraft();
  commitDraft(draft.id);
  log(`committed ${draft.id} atomically to the posted ledger`);
}

function correctDemo(): void {
  const bonus = state.posted.find((entry) => entry.head === 'bonus' && reference(entry.ledgerReference).kind === 'payroll');
  if (!bonus) throw new Error('commit the demo first');
  carryAdjustmentToNextMonth(bonus.postedId, '-500.00');
  log(`carried ₹500 recovery for ${bonus.postedId} into October; September snapshot remains immutable`);
}

function activeDraft(): Draft {
  const draft = [...state.drafts].reverse().find((item) => item.status !== 'abandoned');
  if (!draft) throw new Error('fire the reviewed preparation report into a draft first');
  return draft;
}

function execute(raw: string): void {
  const parts = raw.trim().split(/\s+/);
  const command = parts.shift()?.toLowerCase();
  if (!command) return;
  state.log.push(`> ${raw}`);
  try {
    switch (command) {
      case 'help': state.log.push('join | create-payroll | component ... | salary ... | standing-input <employee> <type> <key> <amount> <head> | one-time-input <employee> <type> <key> <amount> <head> | approve-input <id> | submit-proof <employee> <name> | draft-* | ledger-adjust-next-month ... | demo-prepare | demo-review | demo-fire-draft | demo-challans | demo-form16 | reset'); break;
      case 'reset': reset(); state.log.push('all in-memory state reset'); break;
      case 'join': joinDemoEmployee(); return;
      case 'create-payroll': createDemoPayroll(); return;
      case 'component': defineHead(parts[0], parts[0], parts[1] as HeadKind, parts[2] as Head['effect']); state.log.push(`created head ${parts[0]}`); break;
      case 'salary': { const entry = appendSalary(parts[0], parts[1], parts[2]); state.log.push(`appended salary entry ${entry.id} under ${entry.reference}`); break; }
      case 'standing-input': { const entry = appendPayrollInput(parts[0], parts[1], parts[2], parts[2], parts[3], 'monthly_standing', parts[4]); state.log.push(`appended standing instruction ${entry.id}`); break; }
      case 'one-time-input': { const entry = appendPayrollInput(parts[0], parts[1], parts[2], parts[2], parts[3], 'one_time', parts[4]); state.log.push(`appended one-time input ${entry.id}`); break; }
      case 'approve-input': approveInput(parts[0]); state.log.push(`approved input ${parts[0]}`); break;
      case 'submit-proof': { const attachment = submitProofAttachment(parts[0], new File(['terminal proof'], parts[1] || 'proof.txt', { type: 'text/plain' })); state.log.push(`submitted attachment ${attachment.id}`); break; }
      case 'draft-create': { const draft = createDraft(parts[0], parts[1]); state.log.push(`created draft ${draft.id} under ${draft.reference}`); break; }
      case 'draft-add': { const entry = appendDraft(parts[0], parts[1], parts[2], parts[3], parts[4]); state.log.push(`appended draft entry ${entry.id}`); break; }
      case 'draft-seal': sealDraft(parts[0]); state.log.push(`sealed ${parts[0]}`); break;
      case 'draft-approve': approveDraft(parts[0]); state.log.push(`approved ${parts[0]}`); break;
      case 'draft-commit': commitDraft(parts[0]); state.log.push(`committed ${parts[0]}`); break;
      case 'draft-abandon': abandonDraft(parts[0]); state.log.push(`abandoned ${parts[0]}; posted ledger unchanged`); break;
      case 'ledger-adjust-next-month': carryAdjustmentToNextMonth(parts[0], parts[1], parts[2]); state.log.push(`carried adjustment for ${parts[0]} to the next-month ledger`); break;
      case 'demo-prepare': preparePayrollReport(); return;
      case 'demo-review': reviewPreparationReport(); return;
      case 'demo-fire-draft': fireDraftPayroll(); return;
      case 'demo-challans': payAndReconcileChallans(); return;
      case 'demo-form16': createForm16(); return;
      default: throw new Error(`unknown command: ${command}; try help`);
    }
  } catch (error) {
    state.log.push(`! ${error instanceof Error ? error.message : String(error)}`);
  }
  render();
}

function esc(value: unknown): string {
  return String(value).replace(/[&<>"']/g, (character) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' }[character]!));
}

function rows(items: string[]): string {
  return items.length ? items.join('') : '<div class="empty">No entries yet</div>';
}

function level(): number {
  if (state.form16s.length) return 11;
  if (state.reconciliationMatches.length) return 10;
  if (state.posted.length) return 9;
  if (state.drafts.some((draft) => draft.status === 'approved')) return 8;
  if (state.drafts.some((draft) => draft.entries.length)) return 7;
  if (state.preparations.some((report) => report.reviewed)) return 6;
  if (state.preparations.length) return 5;
  if ([...state.standingInputs, ...state.oneTimeInputs].length && [...state.standingInputs, ...state.oneTimeInputs].every((entry) => entry.approved)) return 4;
  if (state.proofAttachments.length) return 3;
  if (state.salary.length) return 2;
  if (state.employees.length) return 1;
  return 0;
}

function totals(entries: Array<{ head: string; amount: bigint }>): { gross: bigint; deductions: bigint; net: bigint } {
  let gross = 0n;
  let deductions = 0n;
  for (const entry of entries) {
    const head = state.heads.find((item) => item.key === entry.head);
    if (head?.kind === 'earning') gross += entry.amount;
    if (head?.kind === 'deduction') deductions += -entry.amount;
  }
  return { gross, deductions, net: gross - deductions };
}

function reconciliationSummary(statutoryTag: string): { credited: bigint; debited: bigint; matched: bigint; outstanding: bigint; status: string } {
  const entries = state.statutoryLiabilities.filter((entry) => entry.statutoryTag === statutoryTag);
  const credited = entries.reduce((sum, entry) => sum + entry.credit, 0n);
  const debited = entries.reduce((sum, entry) => sum + entry.debit, 0n);
  const matched = state.reconciliationMatches.filter((match) => match.statutoryTag === statutoryTag).reduce((sum, match) => sum + match.amount, 0n);
  const outstanding = credited - debited;
  const status = credited === 0n ? 'NOT POSTED' : outstanding === 0n && matched === credited ? 'MATCHED' : debited < credited ? 'SHORT PAID' : debited > credited ? 'EXCESS PAID' : 'UNMATCHED';
  return { credited, debited, matched, outstanding, status };
}

function render(): void {
  const currentLevel = level();
  const report = state.preparations[state.preparations.length - 1];
  const draft = state.drafts[state.drafts.length - 1];
  const postedTotals = totals(state.posted);
  const draftTotals = totals(draft?.entries || []);
  const reportTotals = totals(report?.entries || []);
  const statutoryTags = [...new Set(state.statutoryLiabilities.map((entry) => entry.statutoryTag))];
  app.innerHTML = `
    <header>
      <div class="eyebrow">THROWAWAY CONCEPT LAB · IN MEMORY ONLY</div>
      <div class="title-row"><div><h1>Employee-to-Compliance Payroll Journey</h1><p>Join, create payroll, review preparation, post payroll, settle liabilities and derive Form 16.</p></div><div class="level">LEVEL <strong>${currentLevel}</strong>/11</div></div>
      <div class="progress">${Array.from({ length: 11 }, (_, index) => `<span class="${index < currentLevel ? 'done' : ''}"></span>`).join('')}</div>
    </header>
    <section class="boundary">
      <div><b>Layer 1</b><span>employee · salary · inputs · payroll · debit/credit · reconciliation</span></div>
      <div class="arrow">→</div>
      <div class="external"><b>External demo player</b><span>PF = 12% Basic · consumes HR-tuned TDS instruction</span></div>
      <div class="arrow">→</div>
      <div><b>Higher-order outputs</b><span>payslip PDF · Form 16 concept PDF</span></div>
    </section>
    <nav class="game-controls">
      <button data-action="join">1 · Join Vinay</button>
      <button data-action="create-payroll">2 · Create payroll</button>
      <button data-action="proof">3 · Attach proof</button>
      <button data-action="approve-inputs">4 · HR review + tune inputs</button>
      <button class="external-button" data-action="prepare">5 · Prepare report</button>
      <button data-action="review-report">6 · Review report</button>
      <button data-action="fire-draft">7 · Fire draft payroll</button>
      <button data-action="approve-draft">8 · Approve draft</button>
      <button data-action="commit">9 · Commit + payslip</button>
      <button data-action="challans">10 · Pay + reconcile liabilities</button>
      <button class="external-button" data-action="form16">11 · Check Form 16 readiness</button>
      <button class="ghost" data-action="correct">Optional · Next-month recovery</button>
      <button class="ghost" data-action="reset">Reset</button>
      <input id="proof-file" type="file" hidden />
    </nav>
    <section class="reference-strip">
      <div class="reference-title">Immutable references</div>
      ${state.references.length ? state.references.map((item) => `<div class="reference-card ${item.kind}"><code>${esc(item.number)}</code><span>${esc(item.kind)} · ${esc(item.status)}</span><small>owner ${esc(item.ledgerOwnerId)} · date ${esc(item.ledgerDate)}</small>${item.corrects ? `<small>adjusts ${esc(item.corrects)} · root ${esc(item.root)}</small>` : `<small>root ${esc(item.root)}</small>`}</div>`).join('') : '<div class="reference-empty">Every proposal receives a number before its first entry.</div>'}
    </section>
    <main>
      <section class="terminal panel">
        <div class="panel-head"><div><span class="dot"></span>Primitive terminal simulator</div><small>one command → one function</small></div>
        <div class="terminal-output">${state.log.map((line) => `<div class="${line.startsWith('!') ? 'error' : line.startsWith('>') ? 'command' : ''}">${esc(line)}</div>`).join('')}</div>
        <form id="terminal-form"><span>›</span><input id="terminal-input" autocomplete="off" placeholder="type help or use the game controls" /><button>Run</button></form>
      </section>
      <section class="ledgers">
        <article class="panel wide employee-panel">
          <div class="panel-head"><div>Employee journey</div><small>${state.employees.length ? 'joined and active' : 'not joined'}</small></div>
          <div class="table">${rows(state.employees.map((employee) => `<div class="ledger-row"><code>${esc(employee.id)}</code><b>${esc(employee.name)}</b><span>${esc(employee.status)}</span><strong>${esc(employee.joinedOn)}</strong><small>owner ${esc(employee.ledgerOwnerId)} · ledger date ${esc(employee.ledgerDate)} · payroll can now be created</small></div>`))}</div>
        </article>
        <article class="panel">
          <div class="panel-head"><div>Salary Earning Ledger</div><small>${state.salary.length} entries</small></div>
          <div class="table">${rows(state.salary.map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.head)}</b><span>owner ${esc(entry.ledgerOwnerId)}</span><strong>+${formatMoney(entry.amount)}</strong><small>date ${esc(entry.ledgerDate)} · ref ${esc(entry.reference)} · ${esc(entry.source)}</small></div>`))}</div>
        </article>
        <article class="panel standing-ledger">
          <div class="panel-head"><div>Monthly standing-instruction ledger</div><small>effective-dated · reusable · ${state.standingInputs.filter((entry) => entry.approved).length}/${state.standingInputs.length} approved</small></div>
          <div class="table">${rows(state.standingInputs.map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.key)}</b><span class="status ${entry.approved ? 'approved' : ''}">${entry.approved ? 'active' : 'proposed'}</span><strong>${formatMoney(entry.amount!)}</strong><small>owner ${esc(entry.ledgerOwnerId)} · date ${esc(entry.ledgerDate)} · effective ${esc(entry.effectiveFrom)}${entry.effectiveUntil ? `–${esc(entry.effectiveUntil)}` : ' onward'} · head ${esc(entry.payrollHead)} · ref ${esc(entry.reference)}</small></div>`))}</div>
        </article>
        <article class="panel one-time-ledger">
          <div class="panel-head"><div>One-time payroll-input ledger</div><small>period-bound · consume once · ${state.oneTimeInputs.filter((entry) => entry.approved).length}/${state.oneTimeInputs.length} approved</small></div>
          <div class="table">${rows(state.oneTimeInputs.map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.key)}</b><span class="status ${entry.approved ? 'approved' : ''}">${entry.consumedBy ? 'consumed' : entry.approved ? 'approved' : 'proposed'}</span><strong>${formatMoney(entry.amount!)}</strong><small>owner ${esc(entry.ledgerOwnerId)} · date ${esc(entry.ledgerDate)} · period ${esc(entry.applicablePeriod)} · head ${esc(entry.payrollHead)} · ref ${esc(entry.reference)}${entry.consumedBy ? ` · consumed by ${esc(entry.consumedBy)}` : ''}</small></div>`))}</div>
        </article>
        <article class="panel wide proof-attachments">
          <div class="panel-head"><div>Employee proof attachments</div><small>files and audit metadata · not a monetary ledger</small></div>
          <div class="table">${rows(state.proofAttachments.map((attachment) => `<div class="ledger-row"><code>${esc(attachment.id)}</code><b>${esc(attachment.category)}</b><span class="status ${attachment.status === 'accepted' ? 'approved' : ''}">${esc(attachment.status)}</span><strong>${esc(attachment.file.name)}</strong><small>employee ${esc(attachment.ledgerOwnerId)} · uploaded ${esc(attachment.uploadedAt)} · FY ${esc(attachment.fiscalYear)} · ${attachment.file.size} B${attachment.reviewedBy ? ` · reviewed by ${esc(attachment.reviewedBy)}` : ''}</small></div>`))}</div>
        </article>
        <article class="panel wide preparation">
          <div class="panel-head"><div>Payroll manager preparation report</div><small>${report ? `NON-CANONICAL QUERY · ${esc(report.queryId)} · ${report.reviewed ? 'reviewed locally' : 'awaiting review'} · employee ${esc(report.ledgerOwnerId)} · as of ${esc(report.asOf)} · checksum ${esc(report.checksum)}` : 'generated by query · no reference · no monetary write'}</small></div>
          <div class="table">${rows((report?.entries || []).map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.head)}</b><span>${esc(entry.source)}</span><strong class="${entry.amount < 0n ? 'negative' : ''}">${entry.amount > 0n ? '+' : ''}${formatMoney(entry.amount)}</strong><small>source ref ${esc(entry.sourceReference)} · owner ${esc(entry.ledgerOwnerId)} · date ${esc(entry.ledgerDate)}</small></div>`))}</div>
          ${report?.entries.length ? `<div class="totals"><span>Gross <b>${formatMoney(reportTotals.gross)}</b></span><span>Deductions <b>${formatMoney(reportTotals.deductions)}</b></span><span>Net <b>${formatMoney(reportTotals.net)}</b></span></div>` : ''}
        </article>
        <article class="panel wide">
          <div class="panel-head"><div>Draft transaction ledger</div><small>${draft ? `${esc(draft.reference)} · owner ${esc(draft.ledgerOwnerId)} · date ${esc(draft.ledgerDate)} · ${esc(draft.id)}/rev-${draft.revision} · ${draft.status} · hash ${draft.hash}` : 'no draft'}</small></div>
          <div class="table">${rows((draft?.entries || []).map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.head)}</b><span>${esc(entry.source)}</span><strong class="${entry.amount < 0n ? 'negative' : ''}">${entry.amount > 0n ? '+' : ''}${formatMoney(entry.amount)}</strong><small>owner ${esc(entry.ledgerOwnerId)} · date ${esc(entry.ledgerDate)} · proposal ${esc(draft.reference)} · source ${esc(entry.sourceReference)}</small></div>`))}</div>
          ${draft?.entries.length ? `<div class="totals"><span>Gross <b>${formatMoney(draftTotals.gross)}</b></span><span>Deductions <b>${formatMoney(draftTotals.deductions)}</b></span><span>Net <b>${formatMoney(draftTotals.net)}</b></span></div>` : ''}
        </article>
        <article class="panel wide posted">
          <div class="panel-head"><div>Payroll Ledger</div><small>committed · earnings · deductions · net · ${state.posted.length} entries</small></div>
          <div class="table">${rows(state.posted.map((entry) => `<div class="ledger-row ${entry.adjustmentFor ? 'contra' : ''}"><code>${esc(entry.postedId)}</code><b>${esc(entry.head)}</b><span>${esc(entry.source)}</span><strong class="${entry.amount < 0n ? 'negative' : ''}">${entry.amount > 0n ? '+' : ''}${formatMoney(entry.amount)}</strong><small>owner ${esc(entry.ledgerOwnerId)} · date ${esc(entry.ledgerDate)} · ref ${esc(entry.ledgerReference)} · source ${esc(entry.sourceReference)}${entry.adjustmentFor ? ` · adjusts ${esc(entry.adjustmentFor)}` : ''}</small></div>`))}</div>
          ${state.posted.length ? `<div class="totals"><span>Gross entries <b>${formatMoney(postedTotals.gross)}</b></span><span>Deduction entries <b>${formatMoney(postedTotals.deductions)}</b></span><span>Ledger net <b>${formatMoney(postedTotals.net)}</b></span></div>` : ''}
        </article>
        <article class="panel wide reconciliation">
          <div class="panel-head"><div>Statutory Liability Ledger</div><small>tag-routed · payroll credits ↔ settlement debits · zero means reconciled</small></div>
          <div class="reconciliation-summary">
            ${statutoryTags.length ? statutoryTags.map((tag) => { const summary = reconciliationSummary(tag); return `<div><b>${esc(tag)} · ${summary.status}</b><span>deducted/credited ${formatMoney(summary.credited)}</span><span>paid/debited ${formatMoney(summary.debited)}</span><span>matched ${formatMoney(summary.matched)}</span><span>outstanding ${formatMoney(summary.outstanding)}</span></div>`; }).join('') : '<div><b>NO LIABILITIES</b><span>statutory tags are configuration, not ledger concepts</span></div>'}
          </div>
          <div class="ledger-subtitle">Liability entries</div>
          <div class="table">${rows(state.statutoryLiabilities.map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.statutoryTag)}</b><span>${entry.credit ? `liability · employee ${esc(entry.employeeId)}` : `settlement · authority ref ${esc(entry.authorityReference)}`}</span><strong>${entry.credit ? `Cr ${formatMoney(entry.credit)}` : `Dr ${formatMoney(entry.debit)}`}</strong><small>owner ${esc(entry.ledgerOwnerId)} · date ${esc(entry.ledgerDate)} · canonical ${esc(entry.canonicalReference)}${entry.payrollEntryId ? ` · payroll entry ${esc(entry.payrollEntryId)}` : ''}${entry.bankReference ? ` · bank ${esc(entry.bankReference)}` : ''}${entry.attachmentReference ? ` · file ${esc(entry.attachmentReference)}` : ''}</small></div>`))}</div>
          <div class="ledger-subtitle">Immutable reconciliation matches</div>
          <div class="table">${rows(state.reconciliationMatches.map((match) => `<div class="ledger-row"><code>${esc(match.id)}</code><b>${esc(match.statutoryTag)}</b><span>${esc(match.payrollCreditEntryId)} ↔ ${esc(match.challanDebitEntryId)}</span><strong>${formatMoney(match.amount)}</strong><small>owner ${esc(match.ledgerOwnerId)} · date ${esc(match.ledgerDate)} · period ${esc(match.period)}</small></div>`))}</div>
        </article>
        <article class="panel wide snapshots">
          <div class="panel-head"><div>Immutable payslip snapshots</div><small>PDF is an optional rendering · ${state.payslips.length} snapshots</small></div>
          <div class="table">${rows(state.payslips.map((snapshot) => `<div class="snapshot-row"><code>${esc(snapshot.id)}</code><div><b>${esc(snapshot.ledgerReference)}</b><small>owner ${esc(snapshot.ledgerOwnerId)} · date ${esc(snapshot.ledgerDate)} · entries ${esc(snapshot.entryIds.join(', '))} · hash ${esc(snapshot.ledgerHash)}</small></div><span>gross ${formatMoney(snapshot.gross)} · deductions ${formatMoney(snapshot.deductions)}</span><strong>net ${formatMoney(snapshot.net)}</strong><button type="button" data-document-kind="payslip" data-payslip-id="${esc(snapshot.id)}">Payslip PDF</button></div>`))}</div>
        </article>
        <article class="panel wide form16-panel">
          <div class="panel-head"><div>Form 16 issuance readiness</div><small class="external-label">HIGHER ORDER · Part A must come from TRACES</small></div>
          <div class="table">${rows(state.form16s.map((form16) => `<div class="snapshot-row"><code>${esc(form16.id)}</code><div><b>FY ${esc(form16.fiscalYear)} · ${esc(form16.status)}</b><small>employee ${esc(form16.ledgerOwnerId)} · payroll ${esc(form16.payrollReference)} · ${form16.missingRequirements.length} mandatory requirements missing · hash ${esc(form16.hash)}</small></div><span>demonstrated gross ${formatMoney(form16.grossSalary)} · reconciled tax ${formatMoney(form16.taxDeducted)}</span><strong>NOT ISSUABLE</strong><button type="button" data-document-kind="form16-readiness" data-form16-id="${esc(form16.id)}">Form 16 Readiness PDF</button></div>`))}</div>
        </article>
      </section>
    </main>
    <footer>No backend · no persistence · no production contract · refresh to lose everything</footer>
  `;
  wireEvents();
}

function attempt(action: () => void): void {
  try { action(); } catch (error) { log(`! ${error instanceof Error ? error.message : String(error)}`); }
}

function wireEvents(): void {
  document.querySelector<HTMLFormElement>('#terminal-form')?.addEventListener('submit', (event) => {
    event.preventDefault();
    const input = document.querySelector<HTMLInputElement>('#terminal-input')!;
    execute(input.value);
  });
  document.querySelectorAll<HTMLButtonElement>('[data-action]').forEach((button) => button.addEventListener('click', () => {
    const action = button.dataset.action;
    if (action === 'join') attempt(joinDemoEmployee);
    if (action === 'create-payroll') attempt(createDemoPayroll);
    if (action === 'proof') attempt(attachDemoProof);
    if (action === 'approve-inputs') attempt(approveDemoInputs);
    if (action === 'prepare') attempt(preparePayrollReport);
    if (action === 'review-report') attempt(reviewPreparationReport);
    if (action === 'fire-draft') attempt(fireDraftPayroll);
    if (action === 'approve-draft') attempt(sealAndApproveDemo);
    if (action === 'commit') attempt(commitDemo);
    if (action === 'challans') attempt(payAndReconcileChallans);
    if (action === 'form16') attempt(createForm16);
    if (action === 'correct') attempt(correctDemo);
    if (action === 'reset') { reset(); render(); }
  }));
  document.querySelectorAll<HTMLButtonElement>('[data-payslip-id]').forEach((button) => button.addEventListener('click', () => {
    attempt(() => {
      if (button.dataset.documentKind !== 'payslip') throw new Error('document-kind mismatch for payslip download');
      downloadPayslip(button.dataset.payslipId!);
    });
  }));
  document.querySelectorAll<HTMLButtonElement>('[data-form16-id]').forEach((button) => button.addEventListener('click', () => {
    attempt(() => {
      if (button.dataset.documentKind !== 'form16-readiness') throw new Error('document-kind mismatch for Form 16 download');
      downloadForm16(button.dataset.form16Id!);
    });
  }));
}

render();
