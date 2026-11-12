#!/usr/bin/env bash
# AirTime check: verifică uneltele și, cu --speed, măsoară cât de repede merge calculatorul.
#   check.sh [--quick|--speed] [--profile NAME] [--json]
# Exit 0 dacă tot ce e obligatoriu e bifat, altfel 1. Compatibil cu bash 3.2.
set -u

DIR="$(cd "$(dirname "$0")" && pwd)"
AIRTIME_HOME="${AIRTIME_HOME:-$HOME/.airtime}"
CFG="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"

MODE=quick
JSON=0
PROFILE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --quick) MODE=quick ;;
    --speed) MODE=speed ;;
    --json) JSON=1 ;;
    --profile)
      [ $# -ge 2 ] || { echo "Lipsește numele profilului după --profile" >&2; exit 2; }
      PROFILE="$2"; shift ;;
    *) echo "Folosire: check.sh [--quick|--speed] [--profile NUME] [--json]" >&2; exit 2 ;;
  esac
  shift
done

# Python for the AirTime venv checks: the venv when it exists, else the system python3.
PY="$AIRTIME_HOME/venv/bin/python"
[ -x "$PY" ] || PY="python3"

NAMES=(); OKS=(); ANCHORS=(); DETAILS=()
ALL_OK=1
SPEED_OK=1   # prerequisites of the speed test: tools, shorts, remotion

out() { [ "$JSON" = 1 ] || printf '%s\n' "$*"; }

# check NAME OK(1|0) ANCHOR DETAIL: records the result and prints the line.
check() {
  NAMES+=("$1"); OKS+=("$2"); ANCHORS+=("$3"); DETAILS+=("$4")
  if [ "$2" = 1 ]; then
    out "✔ $1${4:+ ($4)}"
  else
    ALL_OK=0
    case "$3" in unelte) case "$1" in ecc|marketing|brand-voice|social-seo) ;; *) SPEED_OK=0 ;; esac ;; esac
    out "✘ $1${4:+: $4} → AIRTIME-INSTALL.md#$3"
  fi
}

json_str() {
  printf '%s' "$1" | tr '\n\r\t' '   ' | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'
}

# ---------------------------------------------------------------- tools
for t in ffmpeg ffprobe node; do
  if command -v "$t" >/dev/null 2>&1; then check "$t" 1 unelte ""
  else check "$t" 0 unelte "lipsește"; fi
done

# Informational only (never ✘): without zscale, iPhone HDR clips keep washed-out colours.
if command -v ffmpeg >/dev/null 2>&1; then
  if ffmpeg -hide_banner -filters 2>/dev/null | grep -q ' zscale '; then
    out "✔ ffmpeg zscale (clipurile iPhone HDR se convertesc corect)"
  else
    out "! ffmpeg fără zscale: clipurile iPhone HDR pot ieși cu culori spălate; oprește „Video HDR” în Configurări → Cameră → Formate → AIRTIME-INSTALL.md#probleme"
  fi
fi

# ---------------------------------------------------------------- venvs
if [ -x "$AIRTIME_HOME/venv/bin/python" ] \
   && "$AIRTIME_HOME/venv/bin/python" -c "import googleapiclient, google_auth_oauthlib" >/dev/null 2>&1; then
  check "venv AirTime" 1 unelte ""
else
  check "venv AirTime" 0 unelte "lipsesc bibliotecile Google"
fi

# Shorts locations come from reels.py (single source for the lookup order).
shorts_lookup() {
  python3 -c 'import sys; sys.path.insert(0, sys.argv[1]); import reels; print(getattr(reels, sys.argv[2])())' \
    "$DIR" "$1" 2>/dev/null
}
SHORTS_ROOT_DIR="$(shorts_lookup shorts_root)"
SHORTS_PY="$(shorts_lookup shorts_python)"

if [ -n "$SHORTS_ROOT_DIR" ] && [ -f "$SHORTS_ROOT_DIR/SKILL.md" ]; then
  check "shorts" 1 unelte ""
else
  check "shorts" 0 unelte "nu găsesc skill-ul shorts"
fi
if [ -n "$SHORTS_PY" ] && [ -x "$SHORTS_PY" ] && "$SHORTS_PY" -c "import faster_whisper" >/dev/null 2>&1; then
  check "shorts venv" 1 unelte ""
else
  check "shorts venv" 0 unelte "faster_whisper lipsește"
fi

if [ -d "$AIRTIME_HOME/remotion/node_modules/remotion" ]; then
  check "remotion" 1 unelte ""
else
  check "remotion" 0 unelte "lipsesc pachetele Remotion"
fi

# -------------------------------------------------------------- plugins
# plugin_present NAME KIND: kind "plugin" = key starts with NAME@; kind "skill" = SKILL.md at a plugin root, in a plugin skills/NAME/, or in config skills.
plugin_present() {
  python3 - "$CFG" "$1" "$2" <<'PYEOF' >/dev/null 2>&1
import json, sys
from pathlib import Path
cfg, name, kind = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
try:
    plugins = json.loads((cfg / "plugins" / "installed_plugins.json").read_text()).get("plugins", {})
except Exception:
    plugins = {}
if kind == "plugin":
    sys.exit(0 if any(k.startswith(name + "@") for k in plugins) else 1)
if (cfg / "skills" / name / "SKILL.md").exists():
    sys.exit(0)
for entries in plugins.values():
    for e in entries or []:
        ip = Path(e.get("installPath", ""))
        if (ip / "SKILL.md").exists() or (ip / "skills" / name / "SKILL.md").exists():
            sys.exit(0)
sys.exit(1)
PYEOF
}
for p in ecc marketing brand-voice; do
  if plugin_present "$p" plugin; then check "$p" 1 unelte ""
  else check "$p" 0 unelte "pluginul nu e instalat"; fi
done
if plugin_present social-seo skill; then check "social-seo" 1 unelte ""
else check "social-seo" 0 unelte "skill-ul nu e instalat"; fi

# -------------------------------------------------------------- YouTube
yt_args=()
[ -n "$PROFILE" ] && yt_args=(--profile "$PROFILE")
yt_out="$("$PY" "$DIR/youtube.py" ${yt_args[@]+"${yt_args[@]}"} whoami 2>/dev/null)"
yt_rc=$?
case "$yt_rc" in
  0)
    chan="$(printf '%s' "$yt_out" | sed -n 's/.*"channel": *"\([^"]*\)".*/\1/p')"
    check "YouTube" 1 youtube "canal ${chan:-conectat}" ;;
  3) check "YouTube" 0 youtube "canalul nu e conectat" ;;
  4) check "YouTube" 0 youtube "lipsește fișierul client Google" ;;
  *) check "YouTube" 0 youtube "verificarea a eșuat" ;;
esac

# ------------------------------------------------------------ Instagram
out "… Instagram: se verifică în conversație („AirTime check”) → AIRTIME-INSTALL.md#instagram"

# ---------------------------------------------------------------- speed
now() { python3 -c 'import time; print(time.time())'; }

speed_test() {
  local voice_args=() text t0 t1 m best="" best_spm="" best_est="" est spm
  local intro_sec fallback=0

  if [ "$SPEED_OK" != 1 ]; then
    check "viteză" 0 unelte "testul de viteză cere uneltele de mai sus"
    return
  fi
  TMP_SPEED="$(mktemp -d)" || { check "viteză" 0 unelte "nu pot crea un folder temporar"; return; }
  trap 'rm -rf "$TMP_SPEED"' EXIT
  local tmp="$TMP_SPEED"

  out "Test de viteză: generez 30 de secunde de voce și le transcriu. Durează câteva minute."
  if command -v say >/dev/null 2>&1; then
    if say -v '?' 2>/dev/null | grep -q '^Ioana'; then voice_args=(-v Ioana); fi
    text="Bună ziua, sunt aici ca să verific cât de repede transcrie acest calculator."
    text="$text $text $text $text $text $text"
    say ${voice_args[@]+"${voice_args[@]}"} -o "$tmp/voice.aiff" "$text" >/dev/null 2>&1
  fi
  [ -e "$tmp/voice.aiff" ] || { check "viteză" 0 unelte "nu pot genera vocea de test"; return; }
  if ! ffmpeg -y -loglevel error -f lavfi -i "testsrc=size=640x360:rate=25" -i "$tmp/voice.aiff" \
        -af apad -t 30 -c:v libx264 -pix_fmt yuv420p -c:a aac "$tmp/test.mp4" >/dev/null 2>&1; then
    check "viteză" 0 unelte "ffmpeg nu a putut crea clipul de test"; return
  fi

  # Short clip for an untimed warm-up: downloads and loads each model before the timed run.
  if ! ffmpeg -y -loglevel error -i "$tmp/test.mp4" -t 3 -c copy "$tmp/warm.mp4" >/dev/null 2>&1; then
    check "viteză" 0 unelte "ffmpeg nu a putut crea clipul de încălzire"; return
  fi

  for m in small medium; do
    if ! "$SHORTS_PY" "$DIR/reels.py" transcribe --video "$tmp/warm.mp4" --out "$tmp/warm-$m.json" --model "$m" >/dev/null 2>&1; then
      if [ "$m" = small ]; then check "viteză" 0 unelte "transcrierea cu modelul small a eșuat"; return; fi
      out "! Modelul medium nu a putut fi pregătit (probabil lipsește internetul sau spațiul). Folosesc modelul small."
      break
    fi
    t0="$(now)"
    if ! "$SHORTS_PY" "$DIR/reels.py" transcribe --video "$tmp/test.mp4" --out "$tmp/$m.json" --model "$m" >/dev/null 2>&1; then
      if [ "$m" = small ]; then check "viteză" 0 unelte "transcrierea cu modelul small a eșuat"; return; fi
      out "! Transcrierea cu modelul medium a eșuat. Folosesc modelul small."
      break
    fi
    t1="$(now)"
    # 30 s of audio: seconds per audio minute = elapsed * 2; a 20 min clip = spm * 20 / 60 minutes.
    # C locale: these numbers go into speed.json, which needs a decimal point.
    spm="$(LC_ALL=C awk -v a="$t0" -v b="$t1" 'BEGIN { printf "%.1f", (b - a) * 2 }')"
    est="$(LC_ALL=C awk -v s="$spm" 'BEGIN { printf "%.1f", s * 20 / 60 }')"
    out "  $m: $spm secunde pe minut de înregistrare (estimare pentru 20 de minute: $est minute)"
    if LC_ALL=C awk -v e="$est" 'BEGIN { exit !(e <= 30) }'; then
      best="$m"; best_spm="$spm"; best_est="$est"
    else
      break   # a bigger model is never faster
    fi
  done
  if [ -z "$best" ]; then
    best=small; fallback=1
    best_spm="$spm"; best_est="$est"
  fi

  t0="$(now)"
  printf '{"width":1080,"height":1920,"fps":30,"colors":{"primary":"#14213d","accent":"#fca311"},"intro":{"title":"AirTime","channel":"Test"}}\n' > "$tmp/props.json"
  if ! (cd "$AIRTIME_HOME/remotion" && node render.mjs --props "$tmp/props.json" --out-dir "$tmp/render") >/dev/null 2>&1; then
    check "viteză" 0 unelte "randarea intro-ului a eșuat"; return
  fi
  t1="$(now)"
  intro_sec="$(LC_ALL=C awk -v a="$t0" -v b="$t1" 'BEGIN { printf "%.1f", b - a }')"

  mkdir -p "$AIRTIME_HOME"
  printf '{"model": "%s", "sec_per_min": %s, "intro_sec": %s, "estimate_20min_min": %s}\n' \
    "$best" "$best_spm" "$intro_sec" "$best_est" > "$AIRTIME_HOME/speed.json"

  if [ "$fallback" = 1 ]; then
    out "! Calculatorul e lent: un clip de 20 de minute ar dura circa $best_est minute chiar și cu modelul mic. Merge, dar cere răbdare."
  fi
  check "viteză" 1 unelte "model $best, un clip de 20 de minute se transcrie în circa $best_est minute; intro-ul se randează în $intro_sec secunde"
}

[ "$MODE" = speed ] && speed_test

# ----------------------------------------------------------------- json
if [ "$JSON" = 1 ]; then
  printf '{"ok": %s, "checks": [' "$([ "$ALL_OK" = 1 ] && echo true || echo false)"
  i=0
  while [ "$i" -lt "${#NAMES[@]}" ]; do
    [ "$i" -gt 0 ] && printf ', '
    printf '{"name": "%s", "ok": %s, "anchor": "%s", "detail": "%s"}' \
      "$(json_str "${NAMES[$i]}")" "$([ "${OKS[$i]}" = 1 ] && echo true || echo false)" \
      "${ANCHORS[$i]}" "$(json_str "${DETAILS[$i]}")"
    i=$((i + 1))
  done
  printf '], "instagram": "conversatie"}\n'
fi

[ "$ALL_OK" = 1 ]
