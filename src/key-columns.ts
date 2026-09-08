export function decodeKeyColumns(key: string): string[] {
  const separator = key.indexOf(':');
  if (separator < 1) throw new Error('invalid canonical key');
  const columns = key.slice(0, separator).split('.');
  const identities = [''];
  for (let index = separator + 1; index < key.length; index += 1) {
    const character = key[index];
    if (character === '\\') {
      const escaped = key[++index];
      if (escaped !== ':' && escaped !== '\\') throw new Error('invalid canonical key escape');
      identities[identities.length - 1] += escaped;
    } else if (character === ':') {
      identities.push('');
    } else {
      identities[identities.length - 1] += character;
    }
  }
  const decoded = [...columns, ...identities];
  if (identities.length !== 2 || decoded.some((part) => !part) || decoded.length > 10) throw new Error('invalid canonical key');
  return decoded;
}

for (const [key, expected] of [
  ['payroll.component:BASIC:1', ['payroll', 'component', 'BASIC', '1']],
  [String.raw`payroll.instruction.application:opaque\:id:APP.1`, ['payroll', 'instruction', 'application', 'opaque:id', 'APP.1']],
  [String.raw`payroll.instruction:opaque\\id:1`, ['payroll', 'instruction', 'opaque\\id', '1']],
] as const) {
  if (JSON.stringify(decodeKeyColumns(key)) !== JSON.stringify(expected)) throw new Error('canonical key decoder self-check failed');
}
for (const key of [String.raw`payroll.instruction:bad\q:1`, 'payroll.a.b.c.d.e.f.g.h.i:X:Y']) {
  let rejected = false;
  try { decodeKeyColumns(key); } catch { rejected = true; }
  if (!rejected) throw new Error('canonical key decoder rejection self-check failed');
}
