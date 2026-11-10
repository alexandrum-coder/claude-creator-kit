#!/usr/bin/env node
// node render.mjs --props props.json --out-dir DIR
// props.json: {width, height, fps, colors, intro: {title, channel}, chapters: [{t, text}], lists: [{t, items}]}
// Writes intro.mp4 (H.264), chapter_NN.mov and list_NN.mov (ProRes 4444 with alpha).
// Prints {intro, overlays: [{file, t}]} on stdout (file names relative to DIR); progress goes to stderr.
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
const propsFile = opt('--props');
const outDir = opt('--out-dir');
if (!propsFile || !outDir) {
  console.error('Folosire: node render.mjs --props props.json --out-dir DIR');
  process.exit(2);
}

const props = JSON.parse(readFileSync(propsFile, 'utf8'));
const {width, height, fps, colors} = props;
const common = {width, height, fps, colors};
mkdirSync(outDir, {recursive: true});

const here = path.dirname(fileURLToPath(import.meta.url));
const serveUrl = await bundle({entryPoint: path.join(here, 'src', 'index.ts')});

const pad = (n) => String(n + 1).padStart(2, '0');
const jobs = [
  {id: 'Intro', file: 'intro.mp4', props: {...common, durationSec: 4, ...props.intro}, video: true},
  ...(props.chapters ?? []).map((c, i) => ({id: 'ChapterTitle', file: `chapter_${pad(i)}.mov`, props: {...common, text: c.text}, t: c.t})),
  ...(props.lists ?? []).map((l, i) => ({id: 'ListOverlay', file: `list_${pad(i)}.mov`, props: {...common, items: l.items}, t: l.t})),
];

const log = (...a) => console.error(...a);
for (const job of jobs) {
  const inputProps = job.props;
  const composition = await selectComposition({serveUrl, id: job.id, inputProps});
  const outputLocation = path.join(outDir, job.file);
  const settings = job.video
    ? {codec: 'h264', pixelFormat: 'yuv420p'}
    : {codec: 'prores', proResProfile: '4444', pixelFormat: 'yuva444p10le', imageFormat: 'png'};
  await renderMedia({composition, serveUrl, inputProps, outputLocation, ...settings});
  log(`ok ${job.file}`);
}

const overlays = jobs.filter((j) => !j.video).map((j) => ({file: j.file, t: j.t}));
process.stdout.write(JSON.stringify({intro: 'intro.mp4', overlays}) + '\n');
