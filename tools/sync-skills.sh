#!/bin/bash
# sync-skills.sh — copy the skills listed in skills.txt from Doru's personal
# repo into creator-skills/skills/, then bump the plugin's patch version.
# Read-only on the source repo. Usage: bash tools/sync-skills.sh [source-dir]
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-$HOME/claude-code-sync/obsydia-skills/skills}"
DEST="$KIT/creator-skills/skills"
[ -d "$SRC" ] || { echo "Nu găsesc sursa: $SRC"; exit 1; }
missing=0
while read -r name; do
  [ -z "$name" ] && continue
  [ -f "$SRC/$name/SKILL.md" ] || { echo "✘ $name lipsește din $SRC"; missing=1; }
done < "$KIT/skills.txt"
[ "$missing" -eq 0 ] || exit 1
rm -rf "$DEST.new"; mkdir -p "$DEST.new"
while read -r name; do
  [ -z "$name" ] && continue
  cp -R "$SRC/$name" "$DEST.new/$name"
done < "$KIT/skills.txt"
rm -rf "$DEST"; mv "$DEST.new" "$DEST"
python3 - "$KIT/creator-skills/.claude-plugin/plugin.json" <<'PY'
import json, sys
p = sys.argv[1]
d = json.load(open(p))
major, minor, patch = (int(x) for x in d["version"].split("."))
d["version"] = f"{major}.{minor}.{patch + 1}"
with open(p, "w") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("versiune:", d["version"])
PY
git -C "$KIT" status --short creator-skills | head -20
