#!/usr/bin/env bash
# Test double for scripts/check.sh, used only by the AirTime end-to-end test (run C).
# Runs the real check (kept beside this file as check_real.sh) with CLAUDE_CONFIG_DIR pointed at a
# fake config dir whose plugins/installed_plugins.json lists social-seo, brand-voice, marketing and
# ecc, so the plugin check passes without installing anything. Claude's own config is not touched.
# The fake dir comes from $AIRTIME_E2E_FAKE_CFG (built by make_e2e_copy.sh).
set -u
DIR="$(cd "$(dirname "$0")" && pwd)"
: "${AIRTIME_E2E_FAKE_CFG:?AIRTIME_E2E_FAKE_CFG lipsește}"
CLAUDE_CONFIG_DIR="$AIRTIME_E2E_FAKE_CFG" exec "$DIR/check_real.sh" "$@"
