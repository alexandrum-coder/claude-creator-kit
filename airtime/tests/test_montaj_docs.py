"""Step "agent and skill" of the montage upgrade (PLAN, Note 2.24, D-72 to D-78).

The agent and the skill are the only way the new keys reach a real run, so the documents are tested like code:
the Python blocks the agent is told to run are executed on fake run folders, the JSON examples go through the
validators in scripts/, and every new key must be named in the section that uses it.
No Remotion, no ffmpeg; never reads the real ~/.airtime (AIRTIME_HOME points at tmp_path).
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
SCRIPTS = PLUGIN / "scripts"
AGENT = PLUGIN / "agents" / "airtime.md"
SKILL = PLUGIN / "skills" / "airtime" / "SKILL.md"
sys.path.insert(0, str(SCRIPTS))

import compose  # noqa: E402
import montaj  # noqa: E402
import reels_fx  # noqa: E402


def section(md: Path, heading: str) -> str:
    """Text of the section that starts at `heading` (a line beginning with #) up to the next heading of the same level."""
    text = md.read_text(encoding="utf-8")
    level = len(heading) - len(heading.lstrip("#"))
    start = text.find("\n" + heading)
    assert start >= 0, "missing section %r in %s" % (heading, md.name)
    rest = text[start + 1:]
    nxt = re.search(r"\n#{1,%d} " % level, rest[len(heading):])
    return rest if nxt is None else rest[:len(heading) + nxt.start()]


def code_block(text: str, lang: str, marker: str) -> str:
    blocks = [b for b in re.findall(r"```%s\n(.*?)```" % lang, text, flags=re.S) if marker in b]
    assert blocks, "no %s block with %r" % (lang, marker)
    return re.sub(r"^ {0,3}", "", blocks[0], flags=re.M)


MONTEAZA = lambda: section(AGENT, "## Comanda `monteaza`")  # noqa: E731
TEXTE = lambda: section(AGENT, "## Comanda `texte`")  # noqa: E731
REELS = lambda: section(AGENT, "## Comanda `reels`")  # noqa: E731


def run_block(code: str, args: list, home: Path) -> str:
    env = dict(os.environ, AIRTIME_HOME=str(home), HOME=str(home))
    r = subprocess.run([sys.executable, "-", *map(str, args)], input=code, text=True, capture_output=True, env=env)
    assert r.returncode == 0, r.stderr
    return r.stdout


def words(*spans):
    return {"segments": [{"start": spans[0][0], "end": spans[-1][1],
                          "words": [{"word": "w%d" % i, "start": a, "end": b} for i, (a, b) in enumerate(spans)]}]}


# pauses: 5.0-7.54 (slot t=5.2, d=1.16), 7.64-9.0 (slot t=7.84, d=0.57, too close to the first one for
# check_transitions: 7.84 - 5.2 = 2.64 < 2.4 * 1.16 + 0.12), 20.0-23.0 (slot t=20.2, d=1.16)
TRANSCRIPT = words((0.0, 5.0), (7.54, 7.64), (9.0, 20.0), (23.0, 40.0))


def fake_run(tmp_path, profile: dict, name="test") -> Path:
    home = tmp_path / "home"
    (home / "profiles").mkdir(parents=True)
    (home / "profiles" / ("%s.json" % name)).write_text(json.dumps(profile), encoding="utf-8")
    run = tmp_path / "run"
    (run / "render").mkdir(parents=True)
    (run / "render" / "render.json").write_text(json.dumps({"intro": "intro.mp4", "overlays": [
        {"file": "chapter_01.mov", "t": 30.0}]}), encoding="utf-8")
    (run / "transcript-curat.json").write_text(json.dumps(TRANSCRIPT), encoding="utf-8")
    return run


def montage_keys(tmp_path, profile: dict, w=1920, h=1080, dur=40.0) -> dict:
    run = fake_run(tmp_path, profile)
    code = code_block(MONTEAZA(), "python", "# montaj 0.2.0: render.json")
    run_block(code, [run, "test", SCRIPTS, w, h, 25, dur], tmp_path / "home")
    return json.loads((run / "render" / "render.json").read_text(encoding="utf-8"))


SRC = {"fps": 25.0, "duration": 40.0, "width": 1920, "height": 1080}


def test_montage_block_writes_the_default_keys(tmp_path):
    r = montage_keys(tmp_path, {"channel": "x"})
    assert r["intro"] == "intro.mp4" and r["overlays"] == [{"file": "chapter_01.mov", "t": 30.0}]
    assert r["loudnorm"] is True and r["sfx"] is True                      # D-18, D-41
    assert r["opening"] == {"fade_in": 0.72, "intro_dissolve": 1.24}      # D-35
    assert montaj.pushin_scale(r["pushin"]) == 1.06
    assert "grade" not in r


def test_montage_block_keeps_only_transitions_that_compose_accepts(tmp_path):
    r = montage_keys(tmp_path, {})
    assert [x["t"] for x in r["transitions"]] == [5.2, 20.2]
    assert all(x["kind"] == "dissolve_accel" for x in r["transitions"])
    checked = compose.check_transitions(r["transitions"], SRC)             # raises when two are too close
    assert len(checked) == 2


def test_montage_block_skips_transitions_on_a_vertical_clip(tmp_path):
    r = montage_keys(tmp_path, {}, w=1080, h=1920)
    assert r["transitions"] == []                                         # D-30: compose would drop them anyway


def test_montage_block_music_null_without_profile_music(tmp_path):
    r = montage_keys(tmp_path, {})
    assert "music" in r and r["music"] is None                            # F9: null, not a missing key


def test_montage_block_copies_profile_music_and_grade(tmp_path):
    r = montage_keys(tmp_path, {"music": {"file": "/m/bed.mp3", "gain_db": -26}, "grade": "cald"})
    assert r["music"] == {"file": "/m/bed.mp3", "gain_db": -26}
    assert r["grade"] in compose.GRADES


def test_montage_block_music_string_becomes_an_absolute_file(tmp_path):
    r = montage_keys(tmp_path, {"music": "~/m/bed.mp3"})                  # R4: compose needs {file}, absolute
    assert r["music"] == {"file": str(tmp_path / "home" / "m" / "bed.mp3")}


def chapters_youtube(tmp_path, chapters: list, final_dur: float) -> list:
    run = tmp_path / "run"
    (run / "render").mkdir(parents=True)
    (run / "render" / "render.json").write_text(json.dumps({
        "intro": "intro.mp4", "overlays": [], "opening": {"fade_in": 0.72, "intro_dissolve": 1.24},
        "transitions": [{"t": 12.4, "d": 1.16, "kind": "dissolve_accel"},
                        {"t": 50.0, "d": 1.0, "kind": "dissolve_accel"}]}), encoding="utf-8")
    (run / "chapters.json").write_text(json.dumps(chapters), encoding="utf-8")
    code = code_block(MONTEAZA(), "python", "# montaj 0.2.0: capitole")
    run_block(code, [run, SCRIPTS, 4.0, final_dur], tmp_path)
    return json.loads((run / "chapters-youtube.json").read_text(encoding="utf-8"))


def test_chapter_block_follows_compose_timeline(tmp_path):
    got = chapters_youtube(tmp_path, [{"t": 0, "title": "A"}, {"t": 30, "title": "B"}, {"t": 90, "title": "C"}], 200)
    # compose.py:141-142: map_time(t) + intro - intro_dissolve -> 30 - 1.16 + 2.76 = 31.6; 90 - 2.16 + 2.76 = 90.6
    assert got == [{"t": 0, "title": "A"}, {"t": 32, "title": "B"}, {"t": 91, "title": "C"}]


def test_chapter_block_keeps_ten_seconds_per_chapter(tmp_path):
    got = chapters_youtube(tmp_path, [{"t": 0, "title": "A"}, {"t": 30, "title": "B"}, {"t": 36, "title": "C"},
                                      {"t": 190, "title": "D"}], 200)
    # C lands at 38 (6 s after B), D at 191 (9 s before the end): YouTube needs 10 s per chapter (R2)
    assert got == [{"t": 0, "title": "A"}, {"t": 32, "title": "B"}]


def test_montage_section_names_every_render_key():
    text = MONTEAZA()
    for key in ("transitions", "opening", "pushin", "audio", "layers", "grade", "sfx", "music", "loudnorm",
                "title_pops", '"music": null', "montaj.py", "map_time"):
        assert key in text, key


def test_candidate_example_passes_the_reels_validators():
    text = TEXTE()
    cand = json.loads(code_block(text, "json", '"result_hook"'))
    fps, dur = 30.0, float(cand["duration"])
    assert reels_fx.check_list(cand["list"])
    assert reels_fx.check_impact(cand["impact"], dur, fps)
    assert reels_fx.check_hook(cand["result_hook"], int(round(dur * fps)), fps) == 45
    assert reels_fx.cta_window(cand["cta"], dur, fps) == pytest.approx(dur - 3)
    assert montaj.pushin_scale(cand["pushin"]) == 1.06
    for key in ("demonstratii", "keywords", "30 de caractere"):
        assert key in text, key


def test_reels_command_passes_the_cta_word():
    text = REELS()
    line = next(ln for ln in text.splitlines() if 'reels.py" build' in ln)
    assert '--cta-word "$CTA_WORD"' in line
    assert "keywords" in text and "#14213d" in text and "#fca311" in text  # D-76: fixed colours


@pytest.mark.parametrize("keywords,word", [(["  pilates  ", "core"], "pilates"), ([], ""), (["x" * 31], "")])
def test_cta_word_block_takes_a_valid_first_keyword(tmp_path, keywords, word):
    home = tmp_path / "home"
    (home / "profiles").mkdir(parents=True)
    (home / "profiles" / "test.json").write_text(json.dumps({"keywords": keywords}), encoding="utf-8")
    code = code_block(AGENT.read_text(encoding="utf-8"), "python", "# cuvantul CTA")
    assert run_block(code, ["test", SCRIPTS], home).strip() == word      # R6: 1-30 characters after strip


def test_skill_tells_the_coach_about_the_effects():
    step3 = section(SKILL, "### 3. Tăieturile și montajul")
    for word in ("muzic", "zoom", "dizolv"):
        assert word in step3.lower(), word
    step5 = section(SKILL, "### 5. Alegerea reels-urilor")
    assert "Efecte" in step5
    for key in ("list", "cta", "impact", "result_hook", "pushin", "neschimbat"):
        assert key in step5, key
    last = step5.strip().split("\n\n")[-1]                                 # R7: the single reel of kind: reel
    for key in ("kind: reel", "pushin", "cta", "result_hook", "demonstratii"):
        assert key in last, key


def test_montage_block_leaves_out_the_effects_the_coach_refused(tmp_path):
    run = fake_run(tmp_path, {"music": {"file": "/m/bed.mp3"}, "grade": "cald"})
    code = code_block(MONTEAZA(), "python", "# montaj 0.2.0: render.json")
    out = run_block(code, [run, "test", SCRIPTS, 1920, 1080, 25, 40.0, "music, sfx,transitions,grade"],
                    tmp_path / "home")
    r = json.loads((run / "render" / "render.json").read_text(encoding="utf-8"))
    assert r["music"] is None and r["transitions"] == []                  # F9: null and [], not missing keys
    assert "sfx" not in r and "grade" not in r
    assert r["loudnorm"] is True and montaj.pushin_scale(r["pushin"]) == 1.06
    assert json.loads(out) == {"tranzitii": 0, "muzica": False}


def test_refusing_an_effect_goes_through_monteaza_not_a_hand_edit():
    text = MONTEAZA()
    assert "FARA_EFECTE" in text
    line = next(ln for ln in text.splitlines() if "montaj 0.2.0: render.json" not in ln and '"$RUN_DIR" "$PROFIL"' in ln)
    assert '"<FARA_EFECTE>"' in line
    step3 = section(SKILL, "### 3. Tăieturile și montajul")
    assert "FARA_EFECTE" in step3 and "scoți din `render/render.json`" not in step3


def test_result_hook_takes_the_clip_type_from_the_prompt_first():
    line = next(ln for ln in TEXTE().splitlines() if ln.startswith("- `result_hook:"))
    assert line.index("TIP_CLIP") < line.index("run.json") < line.index("profil")
    texte = section(SKILL, "### 4. Texte YouTube")
    assert "TIP_CLIP" in texte


def test_reel_times_sentence_names_only_timed_keys():
    line = next(ln for ln in TEXTE().splitlines() if "Timpii din" in ln)
    assert "`list`" not in line and "`impact`" in line and "snap" in line


def test_cta_rule_places_the_word_where_ctakeyword_draws_it():
    line = next(ln for ln in TEXTE().splitlines() if ln.startswith("- `cta: {}`"))
    assert "jos" not in line.split("CTA_WORD` se calculează")[0]           # D-53: centred at 48 % of the height
    assert "mijlocul" in line
    assert "CTA_CENTER = 0.48" in (PLUGIN / "remotion" / "src" / "CtaKeyword.tsx").read_text(encoding="utf-8")


def test_agent_keeps_intermediate_outputs_in_logs():
    rules = section(AGENT, "## Reguli care nu se negociază")
    assert "$RUN_DIR/logs/" in rules and "punct" in rules


PROPUNE = lambda: section(AGENT, "## Comanda `propune`")  # noqa: E731


def _run_json_block(tmp_path, args, profile=None, existing=None):
    """F-2 (D-95): run the `propune` block that writes run.json on a fake run folder."""
    home = tmp_path / "home"
    (home / "profiles").mkdir(parents=True)
    (home / "profiles" / "test.json").write_text(json.dumps(profile or {}), encoding="utf-8")
    run = tmp_path / "run"
    run.mkdir()
    if existing is not None:
        raw = existing if isinstance(existing, str) else json.dumps(existing)
        (run / "run.json").write_text(raw, encoding="utf-8")
        os.utime(run / "run.json", (1_000_000_000, 1_000_000_000))
    code = code_block(PROPUNE(), "python", "# propune: run.json")
    run_block(code, [run, "test", *args, SCRIPTS], home)
    return (run / "run.json").read_text(encoding="utf-8"), (run / "run.json").stat().st_mtime


def _block(tmp_path, args, **kw):
    raw, _ = _run_json_block(tmp_path, args, **kw)
    return json.loads(raw)


def test_propune_writes_run_json_when_the_skill_did_not(tmp_path):
    video = tmp_path / "x" / ".." / "clip mic.mp4"                       # stored as an absolute, normalised path
    d = _block(tmp_path, [video, "demonstratii", "true"])
    assert d == {"video": str((tmp_path / "clip mic.mp4").resolve()), "profile": "test", "clip_type": "demonstratii",
                 "voiceover": True}


def test_propune_only_fills_the_keys_the_skill_left_out(tmp_path):
    existing = {"video": "/clipuri/a.mp4", "clip_type": "vorbit", "facebook": True, "kind": "lung"}
    d = _block(tmp_path, [tmp_path / "b.mp4", "demonstratii", "false"], existing=existing)
    assert d == dict(existing, profile="test", voiceover=False)


def test_propune_leaves_a_complete_run_json_byte_for_byte(tmp_path):
    # D-96: the skill's run.json (its own formatting and key order) is not rewritten when nothing is missing
    skill = '{"video":"/clipuri/a.mp4","voiceover":false,"profile":"test","clip_type":"vorbit","kind":"lung"}'
    raw, mtime = _run_json_block(tmp_path, [tmp_path / "b.mp4", "demonstratii", "true"], existing=skill)
    assert raw == skill and mtime == 1_000_000_000


def test_propune_takes_the_clip_type_from_the_profile_when_the_prompt_has_none(tmp_path):
    d = _block(tmp_path, [tmp_path / "c.mp4", "", "false"], profile={"clip_type": "culise"})
    assert d["clip_type"] == "culise" and d["voiceover"] is False


def test_propune_writes_run_json_before_transcribing():
    text = PROPUNE()
    assert "run.json" in next(ln for ln in text.splitlines() if ln.startswith("Intrare:"))
    assert text.index("# propune: run.json") < text.index('reels.py" transcribe')


def test_plugin_version_is_0_2_0():
    data = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert data["version"] == "0.2.0"
