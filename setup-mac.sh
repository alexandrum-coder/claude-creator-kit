#!/bin/bash
# ============================================================================
# setup-mac.sh — install the creator kit (Claude skills, plugins and an MCP
# server for content work: slides, video, social posts, SEO, brand) on a Mac.
#
# One-line install (asks what to install, then the Mac password once, for Homebrew):
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/setup-mac.sh)"
#
# Options (after the one-liner, add: -- <option>):
#   --toate            install everything that is missing, no menu
#   --doar "1 3 13"    install only these items (numbers from the menu)
#   --check            show what is installed, change nothing
#   --dry-run          print the commands, change nothing
#   --fara-unelte      do not install Homebrew/Node/ffmpeg/uv/yt-dlp/the Claude app
#
# No duplicates, ever. Before installing, the script scans this Mac's Claude
# setup (plugins, loose skills, agents, account and Cowork plugins, MCP servers)
# and installs only what is missing:
#   - a kit skill whose name already exists anywhere is skipped;
#   - a plugin already installed under its name is skipped (or updated, if it
#     came from this kit);
#   - a bundle that contains skills or agents you already have is listed and you
#     are asked; with no terminal to ask, it is skipped.
#
# It touches only Claude's own config (~/.claude, or $CLAUDE_CONFIG_DIR, and the
# user MCP list) and backs up settings.json. Runs on the bash 3.2 of macOS.
# For tests: CREATOR_KIT_SOURCE (a local kit folder), CREATOR_KIT_APP_DIR (stands
# in for ~/Library/Application Support/Claude), SKIP_SHORTS_DEPS=1.
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
APP_DIR="${CREATOR_KIT_APP_DIR:-$HOME/Library/Application Support/Claude}"
KIT_SRC="${CREATOR_KIT_SOURCE:-alexandrum-coder/claude-creator-kit}"
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; }
has_tty() { [ -r /dev/tty ] && { : < /dev/tty; } 2>/dev/null; }

# --- Catalog ----------------------------------------------------------------
# id | label | what it does | tools it needs | kind | members
#   kind group:  members are skills, each one its own plugin in creator-kit
#   kind plugin: one plugin; members = its skills when known in advance
#   kind shorts: the claude-shorts skill; kind mcp: the transcript MCP server
# prompt-agent needs prompt-master; both are members of this group.
CREATOR_SKILLS="humanizer brandkit theme-factory prompt-master prompt-agent notebooklm skill-router plan-taskmanager compact-handoff full-output-enforcement imagegen-frontend-web imagegen-frontend-mobile social-seo podcast-insights"
MK_SKILLS="social video content-strategy copy-editing"
REMOTION_SKILLS="remotion-best-practices remotion-captions remotion-create remotion-docs remotion-interactivity remotion-license remotion-maps remotion-markup remotion-multimedia remotion-render remotion-saas remotion-studio remotion-upgrade"
ITEMS=(
  "creator@creator-kit|creator-skills|14 skill-uri: texte naturale, brand, SEO pe rețele, podcasturi|-|group|$CREATOR_SKILLS"
  "ecc@ecc|ecc|montaj video, prezentări animate, conținut pe rețele|node ffmpeg|plugin|"
  "marketing@knowledge-work-plugins|marketing|postări, campanii, emailuri, analiza concurenței|-|plugin|"
  "design@knowledge-work-plugins|design|feedback pe postări și flyere|-|plugin|"
  "brand-voice@knowledge-work-plugins|brand-voice|tonul brandului, aplicat pe texte|-|plugin|"
  "canva@knowledge-work-plugins|canva|editează și redimensionează design-uri Canva (cont Canva)|-|plugin|"
  "superpowers@superpowers-dev|superpowers|plan și pași clari la proiecte mari|-|plugin|"
  "remotion-skills@creator-kit|remotion-skills|clipuri animate făcute din cod|node|plugin|$REMOTION_SKILLS"
  "workout-program-designer@creator-kit|workout-program-designer|programe de antrenament personalizate|-|plugin|workout-program-designer"
  "postiz@knowledge-work-plugins|postiz|programează postări pe rețele (cont Postiz)|-|plugin|"
  "shorts|claude-shorts|reels și shorts verticale din video lung, cu subtitrări (~1 GB)|node ffmpeg|shorts|shorts"
  "mk@creator-kit|marketingskills|ce postezi, scripturi de reels, strategie, corectură|-|group|$MK_SKILLS"
  "youtube-transcript|youtube-transcript (MCP)|transcrierea clipurilor YouTube, fără cheie API|uv|mcp|"
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
MCP_NAME="youtube-transcript"
MCP_FROM="git+https://github.com/jkawamoto/mcp-youtube-transcript@v0.8.3"   # MIT, no API key

find_claude() {
  local app="$HOME/Library/Application Support/Claude/claude-code" found=""
  if [ -d "$app" ]; then
    found="$(find "$app" -path '*/claude.app/Contents/MacOS/claude' -type f 2>/dev/null | sort -V | tail -1)"
    [ -z "$found" ] && found="$(find "$app" -maxdepth 3 -name claude -type f -perm -u+x 2>/dev/null | sort -V | tail -1)"
  fi
  [ -z "$found" ] && found="$(command -v claude 2>/dev/null || true)"
  printf '%s' "$found"
}

# --- Inventory: what this Mac's Claude already has ---------------------------
# One line per name: "I plugin@market" (installed id), "P plugin", "S skill",
# "A agent", "M mcp-server-name" (transcript servers only). Names are lowercased.
INV="$(mktemp -t creator-kit-inv)"
trap 'rm -f "$INV"' EXIT
scan() {
  CONF="$CONF" APP_DIR="$APP_DIR" OWN_CONF="${CLAUDE_CONFIG_DIR:+yes}" python3 - > "$INV" <<'PY'
import glob, json, os, re

conf, app = os.environ["CONF"], os.environ["APP_DIR"]
out = set()

def front_name(path):
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            head = f.read(4000)
    except OSError:
        return None
    m = re.match(r"---\s*\n(.*?)\n---", head, re.S)
    if m:
        n = re.search(r"^name:\s*['\"]?([^'\"\n]+)", m.group(1), re.M)
        if n:
            return n.group(1).strip()
    return None

def add_mcp(servers):
    if not isinstance(servers, dict):
        return
    for name, spec in servers.items():
        text = (name + " " + json.dumps(spec)).lower()
        if "transcript" in text and ("youtube" in text or "yt" in text):
            out.add("M " + name.lower())

def add_skill_dir(d):
    n = front_name(os.path.join(d, "SKILL.md")) or os.path.basename(d.rstrip("/"))
    out.add("S " + n.lower())

def add_plugin_tree(root):
    if os.path.isfile(os.path.join(root, "SKILL.md")):
        add_skill_dir(root)
    for s in glob.glob(os.path.join(root, "skills", "*", "SKILL.md")):
        add_skill_dir(os.path.dirname(s))
    for a in glob.glob(os.path.join(root, "agents", "*.md")):
        out.add("A " + (front_name(a) or os.path.basename(a)[:-3]).lower())
    for mf in (os.path.join(root, ".mcp.json"), os.path.join(root, ".claude-plugin", "plugin.json")):
        try:
            data = json.load(open(mf))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict):
            add_mcp(data.get("mcpServers", data if mf.endswith(".mcp.json") else {}))

# Plugins installed in Claude Code.
try:
    reg = json.load(open(os.path.join(conf, "plugins", "installed_plugins.json"))).get("plugins", {})
except (OSError, ValueError):
    reg = {}
for pid, installs in reg.items():
    out.add("I " + pid.lower())
    out.add("P " + pid.split("@")[0].lower())
    for inst in installs or []:
        if inst.get("installPath"):
            add_plugin_tree(inst["installPath"])

# Loose skills and agents.
for s in glob.glob(os.path.join(conf, "skills", "*", "SKILL.md")):
    add_skill_dir(os.path.dirname(s))
for a in glob.glob(os.path.join(conf, "agents", "*.md")):
    out.add("A " + (front_name(a) or os.path.basename(a)[:-3]).lower())

# Account and Cowork plugins, and the skills that come with the account.
for pj in glob.glob(os.path.join(app, "local-agent-mode-sessions", "*", "*", "rpm", "plugin_*", ".claude-plugin", "plugin.json")):
    root = os.path.dirname(os.path.dirname(pj))
    try:
        out.add("P " + json.load(open(pj))["name"].lower())
    except (OSError, ValueError, KeyError):
        pass
    add_plugin_tree(root)
for mf in glob.glob(os.path.join(app, "local-agent-mode-sessions", "skills-plugin", "*", "*", "manifest.json")):
    try:
        for s in json.load(open(mf)).get("skills", []):
            n = s.get("name") if isinstance(s, dict) else s
            if n:
                out.add("S " + str(n).lower())
    except (OSError, ValueError):
        pass

# MCP servers: Claude Code's user and project lists, the desktop app's list.
cfgs = [os.path.join(conf, ".claude.json")]
if not os.environ.get("OWN_CONF"):
    cfgs.append(os.path.expanduser("~/.claude.json"))
for cfg in cfgs:
    try:
        d = json.load(open(cfg))
    except (OSError, ValueError):
        continue
    add_mcp(d.get("mcpServers", {}) or {})
    for p in (d.get("projects", {}) or {}).values():
        add_mcp((p or {}).get("mcpServers", {}) or {})
try:
    add_mcp(json.load(open(os.path.join(app, "claude_desktop_config.json"))).get("mcpServers", {}) or {})
except (OSError, ValueError):
    pass

print("\n".join(sorted(out)))
PY
}
have() { grep -qxF "$1 $(printf '%s' "$2" | tr 'A-Z' 'a-z')" "$INV"; }

# Skills and agents a not-yet-installed plugin would bring, read from the
# marketplace copy Claude keeps after "marketplace add". Prints "S name"/"A name".
plugin_members() {
  CONF="$CONF" python3 - "$1" "$2" <<'PY'
import glob, json, os, re, sys
conf, market, plugin = os.environ["CONF"], sys.argv[1], sys.argv[2]
mdir = os.path.join(conf, "plugins", "marketplaces", market)
try:
    entries = json.load(open(os.path.join(mdir, ".claude-plugin", "marketplace.json")))["plugins"]
except (OSError, ValueError, KeyError):
    sys.exit(0)
def front_name(path):
    try:
        head = open(path, encoding="utf-8", errors="replace").read(4000)
    except OSError:
        return None
    m = re.match(r"---\s*\n(.*?)\n---", head, re.S)
    n = m and re.search(r"^name:\s*['\"]?([^'\"\n]+)", m.group(1), re.M)
    return n.group(1).strip() if n else None
for e in entries:
    if e.get("name") != plugin or not isinstance(e.get("source"), str):
        continue
    root = os.path.normpath(os.path.join(mdir, e["source"]))
    dirs = [os.path.normpath(os.path.join(root, s)) for s in e.get("skills", [])] or \
           [os.path.dirname(p) for p in glob.glob(os.path.join(root, "skills", "*", "SKILL.md"))]
    for d in dirs:
        if os.path.isfile(os.path.join(d, "SKILL.md")):
            print("S " + (front_name(os.path.join(d, "SKILL.md")) or os.path.basename(d)).lower())
    for a in glob.glob(os.path.join(root, "agents", "*.md")):
        print("A " + (front_name(a) or os.path.basename(a)[:-3]).lower())
PY
}

# Status of item $1 for the menu and --check: "ok", "upd" (from this kit,
# will be updated), "part:K/N" (group, K missing of N) or "new".
status() {
  local id kind mem name k=0 n=0 u=0 m
  id="$(field $1 1)"; kind="$(field $1 5)"; mem="$(field $1 6)"
  case "$kind" in
    group)
      for m in $mem; do
        n=$((n+1)); have S "$m" || k=$((k+1)); have I "$m@creator-kit" && u=$((u+1))
      done
      if [ $k -eq 0 ] && [ $u -gt 0 ]; then echo upd
      elif [ $k -eq 0 ]; then echo ok
      elif [ $k -eq $n ]; then echo new
      else echo "part:$k/$n"; fi ;;
    plugin)
      name="${id%@*}"
      if have I "$id"; then if [ "${id#*@}" = "creator-kit" ]; then echo upd; else echo ok; fi
      elif have P "$name"; then echo ok
      else echo new; fi ;;
    shorts) if [ -f "$CONF/skills/shorts/SKILL.md" ]; then echo upd; elif have S shorts; then echo ok; else echo new; fi ;;
    mcp) if grep -q '^M ' "$INV"; then echo ok; else echo new; fi ;;
  esac
}
label_status() {
  case "$1" in
    ok) printf '✔ ai deja' ;;
    upd) printf '✔ instalat, se actualizează' ;;
    part:*) printf 'lipsesc %s' "$(printf '%s' "${1#part:}" | sed 's|/| din |')" ;;
    *) printf '' ;;
  esac
}

scan

# --- Check mode -------------------------------------------------------------
if [ "$CHECK" = "yes" ]; then
  echo "Ce e instalat:"
  i=0
  while [ $i -lt $N ]; do
    st="$(status $i)"
    case "$st" in
      ok|upd) ok "$(field $i 2)" ;;
      part:*) printf '  – %s (%s)\n' "$(field $i 2)" "$(label_status "$st")" ;;
      *) printf '  – %s (neinstalat)\n' "$(field $i 2)" ;;
    esac
    i=$((i+1))
  done
  exit 0
fi

# --- 1. Choose --------------------------------------------------------------
SEL=()   # indexes of chosen items
echo "Creator Kit: ce se poate instala (ce ai deja nu se instalează a doua oară)"
i=0
while [ $i -lt $N ]; do
  printf '  %2d. %-26s %s' $((i+1)) "$(field $i 2)" "$(field $i 3)"
  s="$(label_status "$(status $i)")"; [ -n "$s" ] && printf '  [%s]' "$s"
  printf '\n'
  i=$((i+1))
done
echo

if [ -z "$MODE" ]; then
  if has_tty; then
    printf 'Instalez [T]oate (doar ce lipsește) sau [A]leg eu? (T/a): '
    read -r ans < /dev/tty || ans=""
    case "$ans" in a|A|aleg|Aleg) MODE="doar" ;; *) MODE="toate" ;; esac
    if [ "$MODE" = "doar" ]; then
      printf 'Scrie numerele dorite, separate prin spațiu (ex: 1 3 11 13): '
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

# Keep only what has something to do; "ok" items are already there.
TODO=()
for i in ${SEL[@]+"${SEL[@]}"}; do
  [ "$(status $i)" = "ok" ] && continue
  TODO+=($i)
done
if [ ${#TODO[@]} -eq 0 ]; then
  [ ${#SEL[@]} -eq 0 ] && { fail "Nu ai ales nimic. Rulează din nou comanda."; exit 1; }
  ok "Ai deja tot ce ai ales. Nu instalez nimic."; exit 0
fi

echo "Instalez sau actualizez:"
WANT_NODE="no"; WANT_FFMPEG="no"; WANT_UV="no"; WANT_YTDLP="no"
for i in "${TODO[@]}"; do
  echo "  • $(field $i 2)"
  case " $(field $i 4) " in *" node "*) WANT_NODE="yes" ;; esac
  case " $(field $i 4) " in *" ffmpeg "*) WANT_FFMPEG="yes" ;; esac
  case " $(field $i 4) " in *" uv "*) WANT_UV="yes" ;; esac
  if [ "$(field $i 1)" = "creator@creator-kit" ] && ! have S podcast-insights; then WANT_YTDLP="yes"; fi
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
load_brew || true
need=()
[ "$WANT_NODE" = "yes" ] && ! command -v node >/dev/null 2>&1 && need+=(node)
[ "$WANT_FFMPEG" = "yes" ] && ! command -v ffmpeg >/dev/null 2>&1 && need+=(ffmpeg)
[ "$WANT_UV" = "yes" ] && ! command -v uvx >/dev/null 2>&1 && need+=(uv)
[ "$WANT_YTDLP" = "yes" ] && ! command -v yt-dlp >/dev/null 2>&1 && need+=(yt-dlp)
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
for t in node ffmpeg uv yt-dlp; do
  case "$t" in node) w="$WANT_NODE"; c=node ;; ffmpeg) w="$WANT_FFMPEG"; c=ffmpeg ;; uv) w="$WANT_UV"; c=uvx ;; *) w="$WANT_YTDLP"; c=yt-dlp ;; esac
  [ "$w" = "yes" ] || continue
  if command -v "$c" >/dev/null 2>&1; then ok "$t: prezent"; else warn "$t lipsește (brew install $t)"; fi
done

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

# --- 3. Install, one item at a time ------------------------------------------
KNOWN="$("$CLAUDE" plugin marketplace list 2>/dev/null || true)"
DONE_M=" "
ensure_market() {
  local m="$1" src
  case "$DONE_M" in *" $m "*) return 0 ;; esac
  DONE_M="$DONE_M$m "
  src="$(market_source "$m")"
  if printf '%s\n' "$KNOWN" | grep -q "❯ $m\$"; then
    run plugin marketplace update "$m" >/dev/null 2>&1 || warn "$m: actualizarea sursei a eșuat, merg mai departe"
  else
    run plugin marketplace add "$src" >/dev/null 2>&1 || { fail "$m: nu am putut adăuga sursa $src"; return 1; }
  fi
}
ask_yes() {   # $1 question; yes only on an explicit "d"
  local a=""
  has_tty || return 1
  printf '    %s (d/N): ' "$1"
  read -r a < /dev/tty || a=""
  case "$a" in d|D|da|Da|y|Y) return 0 ;; *) return 1 ;; esac
}
install_plugin() {   # $1 plugin@market, $2 label
  local out
  if out="$(run plugin install "$1" 2>&1)"; then ok "$2"
  else fail "$2: $(printf '%s' "$out" | tail -1)"; errors=$((errors+1)); fi
}

echo
echo "2. Instalare"
errors=0; ECC_DONE="no"
for i in "${TODO[@]}"; do
  id="$(field $i 1)"; label="$(field $i 2)"; kind="$(field $i 5)"; mem="$(field $i 6)"
  scan
  case "$kind" in
    group)
      ensure_market creator-kit || { errors=$((errors+1)); continue; }
      for m in $mem; do
        if have I "$m@creator-kit"; then run plugin update "$m@creator-kit" >/dev/null 2>&1; ok "$m (actualizat)"
        elif have S "$m"; then ok "$m: îl ai deja, sar peste"
        else install_plugin "$m@creator-kit" "$m"; fi
      done ;;
    plugin)
      market="${id#*@}"; name="${id%@*}"
      ensure_market "$market" || { errors=$((errors+1)); continue; }
      if have I "$id"; then run plugin update "$id" >/dev/null 2>&1; ok "$label (actualizat)"; continue; fi
      if have P "$name"; then ok "$label: îl ai deja, sar peste"; continue; fi
      members="$(plugin_members "$market" "$name")"
      if [ -z "$members" ]; then for m in $mem; do members="$members
S $m"; done; fi
      dup=""; cnt=0
      while read -r kindn nm; do
        [ -z "${nm:-}" ] && continue
        if have "$kindn" "$nm"; then cnt=$((cnt+1)); [ $cnt -le 8 ] && dup="$dup $nm"; fi
      done <<EOF
$members
EOF
      if [ $cnt -gt 0 ]; then
        [ $cnt -gt 8 ] && dup="$dup și încă $((cnt-8))"
        warn "$label conține $cnt skill-uri sau agenți pe care îi ai deja:$dup"
        if ! ask_yes "Instalez $label oricum? Acestea ar exista de două ori."; then
          warn "$label: sărit, ca să nu dublez"; continue
        fi
      fi
      if [ -n "$members" ] || [ "$DRY" = "yes" ]; then
        install_plugin "$id" "$label"
      else
        # Contents unknown before install (the plugin lives in another repo):
        # install, compare what it brought with what was already here, and
        # take it back out unless you say yes.
        cp "$INV" "$INV.before"
        if out="$(run plugin install "$id" 2>&1)"; then
          dup="$(CONF="$CONF" python3 - "$id" "$INV.before" <<'PY'
import glob, json, os, re, sys
conf, pid, before = os.environ["CONF"], sys.argv[1], set(open(sys.argv[2]).read().split("\n"))
def nm(p):
    h = open(p, encoding="utf-8", errors="replace").read(4000)
    m = re.search(r"^name:\s*['\"]?([^'\"\n]+)", h, re.M)
    return (m.group(1).strip() if m else os.path.basename(os.path.dirname(p))).lower()
reg = json.load(open(os.path.join(conf, "plugins", "installed_plugins.json")))["plugins"].get(pid, [])
names = set()
for inst in reg:
    r = inst.get("installPath", "")
    for p in glob.glob(r + "/SKILL.md") + glob.glob(r + "/skills/*/SKILL.md"):
        names.add("S " + nm(p))
    for p in glob.glob(r + "/agents/*.md"):
        names.add("A " + nm(p))
print(" ".join(sorted(n[2:] for n in names & before)))
PY
)"
          if [ -n "$dup" ]; then
            warn "$label conține skill-uri sau agenți pe care îi ai deja: $dup"
            if ask_yes "Îl păstrez oricum? Acestea ar exista de două ori."; then ok "$label"
            else run plugin uninstall "$id" >/dev/null 2>&1; warn "$label: scos la loc, ca să nu dublez"; fi
          else
            ok "$label"
          fi
        else
          fail "$label: $(printf '%s' "$out" | tail -1)"; errors=$((errors+1))
        fi
        rm -f "$INV.before"
      fi
      [ "$id" = "ecc@ecc" ] && ECC_DONE="yes" ;;
    shorts)
      # Not a plugin: it must live in ~/.claude/skills/shorts. Its own setup.sh makes a
      # Python environment in ~/.shorts-skill and runs npm install for its Remotion
      # part (about 1 GB). SKIP_SHORTS_DEPS=1 skips that part (used in tests).
      SHORTS_DIR="$CONF/skills/shorts"
      if [ "$DRY" = "yes" ]; then
        echo "    [dry-run] git clone claude-shorts @ ${SHORTS_SHA:0:7} -> $SHORTS_DIR, apoi setup.sh"; continue
      fi
      tmp="$(mktemp -d)"
      if git clone --quiet "$SHORTS_REPO" "$tmp/shorts" && git -C "$tmp/shorts" checkout --quiet "$SHORTS_SHA"; then
        mkdir -p "$SHORTS_DIR"
        rsync -a --delete --exclude='.git' --exclude='node_modules' --exclude='.remotion' --exclude='*.jpeg' \
          "$tmp/shorts/" "$SHORTS_DIR/"
        ok "claude-shorts: skill copiat"
        if [ "${SKIP_SHORTS_DEPS:-0}" = "1" ]; then
          warn "dependențe sărite (SKIP_SHORTS_DEPS=1)"
        elif ! command -v node >/dev/null 2>&1; then
          warn "lipsește Node.js; instalează-l, apoi rulează din nou comanda"
        else
          echo "    instalez uneltele de transcriere și randare (un minut sau două)..."
          if (cd "$SHORTS_DIR" && bash setup.sh) > "$SHORTS_DIR/setup.log" 2>&1; then ok "claude-shorts: unelte instalate"
          else warn "uneltele n-au mers, vezi $SHORTS_DIR/setup.log"; fi
        fi
      else
        fail "nu am putut descărca claude-shorts"; errors=$((errors+1))
      fi
      rm -rf "$tmp" ;;
    mcp)
      if grep -q '^M ' "$INV"; then ok "$label: ai deja un server de transcriere YouTube"; continue; fi
      if ! command -v uvx >/dev/null 2>&1 && [ "$DRY" != "yes" ]; then
        warn "$label: lipsește uv (brew install uv); rulează din nou comanda după"; errors=$((errors+1)); continue
      fi
      if out="$(run mcp add --scope user "$MCP_NAME" -- uvx --from "$MCP_FROM" mcp-youtube-transcript 2>&1)"; then ok "$label"
      else fail "$label: $(printf '%s' "$out" | tail -1)"; errors=$((errors+1)); fi ;;
  esac
done

# --- 4. Quieter ECC ---------------------------------------------------------
# ECC ships developer hooks; GateGuard stops the first file write of every
# session to ask for "facts". For content work, switch ECC to its minimal hook
# profile and turn GateGuard off. Existing values are left alone.
if [ "$ECC_DONE" = "yes" ]; then
  echo
  echo "3. Reglaj ecc pentru lucru de conținut"
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
echo "Ca să adaugi altceva mai târziu, rulează din nou aceeași comandă: ce ai deja nu se instalează a doua oară."
