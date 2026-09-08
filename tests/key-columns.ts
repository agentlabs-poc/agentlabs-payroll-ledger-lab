import { decodeKeyColumns } from '../src/key-columns';

const valid = [
  ['payroll.component:BASIC:1', ['payroll', 'component', 'BASIC', '1']],
  ['payroll.earning:E101:EARN.BASIC:1', ['payroll', 'earning', 'E101', 'EARN.BASIC', '1']],
  ['payroll.instruction:E101:I-LOAN:2', ['payroll', 'instruction', 'E101', 'I-LOAN', '2']],
  ['payroll.draft:E101:D1:1', ['payroll', 'draft', 'E101', 'D1', '1']],
  ['payroll.draft.control:E101:D1:3', ['payroll', 'draft', 'control', 'E101', 'D1', '3']],
  ['payroll.draft.review:E101:D1:R1', ['payroll', 'draft', 'review', 'E101', 'D1', 'R1']],
  ['payroll.instruction.resolution:E101:D1:RES1', ['payroll', 'instruction', 'resolution', 'E101', 'D1', 'RES1']],
  ['payroll.instruction.application:E101:I-LOAN:APP.1', ['payroll', 'instruction', 'application', 'E101', 'I-LOAN', 'APP.1']],
  ['payroll.operation.receipt:E101:D1:RCPT1', ['payroll', 'operation', 'receipt', 'E101', 'D1', 'RCPT1']],
  ['payroll.employee.settings:E101:1', ['payroll', 'employee', 'settings', 'E101', '1']],
  [String.raw`payroll.instruction:E\:101:opaque\\id:1`, ['payroll', 'instruction', 'E:101', 'opaque\\id', '1']],
] as const;

for (const [key, expected] of valid) {
  const actual = decodeKeyColumns(key);
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`canonical key decoder check failed for ${key}: ${JSON.stringify(actual)}`);
  }
}

for (const key of [
  '',
  'payroll.component',
  'payroll..component:BASIC:1',
  'payroll.unknown:X:Y',
  'payroll.component:BASIC',
  'payroll.component:BASIC:1:extra',
  'payroll.earning:E101:EARN1',
  'payroll.earning:E101:EARN1:1:extra',
  String.raw`payroll.instruction:E101:bad\q:1`,
  'payroll.instruction:E101:I1:bad\\',
  'payroll.instruction:E101::1',
  'payroll.a.b.c.d.e.f.g.h.i:X:Y',
]) {
  let rejected = false;
  try { decodeKeyColumns(key); } catch { rejected = true; }
  if (!rejected) throw new Error(`canonical key decoder accepted ${key}`);
}
