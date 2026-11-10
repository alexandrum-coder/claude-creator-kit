#!/bin/bash
# ============================================================================
# setup-mac.sh — install the creator kit (Claude skills/plugins for content
# work: slides, video, social posts, brand) on a Mac.
#
# One-line install (asks what to install, then the Mac password once, for Homebrew):
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)"
#
# Options (after the one-liner, add: -- <option>):
#   --toate            install everything, no questions
#   --doar "1 3 11"    install only these items (numbers from the menu)
#   --check            show what is installed, change nothing
#   --dry-run          print the commands, change nothing
#   --fara-unelte      do not install Homebrew/Node/ffmpeg/the Claude app
#
# Safe to run again: existing items are updated. It touches only Claude's own
# config folder (~/.claude, or $CLAUDE_CONFIG_DIR) and backs up settings.json.
# CREATOR_KIT_SOURCE overrides where the kit comes from (a local folder, for tests).
# Runs on the bash 3.2 that ships with macOS.
# ============================================================================
set -uo pipefail

DRY="no"; CHECK="no"; TOOLS="yes"; MODE=""; PICK=""
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY="yes"; shift ;;
    --check) CHECK="yes"; shift ;;
    --fara-unelte) TOOLS="no"; shift ;;
    --toate) MODE="toate"; shift ;;
    --doar) MODE="doar"; PICK="${2:-}"; shift 2 ;;
    -h|--help) echo "Vezi https://github.com/alexandrum-coder/claude-creator-kit#readme"; exit 0 ;;
    *) echo "Opțiune necunoscută: $1"; exit 2 ;;
  esac
done
[ "$CHECK" = "yes" ] && TOOLS="no"   # --check only reads

CONF="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
KIT_SRC="${CREATOR_KIT_SOURCE:-alexandrum-coder/claude-creator-kit}"
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; }

# --- Catalog ----------------------------------------------------------------
# plugin@marketplace (or "shorts") | label | what it does | needs
ITEMS=(
  "creator-skills@creator-kit|creator-skills|11 skill-uri: texte naturale, brand, teme, prompturi AI|-"
  "ecc@ecc|ecc|montaj video, prezentări animate, conținut pe rețele|node ffmpeg"
  "marketing@knowledge-work-plugins|marketing|postări, campanii, emailuri|-"
  "design@knowledge-work-plugins|design|feedback pe postări și flyere|-"
  "brand-voice@knowledge-work-plugins|brand-voice|tonul brandului, aplicat pe texte|-"
  "canva@knowledge-work-plugins|canva|editează și redimensionează design-uri Canva (cont Canva)|-"
  "superpowers@superpowers-dev|superpowers|plan și pași clari la proiecte mari|-"
  "remotion-skills@creator-kit|remotion-skills|clipuri animate făcute din cod|node"
  "workout-program-designer@creator-kit|workout-program-designer|programe de antrenament personalizate|-"
  "postiz@knowledge-work-plugins|postiz|programează postări pe rețele (cont Postiz)|-"
  "shorts|claude-shorts|reels și shorts verticale din video lung, cu subtitrări (~1 GB)|node ffmpeg"
)
N=${#ITEMS[@]}
field() { printf '%s' "${ITEMS[$1]}" | cut -d'|' -f"$2"; }
market_source() {
  case "$1" in
    creator-kit) printf '%s' "$KIT_SRC" ;;
    ecc) printf 'affaan-m/ecc' ;;
    knowledge-work-plugins) printf 'anthropics/knowledge-work-plugins' ;;
    superpowers-dev) printf 'obra/superpowers' ;;
  esac
}
SHORTS_REPO="https://github.com/AgriciDaniel/claude-shorts.git"
SHORTS_SHA="a369fad9d84287edbb8fa3ab515f268e770f683b"   # reviewed commit, MIT

find_claude() {
  local app="$HOME/Library/Application Support/Claude/claude-code" found=""
  if [ -d "$app" ]; then
    found="$(find "$app" -path '*/claude.app/Contents/MacOS/claude' -type f 2>/dev/null | sort -V | tail -1)"
    [ -z "$found" ] && found="$(find "$app" -maxdepth 3 -name claude -type f -perm -u+x 2>/dev/null | sort -V | tail -1)"
  fi
  [ -z "$found" ] && found="$(command -v claude 2>/dev/null || true)"
  printf '%s' "$found"
}

# --- Check mode -------------------------------------------------------------
if [ "$CHECK" = "yes" ]; then
  CLAUDE="$(find_claude)"
  [ -z "$CLAUDE" ] && { fail "Nu găsesc Claude."; exit 1; }
  LIST="$("$CLAUDE" plugin list 2>&1)"
  echo "Ce e instalat:"
  i=0
  while [ $i -lt $N ]; do
    id="$(field $i 1)"; label="$(field $i 2)"
    if [ "$id" = "shorts" ]; then
      [ -f "$CONF/skills/shorts/SKILL.md" ] && ok "$label" || printf '  – %s (neinstalat)\n' "$label"
    else
      printf '%s\n' "$LIST" | grep -q "❯ $id\$" && ok "$label" || printf '  – %s (neinstalat)\n' "$label"
    fi
    i=$((i+1))
  done
  exit 0
fi

# --- 1. Choose --------------------------------------------------------------
SEL=()   # indexes of chosen items
echo "Creator Kit: ce se poate instala"
i=0
while [ $i -lt $N ]; do
  printf '  %2d. %-26s %s\n' $((i+1)) "$(field $i 2)" "$(field $i 3)"
  i=$((i+1))
done
echo

if [ -z "$MODE" ]; then
  if [ -r /dev/tty ] && { : < /dev/tty; } 2>/dev/null; then
    printf 'Instalez [T]oate sau [A]leg eu? (T/a): '
    read -r ans < /dev/tty || ans=""
    case "$ans" in a|A|aleg|Aleg) MODE="doar" ;; *) MODE="toate" ;; esac
    if [ "$MODE" = "doar" ]; then
      printf 'Scrie numerele dorite, separate prin spațiu (ex: 1 3 6 11): '
      read -r PICK < /dev/tty || PICK=""
    fi
  else
    MODE="toate"
  fi
fi

if [ "$MODE" = "toate" ]; then
  i=0; while [ $i -lt $N ]; do SEL+=($i); i=$((i+1)); done
else
  for n in $(printf '%s' "$PICK" | tr ',' ' '); do
    case "$n" in ''|*[!0-9]*) warn "ignor „$n”: nu e un număr din listă"; continue ;; esac
    if [ "$n" -ge 1 ] && [ "$n" -le $N ]; then SEL+=($((n-1))); else warn "ignor $n: nu există în listă"; fi
  done
fi
if [ ${#SEL[@]} -eq 0 ]; then fail "Nu ai ales nimic. Rulează din nou comanda."; exit 1; fi

echo "Instalez:"
WANT_NODE="no"; WANT_FFMPEG="no"; WANT_SHORTS="no"; WANT_ECC="no"
for i in "${SEL[@]}"; do
  echo "  • $(field $i 2)"
  case " $(field $i 4) " in *" node "*) WANT_NODE="yes" ;; esac
  case " $(field $i 4) " in *" ffmpeg "*) WANT_FFMPEG="yes" ;; esac
  [ "$(field $i 1)" = "shorts" ] && WANT_SHORTS="yes"
  [ "$(field $i 1)" = "ecc@ecc" ] && WANT_ECC="yes"
done

# --- 2. Base tools ----------------------------------------------------------
echo
echo "1. Unelte de bază"
if ! xcode-select -p >/dev/null 2>&1 || ! command -v git >/dev/null 2>&1; then
  if [ "$DRY" = "yes" ]; then echo "    [dry-run] xcode-select --install"
  else
    xcode-select --install >/dev/null 2>&1 || true
    fail "Lipsesc uneltele Apple (git, python3). S-a deschis o fereastră: apasă Install, așteaptă, apoi rulează din nou aceeași comandă."
    exit 1
  fi
fi
ok "git: $(git --version 2>/dev/null)"

load_brew() {
  local b
  for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [ -x "$b" ] && eval "$("$b" shellenv)" && return 0
  done
  command -v brew >/dev/null 2>&1
}
need=()
[ "$WANT_NODE" = "yes" ] && ! command -v node >/dev/null 2>&1 && need+=(node)
[ "$WANT_FFMPEG" = "yes" ] && ! command -v ffmpeg >/dev/null 2>&1 && need+=(ffmpeg)
app_missing="no"
[ -d "/Applications/Claude.app" ] || [ -d "$HOME/Applications/Claude.app" ] || app_missing="yes"

if [ "$TOOLS" = "yes" ] && { [ ${#need[@]} -gt 0 ] || [ "$app_missing" = "yes" ]; }; then
  if ! load_brew; then
    if [ "$DRY" = "yes" ]; then echo "    [dry-run] instalez Homebrew (https://brew.sh)"
    else
      echo "    Instalez Homebrew, managerul de aplicații pentru Mac. Îți cere parola de Mac."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" || true
      load_brew || { fail "Homebrew nu s-a instalat. Instalează-l de pe https://brew.sh, apoi rulează din nou."; exit 1; }
    fi
  fi
  if [ ${#need[@]} -gt 0 ]; then
    if [ "$DRY" = "yes" ]; then echo "    [dry-run] brew install ${need[*]}"
    else echo "    Instalez: ${need[*]}"; brew install "${need[@]}" >/dev/null 2>&1 || warn "brew install ${need[*]} a eșuat"; fi
  fi
  if [ "$app_missing" = "yes" ]; then
    if [ "$DRY" = "yes" ]; then echo "    [dry-run] brew install --cask claude"
    else echo "    Instalez aplicația Claude"; brew install --cask claude >/dev/null 2>&1 || warn "aplicația Claude nu s-a instalat; descarc-o de pe https://claude.ai/download"; fi
  fi
fi
if [ "$WANT_NODE" = "yes" ]; then
  command -v node >/dev/null 2>&1 && ok "node: $(node --version)" || warn "Node.js lipsește (https://nodejs.org)"
fi
if [ "$WANT_FFMPEG" = "yes" ]; then
  command -v ffmpeg >/dev/null 2>&1 && ok "ffmpeg: prezent" || warn "ffmpeg lipsește (brew install ffmpeg)"
fi

CLAUDE="$(find_claude)"
if [ -z "$CLAUDE" ]; then
  fail "Aplicația Claude nu e pregătită. Deschide-o, intră în cont, deschide o dată tab-ul Code, apoi rulează din nou aceeași comandă."
  exit 1
fi
ok "Claude: $("$CLAUDE" --version 2>/dev/null | head -1)"

run() {
  if [ "$DRY" = "yes" ]; then printf '    [dry-run] claude'; printf ' %q' "$@"; printf '\n'; return 0; fi
  "$CLAUDE" "$@"
}

# --- 3. Plugin sources ------------------------------------------------------
echo
echo "2. Surse de pluginuri"
KNOWN="$("$CLAUDE" plugin marketplace list 2>/dev/null || true)"
DONE_M=" "
for i in "${SEL[@]}"; do
  id="$(field $i 1)"; [ "$id" = "shorts" ] && continue
  m="${id#*@}"
  case "$DONE_M" in *" $m "*) continue ;; esac
  DONE_M="$DONE_M$m "
  src="$(market_source "$m")"
  if printf '%s\n' "$KNOWN" | grep -q "❯ $m\$"; then
    run plugin marketplace update "$m" >/dev/null 2>&1 && ok "$m (actualizat)" || warn "$m: actualizarea a eșuat, merg mai departe"
  else
    run plugin marketplace add "$src" >/dev/null 2>&1 && ok "$m (adăugat)" || fail "$m: nu am putut adăuga $src"
  fi
done

# --- 4. Plugins -------------------------------------------------------------
echo
echo "3. Pluginuri"
errors=0
for i in "${SEL[@]}"; do
  id="$(field $i 1)"; [ "$id" = "shorts" ] && continue
  if out="$(run plugin install "$id" 2>&1)"; then
    if printf '%s' "$out" | grep -q "already installed"; then
      run plugin update "$id" >/dev/null 2>&1; ok "$(field $i 2) (actualizat)"
    else
      ok "$(field $i 2)"
    fi
  else
    fail "$(field $i 2): $(printf '%s' "$out" | tail -1)"; errors=$((errors+1))
  fi
done

# --- 5. claude-shorts -------------------------------------------------------
# Not a plugin: it must live in ~/.claude/skills/shorts. Its own setup.sh makes a
# Python environment in ~/.shorts-skill and runs npm install for its Remotion
# part (about 1 GB). SKIP_SHORTS_DEPS=1 skips that part (used in tests).
if [ "$WANT_SHORTS" = "yes" ]; then
  echo
  echo "4. claude-shorts"
  SHORTS_DIR="$CONF/skills/shorts"
  if [ "$DRY" = "yes" ]; then
    echo "    [dry-run] git clone claude-shorts @ ${SHORTS_SHA:0:7} -> $SHORTS_DIR, apoi setup.sh"
  else
    tmp="$(mktemp -d)"
    if git clone --quiet "$SHORTS_REPO" "$tmp/shorts" && git -C "$tmp/shorts" checkout --quiet "$SHORTS_SHA"; then
      mkdir -p "$SHORTS_DIR"
      rsync -a --delete --exclude='.git' --exclude='node_modules' --exclude='.remotion' --exclude='*.jpeg' \
        "$tmp/shorts/" "$SHORTS_DIR/"
      ok "skill copiat"
      if [ "${SKIP_SHORTS_DEPS:-0}" = "1" ]; then
        warn "dependențe sărite (SKIP_SHORTS_DEPS=1)"
      elif ! command -v node >/dev/null 2>&1; then
        warn "lipsește Node.js; instalează-l, apoi rulează din nou comanda"
      else
        echo "    instalez uneltele de transcriere și randare (un minut sau două)..."
        if (cd "$SHORTS_DIR" && bash setup.sh) > "$SHORTS_DIR/setup.log" 2>&1; then ok "unelte instalate"
        else warn "uneltele n-au mers, vezi $SHORTS_DIR/setup.log"; fi
      fi
    else
      fail "nu am putut descărca claude-shorts"; errors=$((errors+1))
    fi
    rm -rf "$tmp"
  fi
fi

# --- 6. Quieter ECC ---------------------------------------------------------
# ECC ships developer hooks; GateGuard stops the first file write of every
# session to ask for "facts". For content work, switch ECC to its minimal hook
# profile and turn GateGuard off. Existing values are left alone.
if [ "$WANT_ECC" = "yes" ]; then
  echo
  echo "5. Reglaj ecc pentru lucru de conținut"
  SETTINGS="$CONF/settings.json"
  if [ "$DRY" = "yes" ]; then
    echo "    [dry-run] settings.json: ECC_HOOK_PROFILE=minimal, ECC_GATEGUARD=off"
  else
    mkdir -p "$CONF"
    [ -f "$SETTINGS" ] && cp "$SETTINGS" "$SETTINGS.bak-$(date +%Y%m%d-%H%M%S)"
    SETTINGS="$SETTINGS" python3 - <<'PY' && ok "gata (backup alături de settings.json)"
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
fi

echo
if [ "$errors" -eq 0 ]; then
  echo "Gata. Închide complet aplicația Claude (Cmd+Q) și deschide-o din nou."
else
  echo "Gata, cu $errors erori (vezi ✘). Rulează din nou comanda; dacă rămân, trimite mai departe ce scrie la ✘."
fi
echo "Ca să adaugi altceva mai târziu, rulează din nou aceeași comandă și alege doar ce lipsește."
