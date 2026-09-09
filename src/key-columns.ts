const identityArity = {
  'payroll.component': 2,
  'payroll.earning': 3,
  'payroll.instruction': 3,
  'payroll.draft': 3,
  'payroll.draft.control': 3,
  'payroll.draft.review': 3,
  'payroll.instruction.resolution': 3,
  'payroll.instruction.application': 3,
  'payroll.operation.receipt': 3,
  'payroll.employee.settings': 2,
} as const;

export function decodeKeyColumns(key: string): string[] {
  const separator = key.indexOf(':');
  if (separator < 1) throw new Error('invalid canonical key');
  const type = key.slice(0, separator);
  const expectedIdentities = identityArity[type as keyof typeof identityArity];
  if (expectedIdentities === undefined) throw new Error('invalid canonical key');
  const columns = type.split('.');
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
  if (identities.length !== expectedIdentities || decoded.some((part) => !part) || decoded.length > 10) throw new Error('invalid canonical key');
  return decoded;
}
