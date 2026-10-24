// Read shared tokens without a TUI framework or external dependencies.
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export function loadPalette(theme = 'dark', profile = '256') {
  const document = JSON.parse(readFileSync(new URL('../../design/tokens/candidate.json', import.meta.url), 'utf8'));
  if (document.format !== 'tuivory.tokens.draft') throw new Error('Unsupported token format');
  const palette = document.palettes[`${theme}-${profile}`];
  if (!palette) throw new Error(`Unknown palette: ${theme}-${profile}`);
  return palette;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  console.log(JSON.stringify(loadPalette(process.argv[2], process.argv[3])));
}
