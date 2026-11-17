#!/usr/bin/env node
// node overlay.mjs --id COMPOSITION --props props.json --out FILE.mov
// Renders one composition as ProRes 4444 with alpha, with the same settings as the overlays of render.mjs.
// Used by the reels layer (reels_fx.py) for NumberedList (PLAN, D-46). Progress goes to stderr.
import {readFileSync, mkdirSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderMedia, selectComposition} from '@remotion/renderer';

const args = process.argv.slice(2);
const opt = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};
const id = opt('--id');
const propsFile = opt('--props');
const out = opt('--out');
if (!id || !propsFile || !out) {
  console.error('Folosire: node overlay.mjs --id COMPOZITIE --props props.json --out FISIER.mov');
  process.exit(2);
}

const inputProps = JSON.parse(readFileSync(propsFile, 'utf8'));
mkdirSync(path.dirname(path.resolve(out)), {recursive: true});
const here = path.dirname(fileURLToPath(import.meta.url));
const serveUrl = await bundle({entryPoint: path.join(here, 'src', 'index.ts')});
const composition = await selectComposition({serveUrl, id, inputProps, logLevel: 'error'});
await renderMedia({
  composition,
  serveUrl,
  inputProps,
  outputLocation: path.resolve(out),
  logLevel: 'error',
  codec: 'prores',
  proResProfile: '4444',
  pixelFormat: 'yuva444p10le',
  imageFormat: 'png',
});
console.error(`ok ${out}`);
