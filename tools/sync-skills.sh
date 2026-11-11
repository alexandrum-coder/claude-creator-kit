#!/bin/bash
# sync-skills.sh — copy the skills listed in skills.txt from Doru's personal
# repo into creator-skills/<name>/ (one plugin per skill), then bump the
# marketplace version. Only the listed folders are replaced; the kit's own
# skills (social-seo, podcast-insights) are left alone.
# Read-only on the source repo. Usage: bash tools/sync-skills.sh [source-dir]
set -euo pipefail
KIT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SRC="${1:-$HOME/claude-code-sync/obsydia-skills/skills}"
DEST="$KIT/creator-skills"
[ -d "$SRC" ] || { echo "Nu găsesc sursa: $SRC"; exit 1; }
missing=0
while read -r name; do
  [ -z "$name" ] && continue
  [ -f "$SRC/$name/SKILL.md" ] || { echo "✘ $name lipsește din $SRC"; missing=1; }
done < "$KIT/skills.txt"
[ "$missing" -eq 0 ] || exit 1
while read -r name; do
  [ -z "$name" ] && continue
  rm -rf "$DEST/$name.new"
  cp -R "$SRC/$name" "$DEST/$name.new"
  rm -rf "$DEST/$name"
  mv "$DEST/$name.new" "$DEST/$name"
done < "$KIT/skills.txt"
python3 - "$KIT/.claude-plugin/marketplace.json" "$KIT/skills.txt" <<'PY'
import json, sys
p, listed = sys.argv[1], [l.strip() for l in open(sys.argv[2]) if l.strip()]
d = json.load(open(p))
have = {e["name"] for e in d["plugins"]}
for name in listed:
    if name not in have:
        print(f"! {name} nu are intrare în marketplace.json: adaug-o (source ./creator-skills/{name}, strict false, skills [\"./\"])")
major, minor, patch = (int(x) for x in d["metadata"]["version"].split("."))
d["metadata"]["version"] = f"{major}.{minor}.{patch + 1}"
with open(p, "w") as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write("\n")
print("versiune:", d["metadata"]["version"])
PY
git -C "$KIT" status --short creator-skills | head -20
