import './styles.css';

type HeadKind = 'earning' | 'deduction' | 'relief';
type DraftStatus = 'open' | 'sealed' | 'approved' | 'committed' | 'abandoned';
type ReferenceKind = 'salary' | 'exception' | 'payroll' | 'correction';
type ReferenceStatus = 'proposed' | 'draft' | 'sealed' | 'approved' | 'committed' | 'abandoned';

interface LedgerReference {
  number: string;
  kind: ReferenceKind;
  status: ReferenceStatus;
  employee: string;
  period: string;
  root: string;
  corrects?: string;
}

interface Head {
  key: string;
  label: string;
  kind: HeadKind;
  effect: 'add' | 'subtract' | 'input';
}

interface SalaryEntry {
  id: string;
  reference: string;
  employee: string;
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

interface ExceptionEntry {
  id: string;
  reference: string;
  employee: string;
  type: string;
  key: string;
  value: string;
  amount?: bigint;
  period: string;
  approved: boolean;
  evidence?: Evidence;
}

interface DraftEntry {
  id: string;
  head: string;
  amount: bigint;
  source: string;
  sourceReference: string;
}

interface Draft {
  id: string;
  reference: string;
  revision: number;
  employee: string;
  period: string;
  status: DraftStatus;
  entries: DraftEntry[];
  hash: string;
}

interface PostedEntry extends DraftEntry {
  postedId: string;
  draftId: string;
  ledgerReference: string;
  reversalOf?: string;
}

const state = {
  references: [] as LedgerReference[],
  heads: [] as Head[],
  salary: [] as SalaryEntry[],
  exceptions: [] as ExceptionEntry[],
  drafts: [] as Draft[],
  posted: [] as PostedEntry[],
  log: [] as string[],
  counter: 1,
  referenceCounter: 1,
};

const app = document.querySelector<HTMLDivElement>('#app')!;

function next(prefix: string): string {
  return `${prefix}${state.counter++}`;
}

function createReference(kind: ReferenceKind, employee: string, period: string, corrects?: string): LedgerReference {
  const prefix = kind === 'salary' ? 'SAL' : kind === 'exception' ? 'EXC' : 'PAY';
  const number = `${prefix}-${String(state.referenceCounter++).padStart(6, '0')}`;
  const corrected = corrects ? state.references.find((reference) => reference.number === corrects) : undefined;
  const reference: LedgerReference = {
    number,
    kind,
    status: kind === 'payroll' || kind === 'correction' ? 'draft' : 'proposed',
    employee,
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

function defineHead(key: string, label: string, kind: HeadKind, effect: Head['effect']): void {
  if (state.heads.some((head) => head.key === key)) throw new Error(`head already exists: ${key}`);
  state.heads.push({ key, label, kind, effect });
}

function appendSalary(employee: string, head: string, amount: string, ledgerReference?: string): SalaryEntry {
  requireHead(head, 'earning');
  const assignedReference = ledgerReference || createReference('salary', employee, 'effective:2026-04-01').number;
  const entry = { id: next('S'), reference: assignedReference, employee, head, amount: money(amount), effectiveFrom: '2026-04-01', source: 'offer-letter-demo' };
  state.salary.push(entry);
  return entry;
}

function appendException(employee: string, type: string, key: string, value: string, amount?: string): ExceptionEntry {
  const assignedReference = createReference('exception', employee, type === 'exemption_claim' ? 'FY-2026-27' : '2026-09');
  const entry: ExceptionEntry = {
    id: next('X'), reference: assignedReference.number, employee, type, key, value, period: assignedReference.period, approved: false,
  };
  if (amount) entry.amount = money(amount);
  state.exceptions.push(entry);
  return entry;
}

function approveException(id: string): void {
  const entry = state.exceptions.find((item) => item.id === id);
  if (!entry) throw new Error(`exception not found: ${id}`);
  if (entry.type === 'exemption_claim' && !entry.evidence) throw new Error('exemption requires evidence before approval');
  entry.approved = true;
  reference(entry.reference).status = 'approved';
}

function attachEvidence(id: string, file: File): void {
  const entry = state.exceptions.find((item) => item.id === id);
  if (!entry) throw new Error(`exception not found: ${id}`);
  entry.evidence = { name: file.name, type: file.type || 'application/octet-stream', size: file.size, file };
}

function createDraft(employee: string, period: string): Draft {
  const ledgerReference = createReference('payroll', employee, period);
  const draft: Draft = { id: next('D'), reference: ledgerReference.number, revision: 1, employee, period, status: 'open', entries: [], hash: '' };
  state.drafts.push(draft);
  refreshHash(draft);
  return draft;
}

function appendDraft(draftId: string, head: string, amount: string, source: string, sourceReference = 'manual'): DraftEntry {
  const draft = getDraft(draftId);
  if (draft.status !== 'open') throw new Error(`draft ${draftId} is ${draft.status}`);
  requireHead(head);
  const entry = { id: next('L'), head, amount: money(amount), source, sourceReference };
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
}

function abandonDraft(id: string): void {
  const draft = getDraft(id);
  if (draft.status !== 'open' && draft.status !== 'sealed') throw new Error('only an uncommitted draft can be abandoned');
  draft.status = 'abandoned';
  reference(draft.reference).status = 'abandoned';
}

function correctPosted(id: string, replacement: string): void {
  const original = state.posted.find((entry) => entry.postedId === id);
  if (!original || original.reversalOf) throw new Error(`normal posted entry not found: ${id}`);
  if (state.posted.some((entry) => entry.reversalOf === id)) throw new Error(`entry already corrected: ${id}`);
  const originalReference = reference(original.ledgerReference);
  const correctionRef = createReference('correction', originalReference.employee, originalReference.period, originalReference.number);
  correctionRef.status = 'committed';
  state.posted.push({ ...original, id: next('L'), postedId: next('P'), amount: -original.amount, source: `contra:${id}`, sourceReference: original.ledgerReference, ledgerReference: correctionRef.number, reversalOf: id });
  state.posted.push({ ...original, id: next('L'), postedId: next('P'), amount: money(replacement), source: `replacement:${id}`, sourceReference: original.ledgerReference, ledgerReference: correctionRef.number, reversalOf: undefined });
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
  let hash = 2166136261;
  for (const character of input) hash = Math.imul(hash ^ character.charCodeAt(0), 16777619);
  draft.hash = Math.abs(hash >>> 0).toString(16).padStart(8, '0');
}

function reset(): void {
  state.references.length = 0;
  state.heads.length = 0;
  state.salary.length = 0;
  state.exceptions.length = 0;
  state.drafts.length = 0;
  state.posted.length = 0;
  state.log.length = 0;
  state.counter = 1;
  state.referenceCounter = 1;
}

function seedDemo(): void {
  reset();
  defineHead('basic', 'Basic', 'earning', 'add');
  defineHead('hra', 'HRA', 'earning', 'add');
  defineHead('special', 'Special Allowance', 'earning', 'add');
  defineHead('bonus', 'Performance Bonus', 'earning', 'add');
  defineHead('pf', 'Provident Fund', 'deduction', 'subtract');
  defineHead('unpaid_leave', 'Unpaid Leave', 'deduction', 'subtract');
  defineHead('income_tax', 'Income Tax', 'deduction', 'subtract');
  defineHead('hra_relief', 'HRA Relief Input', 'relief', 'input');
  const salaryReference = createReference('salary', 'vinay', 'effective:2026-04-01');
  salaryReference.status = 'approved';
  appendSalary('vinay', 'basic', '50000.00', salaryReference.number);
  appendSalary('vinay', 'hra', '20000.00', salaryReference.number);
  appendSalary('vinay', 'special', '10000.00', salaryReference.number);
  appendException('vinay', 'one_time_earning', 'performance_bonus', 'approved bonus', '5000.00');
  appendException('vinay', 'one_time_deduction', 'unpaid_leave', '1 day', '2000.00');
  appendException('vinay', 'exemption_claim', 'hra_rent_paid', 'annual rent', '180000.00');
  state.log.push('demo inputs seeded through primitive ledger calls');
  render();
}

function attachDemoProof(): void {
  const exemption = state.exceptions.find((entry) => entry.type === 'exemption_claim');
  if (!exemption) throw new Error('seed the demo first');
  attachEvidence(exemption.id, new File(['synthetic rent receipt'], 'rent-receipt-demo.txt', { type: 'text/plain' }));
  log(`attached in-memory proof to ${exemption.id}`);
}

function approveDemoInputs(): void {
  if (!state.exceptions.length) throw new Error('seed the demo first');
  state.exceptions.forEach((entry) => approveException(entry.id));
  log('approved all exception inputs');
}

// This is deliberately higher-order demo code. It is not a ledger primitive.
function runExternalCalculator(): void {
  if (!state.salary.length || state.exceptions.some((entry) => !entry.approved)) {
    throw new Error('approved salary and exception inputs are required');
  }
  if (state.drafts.some((draft) => draft.status !== 'abandoned')) throw new Error('an active demo draft already exists');
  const draft = createDraft('vinay', '2026-09');
  for (const salary of state.salary) appendDraft(draft.id, salary.head, formatMoney(salary.amount), `salary:${salary.id}`, salary.reference);
  const bonus = state.exceptions.find((entry) => entry.key === 'performance_bonus')!;
  const leave = state.exceptions.find((entry) => entry.key === 'unpaid_leave')!;
  const proof = state.exceptions.find((entry) => entry.key === 'hra_rent_paid')!;
  appendDraft(draft.id, 'bonus', formatMoney(bonus.amount!), `exception:${bonus.id}`, bonus.reference);
  appendDraft(draft.id, 'unpaid_leave', formatMoney(-leave.amount!), `exception:${leave.id}`, leave.reference);
  const basic = state.salary.find((entry) => entry.head === 'basic')!;
  appendDraft(draft.id, 'pf', formatMoney(-(basic.amount * 12n / 100n)), `demo-rule:12%-basic|salary:${basic.id}`, basic.reference);
  const tax = proof.evidence ? '-4500.00' : '-7000.00';
  appendDraft(draft.id, 'income_tax', tax, `demo-rule:proof-sensitive|exception:${proof.id}`, proof.reference);
  log(`EXTERNAL DEMO calculated draft ${draft.id}; Core primitives calculated nothing`);
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
  const tax = state.posted.find((entry) => entry.head === 'income_tax' && !entry.reversalOf && reference(entry.ledgerReference).kind === 'payroll');
  if (!tax) throw new Error('commit the demo first');
  correctPosted(tax.postedId, '-4000.00');
  log(`appended contra + replacement for ${tax.postedId}; original remains immutable`);
}

function activeDraft(): Draft {
  const draft = [...state.drafts].reverse().find((item) => item.status !== 'abandoned');
  if (!draft) throw new Error('calculate a draft first');
  return draft;
}

function execute(raw: string): void {
  const parts = raw.trim().split(/\s+/);
  const command = parts.shift()?.toLowerCase();
  if (!command) return;
  state.log.push(`> ${raw}`);
  try {
    switch (command) {
      case 'help': state.log.push('seed | component <key> <earning|deduction|relief> <add|subtract|input> | salary <employee> <head> <amount> | exception <employee> <type> <key> <value> [amount] | approve-exception <id> | evidence <id> <name> | draft-create <employee> <period> | draft-add <id> <head> <amount> <source> [source-reference] | draft-seal <id> | draft-approve <id> | draft-commit <id> | draft-abandon <id> | ledger-correct <posted-id> <replacement> | demo-calculate | reset'); break;
      case 'reset': reset(); state.log.push('all in-memory state reset'); break;
      case 'seed': seedDemo(); return;
      case 'component': defineHead(parts[0], parts[0], parts[1] as HeadKind, parts[2] as Head['effect']); state.log.push(`created head ${parts[0]}`); break;
      case 'salary': { const entry = appendSalary(parts[0], parts[1], parts[2]); state.log.push(`appended salary entry ${entry.id} under ${entry.reference}`); break; }
      case 'exception': { const entry = appendException(parts[0], parts[1], parts[2], parts[3], parts[4]); state.log.push(`appended exception ${entry.id} under ${entry.reference}`); break; }
      case 'approve-exception': approveException(parts[0]); state.log.push(`approved ${parts[0]}`); break;
      case 'evidence': attachEvidence(parts[0], new File(['terminal evidence'], parts[1] || 'proof.txt', { type: 'text/plain' })); state.log.push(`attached evidence to ${parts[0]}`); break;
      case 'draft-create': { const draft = createDraft(parts[0], parts[1]); state.log.push(`created draft ${draft.id} under ${draft.reference}`); break; }
      case 'draft-add': { const entry = appendDraft(parts[0], parts[1], parts[2], parts[3], parts[4]); state.log.push(`appended draft entry ${entry.id}`); break; }
      case 'draft-seal': sealDraft(parts[0]); state.log.push(`sealed ${parts[0]}`); break;
      case 'draft-approve': approveDraft(parts[0]); state.log.push(`approved ${parts[0]}`); break;
      case 'draft-commit': commitDraft(parts[0]); state.log.push(`committed ${parts[0]}`); break;
      case 'draft-abandon': abandonDraft(parts[0]); state.log.push(`abandoned ${parts[0]}; posted ledger unchanged`); break;
      case 'ledger-correct': correctPosted(parts[0], parts[1]); state.log.push(`corrected ${parts[0]} by append only`); break;
      case 'demo-calculate': runExternalCalculator(); return;
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
  if (state.posted.some((entry) => entry.reversalOf)) return 7;
  if (state.posted.length) return 6;
  if (state.drafts.some((draft) => draft.status === 'approved')) return 5;
  if (state.drafts.some((draft) => draft.entries.length)) return 4;
  if (state.exceptions.length && state.exceptions.every((entry) => entry.approved)) return 3;
  if (state.salary.length) return 2;
  if (state.heads.length) return 1;
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

function render(): void {
  const currentLevel = level();
  const draft = state.drafts[state.drafts.length - 1];
  const postedTotals = totals(state.posted);
  const draftTotals = totals(draft?.entries || []);
  app.innerHTML = `
    <header>
      <div class="eyebrow">THROWAWAY CONCEPT LAB · IN MEMORY ONLY</div>
      <div class="title-row"><div><h1>Payroll Ledger Game</h1><p>Can an external calculator complete payroll using only primitive ledgers?</p></div><div class="level">LEVEL <strong>${currentLevel}</strong>/7</div></div>
      <div class="progress">${Array.from({ length: 7 }, (_, index) => `<span class="${index < currentLevel ? 'done' : ''}"></span>`).join('')}</div>
    </header>
    <section class="boundary">
      <div><b>Layer 1</b><span>definitions · salary · exceptions · evidence · draft · posted</span></div>
      <div class="arrow">→</div>
      <div class="external"><b>External demo player</b><span>PF = 12% Basic · demo tax rule</span></div>
      <div class="arrow">→</div>
      <div><b>Layer 1</b><span>writes exact draft entries</span></div>
    </section>
    <nav class="game-controls">
      <button data-action="seed">1 · Seed inputs</button>
      <button data-action="proof">2 · Attach proof</button>
      <button data-action="approve-inputs">3 · Approve inputs</button>
      <button class="external-button" data-action="calculate">4 · Run external calculator</button>
      <button data-action="approve-draft">5 · Seal + approve</button>
      <button data-action="commit">6 · Commit</button>
      <button data-action="correct">7 · Correct tax</button>
      <button class="ghost" data-action="reset">Reset</button>
      <input id="proof-file" type="file" hidden />
    </nav>
    <section class="reference-strip">
      <div class="reference-title">Immutable references</div>
      ${state.references.length ? state.references.map((item) => `<div class="reference-card ${item.kind}"><code>${esc(item.number)}</code><span>${esc(item.kind)} · ${esc(item.status)}</span>${item.corrects ? `<small>corrects ${esc(item.corrects)} · root ${esc(item.root)}</small>` : `<small>root ${esc(item.root)}</small>`}</div>`).join('') : '<div class="reference-empty">Every proposal receives a number before its first entry.</div>'}
    </section>
    <main>
      <section class="terminal panel">
        <div class="panel-head"><div><span class="dot"></span>Primitive terminal simulator</div><small>one command → one function</small></div>
        <div class="terminal-output">${state.log.map((line) => `<div class="${line.startsWith('!') ? 'error' : line.startsWith('>') ? 'command' : ''}">${esc(line)}</div>`).join('')}</div>
        <form id="terminal-form"><span>›</span><input id="terminal-input" autocomplete="off" placeholder="type help or use the game controls" /><button>Run</button></form>
      </section>
      <section class="ledgers">
        <article class="panel">
          <div class="panel-head"><div>Salary entitlement ledger</div><small>${state.salary.length} entries</small></div>
          <div class="table">${rows(state.salary.map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.head)}</b><span>${esc(entry.employee)}</span><strong>+${formatMoney(entry.amount)}</strong><small>ref ${esc(entry.reference)} · ${esc(entry.source)}</small></div>`))}</div>
        </article>
        <article class="panel">
          <div class="panel-head"><div>Exception / input ledger</div><small>${state.exceptions.filter((entry) => entry.approved).length}/${state.exceptions.length} approved</small></div>
          <div class="table">${rows(state.exceptions.map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.key)}</b><span class="status ${entry.approved ? 'approved' : ''}">${entry.approved ? 'approved' : 'proposed'}</span><strong>${entry.amount === undefined ? esc(entry.value) : formatMoney(entry.amount)}</strong><small>ref ${esc(entry.reference)} · ${entry.evidence ? `📎 ${esc(entry.evidence.name)} · ${entry.evidence.size} B` : esc(entry.type)}</small></div>`))}</div>
        </article>
        <article class="panel wide">
          <div class="panel-head"><div>Draft transaction ledger</div><small>${draft ? `${esc(draft.reference)} · ${esc(draft.id)}/rev-${draft.revision} · ${draft.status} · hash ${draft.hash}` : 'no draft'}</small></div>
          <div class="table">${rows((draft?.entries || []).map((entry) => `<div class="ledger-row"><code>${esc(entry.id)}</code><b>${esc(entry.head)}</b><span>${esc(entry.source)}</span><strong class="${entry.amount < 0n ? 'negative' : ''}">${entry.amount > 0n ? '+' : ''}${formatMoney(entry.amount)}</strong><small>proposal ${esc(draft.reference)} · source ${esc(entry.sourceReference)}</small></div>`))}</div>
          ${draft?.entries.length ? `<div class="totals"><span>Gross <b>${formatMoney(draftTotals.gross)}</b></span><span>Deductions <b>${formatMoney(draftTotals.deductions)}</b></span><span>Net <b>${formatMoney(draftTotals.net)}</b></span></div>` : ''}
        </article>
        <article class="panel wide posted">
          <div class="panel-head"><div>Immutable posted ledger</div><small>${state.posted.length} entries</small></div>
          <div class="table">${rows(state.posted.map((entry) => `<div class="ledger-row ${entry.reversalOf ? 'contra' : ''}"><code>${esc(entry.postedId)}</code><b>${esc(entry.head)}</b><span>${esc(entry.source)}</span><strong class="${entry.amount < 0n ? 'negative' : ''}">${entry.amount > 0n ? '+' : ''}${formatMoney(entry.amount)}</strong><small>ref ${esc(entry.ledgerReference)} · source ${esc(entry.sourceReference)}${entry.reversalOf ? ` · contra of ${esc(entry.reversalOf)}` : ''}</small></div>`))}</div>
          ${state.posted.length ? `<div class="totals"><span>Gross entries <b>${formatMoney(postedTotals.gross)}</b></span><span>Deduction entries <b>${formatMoney(postedTotals.deductions)}</b></span><span>Ledger net <b>${formatMoney(postedTotals.net)}</b></span></div>` : ''}
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
    if (action === 'seed') attempt(seedDemo);
    if (action === 'proof') attempt(attachDemoProof);
    if (action === 'approve-inputs') attempt(approveDemoInputs);
    if (action === 'calculate') attempt(runExternalCalculator);
    if (action === 'approve-draft') attempt(sealAndApproveDemo);
    if (action === 'commit') attempt(commitDemo);
    if (action === 'correct') attempt(correctDemo);
    if (action === 'reset') { reset(); render(); }
  }));
}

render();
