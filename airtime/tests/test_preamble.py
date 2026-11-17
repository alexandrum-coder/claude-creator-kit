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


# --- function 5, after the feace2e checkpoint (D-12 (8), (9))

def test_skill_past_date_only_for_stopped_runs():
    step1 = _step1()
    assert "La o rulare cu `oprit_la`, dacă data aleasă pentru YouTube a trecut" in step1
    assert "scrii data nouă în `data_youtube` din `run.json`" in step1


def test_skill_run_json_keeps_step_by_step_on_resume():
    step1 = _step1()
    assert "`pas_cu_pas` (`true` doar la „pas cu pas”), care la reluare rămâne valoarea din `run.json`" in step1


# --- function 6: "AirTime doar reels", the short route (D-13)

CALENDAR = PLUGIN / "skills" / "airtime" / "references" / "calendar.md"


def _agent_section(heading: str) -> str:
    text = AGENT.read_text(encoding="utf-8")
    m = re.search(r"^## %s\n(.*?)(?=^## |\Z)" % re.escape(heading), text, flags=re.S | re.M)
    assert m, "no section %r in airtime.md" % heading
    return m.group(1)


def test_skill_description_triggers_only_reels():
    front = SKILL.read_text(encoding="utf-8").split("---")[1]
    assert "AirTime doar reels" in front


def test_skill_only_reels_start():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Doar reels")
    for phrase in ("„doar reels”", "„Vrei și videoclip YouTube sau doar reels?”", "`kind: lung`",
                   "Nu o pui la „Doar montaj”", "nici la reluare"):
        assert phrase in sec, phrase


def test_skill_only_reels_conflicts_and_short_vertical():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Doar reels")
    assert "„doar reels” și „doar montaj” se contrazic" in sec
    assert "întrebi care dintre ele" in sec
    assert "clip vertical de cel mult 180 de secunde, „doar reels” nu schimbă nimic" in sec


def test_skill_only_reels_route():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Doar reels")
    for phrase in ("tăieturile rămân ca la pasul 3", "`DOAR_REELS: true`", "doar `curat.mp4`",
                   "fără intro, fără capitole, fără `youtube.mp4`", "fără `youtube-meta.json`",
                   "`COMANDA: candidati`"):
        assert phrase in sec, phrase


def test_skill_only_reels_publishing_and_combinations():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Doar reels")
    for phrase in ("prima zi liberă (nu mai devreme de poimâine) pentru reel-ul 1",
                   "câte un reel pe zi, la `reels_time`", "Shorts",
                   "„fără publicare”", "„pas cu pas”", "„în <dosar>”", "„cu sunet separat”",
                   "după `curat.mp4` și după reels, fără oprirea de la texte",
                   "`doar_reels`", "nu face videoclipul YouTube"):
        assert phrase in sec, phrase


def test_skill_step0_youtube_only_needed_with_shorts():
    step0 = _section(SKILL.read_text(encoding="utf-8"), "Fluxul unei rulări (pașii 0-9)").split("### 1.")[0]
    assert "Pe ruta scurtă („Doar reels”), YouTube neconectat oprește lucrul numai dacă `shorts` e pornit în profil." in step0


def test_skill_step1_asks_and_records_only_reels():
    step1 = _step1()
    assert "„Vrei și videoclip YouTube sau doar reels?”" in step1
    assert "`doar_reels` (`true` doar pe ruta scurtă), care la reluare rămâne valoarea din `run.json`" in step1
    assert "La o rulare cu `doar_reels`, lipsa `youtube.mp4` și a `youtube-meta.json` nu e un pas lipsă" in step1


def test_skill_step3_only_reels_montaj():
    assert "Pe ruta scurtă dai agentului și `DOAR_REELS: true`" in _step(3)


def test_skill_step4_only_reels_uses_candidati():
    step4 = _step(4)
    assert "Pe ruta scurtă (`doar_reels`) nu chemi `texte`" in step4
    assert "`COMANDA: candidati`" in step4


def test_calendar_only_reels_dates():
    cal = CALENDAR.read_text(encoding="utf-8")
    assert "Pe ruta scurtă („Doar reels”), fără videoclip YouTube: reel-ul 1 în ziua aleasă, apoi câte unul pe zi, la `reels_time`." in cal


def test_agent_lists_candidati_command():
    text = AGENT.read_text(encoding="utf-8")
    front = text.split("---")[1]
    assert "candidati" in front
    assert "- `COMANDA`: `propune`, `monteaza`, `texte`, `candidati` sau `reels`." in text
    assert "- Pentru `monteaza`: `TITLU` (opțional, pentru intro) și `DOAR_REELS`" in text


def test_agent_monteaza_only_reels_stops_after_curat():
    sec = _agent_section("Comanda `monteaza`")
    assert "Cu `DOAR_REELS: true` te oprești după pasul 3" in sec
    assert "MONTEAZA gata (doar reels)" in sec


def test_agent_candidati_command():
    sec = _agent_section("Comanda `candidati`")
    for phrase in ("`curat.mp4`", "`transcript-curat.json`", "`candidati.json`",
                   "fără `youtube.mp4` și fără capitole", "aceleași reguli ca la pasul 4 din `texte`",
                   "CANDIDATI gata"):
        assert phrase in sec, phrase


def test_agent_error_rule_unchanged():
    # D-13 (d): regression guard, the old rule already covers the new command
    text = AGENT.read_text(encoding="utf-8")
    assert ("- Dacă un script iese cu cod diferit de 0, oprești, nu improvizezi alt drum. Întorci `EROARE: <pas> - "
            "<mesajul scriptului, scurt>`. Excepție: exporturile de la sfârșitul lui `monteaza` și `reels` "
            "(`exports.py`); acolo montajul și reels-urile rămân, iar problema merge pe rândul `Avertismente:`.") in text


# --- function 6, after the 0e20c45 checkpoint (D-13 (j), (k))

def test_skill_step7_only_reels_first_reel_on_chosen_day():
    assert ("pe ruta scurtă („Doar reels”), reel-ul 1 e chiar în ziua aleasă "
            "(vezi „Doar reels” și `references/calendar.md`)") in _step(7)


def test_skill_only_reels_no_day_question_without_publishing():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Doar reels")
    assert "Nu o întrebi în modurile fără publicare." in sec


def test_skill_step1_first_reel_day_replaces_question_4():
    assert "Pe ruta scurtă, în locul întrebării 4, propui ziua primului reel." in _step1()


def test_skill_only_reels_also_shorts():
    sec = _section(SKILL.read_text(encoding="utf-8"), "Doar reels")
    assert "și ca Shorts dacă `shorts` e pornit în profil" in sec


def test_agent_monteaza_only_reels_skips_youtube_outputs():
    sec = _agent_section("Comanda `monteaza`")
    assert "fără `chapters-youtube.json` și fără exporturile de la pasul 9" in sec
