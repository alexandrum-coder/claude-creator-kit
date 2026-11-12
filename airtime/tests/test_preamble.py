"""Runs the bash blocks the agent and the skill tell the model to run, in a fake install.

Never reads the real ~/.claude or ~/.airtime: HOME, CLAUDE_CONFIG_DIR and AIRTIME_HOME point at tmp_path.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
AGENT = PLUGIN / "agents" / "airtime.md"
SKILL = PLUGIN / "skills" / "airtime" / "SKILL.md"


# what the agent's environment preamble sets before every other block
AGENT_PY = 'PY="$AIRTIME_HOME/venv/bin/python"\n'


def bash_block(md: Path, marker: str) -> str:
    blocks = re.findall(r"```bash\n(.*?)```", md.read_text(encoding="utf-8"), flags=re.S)
    found = [b for b in blocks if marker in b]
    assert found, "no bash block with %r in %s" % (marker, md.name)
    return re.sub(r"^ {0,3}", "", found[0], flags=re.M)


def fake_install(tmp_path: Path, plugins: dict) -> dict:
    cfg = tmp_path / "cfg"
    (cfg / "plugins").mkdir(parents=True)
    (cfg / "plugins" / "installed_plugins.json").write_text(json.dumps({"version": 2, "plugins": plugins}))
    ah = tmp_path / "ahome"
    (ah / "venv" / "bin").mkdir(parents=True)
    os.symlink(sys.executable, ah / "venv" / "bin" / "python")
    bindir = tmp_path / "bin"
    bindir.mkdir()
    os.symlink(sys.executable, bindir / "python3")
    path = "%s:/usr/bin:/bin" % bindir
    return {"PATH": path, "HOME": str(tmp_path / "home"), "CLAUDE_CONFIG_DIR": str(cfg),
            "AIRTIME_HOME": str(ah)}


def run_block(block: str, env: dict, echo: str) -> str:
    r = subprocess.run(["/bin/bash", "-c", block + "\n" + echo], env=env, capture_output=True, text=True)
    return r.stdout.strip()


def test_skill_preamble_finds_plugin_root_without_env(tmp_path):
    inst = tmp_path / "cache" / "creator-kit" / "airtime" / "0.1.1"
    (inst / "scripts").mkdir(parents=True)
    env = fake_install(tmp_path, {"airtime@creator-kit": [{"installPath": str(inst)}]})
    block = bash_block(SKILL, 'SCRIPTS="$ROOT/scripts"')
    assert run_block(block, env, 'echo "$SCRIPTS"') == str(inst / "scripts")


def test_skill_preamble_prefers_claude_plugin_root(tmp_path):
    env = fake_install(tmp_path, {})
    env["CLAUDE_PLUGIN_ROOT"] = str(tmp_path / "pr")
    block = bash_block(SKILL, 'SCRIPTS="$ROOT/scripts"')
    assert run_block(block, env, 'echo "$SCRIPTS"') == str(tmp_path / "pr" / "scripts")


def test_skill_preamble_empty_root_when_not_installed(tmp_path):
    env = fake_install(tmp_path, {})
    (tmp_path / "cfg" / "plugins" / "installed_plugins.json").unlink()
    block = bash_block(SKILL, 'SCRIPTS="$ROOT/scripts"')
    assert run_block(block, env, 'echo "[$ROOT]"') == "[]"


def test_skill_uses_airtime_home_for_profiles():
    text = SKILL.read_text(encoding="utf-8")
    assert "~/.airtime/profiles" not in text
    assert "$AIRTIME_HOME/profiles" in text
    assert "${CLAUDE_PLUGIN_ROOT}/scripts" not in text
    assert "find /" not in text


@pytest.mark.parametrize("layout", ["root", "skills"])
def test_agent_finds_social_seo(tmp_path, layout):
    seo = tmp_path / "cache" / "creator-kit" / "social-seo" / "1.0.0"
    other = tmp_path / "cache" / "creator-kit" / "brandkit" / "1.0.0"
    target = seo / "SKILL.md" if layout == "root" else seo / "skills" / "social-seo" / "SKILL.md"
    target.parent.mkdir(parents=True)
    target.write_text("x")
    other.mkdir(parents=True)
    (other / "SKILL.md").write_text("brandkit")
    env = fake_install(tmp_path, {"brandkit@creator-kit": [{"installPath": str(other)}],
                                  "social-seo@creator-kit": [{"installPath": str(seo)}]})
    block = AGENT_PY + bash_block(AGENT, "SEO=$(")
    assert run_block(block, env, 'echo "$SEO"') == str(target)


def test_agent_social_seo_missing_is_empty(tmp_path):
    other = tmp_path / "brandkit"
    other.mkdir()
    (other / "SKILL.md").write_text("brandkit")
    env = fake_install(tmp_path, {"brandkit@creator-kit": [{"installPath": str(other)}]})
    block = AGENT_PY + bash_block(AGENT, "SEO=$(")
    assert run_block(block, env, 'echo "[$SEO]"') == "[]"
