import './styles.css';

type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
type Row = Record<string, Json>;
type Summary = {
  payroll: { gross_minor: number; deductions_minor: number; net_minor: number };
  liability: { due_minor: number; paid_minor: number; allocated_minor: number; outstanding_minor: number };
};
type Stage = { id: string; title: string; explanation: string; outcome: Row; summary: Summary; tables: Record<string, Row[]> };
type Flow = {
  source: { revision: string; sha256: Record<string, string> };
  fixture: Record<string, Json>;
  catalogue: { record_types: string[]; ledger_kinds: string[] };
  stages: Stage[];
};

const app = document.querySelector<HTMLDivElement>('#app')!;
const storageMap = new URL('../docs/diagrams/payroll-canonical-storage.svg', import.meta.url).href;
const employeeJourney = new URL('../docs/diagrams/payroll-employee-journey.svg', import.meta.url).href;
let flow: Flow;
let selected = 0;

const escapeHtml = (value: unknown): string => String(value)
  .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
  .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
const money = (minor: number): string => new Intl.NumberFormat('en-IN', {
  style: 'currency', currency: 'INR', minimumFractionDigits: 2,
}).format(minor / 100);
const rowId = (row: Row): string => String(row.key ?? row.entry_id ?? row.ledger_entry_id);
const recordType = (row: Row): string => flow.catalogue.record_types.find((type) => String(row.key).startsWith(`${type}:`)) ?? 'unknown';

function jsonDetails(row: Row, isNew: boolean): string {
  const value = row.value as Row | undefined;
  const label = value?.label ?? value?.operation ?? value?.direction ?? row.row_kind ?? rowId(row);
  return `<details class="json-row${isNew ? ' new' : ''}">
    <summary><code>${escapeHtml(rowId(row))}</code><span>${escapeHtml(label)}</span>${isNew ? '<b>new</b>' : ''}</summary>
    <pre>${escapeHtml(JSON.stringify(row, null, 2))}</pre>
  </details>`;
}

function tablePanel(table: string, title: string, description: string, rows: Row[], previous: Row[]): string {
  const old = new Set(previous.map(rowId));
  return `<section class="panel ledger-panel">
    <div class="panel-head"><div><span class="dot"></span><h2>${title}</h2></div><code>${table}</code></div>
    <p class="panel-copy">${description}</p>
    <div class="rows">${rows.length ? rows.map((row) => jsonDetails(row, !old.has(rowId(row)))).join('') : '<p class="empty">No rows at this stage</p>'}</div>
  </section>`;
}

function recordPanel(table: string, title: string, rows: Row[], previous: Row[], grouped: boolean): string {
  const old = new Set(previous.map(rowId));
  const groups = grouped
    ? flow.catalogue.record_types.filter((type) => type !== 'payroll.employee.settings').map((type) => [type, rows.filter((row) => recordType(row) === type)] as const)
    : [['payroll.employee.settings', rows] as const];
  return `<section class="panel records-panel">
    <div class="panel-head"><div><span class="dot"></span><h2>${title}</h2></div><code>${table}</code></div>
    <p class="panel-copy">Every record shows its exact <code>tenant</code>, canonical <code>key</code>, immutable <code>value</code>, <code>ts</code>, and availability <code>state</code>.</p>
    ${groups.map(([type, records]) => `<details class="record-group"${records.length ? ' open' : ''}>
      <summary><code>${type}</code><span>${records.length} row${records.length === 1 ? '' : 's'}</span></summary>
      <div class="rows">${records.length ? records.map((row) => jsonDetails(row, !old.has(rowId(row)))).join('') : '<p class="empty">Not witnessed yet</p>'}</div>
    </details>`).join('')}
  </section>`;
}

function render(focusSelector?: string): void {
  const stage = flow.stages[selected];
  const before = selected ? flow.stages[selected - 1].tables : {};
  const p = stage.summary.payroll;
  const l = stage.summary.liability;
  app.innerHTML = `
    <header>
      <div class="eyebrow">PAYROLL LEDGER LAB · ACTUAL SQLITE SNAPSHOTS</div>
      <div class="title-row"><div><h1>Three ledgers. One connected payroll.</h1><p>Browser playback of captured rows from a fresh SQLite run — this page is not a live database.</p></div><div class="fixture"><b>E101</b><span>November 2026 · INR minor units</span></div></div>
      <nav class="stage-rail" aria-label="Simulation stages">${flow.stages.map((item, index) => `<button data-stage="${index}" class="${index === selected ? 'active' : ''} ${index < selected ? 'done' : ''}" aria-current="${index === selected ? 'step' : 'false'}"><span>${index + 1}</span>${escapeHtml(item.title)}</button>`).join('')}</nav>
    </header>
    <main>
      <section class="stage-card" aria-live="polite">
        <div><span class="step">Stage ${selected + 1} of ${flow.stages.length}</span><h2>${escapeHtml(stage.title)}</h2><p>${escapeHtml(stage.explanation)}</p></div>
        <div class="controls">
          <label>Jump to stage<select id="stage-select">${flow.stages.map((item, index) => `<option value="${index}" ${index === selected ? 'selected' : ''}>${index + 1}. ${escapeHtml(item.title)}</option>`).join('')}</select></label>
          <button id="previous" ${selected === 0 ? 'disabled' : ''}>← Previous</button><button id="next" ${selected === flow.stages.length - 1 ? 'disabled' : ''}>Next →</button>
          <button id="complete">Show completed flow</button><button id="reset" class="ghost">Reset to start</button>
        </div>
        <details class="outcome"><summary>Operation outcome</summary><pre>${escapeHtml(JSON.stringify(stage.outcome, null, 2))}</pre></details>
      </section>
      <section class="summary" aria-label="Selected snapshot totals">
        <div><span>Gross</span><b>${money(p.gross_minor)}</b><small>${p.gross_minor.toLocaleString('en-IN')} minor</small></div>
        <div><span>Deductions</span><b>${money(p.deductions_minor)}</b><small>${p.deductions_minor.toLocaleString('en-IN')} minor</small></div>
        <div><span>Net</span><b>${money(p.net_minor)}</b><small>${p.net_minor.toLocaleString('en-IN')} minor</small></div>
        <div class="liability"><span>Employer liability</span><b>${money(l.outstanding_minor)} outstanding</b><small>due ${money(l.due_minor)} · paid ${money(l.paid_minor)} · allocated ${money(l.allocated_minor)}</small></div>
      </section>
      <section class="concepts panel">
        <h2>How the records connect</h2>
        <p><code>payroll.earning</code> is a salary entitlement; <code>payroll.instruction</code> is a monthly or one-time source. <code>payroll.draft</code> fixes the header, sources, hash, and totals while draft-ledger rows hold amounts. <code>payroll.draft.control</code> records hold/release state, and <code>payroll.draft.review</code> is an optional review bound to exact content.</p>
        <p>A resolution records draft treatment. An application records committed consumption. The operation receipt is durable replay evidence. <code>payroll.draft.*</code> is family shorthand, never a stored record type.</p>
        <p>Keys use <code>&lt;type&gt;:&lt;subject&gt;:&lt;record&gt;</code>; opaque colons and backslashes are escaped. Expand the rows below to inspect exact references.</p>
        <div class="diagram-links"><a href="${storageMap}">Storage map ↗</a><a href="${employeeJourney}">Employee journey ↗</a><a href="/canonical-flow.json" download>Download snapshot JSON ↓</a></div>
      </section>
      <div class="ledger-grid">
        ${tablePanel('payroll_draft_ledger', 'Draft ledger', 'Immutable monetary effects of the exact employee draft.', stage.tables.payroll_draft_ledger, before.payroll_draft_ledger ?? [])}
        ${tablePanel('payroll_ledger', 'Payroll ledger', 'Immutable posted effects. Commit appends these with application and receipt evidence.', stage.tables.payroll_ledger, before.payroll_ledger ?? [])}
        ${tablePanel('payroll_employer_liability_ledger', 'Employer liability ledger', 'Obligation, challan-backed remittance, and allocation are distinct facts.', stage.tables.payroll_employer_liability_ledger, before.payroll_employer_liability_ledger ?? [])}
      </div>
      ${recordPanel('payroll_l1_records', 'L1 records', stage.tables.payroll_l1_records, before.payroll_l1_records ?? [], true)}
      ${recordPanel('payroll_l2_records', 'L2 auxiliary records', stage.tables.payroll_l2_records, before.payroll_l2_records ?? [], false)}
      <footer><span>Source revision ${escapeHtml(flow.source.revision)}</span><details><summary>Provenance hashes</summary><pre>${escapeHtml(JSON.stringify(flow.source.sha256, null, 2))}</pre></details></footer>
    </main>`;

  document.querySelectorAll<HTMLButtonElement>('[data-stage]').forEach((button) => button.addEventListener('click', () => go(Number(button.dataset.stage))));
  document.querySelector<HTMLSelectElement>('#stage-select')!.addEventListener('change', (event) => go(Number((event.target as HTMLSelectElement).value)));
  document.querySelector<HTMLButtonElement>('#previous')!.addEventListener('click', () => go(selected - 1));
  document.querySelector<HTMLButtonElement>('#next')!.addEventListener('click', () => go(selected + 1));
  document.querySelector<HTMLButtonElement>('#complete')!.addEventListener('click', () => go(flow.stages.length - 1));
  document.querySelector<HTMLButtonElement>('#reset')!.addEventListener('click', () => go(0));
  if (focusSelector) {
    const target = document.querySelector<HTMLElement>(focusSelector);
    ((target instanceof HTMLButtonElement && target.disabled) ? document.querySelector<HTMLSelectElement>('#stage-select') : target)?.focus();
  }
}

function go(index: number): void {
  const active = document.activeElement as HTMLElement;
  const focusSelector = active.dataset.stage === undefined
    ? (active.id ? `#${active.id}` : undefined)
    : `[data-stage="${active.dataset.stage}"]`;
  selected = Math.max(0, Math.min(index, flow.stages.length - 1));
  render(focusSelector);
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function load(): Promise<void> {
  app.innerHTML = '<main class="loading"><p>Loading canonical SQLite snapshots…</p></main>';
  try {
    const response = await fetch('/canonical-flow.json');
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    flow = await response.json() as Flow;
    render();
  } catch (error) {
    app.innerHTML = `<main class="loading error"><h1>Snapshot could not be loaded</h1><p>${escapeHtml(error)}</p><p>Regenerate it with <code>python3 -m sqlite_lab.demo --output public/canonical-flow.json</code>, then reload this page.</p><button onclick="location.reload()">Retry</button></main>`;
  }
}

void load();
