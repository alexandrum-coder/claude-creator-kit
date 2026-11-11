#!/usr/bin/env bash
# Builds SHORTS_ROOT for the end-to-end test: a copy of claude-shorts where compute_reframe.py survives
# a mediapipe without the legacy `solutions` API (mediapipe 1.x, which is what a fresh setup.sh installs).
#   make_shorts_copy.sh SHORTS_SRC DEST
# Only scripts/ is copied (and patched); every other entry is a symlink to the original.
# Three patches in the copy: (1) mediapipe without `solutions`, (2) node_modules for remotion, (3) BSD paste in export.sh.
# Effect of (1): face tracking returns no positions (the test clip has no face anyway), so the reframe falls back to its
# default crop. A real fix belongs in the plugin or in the pinned mediapipe version; see e2e.md.
set -eu
SRC="${1:?SHORTS_SRC}"; DEST="${2:?DEST}"
rm -rf "$DEST"   # rebuilt from scratch on every call (DEST is a scratch folder)
mkdir -p "$DEST"
for e in "$SRC"/* "$SRC"/.[!.]*; do
  [ -e "$e" ] || continue
  n="$(basename "$e")"
  [ "$n" = scripts ] && continue
  ln -sfn "$e" "$DEST/$n"
done
mkdir -p "$DEST/scripts"
cp -R "$SRC/scripts/." "$DEST/scripts/"
python3 - "$DEST/scripts/compute_reframe.py" <<'PYEOF'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
old = "    mp_face = mp.solutions.face_detection\n"
new = "    if not hasattr(mp, 'solutions'):  # e2e patch: mediapipe 1.x has no legacy solutions API\n        return []\n    mp_face = mp.solutions.face_detection\n"
if old not in s:
    sys.exit("pattern not found")
open(p, "w", encoding="utf-8").write(s.replace(old, new, 1))
PYEOF
# remotion/: real folder (copy) plus node_modules from the AirTime remotion install ($REMOTION_MODULES), because the
# scratch claude-shorts clone never had `npm install` run (setup.sh would do it); no new install in the test.
if [ -n "${REMOTION_MODULES:-}" ]; then
  rm -f "$DEST/remotion"   # was a symlink above
  mkdir -p "$DEST/remotion"
  cp -R "$SRC/remotion/." "$DEST/remotion/"   # copies, not symlinks: node resolves modules from the real path
  ln -sfn "$REMOTION_MODULES" "$DEST/remotion/node_modules"
fi
# export.sh ends with `paste -sd ','` (GNU form); BSD paste on macOS needs the `-` for stdin, so export.sh exits 1
# after writing the files. Patched in the copy only.
sed -i.bak "s/paste -sd ','/paste -sd ',' -/" "$DEST/scripts/export.sh"
grep -q "paste -sd ',' -" "$DEST/scripts/export.sh" || { echo "export.sh patch failed" >&2; exit 1; }
echo "shorts copy: $DEST"
