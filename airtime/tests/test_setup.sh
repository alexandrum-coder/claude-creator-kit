#!/bin/bash
# Test for the AirTime item in setup-mac.sh (dry-run only, nothing is installed).
# Uses a fresh CLAUDE_CONFIG_DIR, CREATOR_KIT_APP_DIR and AIRTIME_HOME in a temp
# folder; never reads or writes the real ~/.claude, ~/.airtime or ~/AirTime.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
SETUP="$ROOT/setup-mac.sh"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
FAILS=0

fail() { echo "FAIL: $1"; FAILS=$((FAILS + 1)); }
ok()   { echo "ok:   $1"; }

run_setup() {   # $1 = scratch name, rest = setup-mac.sh arguments
  local d="$TMP/$1"; shift
  mkdir -p "$d/conf" "$d/app" "$d/ahome"
  CREATOR_KIT_SOURCE="$ROOT" CLAUDE_CONFIG_DIR="$d/conf" CREATOR_KIT_APP_DIR="$d/app" \
    AIRTIME_HOME="$d/ahome" SKIP_SHORTS_DEPS=1 SKIP_AIRTIME_DEPS=1 \
    /bin/bash "$SETUP" --dry-run "$@" 2>&1
}

has() { printf '%s\n' "$2" | grep -qF -- "$1"; }

# The menu number of AirTime, read from the menu the script prints.
MENU="$(run_setup menu --doar "1")"
N="$(printf '%s\n' "$MENU" | sed -n 's/^ *\([0-9][0-9]*\)\. airtime .*/\1/p' | head -1)"
[ -n "$N" ] || { fail "airtime is not in the menu"; echo "$FAILS failed"; exit 1; }
ok "airtime is menu item $N"
[ "$N" = "$(printf '%s\n' "$MENU" | sed -n '/^Creator Kit/,/^Instalez/p' | grep -c '^ *[0-9][0-9]*\. ')" ] && ok "airtime is the last item" || fail "airtime is not the last item"

# 1. --doar N installs AirTime and everything it needs.
OUT="$(run_setup one --doar "$N")"
for w in "• ecc" "• marketing" "• brand-voice" "• remotion-skills" "• claude-shorts" "• airtime" \
         "• social-seo" "• brandkit" "• browser-harness"; do
  has "$w" "$OUT" && ok "lists $w" || fail "missing: $w"
done
# ...and installs them (dry-run prints a check mark per installed plugin).
for w in social-seo brandkit browser-harness ecc marketing brand-voice remotion-skills airtime; do
  printf '%s\n' "$OUT" | sed -n '/^2\. Instalare/,$p' | grep -q "✔.* $w\$" && ok "installs $w" || fail "does not install $w"
done
# The skills come one by one, never the whole creator group.
has "• creator-skills" "$OUT" && fail "pulled in the whole creator-skills group" || ok "no creator-skills group"
printf '%s\n' "$OUT" | grep -q "humanizer" && fail "installed humanizer (not a dependency)" || ok "humanizer not installed"
# Tools: the script reports each tool it wants ("node: prezent" or "ffmpeg lipsește").
for t in node ffmpeg; do
  printf '%s\n' "$OUT" | grep -Eq "(✔|!).* $t( |:)" && ok "$t among the tools" || fail "$t is not among the tools"
done
# No duplicates in the list.
DUP="$(printf '%s\n' "$OUT" | grep '^  • ' | sort | uniq -d)"
[ -z "$DUP" ] && ok "no item listed twice" || fail "duplicates: $DUP"

# 2. Selecting AirTime together with one of its dependencies lists it once.
OUT2="$(run_setup two --doar "$N 2")"
[ "$(printf '%s\n' "$OUT2" | grep -c '^  • ecc$')" = "1" ] && ok "ecc once when picked twice" || fail "ecc listed more or less than once"

# 2b. With the whole creator group chosen, its skills are not listed a second time.
OUT2B="$(run_setup twob --doar "1 $N")"
[ "$(printf '%s\n' "$OUT2B" | grep -c '^  • social-seo$')" = "0" ] && ok "group covers social-seo" || fail "social-seo listed next to the group"

# 3. Dependencies already installed are skipped by the normal status logic.
d="$TMP/pre"; mkdir -p "$d/conf/plugins" "$d/app" "$d/ahome"
printf '{"plugins":{"ecc@ecc":[{"installPath":"%s/x"}]}}\n' "$d" > "$d/conf/plugins/installed_plugins.json"
OUT3="$(CREATOR_KIT_SOURCE="$ROOT" CLAUDE_CONFIG_DIR="$d/conf" CREATOR_KIT_APP_DIR="$d/app" AIRTIME_HOME="$d/ahome" \
  SKIP_SHORTS_DEPS=1 SKIP_AIRTIME_DEPS=1 /bin/bash "$SETUP" --dry-run --doar "$N" 2>&1)"
has "• ecc" "$OUT3" && fail "ecc listed although installed" || ok "installed ecc is skipped"

# 4. A bad number does not pull AirTime in.
OUT4="$(run_setup four --doar "2")"
has "• airtime" "$OUT4" && fail "airtime listed for item 2" || ok "airtime only when chosen"

# 5. The AirTime post-install step is announced.
printf '%s\n' "$OUT" | grep 'dry-run' | grep -q "airtime: venv" && ok "post-install step shown" || fail "no post-install step in dry-run"

# 5b. The dry-run announces the speed test, and airtime_post calls it.
printf '%s\n' "$OUT" | grep 'dry-run' | grep -q "test de viteză" && ok "speed test announced in dry-run" || fail "no speed test in dry-run"
sed -n '/^airtime_post() {/,/^}/p' "$SETUP" | grep -qF 'airtime_speed "$src" "$AH"' \
  && ok "airtime_post calls airtime_speed" || fail "airtime_post does not call airtime_speed"

# 5d. --fara-test-viteza is accepted and skips the speed test.
OUT5="$(run_setup nospeed --doar "$N" --fara-test-viteza)"
has "Opțiune necunoscută" "$OUT5" && fail "--fara-test-viteza rejected" || ok "--fara-test-viteza accepted"
printf '%s\n' "$OUT5" | grep 'dry-run' | grep -q "fără test de viteză" && ok "--fara-test-viteza: dry-run says skipped" || fail "--fara-test-viteza: no skip in dry-run"
printf '%s\n' "$OUT5" | grep -q "test de viteză (check.sh --speed)" && fail "--fara-test-viteza: speed test still announced" || ok "--fara-test-viteza: speed test not announced"
sed -n '/^airtime_post() {/,/^}/p' "$SETUP" | grep -qF '"$SPEED_TEST" = "no"' \
  && ok "airtime_post honours SPEED_TEST" || fail "airtime_post ignores SPEED_TEST"

# 5c. airtime_speed, extracted from setup-mac.sh and run against a fake check.sh.
FN="$(sed -n '/^airtime_speed() {/,/^}/p' "$SETUP")"
if [ -z "$FN" ]; then
  fail "no airtime_speed() in setup-mac.sh"
else
  cat > "$TMP/fake-check.sh" <<'EOF'
#!/bin/bash
printf '%s|%s|%s\n' "$*" "${CLAUDE_CONFIG_DIR:-}" "${AIRTIME_HOME:-}" > "$FAKE_ARGS"
printf '%s\n' "$FAKE_JSON"
exit 1
EOF
  speed_case() {   # $1 scratch name, $2 what the fake check.sh prints; prints airtime_speed's output
    local d="$TMP/speed-$1"; mkdir -p "$d/plug/scripts" "$d/ahome"
    cp "$TMP/fake-check.sh" "$d/plug/scripts/check.sh"
    [ "$1" = done ] && echo '{"model": "small"}' > "$d/ahome/speed.json"
    FAKE_JSON="$2" FAKE_ARGS="$d/args" CONF="$d/conf" \
      /bin/bash -c "ok() { echo \"OK \$1\"; }; warn() { echo \"WARN \$1\"; }; $FN
airtime_speed '$d/plug' '$d/ahome'" 2>&1
  }
  J_OK='{"ok": false, "checks": [{"name": "youtube", "ok": false, "anchor": "youtube", "detail": "lipsește"}, {"name": "viteză", "ok": true, "anchor": "unelte", "detail": "model medium, un clip de 20 de minute se transcrie în circa 12.0 minute"}]}'
  J_FAIL='{"ok": false, "checks": [{"name": "viteză", "ok": false, "anchor": "unelte", "detail": "transcrierea cu modelul small a eșuat"}]}'
  S="$(speed_case good "$J_OK")"
  has "OK airtime: test de viteză: model medium" "$S" && ok "speed ok: model reported" || { fail "speed ok"; echo "$S"; }
  has "WARN" "$S" && fail "speed ok: warns about youtube" || ok "speed ok: other checks ignored"
  [ "$(cat "$TMP/speed-good/args" 2>/dev/null)" = "--speed --json|$TMP/speed-good/conf|$TMP/speed-good/ahome" ] \
    && ok "speed: check.sh --speed --json with CONF and AIRTIME_HOME" || fail "speed args: $(cat "$TMP/speed-good/args" 2>/dev/null)"
  S="$(speed_case bad "$J_FAIL")"
  has "WARN" "$S" && has "transcrierea cu modelul small a eșuat" "$S" && has "check.sh --speed" "$S" \
    && ok "speed fails: warning with reason and rerun" || { fail "speed fails"; echo "$S"; }
  J_TOOLS='{"ok": false, "checks": [{"name": "viteză", "ok": false, "anchor": "unelte", "detail": "testul de viteză cere uneltele de mai sus"}]}'
  S="$(speed_case tools "$J_TOOLS")"
  has "WARN" "$S" && ! has "de mai sus" "$S" && has "check.sh" "$S" \
    && ok "speed tools missing: no 'de mai sus', points to check.sh" || { fail "speed tools missing"; echo "$S"; }
  S="$(speed_case garbage "nu e json")"
  has "WARN" "$S" && ok "speed garbage: warning" || { fail "speed garbage"; echo "$S"; }
  S="$(speed_case done "$J_OK")"
  has "OK" "$S" && has "deja" "$S" && [ ! -e "$TMP/speed-done/args" ] \
    && ok "speed.json present: test skipped" || { fail "speed.json present"; echo "$S"; }
fi

# 6. --check shows the AirTime block only when the plugin is installed.
d="$TMP/chk"; mkdir -p "$d/conf/plugins" "$d/app" "$d/ahome"
CHK="$(CREATOR_KIT_SOURCE="$ROOT" CLAUDE_CONFIG_DIR="$d/conf" CREATOR_KIT_APP_DIR="$d/app" AIRTIME_HOME="$d/ahome" /bin/bash "$SETUP" --check 2>&1)"
has "AirTime:" "$CHK" && fail "AirTime block shown without the plugin" || ok "no AirTime block when not installed"
printf '{"plugins":{"airtime@creator-kit":[{"installPath":"%s/airtime"}]}}\n' "$ROOT" > "$d/conf/plugins/installed_plugins.json"
CHK="$(CREATOR_KIT_SOURCE="$ROOT" CLAUDE_CONFIG_DIR="$d/conf" CREATOR_KIT_APP_DIR="$d/app" AIRTIME_HOME="$d/ahome" /bin/bash "$SETUP" --check 2>&1)"
has "AirTime:" "$CHK" && has "ffmpeg" "$CHK" && ok "AirTime block with check.sh --quick output" || fail "no AirTime block in --check"

# 7. Syntax.
bash -n "$SETUP" && ok "bash -n setup-mac.sh" || fail "syntax error"

[ "$FAILS" -eq 0 ] && { echo "PASS"; exit 0; } || { echo "$FAILS failed"; exit 1; }
