#!/bin/bash
# ============================================================================
# postiz-local.sh — run Postiz (social media scheduler) for free on this Mac,
# with Colima + Docker Compose and the official postiz-docker-compose files.
#
#   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/alexandrum-coder/claude-creator-kit/main/postiz-local.sh)" -- install
#
#   install   install Colima + Docker, download Postiz, start it, open the browser
#   start     start Postiz again (after a restart of the Mac)
#   stop      stop Postiz and free the memory
#   status    show whether it runs
#   update    download the latest Postiz and restart
#
# Postiz lives in ~/postiz and answers at http://localhost:4007.
# It needs about 6 GB of RAM while running and 20 GB of disk.
# ============================================================================
set -uo pipefail

DIR="$HOME/postiz"
URL="http://localhost:4007"
REPO="https://github.com/gitroomhq/postiz-docker-compose.git"
ok()   { printf '  \033[32m✔\033[0m %s\n' "$1"; }
warn() { printf '  \033[33m!\033[0m %s\n' "$1"; }
fail() { printf '  \033[31m✘\033[0m %s\n' "$1"; }

load_brew() {
  local b
  for b in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    [ -x "$b" ] && eval "$("$b" shellenv)" && return 0
  done
  command -v brew >/dev/null 2>&1
}

start_vm() {
  if colima status >/dev/null 2>&1; then ok "Colima pornit"; return 0; fi
  echo "    pornesc Colima (mașina virtuală pentru Docker)..."
  colima start --cpu 4 --memory 6 --disk 40 >/dev/null 2>&1 && ok "Colima pornit" \
    || { fail "Colima nu a pornit. Încearcă: colima start --cpu 2 --memory 4"; exit 1; }
}

wait_up() {
  echo "    aștept să pornească Postiz (prima dată durează câteva minute)..."
  local i=0
  while [ $i -lt 60 ]; do
    if curl -fsS -o /dev/null "$URL"; then ok "Postiz rulează la $URL"; open "$URL" 2>/dev/null; return 0; fi
    sleep 5; i=$((i+1))
  done
  warn "Postiz nu răspunde încă. Verifică peste un minut cu: bash postiz-local.sh status"
}

load_brew || true
cmd="${1:-}"
case "$cmd" in
  install)
    echo "1. Unelte"
    load_brew || { fail "Lipsește Homebrew. Rulează întâi setup-mac.sh din Creator Kit sau instalează-l de pe https://brew.sh."; exit 1; }
    brew install colima docker docker-compose >/dev/null 2>&1 && ok "Colima, Docker, Docker Compose" \
      || { fail "brew install colima docker docker-compose a eșuat"; exit 1; }
    start_vm
    echo "2. Postiz"
    if [ -d "$DIR/.git" ]; then ok "Postiz deja descărcat în $DIR"
    else git clone --quiet "$REPO" "$DIR" && ok "descărcat în $DIR" || { fail "descărcarea a eșuat"; exit 1; }
    fi
    # Each install needs its own secret; replace the placeholder once.
    if grep -q "random string that is unique to every install" "$DIR/docker-compose.yaml"; then
      secret="$(openssl rand -hex 32)"
      sed -i '' "s|random string that is unique to every install - just type random characters here!|$secret|" "$DIR/docker-compose.yaml"
      ok "cheie secretă generată"
    fi
    (cd "$DIR" && docker-compose up -d >/dev/null 2>&1) && ok "containere pornite" \
      || { fail "docker-compose up a eșuat; rulează: cd ~/postiz && docker-compose up"; exit 1; }
    wait_up
    echo
    echo "Primul cont creat în pagină devine administrator."
    ;;
  start)
    start_vm
    (cd "$DIR" && docker-compose up -d >/dev/null 2>&1) && ok "containere pornite" || fail "nu au pornit"
    wait_up
    ;;
  stop)
    (cd "$DIR" && docker-compose down >/dev/null 2>&1) && ok "Postiz oprit"
    colima stop >/dev/null 2>&1 && ok "Colima oprit, memoria e eliberată"
    ;;
  status)
    colima status 2>&1 | head -1
    (cd "$DIR" && docker-compose ps 2>/dev/null)
    curl -fsS -o /dev/null "$URL" && ok "răspunde la $URL" || warn "nu răspunde la $URL"
    ;;
  update)
    start_vm
    (cd "$DIR" && git pull --quiet && docker-compose pull >/dev/null 2>&1 && docker-compose up -d >/dev/null 2>&1) \
      && ok "actualizat" || fail "actualizarea a eșuat"
    wait_up
    ;;
  *)
    echo "Folosire: bash postiz-local.sh install | start | stop | status | update"
    exit 2
    ;;
esac
