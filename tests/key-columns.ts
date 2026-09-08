import { decodeKeyColumns } from '../src/key-columns';

for (const [key, expected] of [
  ['payroll.component:BASIC:1', ['payroll', 'component', 'BASIC', '1']],
  [String.raw`payroll.instruction.application:opaque\:id:APP.1`, ['payroll', 'instruction', 'application', 'opaque:id', 'APP.1']],
  [String.raw`payroll.instruction:opaque\\id:1`, ['payroll', 'instruction', 'opaque\\id', '1']],
] as const) {
  if (JSON.stringify(decodeKeyColumns(key)) !== JSON.stringify(expected)) throw new Error('canonical key decoder check failed');
}
for (const key of [String.raw`payroll.instruction:bad\q:1`, 'payroll.a.b.c.d.e.f.g.h.i:X:Y']) {
  let rejected = false;
  try { decodeKeyColumns(key); } catch { rejected = true; }
  if (!rejected) throw new Error('canonical key decoder rejection check failed');
}
