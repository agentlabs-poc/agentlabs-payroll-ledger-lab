import './styles.css';
import { decodeKeyColumns } from './key-columns';

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
type CanonicalDefinitions = {
  status: string;
  identity_rule: string;
  prototype_notice: string;
  open_decision: { id: string; question: string };
  storage_contract: {
    status: string;
    columns: string[];
    example: { serialized: string; segments: string[] };
    meaning_rule: string;
    indexing_rule: string;
    prototype_notice: string;
  };
  tables: { name: string; role: string; meaning: string }[];
  record_types: { type: string; layer: string; owner: string; meaning: string; identity: string }[];
};

const app = document.querySelector<HTMLDivElement>('#app')!;
const storageMap = new URL('../docs/diagrams/payroll-canonical-storage.svg', import.meta.url).href;
const employeeJourney = new URL('../docs/diagrams/payroll-employee-journey.svg', import.meta.url).href;
const definitionsUrl = new URL('../docs/design/canonical-definitions.json', import.meta.url).href;
let flow: Flow;
let definitions: CanonicalDefinitions;
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
  const columns = typeof row.key === 'string' ? decodeKeyColumns(row.key) : [];
  const preview = columns.length ? `<div class="key-preview"><div><b>Decoded key columns · storage preview</b><small>Existing snapshot key; final employee identity is pending.</small></div><div class="key-preview-columns">${Array.from({ length: 10 }, (_, index) => {
    const column = `key${index + 1}`;
    return `<div class="key-column" data-column="${column}"><span>${column}</span>${columns[index] === undefined ? '<em>unused</em>' : `<code>${escapeHtml(columns[index])}</code>`}</div>`;
  }).join('')}</div></div>` : '';
  return `<details class="json-row${isNew ? ' new' : ''}">
    <summary><code>${escapeHtml(rowId(row))}</code><span>${escapeHtml(label)}</span>${isNew ? '<b>new</b>' : ''}</summary>
    <pre>${escapeHtml(JSON.stringify(row, null, 2))}</pre>
    ${preview}
  </details>`;
}

function timelineStage(stage: Stage, index: number): string {
  const previous = index ? flow.stages[index - 1].tables : {};
  const contributions = Object.entries(stage.tables).flatMap(([table, rows]) => {
    const old = new Set((previous[table] ?? []).map(rowId));
    const added = rows.filter((row) => !old.has(rowId(row)));
    if (!added.length) return [];
    const groups = table === 'payroll_l1_records' || table === 'payroll_l2_records'
      ? flow.catalogue.record_types.map((type) => [type, added.filter((row) => recordType(row) === type)] as const).filter(([, records]) => records.length)
      : [[table, added] as const];
    return groups.map(([type, records]) => `<section class="contribution">
      <div class="contribution-head"><code>${table}</code>${type === table ? '' : `<span>${type}</span>`}<b>${records.length} added</b></div>
      <div class="rows">${records.map((row) => jsonDetails(row, index === selected)).join('')}</div>
    </section>`);
  });
  return `<article class="timeline-step${index === selected ? ' current' : ''}" ${index === selected ? 'data-timeline-current' : ''}>
    <div class="timeline-marker"><span>${index + 1}</span></div>
    <div class="timeline-content panel">
      <div class="timeline-head"><div><span class="step">${escapeHtml(stage.id)}</span><h2>${escapeHtml(stage.title)}</h2></div><small>${contributions.length} contribution${contributions.length === 1 ? '' : 's'}</small></div>
      <p class="panel-copy">${escapeHtml(stage.explanation)}</p>
      ${contributions.length ? contributions.join('') : '<p class="empty">No rows appended</p>'}
    </div>
  </article>`;
}

function definitionsPanel(): string {
  const storage = definitions.storage_contract;
  const keyColumns = storage.columns.filter((column) => /^key\d+$/.test(column));
  return `<section class="definitions panel">
    <div class="definitions-head"><div><span class="eyebrow">PINNED CANONICAL DEFINITIONS</span><h2>Meaning, ownership, and identity status</h2></div><a href="${definitionsUrl}">Definition source ↗</a></div>
    <p>${escapeHtml(definitions.status)}</p>
    <div class="definition-notices">
      <div><b>Identity rule</b><p>${escapeHtml(definitions.identity_rule)}</p></div>
      <div class="prototype"><b>Prototype snapshot notice</b><p>${escapeHtml(definitions.prototype_notice)}</p></div>
      <div class="open-decision"><b>Open decision · ${escapeHtml(definitions.open_decision.id)}</b><p>${escapeHtml(definitions.open_decision.question)}</p></div>
    </div>
    <section class="storage-contract">
      <div><span class="eyebrow">PINNED STORAGE CONTRACT</span><h3>Generic key segments</h3><p>${escapeHtml(storage.status)}</p></div>
      <div class="key-columns">${storage.columns.map((column) => `<code>${escapeHtml(column)}</code>`).join('')}</div>
      <div class="key-example"><code>${escapeHtml(storage.example.serialized)}</code><ol>${storage.example.segments.map((segment, index) => `<li><span>${escapeHtml(keyColumns[index] ?? `key${index + 1}`)}</span><code>${escapeHtml(segment)}</code></li>`).join('')}</ol></div>
      <p><b>Meaning rule</b> ${escapeHtml(storage.meaning_rule)}</p>
      <p><b>Indexing rule</b> ${escapeHtml(storage.indexing_rule)}</p>
      <p class="prototype-contract"><b>Snapshot notice</b> ${escapeHtml(storage.prototype_notice)}</p>
    </section>
    <details open><summary>Five storage tables</summary><div class="definition-list">${definitions.tables.map((item) => `<article><code>${escapeHtml(item.name)}</code><span>${escapeHtml(item.role)}</span><p>${escapeHtml(item.meaning)}</p></article>`).join('')}</div></details>
    <details><summary>Ten canonical record types</summary><div class="definition-list">${definitions.record_types.map((item) => `<article><code>${escapeHtml(item.type)}</code><span>${escapeHtml(item.layer)} · ${escapeHtml(item.owner)}</span><p>${escapeHtml(item.meaning)}</p><small>${escapeHtml(item.identity)}</small></article>`).join('')}</div></details>
  </section>`;
}

function render(focusSelector?: string): void {
  const stage = flow.stages[selected];
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
        <p><code>payroll.earning</code> links an employee amount and effective dates to one component version; Basic and HRA are distinct earning components. <code>payroll.instruction</code> is a monthly or one-time source. <code>payroll.draft</code> fixes the header, sources, hash, and totals while draft-ledger rows hold amounts. <code>payroll.draft.control</code> records hold/release state, and <code>payroll.draft.review</code> is an optional review bound to exact content.</p>
        <p>A resolution records draft treatment. An application records committed consumption. The operation receipt is durable replay evidence. <code>payroll.draft.*</code> is family shorthand, never a stored record type.</p>
        <div class="diagram-links"><a href="${storageMap}">Storage map ↗</a><a href="${employeeJourney}">Employee journey ↗</a><a href="/canonical-flow.json" download>Download snapshot JSON ↓</a></div>
      </section>
      ${definitionsPanel()}
      <section class="timeline" aria-label="SQLite append timeline">
        <div class="timeline-title"><div><span class="eyebrow">APPEND TIMELINE</span><h2>L1 records and ledger rows in flow order</h2></div><p>Each step shows only rows first appended at that point. Expand any row for its complete SQLite snapshot.</p></div>
        ${flow.stages.slice(0, selected + 1).map(timelineStage).join('')}
      </section>
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
    const [flowResponse, definitionsResponse] = await Promise.all([fetch('/canonical-flow.json'), fetch(definitionsUrl)]);
    if (!flowResponse.ok) throw new Error(`${flowResponse.status} ${flowResponse.statusText}`);
    if (!definitionsResponse.ok) throw new Error(`${definitionsResponse.status} ${definitionsResponse.statusText}`);
    [flow, definitions] = await Promise.all([flowResponse.json(), definitionsResponse.json()]) as [Flow, CanonicalDefinitions];
    render();
  } catch (error) {
    app.innerHTML = `<main class="loading error"><h1>Demo data could not be loaded</h1><p>${escapeHtml(error)}</p><p>Check the pinned canonical definitions and regenerate snapshots with <code>python3 -m sqlite_lab.demo --output public/canonical-flow.json</code>, then reload this page.</p><button onclick="location.reload()">Retry</button></main>`;
  }
}

void load();
