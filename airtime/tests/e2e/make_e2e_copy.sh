#!/usr/bin/env bash
# Builds the plugin copy used by run C of the end-to-end test.
#   make_e2e_copy.sh SRC_PLUGIN_DIR DEST_DIR FAKE_CFG_DIR
# 1. rsync of the plugin (without tests/) into DEST_DIR;
# 2. scripts/youtube.py and scripts/check.sh become the test doubles from this folder; the real ones
#    stay beside them as youtube_real.py and check_real.sh (the doubles delegate to them);
# 3. FAKE_CFG_DIR/plugins/installed_plugins.json lists social-seo, brand-voice, marketing and ecc,
#    each with an installPath that holds a stub skills/<name>/SKILL.md.
set -eu
SRC="${1:?SRC_PLUGIN_DIR}"; DEST="${2:?DEST_DIR}"; FAKE="${3:?FAKE_CFG_DIR}"
HERE="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$DEST" "$FAKE/plugins"
rsync -a --delete --exclude tests/ --exclude __pycache__/ "$SRC"/ "$DEST"/
mv "$DEST/scripts/youtube.py" "$DEST/scripts/youtube_real.py"
mv "$DEST/scripts/check.sh" "$DEST/scripts/check_real.sh"
cp "$HERE/youtube.py" "$DEST/scripts/youtube.py"
cp "$HERE/check.sh" "$DEST/scripts/check.sh"
chmod +x "$DEST/scripts/youtube.py" "$DEST/scripts/check.sh" "$DEST/scripts/check_real.sh" "$DEST/scripts/youtube_real.py"

python3 - "$FAKE" <<'PYEOF'
import json, sys
from pathlib import Path
fake = Path(sys.argv[1])
plugins = {}
for name in ("social-seo", "brand-voice", "marketing", "ecc"):
    root = fake / "stub-plugins" / name
    (root / "skills" / name).mkdir(parents=True, exist_ok=True)
    (root / "skills" / name / "SKILL.md").write_text(f"---\nname: {name}\ndescription: stub for the e2e test\n---\n", encoding="utf-8")
    plugins[f"{name}@e2e-stub"] = [{"scope": "user", "installPath": str(root), "version": "0.0.0"}]
(fake / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": plugins}, indent=2), encoding="utf-8")
PYEOF
echo "copy: $DEST (doubles: scripts/youtube.py, scripts/check.sh; fake config: $FAKE)"
