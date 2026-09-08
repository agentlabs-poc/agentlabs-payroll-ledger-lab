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
