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


def _model_env(tmp_path: Path) -> dict:
    env = fake_install(tmp_path, {})
    env["SCRIPTS"] = str(PLUGIN / "scripts")
    env["PROFIL"] = "principal"
    return env


def test_agent_model_medium_for_ro_without_speed_json(tmp_path):
    env = _model_env(tmp_path)
    block = AGENT_PY + bash_block(AGENT, "MODEL=$(")
    assert run_block(block, env, 'echo "$MODEL"') == "medium"


def test_agent_model_from_speed_json(tmp_path):
    env = _model_env(tmp_path)
    Path(env["AIRTIME_HOME"], "speed.json").write_text(json.dumps({"model": "small"}))
    block = AGENT_PY + bash_block(AGENT, "MODEL=$(")
    assert run_block(block, env, 'echo "$MODEL"') == "small"


def test_agent_model_small_for_other_language(tmp_path):
    env = _model_env(tmp_path)
    prof = Path(env["AIRTIME_HOME"], "profiles")
    prof.mkdir()
    (prof / "principal.json").write_text(json.dumps({"language": "en"}))
    block = AGENT_PY + bash_block(AGENT, "MODEL=$(")
    assert run_block(block, env, 'echo "$MODEL"') == "small"


def test_agent_model_small_when_python_fails(tmp_path):
    env = _model_env(tmp_path)
    os.unlink(Path(env["AIRTIME_HOME"], "venv", "bin", "python"))
    block = AGENT_PY + bash_block(AGENT, "MODEL=$(")
    assert run_block(block, env, 'echo "$MODEL"') == "small"


def _section(text: str, heading: str) -> str:
    m = re.search(r"^## %s\n(.*?)(?=^## |\Z)" % re.escape(heading), text, flags=re.S | re.M)
    assert m, "no section %r in SKILL.md" % heading
    return m.group(1)


NO_PUBLISH = ["fără publicare", "no publish", "AirTime local", "clip local"]
ONLY_EDIT = ["doar clip", "doar montaj", "Final Edit"]


def test_skill_description_triggers_no_publish_modes():
    front = SKILL.read_text(encoding="utf-8").split("---")[1]
    assert "fără publicare" in front
    assert "doar montaj" in front
    assert "în <dosar>" in front


def test_skill_section_lists_both_modes_and_phrases():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Moduri fără publicare")
    for phrase in NO_PUBLISH + ONLY_EDIT:
        assert "„%s”" % phrase in sec, phrase
    assert "**Tot gata**" in sec and "**Doar montaj**" in sec
    assert "raport.md" in sec
    assert "root=" in sec


def test_skill_steps_0_and_1_follow_the_mode():
    flow = _section(SKILL.read_text(encoding="utf-8"), "Fluxul unei rulări (pașii 0-9)")
    step0 = flow.split("### 1.")[0]
    step1 = flow.split("### 1.")[1].split("### 2.")[0]
    assert "Moduri fără publicare" in step0
    assert "`mod`" in step1
    assert "fără `calendar.json`" in step1
    assert "new_run_dir(Path(clip), date.today(), root=" in step1


def _step1() -> str:
    flow = _section(SKILL.read_text(encoding="utf-8"), "Fluxul unei rulări (pașii 0-9)")
    return flow.split("### 1.")[1].split("### 2.")[0]


def test_skill_resume_for_publishing_revalidates_with_chosen_date():
    step1 = _step1()
    assert "validezi din nou `youtube-meta.json` cu data aleasă" in step1
    assert "--dry-run" in step1


def test_skill_resume_without_publishing_stops_again():
    step1 = _step1()
    assert 'La "da" pentru o rulare cu `calendar.json`' in step1
    assert "te oprești din nou fără urcare" in step1


def test_skill_no_publish_details_approved_after_checkpoint():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Moduri fără publicare")
    assert "data propusă implicit" in sec
    assert "publicarea, mai târziu, va cere conectarea" in sec
    assert "„Nimic nu a fost urcat sau programat.”" in sec


# --- function 5: "AirTime pas cu pas" (D-12)

def _step(n: int) -> str:
    flow = _section(SKILL.read_text(encoding="utf-8"), "Fluxul unei rulări (pașii 0-9)")
    return flow.split("### %d." % n)[1].split("### %d." % (n + 1))[0]


def test_skill_description_triggers_step_by_step():
    front = SKILL.read_text(encoding="utf-8").split("---")[1]
    assert "AirTime pas cu pas" in front


def test_skill_step_by_step_stops():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Pas cu pas")
    for phrase in ("**după montaj**", "**după textele YouTube**", "**după reels randate**",
                   "un Short n-are oprirea de la reels", "un reel direct n-are oprirea de la texte",
                   "„Doar montaj” se termină oricum după montaj", "„Tot gata” are aceleași opriri"):
        assert phrase in sec, phrase


def test_skill_step_by_step_answers():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Pas cu pas")
    for phrase in ("orice „da” limpede", "„Da” sau „confirm” exact rămân cerute doar la tabelul de la pasul 7",
                   "apoi te oprești din nou", "tabelul cu tăieturi de la pasul 3",
                   "`youtube-meta.json`", "`--dry-run`", "alegerea reels-urilor de la pasul 5",
                   "nu urci nimic", "`oprit_la` (`montaj`, `texte` sau `reels`)"):
        assert phrase in sec, phrase


def test_skill_step_by_step_resume():
    step1 = _step1()
    for phrase in ("`oprit_la`", "pornești de la pasul de după oprire", "ștergi `oprit_la`",
                   "`pas_cu_pas` din `run.json`", "`pas_cu_pas` (`true` doar la „pas cu pas”)"):
        assert phrase in step1, phrase


def test_skill_steps_3_4_6_stop_in_step_by_step():
    for n in (3, 4, 6):
        assert "În modul pas cu pas, te oprești aici (vezi „Pas cu pas”)." in _step(n), n


# --- function 5, correction after the b184b80 checkpoint (D-12, addition 13:5x)

def test_skill_step_by_step_short_and_reel_show_curat():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Pas cu pas")
    assert "la un Short sau la un reel direct, calea `curat.mp4` și durata, fără capitole" in sec


def test_skill_step_by_step_kept_on_resume():
    step1 = _step1()
    for phrase in ("nu se rescrie cu `false`",
                   "„Doar montaj” pas cu pas, reluată pentru texte și reels, rămâne pas cu pas",
                   "faci întâi pașii lipsă de după oprire, cu opriri"):
        assert phrase in step1, phrase


def test_skill_step_by_step_finer_changes():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Pas cu pas")
    assert "capitolele din descriere" in sec
    assert "doar în `instagram.json`, fără să randezi din nou" in sec


def test_skill_step_by_step_resume_with_past_date():
    step1 = _step1()
    assert "data aleasă pentru YouTube a trecut" in step1
    assert "propui o dată nouă" in step1


def test_skill_step_by_step_resume_needs_no_phrase():
    text = SKILL.read_text(encoding="utf-8")
    assert "fără ca coachul să mai spună fraza" in _step1()
    assert "tot pas cu pas" in _section(text, "Pas cu pas")
    assert "aceeași frază de pornire" not in text
