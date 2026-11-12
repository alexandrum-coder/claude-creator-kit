#!/bin/bash
# Test for scripts/check.sh with a fake PATH, HOME, AIRTIME_HOME, CLAUDE_CONFIG_DIR and SHORTS_ROOT.
# Never reads the real ~/.claude, ~/.airtime or ~/AirTime.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
CHECK="$HERE/../scripts/check.sh"
REAL_PY="$(command -v python3)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILS=0

fail() { echo "FAIL: $1"; FAILS=$((FAILS + 1)); }
ok()   { echo "ok:   $1"; }

# Build a fresh fake environment where every check passes. $1 = directory name.
make_env() {
  local e="$TMP/$1"
  mkdir -p "$e/bin" "$e/home/.shorts-skill/bin" "$e/ahome/venv/bin" \
           "$e/ahome/remotion/node_modules/remotion" "$e/cfg/plugins" \
           "$e/cfg/skills" "$e/shorts" "$e/plug/skills/social-seo"
  # Only the utilities bash and check.sh need; no ffmpeg unless the test adds it.
  local u p
  for u in dirname basename mktemp rm cat grep sed awk date tr head cut sort mkdir ls sleep; do
    p="$(command -v "$u")"
    [ -n "$p" ] && ln -s "$p" "$e/bin/$u"
  done
  ln -s "$REAL_PY" "$e/bin/python3"
  for u in ffmpeg ffprobe; do
    printf '#!/bin/bash\nfor a; do last="$a"; done\ncase "$last" in -*) ;; *) : > "$last" 2>/dev/null ;; esac\nexit 0\n' > "$e/bin/$u"
    chmod +x "$e/bin/$u"
  done
  printf '#!/bin/bash\nif [ "$1" = "-v" ] && [ "$2" = "?" ]; then echo "Ioana ro_RO # Salut"; exit 0; fi\nwhile [ $# -gt 0 ]; do [ "$1" = "-o" ] && : > "$2"; shift; done\nexit 0\n' > "$e/bin/say"
  # node stub for the intro render: prints one JSON object.
  printf '#!/bin/bash\necho "{\\"video\\": \\"intro.mp4\\"}"\n' > "$e/bin/node"
  # AirTime venv: imports pass; whoami answers as a connected channel.
  cat > "$e/ahome/venv/bin/python" <<'PYEOF'
#!/bin/bash
if [ "$1" = "-c" ]; then exit 0; fi
for a in "$@"; do
  if [ "$a" = "whoami" ]; then
    echo '{"channel": "Canalul Testului"}'
    exit "${FAKE_WHOAMI_EXIT:-0}"
  fi
done
exit 0
PYEOF
  # shorts venv: imports pass; transcribe writes the --out file.
  cat > "$e/home/.shorts-skill/bin/python3" <<'PYEOF'
#!/bin/bash
if [ "$1" = "-c" ]; then exit 0; fi
while [ $# -gt 0 ]; do
  [ "$1" = "--out" ] && out="$2"
  [ "$1" = "--model" ] && model="$2"
  shift
done
[ -n "${FAKE_FAIL_MODEL:-}" ] && [ "$model" = "$FAKE_FAIL_MODEL" ] && exit 1
: > "$out"
echo '{"transcript": "x"}'
PYEOF
  chmod +x "$e/bin/say" "$e/bin/node" "$e/ahome/venv/bin/python" "$e/home/.shorts-skill/bin/python3"
  : > "$e/shorts/SKILL.md"
  : > "$e/plug/skills/social-seo/SKILL.md"
  cat > "$e/cfg/plugins/installed_plugins.json" <<JEOF
{"version":2,"plugins":{
 "ecc@m":[{"installPath":"$e/plug"}],
 "marketing@m":[{"installPath":"$e/plug"}],
 "brand-voice@m":[{"installPath":"$e/plug"}]}}
JEOF
  echo "$e"
}

# Run check.sh inside env $1 with the remaining arguments; sets OUT and RC.
run_check() {
  local e="$1"; shift
  OUT="$(env -i PATH="$e/bin" HOME="$e/home" AIRTIME_HOME="$e/ahome" \
        CLAUDE_CONFIG_DIR="$e/cfg" SHORTS_ROOT="$e/shorts" FAKE_WHOAMI_EXIT="${FAKE_WHOAMI_EXIT:-0}" FAKE_FAIL_MODEL="${FAKE_FAIL_MODEL:-}" LC_ALL="${TEST_LC_ALL:-C}" \
        /bin/bash "$CHECK" "$@" 2>&1)"
  RC=$?
}

# 1. Everything passes.
E="$(make_env good)"
run_check "$E" --quick
[ "$RC" = 0 ] && ok "all pass: exit 0" || { fail "all pass: exit $RC"; echo "$OUT"; }
case "$OUT" in *"✘"*) fail "all pass: unexpected ✘"; echo "$OUT" ;; *) ok "all pass: no ✘" ;; esac
case "$OUT" in *"! ffmpeg fără zscale"*"Video HDR"*) ok "zscale info line (!, not ✘)" ;; *) fail "zscale info line missing" ;; esac
case "$OUT" in *"Instagram: se verifică în conversație"*) ok "instagram info line" ;; *) fail "instagram info line missing" ;; esac
[ ! -e "$E/ahome/speed.json" ] && ok "quick writes no speed.json" || fail "quick wrote speed.json"
echo "$OUT" | grep -q 's[â]nt' && fail "forbidden spelling in output"

# 2. No ffmpeg.
E="$(make_env noffmpeg)"; rm "$E/bin/ffmpeg"
run_check "$E" --quick
[ "$RC" = 1 ] && ok "no ffmpeg: exit 1" || fail "no ffmpeg: exit $RC"
case "$OUT" in *"✘ ffmpeg"*"AIRTIME-INSTALL.md#unelte"*) ok "no ffmpeg: ✘ + anchor" ;; *) fail "no ffmpeg: line"; echo "$OUT" ;; esac

# 3. YouTube not connected.
E="$(make_env noyt)"
FAKE_WHOAMI_EXIT=3 run_check "$E" --quick
[ "$RC" = 1 ] && ok "youtube: exit 1" || fail "youtube: exit $RC"
case "$OUT" in *"✘ YouTube"*"AIRTIME-INSTALL.md#youtube"*) ok "youtube: ✘ + anchor" ;; *) fail "youtube line"; echo "$OUT" ;; esac
[ "$(echo "$OUT" | grep -c '✘')" = 1 ] && ok "youtube: only one ✘" || fail "youtube: more than one ✘"

# 4. Missing plugin, and social-seo found in the config skills folder instead.
E="$(make_env noplug)"
cat > "$E/cfg/plugins/installed_plugins.json" <<JEOF
{"version":2,"plugins":{"ecc@m":[{"installPath":"$E/plug"}],"marketing@m":[]}}
JEOF
rm "$E/plug/skills/social-seo/SKILL.md"
run_check "$E" --quick
case "$OUT" in *"✘ brand-voice"*"#unelte"*) ok "plugin: brand-voice ✘" ;; *) fail "plugin brand-voice"; echo "$OUT" ;; esac
case "$OUT" in *"✘ social-seo"*) ok "plugin: social-seo ✘" ;; *) fail "plugin social-seo" ;; esac
mkdir -p "$E/cfg/skills/social-seo"; : > "$E/cfg/skills/social-seo/SKILL.md"
run_check "$E" --quick
case "$OUT" in *"✘ social-seo"*) fail "social-seo from config skills not found" ;; *) ok "social-seo from config skills" ;; esac

# 4b. Real social-seo layout: SKILL.md at the plugin root, no skills/ folder.
E="$(make_env rootskill)"
mkdir -p "$E/plug2"; : > "$E/plug2/SKILL.md"
rm "$E/plug/skills/social-seo/SKILL.md"
cat > "$E/cfg/plugins/installed_plugins.json" <<JEOF
{"version":2,"plugins":{"ecc@m":[{"installPath":"$E/plug"}],"marketing@m":[{"installPath":"$E/plug"}],"brand-voice@m":[{"installPath":"$E/plug"}],"social-seo@creator-kit":[{"installPath":"$E/plug2"}]}}
JEOF
run_check "$E" --quick
case "$OUT" in *"✔ social-seo"*) ok "social-seo with SKILL.md at plugin root" ;; *) fail "social-seo at plugin root not found"; echo "$OUT" ;; esac

# 5. Failing shorts venv import and missing remotion.
E="$(make_env nodeps)"
printf '#!/bin/bash\nexit 1\n' > "$E/home/.shorts-skill/bin/python3"
rm -rf "$E/ahome/remotion/node_modules"
run_check "$E" --quick
case "$OUT" in *"✘ shorts venv"*"#unelte"*) ok "shorts venv ✘" ;; *) fail "shorts venv"; echo "$OUT" ;; esac
case "$OUT" in *"✘ remotion"*"#unelte"*) ok "remotion ✘" ;; *) fail "remotion"; echo "$OUT" ;; esac

# 6. --json: exactly one object, no ✔/✘ lines.
E="$(make_env json)"
FAKE_WHOAMI_EXIT=3 run_check "$E" --json
[ "$RC" = 1 ] && ok "json: exit 1" || fail "json: exit $RC"
echo "$OUT" | "$REAL_PY" -c '
import json, sys
d = json.loads(sys.stdin.read())
assert d["ok"] is False and d["instagram"] == "conversatie"
names = {c["name"]: c for c in d["checks"]}
assert names["ffmpeg"]["ok"] is True and names["ffmpeg"]["anchor"] == "unelte"
yt = [c for c in d["checks"] if c["anchor"] == "youtube"][0]
assert yt["ok"] is False
assert set(yt) == {"name", "ok", "anchor", "detail"}
' && ok "json: shape" || { fail "json shape"; echo "$OUT"; }
case "$OUT" in *"✔"*|*"✘"*) fail "json: has ✔/✘ lines" ;; *) ok "json: no ✔/✘ lines" ;; esac

# 7. --speed with stubs writes a valid speed.json.
E="$(make_env speed)"
run_check "$E" --speed
[ "$RC" = 0 ] && ok "speed: exit 0" || { fail "speed: exit $RC"; echo "$OUT"; }
"$REAL_PY" -c '
import json, sys
d = json.load(open(sys.argv[1]))
assert set(d) == {"model", "sec_per_min", "intro_sec", "estimate_20min_min"}, d
assert d["model"] in ("small", "medium")
assert d["estimate_20min_min"] >= 0
' "$E/ahome/speed.json" && ok "speed.json valid" || { fail "speed.json"; echo "$OUT"; }
case "$OUT" in *"minute"*) ok "speed: romanian estimate" ;; *) fail "speed message"; echo "$OUT" ;; esac

# 8. Medium transcription fails: warn, fall back to small, still write speed.json.
E="$(make_env medfail)"
FAKE_FAIL_MODEL=medium run_check "$E" --speed
[ "$RC" = 0 ] && ok "medium fails: exit 0" || { fail "medium fails: exit $RC"; echo "$OUT"; }
"$REAL_PY" -c '
import json, sys
d = json.load(open(sys.argv[1]))
assert d["model"] == "small", d
' "$E/ahome/speed.json" && ok "medium fails: speed.json model small" || { fail "medium fails: speed.json"; echo "$OUT"; }
case "$OUT" in *"medium"*"small"*) ok "medium fails: romanian warning" ;; *) fail "medium warning"; echo "$OUT" ;; esac

# 8b. Small fails: loud failure, no speed.json.
E="$(make_env smallfail)"
FAKE_FAIL_MODEL=small run_check "$E" --speed
[ "$RC" = 1 ] && [ ! -e "$E/ahome/speed.json" ] && ok "small fails: exit 1, no speed.json" || { fail "small fails: rc $RC"; echo "$OUT"; }

# 9. Romanian locale: speed.json numbers keep a decimal point.
E="$(make_env locale)"
TEST_LC_ALL=ro_RO.UTF-8 run_check "$E" --speed
[ "$RC" = 0 ] && ok "ro locale: exit 0" || { fail "ro locale: exit $RC"; echo "$OUT"; }
"$REAL_PY" -c 'import json, sys; json.load(open(sys.argv[1]))' "$E/ahome/speed.json" \
  && ok "ro locale: speed.json parses" || fail "ro locale: speed.json invalid"

echo
if [ "$FAILS" = 0 ]; then echo "PASS"; exit 0; else echo "FAIL ($FAILS)"; exit 1; fi
