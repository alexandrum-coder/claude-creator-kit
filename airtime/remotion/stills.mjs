#!/usr/bin/env node
// node stills.mjs --id COMPOSITION --props props.json --frames 0,2,5 --out-dir DIR
// Renders single frames of a composition as PNG (frame_NNN.png, with alpha) to check motion without
// watching a video: a settled frame looks the same whether something animated or snapped into place.
// Run it with the working directory set to the remotion folder you test (the webpack cache is written
// next to the package.json nearest to the working directory). Files in ./public are served by staticFile().
import {readFileSync, mkdirSync} from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';

const args = process.argv.slice(2);
const opt = (name) => {
  const i = args.indexOf(name);
  return i >= 0 ? args[i + 1] : undefined;
};
const id = opt('--id');
const propsFile = opt('--props');
const frames = (opt('--frames') ?? '').split(',').filter(Boolean).map(Number);
const outDir = opt('--out-dir');
if (!id || !propsFile || !outDir || frames.length === 0) {
  console.error('Folosire: node stills.mjs --id COMPOZITIE --props props.json --frames 0,2,5 --out-dir DIR');
  process.exit(2);
}

const inputProps = JSON.parse(readFileSync(propsFile, 'utf8'));
mkdirSync(outDir, {recursive: true});
const here = path.dirname(fileURLToPath(import.meta.url));
const serveUrl = await bundle({entryPoint: path.join(here, 'src', 'index.ts'), publicDir: path.join(here, 'public')});
const composition = await selectComposition({serveUrl, id, inputProps, logLevel: 'error'});
for (const frame of frames) {
  const output = path.join(outDir, `frame_${String(frame).padStart(3, '0')}.png`);
  await renderStill({composition, serveUrl, inputProps, frame, output, imageFormat: 'png', logLevel: 'error'});
  console.error(`ok ${output}`);
}
process.stdout.write(JSON.stringify({id, frames, durationInFrames: composition.durationInFrames}) + '\n');
