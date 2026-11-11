#!/usr/bin/env bash
# AirTime end-to-end test on an isolated profile, up to the confirmation table. Phases (run one at a time):
#   run.sh prep       clip, e2e AIRTIME_HOME, run folder, plugin copy with the two test doubles
#   run.sh a          (first attempt, kept for the record: the agent alone, propune. It failed on the missing plugin root.)
#   run.sh approve    (script) writes cuts-aprobate.json approving every proposed cut; not used in the final run, see b
#   run.sh b          claude -p run B (final budget: 3 runs in all): agent propune, then monteaza, texte, reels; the
#                     main Claude writes cuts-aprobate.json (all cuts) and reels-aprobate.json (first 3 candidates) between calls
#   run.sh c          claude -p run C: skill flow "AirTime" up to the confirmation table (plugin copy with doubles)
#   run.sh checkc     transcript checks for run C
# Everything generated lives under $SCR. Nothing touches ~/.claude, ~/.airtime or ~/AirTime.
set -eu

S="${S:-/private/tmp/claude-501/-Users-pixelpoetry-Claude-Cowork-Tools/d109280c-9e44-404e-9a3d-0b312ae9e2d8/scratchpad}"
SCR="$S/airtime-e2e"
KIT="${KIT:-/Users/pixelpoetry/claude-creator-kit-airtime}"
PLUGIN="$KIT/airtime"
HERE="$(cd "$(dirname "$0")" && pwd)"
PY="$S/airtime-venv/bin/python"
export PATH="$S/ffshim:$HOME/.local/node/bin:$PATH"
CFG="$S/cfg-test"                 # isolated, already logged in; never modified by the test
CLIP_DIR="$SCR/in"
LOGS="$SCR/logs"
C_NAME="${C_NAME:-runC}"; C_REF="$(printf %s "${C_NAME#run}" | tr A-Z a-z)"   # Task 14 overrides: C_NAME, C_HOME, C_RUNS, C_PLUGIN, C_FAKECFG (defaults = Task 10 paths)
mkdir -p "$LOGS"
cd "$SCR"   # Remotion downloads its headless Chrome into ./.remotion of the current folder: keep it out of the worktree

# CLAUDE_PLUGIN_ROOT is exported by hand: with --plugin-dir the agent's Bash does not get it and cfg-test has no
# installed_plugins.json, so the agent's environment preamble finds no plugin root (see e2e.md, "Found in the plugin").
env_ab() { export AIRTIME_HOME="$SCR/home" AIRTIME_RUNS="$SCR/runs-ab" SHORTS_ROOT="$SCR/shorts-e2e" CLAUDE_CONFIG_DIR="$CFG" CLAUDE_PLUGIN_ROOT="$PLUGIN"; }
env_c()  { export AIRTIME_HOME="${C_HOME:-$SCR/home}" AIRTIME_RUNS="${C_RUNS:-$SCR/runs-c}" SHORTS_ROOT="$SCR/shorts-e2e" CLAUDE_CONFIG_DIR="$CFG" \
                  CLAUDE_PLUGIN_ROOT="${C_PLUGIN:-$SCR/plugin-c}" AIRTIME_E2E_FAKE_CFG="${C_FAKECFG:-$SCR/fakecfg}" \
                  AIRTIME_E2E_REFUSAL_LOG="$LOGS/refused-$C_REF.log"; }

clip() { ls "$CLIP_DIR"/*.mov | head -1; }
rundir() { cat "$SCR/rundir-ab.txt"; }

claude_run() {   # claude_run NAME PLUGIN_DIR TOOLS PROMPT
  local name="$1" pdir="$2" tools="$3" prompt="$4"
  claude -p --model sonnet --strict-mcp-config --mcp-config '{"mcpServers":{}}' --plugin-dir "$pdir" \
    --allowedTools="$tools" --output-format stream-json --verbose -- "$prompt" \
    > "$LOGS/$name.jsonl" 2> "$LOGS/$name.err"
}

case "${1:-}" in
prep)
  mkdir -p "$CLIP_DIR" "$SCR/runs-ab" "$SCR/runs-c"
  /bin/bash "$HERE/../make_test_clip.sh" "$CLIP_DIR"
  mkdir -p "$SCR/home"
  ln -sfn "$S/airtime-venv" "$SCR/home/venv"; ln -sfn "$S/remotion" "$SCR/home/remotion"
  cp "$S/ahome-speed/speed.json" "$SCR/home/speed.json"      # whisper model: small
  env_ab
  "$PY" - "$PLUGIN/scripts" "$(clip)" "$SCR/rundir-ab.txt" <<'PYEOF'
import json, sys
from datetime import date
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import airtime_config as c
p = dict(c.DEFAULTS)
p.update(channel="Coach Test", intro_text="Antrenament spate", keywords=["spate", "postura"], clip_type="demonstratii")
c.save_profile("principal", p)
(c.home() / "config.json").write_text(json.dumps({"default_profile": "principal"}))
run = c.new_run_dir(Path(sys.argv[2]), date.today())
(run / "run.json").write_text(json.dumps({"video": sys.argv[2], "profile": "principal", "clip_type": "demonstratii",
    "voiceover": False, "facebook": False, "shorts": False, "data_youtube": "2026-11-14", "orientation": "horizontal", "kind": "lung"},
    ensure_ascii=False, indent=2))
Path(sys.argv[3]).write_text(str(run))
print(run)
PYEOF
  REMOTION_MODULES="$S/remotion/node_modules" /bin/bash "$HERE/make_shorts_copy.sh" "$S/claude-shorts" "$SCR/shorts-e2e"
  /bin/bash "$HERE/make_e2e_copy.sh" "$PLUGIN" "$SCR/plugin-c" "$SCR/fakecfg"
  ;;
a)
  env_ab
  claude_run runA "$PLUGIN" "Agent,Bash,Read,Write,Glob,Grep" "Cheamă agentul airtime:airtime (instrumentul Agent, subagent_type airtime:airtime) cu exact acest prompt, apoi răspunde numai cu blocul pe care ți-l întoarce:
COMANDA: propune
RUN_DIR: $(rundir)
PROFIL: principal
VIDEO: $(clip)
TIP_CLIP: demonstratii
VOICEOVER: false"
  ;;
approve)
  "$PY" - "$(rundir)" <<'PYEOF'
import json, sys
from pathlib import Path
run = Path(sys.argv[1])
d = json.loads((run / "cuts-propuse.json").read_text(encoding="utf-8"))
(run / "cuts-aprobate.json").write_text(json.dumps({"cuts": d["cuts"]}, ensure_ascii=False, indent=2), encoding="utf-8")
print("approved", len(d["cuts"]), "cuts")
PYEOF
  ;;
b)
  env_ab
  R="$(rundir)"; V="$(clip)"
  claude_run runB "$PLUGIN" "Agent,Bash,Read,Write,Glob,Grep" "Cheamă agentul airtime:airtime (instrumentul Agent, subagent_type airtime:airtime) de patru ori, pe rând, și așteaptă răspunsul fiecăruia înainte de următoarea chemare. Promptul fiecărei chemări e blocul ei, cu liniile CHEIE: valoare exact ca mai jos.
Chemarea 1:
COMANDA: propune
RUN_DIR: $R
PROFIL: principal
VIDEO: $V
TIP_CLIP: demonstratii
VOICEOVER: false

După chemarea 1 scrie tu $R/cuts-aprobate.json, cu forma {\"cuts\": [...]}: toate tăieturile din $R/cuts-propuse.json, fără să scoți vreuna.
Chemarea 2:
COMANDA: monteaza
RUN_DIR: $R
PROFIL: principal
VIDEO: $V
TITLU: Antrenament spate

Chemarea 3:
COMANDA: texte
RUN_DIR: $R
PROFIL: principal
DATA_YOUTUBE: 2026-11-14 18:00

După chemarea 3 scrie tu $R/reels-aprobate.json: citește $R/candidati.json și păstrează primii 3 candidați din listă (aceeași formă ca în candidati.json, cheile segments, style, platform, content_type), cu style pus pe bold.
Chemarea 4:
COMANDA: reels
RUN_DIR: $R
PROFIL: principal
STIL: bold

La final răspunde cu cele patru blocuri întoarse, unul sub altul."
  ;;
c)
  env_c
  claude_run "$C_NAME" "${C_PLUGIN:-$SCR/plugin-c}" "Agent,Bash,Read,Write,Glob,Grep,Skill" "AirTime
Clipul e $(clip)
Vocea nu e înregistrată separat. Facebook: nu. YouTube Shorts: nu. Data clipului lung: 2026-11-14.
Aprobă toate tăieturile propuse, fără să scoți niciuna. Pentru reels alege candidații 1, 2 și 3, cu stilul bold.
Aici sunt toate răspunsurile; nu pune întrebări. Oprește-te când arăți tabelul final cu calendarul și textele complete: nu urca și nu programa nimic."
  ;;
checkc)
  "$PY" - "$LOGS/$C_NAME.jsonl" "$LOGS/refused-$C_REF.log" <<'PYEOF'
import json, re, sys
from pathlib import Path
tr = Path(sys.argv[1]); refused = Path(sys.argv[2])
bad, browser, bashn, tools = [], [], 0, {}
for line in tr.read_text(encoding="utf-8").splitlines():
    try: ev = json.loads(line)
    except ValueError: continue
    msg = ev.get("message") or {}
    for blk in (msg.get("content") if isinstance(msg.get("content"), list) else []):
        if blk.get("type") != "tool_use": continue
        name = blk.get("name", ""); tools[name] = tools.get(name, 0) + 1
        if re.search(r"chrome|browser|playwright", name, re.I): browser.append(name)
        if name == "Bash":
            bashn += 1
            cmd = (blk.get("input") or {}).get("command", "")
            if re.search(r"youtube(_real)?\.py", cmd) and re.search(r"\b(upload|verify)\b", cmd) and "--dry-run" not in cmd:
                bad.append(cmd[:200])
print("tool calls:", tools)
print("bash calls:", bashn)
print("youtube upload/verify without --dry-run:", bad or "none")
print("browser tool calls:", browser or "none")
print("refusal log:", "empty or absent" if (not refused.exists() or not refused.read_text().strip()) else refused.read_text())
sys.exit(1 if bad or browser or (refused.exists() and refused.read_text().strip()) else 0)
PYEOF
  ;;
*) echo "Folosire: run.sh prep|a|approve|b|c|checkc" >&2; exit 2 ;;
esac
