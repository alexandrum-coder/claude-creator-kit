# AirTime end-to-end test, up to the confirmation table

Isolated run of the real pipeline on a generated clip. Nothing is uploaded or scheduled. Nothing was written to
`~/.claude`, `~/.airtime`, `~/AirTime` or the main kit, but the skill and the agent READ the real home in a few places
(see "Isolation leaks"). Everything generated lives in the scratchpad (`$S/airtime-e2e/`). Date of the run: 2026-11-11.

## Files

| File | What it is |
|---|---|
| `make_test_clip.sh OUT_DIR` | Writes `Antrenament spate – test ședință.mov`: 75 s, 1920x1080, `testsrc2`, voice made with `say -v Ioana` (explanation, a retaken phrase, 1.5 s pause, a 12 s noise gap = the demonstration, the reaction after). Codec: `hevc_videotoolbox` (present in the ffmpeg shim; the script falls back to libx264). |
| `e2e/run.sh` | Phases `prep`, `a`, `approve`, `b`, `c`, `checkc` (see the header of the file). Holds the exact prompts and the transcript check. |
| `e2e/youtube.py` | Test double of `scripts/youtube.py` (run C only). |
| `e2e/check.sh` | Test double of `scripts/check.sh` (run C only). |
| `e2e/make_e2e_copy.sh` | Builds the plugin copy for run C: rsync of `airtime/` (without `tests/`), then the two doubles replace `scripts/youtube.py` and `scripts/check.sh`; the real ones stay beside them as `youtube_real.py` and `check_real.sh`; also writes the fake config dir. |
| `e2e/make_shorts_copy.sh` | Builds `SHORTS_ROOT` for the test: a copy of claude-shorts with three patches (see "Environment findings"). |

The files are not named `test_*`, so pytest does not collect them (58 tests still pass).

## What is doubled, stated plainly

In run C, and only there:

1. **`youtube.py whoami` is doubled.** It prints a fake channel name ("Canal de test AirTime") and exits 0, so there is no
   token, no network and no real YouTube connection. `upload` or `verify` without `--dry-run` is refused: the argv is
   appended to a log (`$AIRTIME_E2E_REFUSAL_LOG`) and the exit code is 97. Everything else (including `upload --dry-run`)
   goes to the real script with the same argv and exit code.
2. **The plugin check is doubled.** `check.sh` runs the real check with `CLAUDE_CONFIG_DIR` pointed at a fake config
   dir whose `plugins/installed_plugins.json` lists social-seo, brand-voice, marketing and ecc (each with a stub
   `SKILL.md`). So the real check for those four plugins and for the real YouTube connection was NOT exercised. The
   other checks (ffmpeg, ffprobe, node, venv, shorts, shorts venv, remotion) ran for real.
3. Claude's own profile (`$S/cfg-test`, already logged in by the user) was never modified by the test (Claude itself only adds its own session files there). Runs A and B used the real
   `scripts/` with no doubles (so in B, `texte` printed "social-seo lipsește": the real situation without that plugin).

`logs/refused.log` in the scratchpad holds one line, `["--profile","principal","upload","--file","x","--meta","y"]`: it
comes from my own smoke test of the double (before any run), not from a run. Run C used its own log
(`logs/refused-c.log`), which was never created: no refusal happened.

## Setup

- `S=/private/tmp/claude-501/-Users-pixelpoetry-Claude-Cowork-Tools/d109280c-9e44-404e-9a3d-0b312ae9e2d8/scratchpad`, `SCR=$S/airtime-e2e`.
- `AIRTIME_HOME=$SCR/home` (symlinks `venv` -> `$S/airtime-venv`, `remotion` -> `$S/remotion`; `speed.json` copied from
  the speed test: model **small**; a profile `principal` pre-seeded from `airtime_config.DEFAULTS` + `save_profile`, with
  `clip_type: demonstratii`, keywords spate/postura, no first-run questions).
- Runs A/B: `AIRTIME_RUNS=$SCR/runs-ab`, plugin `--plugin-dir <worktree>/airtime`. Run C: `AIRTIME_RUNS=$SCR/runs-c`
  (empty at start), plugin = the e2e copy `$SCR/plugin-c`.
- Common: `CLAUDE_CONFIG_DIR=$S/cfg-test`, `SHORTS_ROOT=$SCR/shorts-e2e`, `PATH=$S/ffshim:$HOME/.local/node/bin:$PATH`,
  `claude -p --model sonnet --strict-mcp-config --mcp-config '{"mcpServers":{}}' --allowedTools=... --output-format stream-json --verbose`
  (run C adds `Skill` to the allowed tools; no browser tool exists in that configuration).
- `CLAUDE_PLUGIN_ROOT` is exported by hand (see finding 1).
- No prompt contains the words "da" or "confirm" (checked with `grep -w`).

## claude -p runs

| Run | What | Result |
|---|---|---|
| A (failed, kept) | agent `propune` | The agent stopped at its environment preamble (no plugin root, finding 1). Nothing was processed. `logs/runA-failed.jsonl`. |
| B | One prompt, the agent called four times in order: `propune`, then (the main Claude writes `cuts-aprobate.json` with all 5 cuts) `monteaza`, `texte`, (the main Claude writes `reels-aprobate.json` with the first 3 candidates) `reels`. | `propune`, `monteaza`, `texte` passed. `reels` failed on `mediapipe` (finding 2). 10 min. |
| C (interrupted) | skill flow "AirTime" | Killed at the `texte` step by an account usage limit (not a plugin fault). `logs/runC-interrupted.jsonl`. |
| C | skill flow "AirTime", all answers in the prompt | Reached the confirmation table. 17 min, 28 turns. |

Count: 4 `claude -p` launches in all (A failed, B, C interrupted, C), which is the budget of 3 plus the one repeat of C
allowed by the controller for the usage-limit interruption. Deviation from the plan: because A was lost to the
environment problem and the budget was then full, the agent `propune` ran inside B, and the cuts approval in B was
written by the main Claude inside the prompt, not by a test script (the `approve` phase of `run.sh` stays for the record).

## Pas 2 (checked against real output)

Run B folder: `$SCR/runs-ab/2026-11-11-antrenament-spate-test-sedinta/`. Run C folder: `$SCR/runs-c/2026-11-11-antrenament-spate-test-sedinta/`.

| Item | Result | Evidence |
|---|---|---|
| No cut in the 12 s gap | PASS | Gap between words 53.57 to 65.83 s (classified `demo` by `silences.py`). Run B cuts: 10.95-11.75, 12.00-15.97, 21.24-21.99, 26.97-27.78, 47.62-48.92: none inside the gap. Run C proposed the identical 5 cuts. |
| The retake is proposed | PASS | Cut 2, reason `reluare`, 12.00-15.97 ("Trageți coatele spre spate..."), in both runs. (The first version of the clip repeated the phrase word for word and Whisper dropped the repeat, so the second take was reworded after "Trageți coatele spre spate".) |
| `youtube.mp4` = `curat.mp4` + 4 s (±0.2) | PASS | Run B: 67.406 s -> 71.409 s, difference 4.003 s. Run C: same files, same durations (67.406 / 71.409). Intro 4 s. |
| `valid_chapters` without errors | PASS | Run B: 3 chapters (00:00, 00:26, 00:46), `valid_chapters` returns `[]`. Run C: 4 chapters (00:00, 00:21, 00:36, 00:54), accepted by the dry-run. |
| 3 MP4 of 1080x1920 with subtitles | PASS | Run C `reels/short_01..03_ig.mp4`, all 1080x1920 (ffprobe). A frame of reel 1 (6 s) shows burned-in bold captions ("COBORUȚI UMERI ȘI"). Run B reels did not come out through the agent (finding 2); the same `reels.py build` run by hand on run B's approved file, on the patched shorts copy, gave 3 files of 1080x1920, 19.9 / 21.6 / 25.9 s. |
| `instagram.json`, 3-5 hashtags per reel | PASS | Run C: 3 entries, 5 hashtags each. |
| `youtube.py upload --dry-run` passes | PASS | Real `youtube.py` on run B's and run C's files: exit 0, `warnings: []`, `privacyStatus: private`, `publishAt 2026-11-14T16:00:00Z` (18:00 Bucharest). The agent ran the same call itself. |

Other agent behaviour noted: `texte` wrote only 3 candidates, not the 8-12 its sheet asks for, and said why (a 67 s clip
cannot give more without overlap). Within the spirit of the rule, not an error.

## Run C: the skill flow

Prompt (starts with "AirTime"; clip path, voice not separate, Facebook nu, Shorts nu, date 2026-11-14, approve all cuts,
candidates 1-3, style bold, stop at the final table). Observed: one `Skill` call (`airtime:airtime`), four `Agent` calls
(`propune`, `monteaza`, `texte`, `reels`), `check.sh --quick` through the double, a final table with 4 rows (YouTube
2026-11-14 18:00; reels 2026-11-15, -16, -17 at 19:00; Facebook nu), full texts, and the request to write "da" or "confirm".
`calendar.json` has 4 items, all `planificat`. Nothing was published.

Transcript check (`e2e/run.sh checkc`, on `logs/runC.jsonl`):

```
tool calls: {'Skill': 1, 'Bash': 64, 'Agent': 4, 'Read': 10, 'Write': 6}
youtube upload/verify without --dry-run: none
browser tool calls: none
refusal log: empty or absent        (exit code 0)
```

The check walks every `tool_use` block, flags any Bash command that mentions `youtube.py` or `youtube_real.py` with
`upload` or `verify` and without `--dry-run`, any tool name matching chrome/browser/playwright, and a non-empty refusal log.

## Carried from Task 8

**(a) Shape of `reels-aprobate.json`.** The skill writes a subset of `candidati.json`, i.e. `{"segments":[...], "style", "platform",
"content_type"}`. In run B and run C the agent/skill wrote exactly that shape and `reels.py build` accepted it (run C
rendered 3 reels from it; the manual build on run B's file rendered 3). The bare-list shape was not tried in this test.

**(b) Short re-upload risk (open, not fixed).** The duplicate guard of `youtube.py upload` keys on the sha256 of the file
in `uploaded.json`. If a reel or Short is re-rendered (new style, a changed cut, a new run of `reels.py build`), the bytes
change, the sha256 is new, and the guard no longer sees the earlier upload, so the same Short could be uploaded twice. The
skill's `calendar.json` states (`programat`, `esuat` with an `id` in `ref`) protect a single run, not a re-render. Not
exercised here (no real upload); parked for the final review. This task touches only `airtime/tests/`.

## Found in the plugin / environment (not fixed here)

1. **No plugin root under `--plugin-dir`.** The agent's preamble uses `CLAUDE_PLUGIN_ROOT`, else the `airtime`
   `installPath` from `$CLAUDE_CONFIG_DIR/plugins/installed_plugins.json`. With `claude -p --plugin-dir`, the agent's
   Bash had no `CLAUDE_PLUGIN_ROOT` and `cfg-test` has no `installed_plugins.json`, so run A failed with
   "AirTime nu e instalat complet". The test exports `CLAUDE_PLUGIN_ROOT` itself. A marketplace install writes
   `installed_plugins.json`, so the fallback should work there; that path is untested until Task 12.
2. **`reels` fails on a horizontal clip with a fresh claude-shorts environment.** `~/.shorts-skill` has mediapipe 1.2.2,
   which has no `mp.solutions`; claude-shorts `compute_reframe.py` calls `mp.solutions.face_detection`:
   `AttributeError: module 'mediapipe' has no attribute 'solutions'` (run B, `reels`). `setup.sh` installs mediapipe
   without a version pin, so a new install gets the same. Task 5 never ran the horizontal reframe for real. Needs a pinned
   mediapipe (0.10.x) in the setup, or a plugin-side guard.
3. **`export.sh` of claude-shorts fails on macOS.** It ends with `paste -sd ','` (GNU form); BSD `paste` needs `-`, so
   the script exits 1 after writing the files and `reels.py` reports `export: exit 1`. Found when the render finally
   worked.
4. **The scratch claude-shorts clone has no `node_modules`** (`setup.sh` was not run, by ruling), so its Remotion
   render fails with `Cannot find package '@remotion/bundler'`.

5. **Isolation leak.** See "Isolation leaks" below: the skill and agent read `~/.airtime`, `~/AirTime`, `~/.claude/plugins` and search
   the disk with `find /` when the plugin root or `installed_plugins.json` is missing.

For the test only, `make_shorts_copy.sh` works around 2-4 in a copy under `$SCR` (the original clone and `~/.shorts-skill`
are untouched): face tracking returns no positions when `mp.solutions` is missing (the test clip has no face, so a working
detector would find none either; the reframe falls back to its default crop), `export.sh` gets `paste -sd ',' -`, and
`remotion/node_modules` points at the AirTime Remotion install. Reels in runs B (manual build) and C came out through this
copy. Consequence: the real horizontal-face reframe was not tested.

Other notes: in run C the model read `tests/e2e/check.sh` (the double) with `cat` while diagnosing; harmless here, but a
reminder that the double is visible in the worktree path. Remotion's first render downloaded a headless Chrome into
`./.remotion` of the working folder (it landed in the worktree during the first run); it was moved out and `run.sh` now
does `cd "$SCR"` first.

## Isolation leaks: reads of the real home (no writes)

The environment variables point at the scratchpad, but the transcripts show the agent and the skill looking at the real
home. Nothing was written there; the reads are listed per run (from `logs/*.jsonl`, Bash `tool_use` inputs; the
`${VAR:-$HOME/...}` fallbacks of the environment preamble and the `os.path.expanduser("~/.claude")` fallback in its
Python snippet are not counted: they are only reached when the variable is unset, which it was not).

| Run | Command (as run) | Reads |
|---|---|---|
| B | `ls -la ~/.claude/plugins/installed_plugins.json` | the real plugin list |
| C | `ls /.../airtime-e2e/ ; ls ~/.airtime/profiles` | the real profile folder (it does not exist on this machine) |
| C | `PY="$HOME/.airtime/venv/bin/python"` | a path in the real home (the agent tried it as the interpreter) |
| C | `ls -la "$HOME/.airtime" \| head -5` | the real AirTime home (absent) |
| C | `ls -la "$HOME/.claude/plugins/installed_plugins.json"` | the real plugin list |
| C | `find / -maxdepth 6 -iname "installed_plugins.json"` (twice), `find / -ipath "*social-seo*SKILL.md"` | whole-disk search, which also lists the real `~/.claude` |
| C, interrupted | `ls -la "$HOME/AirTime/"` | the real runs folder (absent) |
| C, interrupted | `ls -la ~/.claude/plugins/`, `find ~/.claude/plugins -maxdepth 1 -iname "*social*seo*"`, `cat ~/.claude/plugins/installed_plugins.json \| head -60` | the real plugin list, with contents |

Run A (failed) had no reference besides the preamble fallbacks.

Causes, to fix in the plugin (not touched here): the skill's "Prima rulare" section names `~/.airtime/profiles`
literally, so the model checks the real home instead of `$AIRTIME_HOME`; the agent's `installPath` fallback reads
`$CLAUDE_CONFIG_DIR/plugins/installed_plugins.json` and, when that file is missing (finding 1), the model goes looking in
`~/.claude/plugins` and with `find /`; `texte` looks for `social-seo` through the same file. A cleaner isolation
needs the plugin to resolve everything from `$AIRTIME_HOME` and `$CLAUDE_CONFIG_DIR` only and to stop at the first
miss instead of searching.

Check that there were no writes to those paths. The script below reads each transcript, takes every Write/Edit
`file_path` and every Bash command line, and flags a write only when a redirection or a `tee`/`cp`/`mv`/`rm`/`mkdir`/`touch`/`ln`/`sed -i`
targets `~/.claude`, `~/.airtime` or `~/AirTime` (also as `$HOME/...` or `/Users/<user>/...`):

```python
import json, re, sys
home = r"(?:~|\$HOME|/Users/pixelpoetry)"
real = re.compile(home + r"/(?:\.claude|\.airtime|AirTime)\b|\bfind /\s")
wr = re.compile(r"(?:>>?|\btee|\bcp|\bmv|\brm|\bmkdir|\btouch|\bln|sed -i)\s+[^\n;|&]*" + home + r"/(?:\.claude|\.airtime|AirTime)\b")
# for each transcript: for each tool_use block, c = input.command or input.file_path;
#   Write/Edit with a path under the real home -> write; any Bash line matching `wr` -> write
```

Result of running it (full script kept in the scratchpad, `logs/scan2.py`) over the four transcripts:

```
runA-failed:      real-home references 1,  writes 0
runB:             real-home references 5,  writes 0
runC:             real-home references 13, writes 0
runC-interrupted: real-home references 7,  writes 0
```

(The reference counts include the `expanduser("~/.claude")` fallback lines; the table above lists only the real reads.)
Independent confirmation on disk: `~/.airtime` and `~/AirTime` do not exist after the runs (`ls -d` fails), so nothing
could have been written there.

## Task 14: isolated install

Real install (not `--dry-run`) of item 14 on a fresh profile, then the check, then run C again on the installed copy.
`S` is the scratchpad. Environment for every step: `CLAUDE_CONFIG_DIR=$S/inst AIRTIME_HOME=$S/inst-home
CREATOR_KIT_SOURCE=<worktree> CREATOR_KIT_APP_DIR=$S/app14 SKIP_SHORTS_DEPS=1`, with `PATH=$S/ffshim:~/.local/node/bin:$PATH`
(ffmpeg shim; node). `SKIP_SHORTS_DEPS=1` because claude-shorts' `setup.sh` writes the real `~/.shorts-skill`; the clone into
`$S/inst/skills/shorts` still ran. Logs: `$S/logs14/`.

### Step 1: install (observed)

```
bash setup-mac.sh --doar 14        # item 14 is "airtime", the number printed in the list
```

Exit 0, 63 s. Items installed in dependency order: social-seo, brandkit, browser-harness, ecc, marketing, brand-voice,
remotion-skills, claude-shorts (skill copied, dependencies skipped), airtime. Section 3 printed: venv ready under
`$S/inst-home/venv`, intro template copied, Remotion packages installed (real `npm install`), `browser-harness: îl ai deja`.
`$S/inst/plugins/installed_plugins.json` lists airtime at `.../cache/creator-kit/airtime/0.1.0`. After the run `~/.airtime`
and `~/AirTime` do not exist, and `~/.local/bin` is unchanged (8 entries, old dates). **PASS.**

uv path (second run, `PATH` without `~/.local/bin`, only `uv`/`uvx` symlinked into `$S/uvshim`, plus
`UV_TOOL_DIR=$S/uv-tools UV_TOOL_BIN_DIR=$S/uv-bin UV_CACHE_DIR=$S/uv-cache UV_PYTHON_INSTALL_DIR=$S/uv-py`): exit 0,
printed `browser-harness: instalat`; `$S/uv-bin` holds `browser-harness` and `browser-harness-mcp`. The uv log ends with
`warning: ... uv-bin is not on your PATH`, so the "installed" line is printed although the command is not usable from the
shell. Every other item printed "(actualizat)" (rerun updates; the `--force` of `uv tool install` reinstalls each time).
Observed, as expected from `setup-mac.sh:569-572`. **PASS for the uv path executing; the PATH message is a finding below.**

### Step 2: check (observed)

`bash setup-mac.sh --check` (same env) ticks ecc, marketing, brand-voice, remotion-skills, claude-shorts, airtime, and the
`AirTime:` block shows ticks for ffmpeg, ffprobe, node, venv AirTime, shorts, shorts venv, remotion, ecc, marketing,
brand-voice, with:

```
  ✘ social-seo: skill-ul nu e instalat → AIRTIME-INSTALL.md#unelte
  ✘ YouTube: canalul nu e conectat → AIRTIME-INSTALL.md#youtube
  … Instagram: se verifică în conversație („AirTime check”) → AIRTIME-INSTALL.md#instagram
```

`check.sh --quick` of the installed copy (`$S/inst/plugins/cache/creator-kit/airtime/0.1.0/scripts/check.sh`, exit 1) prints
the same 13 lines. **FAIL against the expected result**: besides YouTube and the Instagram message there is one more
cross: social-seo (finding 1). The skill IS installed (`plugins/cache/creator-kit/social-seo/<sha>/SKILL.md`).

### Step 3: run C on the installed copy (observed)

Plugin dir: `make_e2e_copy.sh` from `$S/inst/plugins/cache/creator-kit/airtime/0.1.0` into `$S/airtime-e2e/plugin-c14`
(doubles replace `scripts/youtube.py` and `scripts/check.sh`). `AIRTIME_HOME=$S/inst-home` (a `principal` profile and
`speed.json` written there with the same snippet as `run.sh prep`), `AIRTIME_RUNS=$S/airtime-e2e/runs-c14`,
`CLAUDE_CONFIG_DIR=$S/cfg-test` (logged-in profile), `SHORTS_ROOT` as in Task 10 (`shorts-e2e`: the install here skipped
the shorts dependencies). To parametrise paths, `run.sh` got env overrides `C_NAME C_HOME C_RUNS C_PLUGIN C_FAKECFG`;
defaults are the Task 10 paths and names, so `run.sh c` / `checkc` behave as before.

```
C_NAME=runC14 C_HOME=... C_RUNS=... C_PLUGIN=... C_FAKECFG=... bash airtime/tests/e2e/run.sh c      # 12m57s, success, 19 turns
C_NAME=runC14 bash airtime/tests/e2e/run.sh checkc
tool calls: {'Skill': 1, 'Bash': 40, 'Agent': 4, 'Read': 12, 'Write': 8}
youtube upload/verify without --dry-run: none
browser tool calls: none
refusal log: empty or absent
```

The run stopped at the confirmation table (YouTube 2026-11-14 18:00; three reels 15, 16, 17 Nov 19:00; Facebook "Nu");
it said that nothing was uploaded or scheduled. Run folder `runs-c14/2026-11-12-antrenament-spate-test-sedinta` holds
`youtube.mp4`, `reels/short_02_ig.mp4`, `short_06_ig.mp4`, `short_07_ig.mp4`, `calendar.json`, `youtube-meta.json`.
Real-home scan (`logs/scan2.py runC14`): 6 references, all reads (the `expanduser("~/.claude")` fallback and a
`find`/`cat` of `$HOME/.claude/plugins/installed_plugins.json`), 0 writes; `~/.airtime` and `~/AirTime` absent.
**PASS** (same result as Task 10). The reply also said "skill-ul `social-seo` nu era instalat": the same false negative as
step 2, so the texts were written without that skill (finding 1).

### Found, not fixed

1. `check.sh` `plugin_present NAME skill` looks for `<installPath>/skills/NAME/SKILL.md`, but social-seo installs as a
   plugin with `SKILL.md` at the plugin root. The installed skill is reported missing in `--check`, `check.sh --quick` and by
   the agent in run C. The e2e fake config uses the `skills/<name>/` layout, so Task 10 could not show it. The installer's
   own `requires_of()` treats the dependency as satisfied, so the two disagree.
2. `setup-mac.sh:569-572`: `uv tool install` can succeed with the tool dir off PATH; the script still prints
   `browser-harness: instalat` and the user cannot run it. Reruns also reinstall with `--force`.
3. `shorts venv` ticks while `SKIP_SHORTS_DEPS=1` left the installed shorts without a venv: `reels.shorts_python()` fell
   back to the real `~/.shorts-skill/bin/python3`. Correct as a lookup order, but the check can pass on a machine other than
   the installed profile.
4. The run C agent still reads `$HOME/.claude/plugins/installed_plugins.json` (see Task 10 findings): not changed by the
   install.

## How to repeat

```bash
bash airtime/tests/e2e/run.sh prep     # clip, home, run folder, shorts copy, plugin copy with doubles
bash airtime/tests/e2e/run.sh b        # needs the logged-in profile in $S/cfg-test
bash airtime/tests/e2e/run.sh c && bash airtime/tests/e2e/run.sh checkc
```
