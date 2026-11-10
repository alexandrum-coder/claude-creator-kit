#!/bin/bash
# ============================================================================
# setup-mac.sh — install the creator kit (Claude skills/plugins for content
# work: slides, video, social posts, brand) on a Mac.
#
#   bash setup-mac.sh             # install or update everything
#   bash setup-mac.sh --dry-run   # print the commands, change nothing
#   bash setup-mac.sh --check     # show what is installed, change nothing
#
# Safe to run again: existing marketplaces are refreshed, installed plugins
# are updated. It touches only Claude's own config folder (~/.claude, or
# $CLAUDE_CONFIG_DIR when set) and backs up settings.json before editing it.
# CREATOR_KIT_SOURCE overrides where the kit comes from (a local folder, for tests).
# After it finishes: quit the Claude desktop app completely (Cmd+Q) and
# open it again — a new chat alone does not load new plugins.
# ============================================================================
set -uo pipefail

DRY="no"
CHECK="no"
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY="yes"; shift ;;
    --check) CHECK="yes"; shift ;;
    -h|--help) sed -n '2,16p' "$0"; exit 0 ;;
    *) echo "Opțiune necunoscută: $1 (vezi --help)"; exit 2 ;;
  esac
done

CONF="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; }

# --- 1. Find the claude binary ----------------------------------------------
# The desktop app ships its own copy; its folder name changes with each
# version, so search for it. Fall back to a `claude` on PATH (CLI install).
find_claude() {
  local app="$HOME/Library/Application Support/Claude/claude-code"
  local found=""
  if [ -d "$app" ]; then
    found="$(find "$app" -path '*/claude.app/Contents/MacOS/claude' -type f 2>/dev/null | sort -V | tail -1)"
    [ -z "$found" ] && found="$(find "$app" -maxdepth 3 -name claude -type f -perm -u+x 2>/dev/null | sort -V | tail -1)"
  fi
  [ -z "$found" ] && found="$(command -v claude 2>/dev/null || true)"
  printf '%s' "$found"
}

echo "1. Verific ce e instalat pe Mac"
CLAUDE="$(find_claude)"
if [ -z "$CLAUDE" ]; then
  fail "Nu găsesc Claude. Instalează aplicația Claude de pe https://claude.ai/download, deschide-o o dată, intră în tab-ul Code, apoi rulează din nou scriptul."
  exit 1
fi
ok "Claude: $("$CLAUDE" --version 2>/dev/null | head -1)"

if xcode-select -p >/dev/null 2>&1 && command -v git >/dev/null 2>&1; then
  ok "git: $(git --version)"
else
  fail "Lipsește git. Rulează: xcode-select --install  (apare o fereastră, apasă Install), apoi rulează din nou scriptul."
  exit 1
fi
command -v python3 >/dev/null 2>&1 && ok "python3: $(python3 --version 2>&1)" \
  || warn "python3 lipsește: unele skill-uri nu vor merge. Vine cu xcode-select --install."
command -v node >/dev/null 2>&1 && ok "node: $(node --version)" \
  || warn "Node.js lipsește: pluginul ecc are nevoie de el pentru hook-uri. Instalează-l de pe https://nodejs.org (varianta LTS)."
command -v ffmpeg >/dev/null 2>&1 && ok "ffmpeg: prezent (montaj video)" \
  || warn "ffmpeg lipsește: skill-ul de montaj video îl folosește. Opțional: instalează Homebrew (https://brew.sh), apoi brew install ffmpeg."

# --- 2. What to install -----------------------------------------------------
# name|source  (source = GitHub owner/repo)
MARKETS=(
  "creator-kit|${CREATOR_KIT_SOURCE:-alexandrum-coder/claude-creator-kit}"
  "ecc|affaan-m/ecc"
  "knowledge-work-plugins|anthropics/knowledge-work-plugins"
  "superpowers-dev|obra/superpowers"
)
PLUGINS=(
  "creator-skills@creator-kit"
  "ecc@ecc"
  "marketing@knowledge-work-plugins"
  "design@knowledge-work-plugins"
  "brand-voice@knowledge-work-plugins"
  "canva@knowledge-work-plugins"
  "superpowers@superpowers-dev"
)

# --- check mode -------------------------------------------------------------
if [ "$CHECK" = "yes" ]; then
  echo
  echo "2. Ce e instalat acum"
  LIST="$("$CLAUDE" plugin list 2>&1)"
  missing=0
  for p in "${PLUGINS[@]}"; do
    if printf '%s\n' "$LIST" | grep -q "❯ $p\$"; then ok "$p"; else fail "$p lipsește"; missing=$((missing+1)); fi
  done
  [ "$missing" -eq 0 ] && echo "Totul e la locul lui." || echo "Lipsesc $missing pluginuri: rulează scriptul fără --check."
  exit 0
fi

run() {
  if [ "$DRY" = "yes" ]; then
    printf '    [dry-run] %q' "$CLAUDE"; printf ' %q' "$@"; printf '\n'
    return 0
  fi
  "$CLAUDE" "$@"
}

# --- 3. Marketplaces --------------------------------------------------------
echo
echo "2. Adaug sursele de pluginuri"
KNOWN="$("$CLAUDE" plugin marketplace list 2>/dev/null || true)"
for entry in "${MARKETS[@]}"; do
  name="${entry%%|*}"; src="${entry#*|}"
  if printf '%s\n' "$KNOWN" | grep -q "❯ $name\$"; then
    if run plugin marketplace update "$name" >/dev/null 2>&1; then ok "$name (actualizat)"; else warn "$name: actualizarea a eșuat, merg mai departe"; fi
  else
    if run plugin marketplace add "$src" >/dev/null 2>&1; then ok "$name (adăugat din $src)"; else fail "$name: nu am putut adăuga $src"; fi
  fi
done

# --- 4. Plugins -------------------------------------------------------------
echo
echo "3. Instalez pluginurile"
errors=0
for p in "${PLUGINS[@]}"; do
  if out="$(run plugin install "$p" 2>&1)"; then
    if printf '%s' "$out" | grep -q "already installed"; then
      run plugin update "$p" >/dev/null 2>&1 && ok "$p (era instalat, l-am actualizat)" || ok "$p (era instalat)"
    else
      ok "$p"
    fi
  else
    fail "$p: $(printf '%s' "$out" | tail -1)"
    errors=$((errors+1))
  fi
done

# --- 5. Quieter ECC ---------------------------------------------------------
# ECC ships many developer hooks; one of them (GateGuard) stops the first file
# write of every session to ask for "facts". For content work that only gets
# in the way, so switch ECC to its minimal hook profile and turn GateGuard off.
# Existing values are left alone.
echo
echo "4. Reglez pluginul ecc pentru lucru de conținut"
SETTINGS="$CONF/settings.json"
if [ "$DRY" = "yes" ]; then
  echo "    [dry-run] în $SETTINGS: env.ECC_HOOK_PROFILE=minimal, env.ECC_GATEGUARD=off (dacă lipsesc)"
else
  mkdir -p "$CONF"
  [ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%d-%H%M%S)"
  SETTINGS="$SETTINGS" python3 - <<'PY' && ok "settings.json: ECC în profil minimal, GateGuard oprit (backup alături)"
import json, os
path = os.environ["SETTINGS"]
data = {}
if os.path.exists(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
env = data.setdefault("env", {})
env.setdefault("ECC_HOOK_PROFILE", "minimal")
env.setdefault("ECC_GATEGUARD", "off")
with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY
fi

# --- 6. Done ----------------------------------------------------------------
echo
if [ "$errors" -eq 0 ]; then
  echo "Gata. Acum: închide complet aplicația Claude (Cmd+Q) și deschide-o din nou."
else
  echo "Gata, cu $errors erori (vezi ✘ mai sus). Rulează scriptul încă o dată; dacă rămân, trimite mai departe ce scrie la ✘."
fi
echo "Verificare oricând: bash setup-mac.sh --check"
