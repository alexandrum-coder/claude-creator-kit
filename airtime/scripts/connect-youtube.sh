#!/usr/bin/env bash
# Conectează AirTime la canalul YouTube: ghid pas cu pas prin Google Cloud, apoi autorizare.
set -u

PROFILE_ARGS=()
if [ "${1:-}" = "--profile" ] && [ -n "${2:-}" ]; then
  PROFILE_ARGS=(--profile "$2")
fi

DIR="$(cd "$(dirname "$0")" && pwd)"
PY="${AIRTIME_HOME:-$HOME/.airtime}/venv/bin/python"
[ -x "$PY" ] || PY="python3"

pas() {
  # $1 = adresa paginii, $2 = ce are de făcut utilizatorul
  open "$1"
  echo
  echo "$2"
  printf "Apasă Enter când ai terminat... "
  read -r _
}

echo "Conectăm AirTime la canalul tău YouTube. Sunt patru pași în browser."

pas "https://console.cloud.google.com/projectcreate" \
"Pasul 1: creează un proiect nou (de exemplu „AirTime”) și apasă Create."

pas "https://console.cloud.google.com/apis/library/youtube.googleapis.com" \
"Pasul 2: apasă Enable la „YouTube Data API v3”."

pas "https://console.cloud.google.com/apis/credentials/consent" \
"Pasul 3: la ecranul de consimțământ alege External, completează numele aplicației și e-mailul tău, apoi adaugă-te ca Test user."

open "https://console.cloud.google.com/apis/credentials"
echo
echo "Pasul 4: apasă Create credentials, apoi OAuth client ID, tip Desktop app, apoi Download JSON."
echo "Fișierul se salvează în Descărcări. Îl caut singur, așteaptă."

END=$(( $(date +%s) + 600 ))
CLIENT=""
while [ "$(date +%s)" -lt "$END" ]; do
  OUT="$("$PY" "$DIR/youtube.py" ${PROFILE_ARGS[@]+"${PROFILE_ARGS[@]}"} find-client 2>/dev/null)"
  if [ $? -eq 0 ]; then
    CLIENT="$(printf '%s' "$OUT" | "$PY" -c 'import json,sys; print(json.load(sys.stdin)["path"])')"
    break
  fi
  sleep 3
done

if [ -z "$CLIENT" ]; then
  echo "Nu am găsit fișierul în 10 minute. Rulează din nou scriptul după ce îl descarci."
  exit 4
fi

echo "Am găsit fișierul. Se deschide pagina Google pentru autorizare."
"$PY" "$DIR/youtube.py" ${PROFILE_ARGS[@]+"${PROFILE_ARGS[@]}"} auth --client "$CLIENT"
