"""Exports after editing (D-11): .srt subtitles, voice-only .wav, picture-only .mp4."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

import exports

PLUGIN = Path(__file__).resolve().parent.parent
AGENT = PLUGIN / "agents" / "airtime.md"
SKILL = PLUGIN / "skills" / "airtime" / "SKILL.md"

STAMP = re.compile(r"^(\d\d):(\d\d):(\d\d),(\d\d\d) --> (\d\d):(\d\d):(\d\d),(\d\d\d)$")


def _transcript(text: str, start: float = 0.0, step: float = 0.4) -> dict:
    words, t = [], start
    for w in text.split():
        words.append({"word": w, "start": round(t, 3), "end": round(t + step - 0.05, 3)})
        t += step
    return {"segments": [{"start": words[0]["start"], "end": words[-1]["end"], "text": text, "words": words}]}


def _cues(srt: str) -> list[dict]:
    out = []
    for block in srt.strip().split("\n\n"):
        lines = block.split("\n")
        m = STAMP.match(lines[1])
        assert m, lines[1]
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        out.append({"n": int(lines[0]), "start": start, "end": end, "lines": lines[2:]})
    return out


def _texts(srt: str) -> list[str]:
    return [" ".join(c["lines"]) for c in _cues(srt)]


def _seconds(srt: str) -> list[tuple[float, float]]:
    return [(c["start"], c["end"]) for c in _cues(srt)]


def test_srt_cues_have_at_most_two_lines_of_42_chars():
    text = " ".join(["antrenament"] * 30)
    cues = _cues(exports.build_srt(_transcript(text)))
    assert len(cues) > 1
    for c in cues:
        assert 1 <= len(c["lines"]) <= 2
        assert all(len(line) <= 42 for line in c["lines"])
    assert [c["n"] for c in cues] == list(range(1, len(cues) + 1))


def test_srt_breaks_at_sentence_end():
    assert _texts(exports.build_srt(_transcript("Bună ziua. Azi facem genuflexiuni."))) == \
        ["Bună ziua.", "Azi facem genuflexiuni."]


def test_srt_breaks_at_comma_only_after_42_chars():
    assert len(_cues(exports.build_srt(_transcript("Bună, azi facem genuflexiuni")))) == 1
    first = "Antrenamentul de astăzi pentru spate drept,"   # 43 characters, ends with a comma
    assert len(first) == 43
    assert _texts(exports.build_srt(_transcript(first + " apoi stretching"))) == [first, "apoi stretching"]


def test_srt_timestamps_follow_the_words():
    srt = exports.build_srt(_transcript("Bună ziua.", start=1.0, step=0.5))
    assert srt.split("\n")[1] == "00:00:01,000 --> 00:00:01,950"


def test_srt_offset_shifts_by_intro():
    srt = exports.build_srt(_transcript("Bună ziua.", start=1.0, step=0.5), offset=9.8)
    assert _seconds(srt) == [pytest.approx((10.8, 11.75))]


def test_srt_window_is_relative_to_reel_start():
    tr = _transcript("Unu. Doi. Trei. Patru.", start=0.0, step=1.0)
    srt = exports.build_srt(tr, start=1.0, end=3.0)
    assert _texts(srt) == ["Doi.", "Trei."]
    assert _seconds(srt) == [pytest.approx((0.0, 0.95)), pytest.approx((1.0, 1.95))]


def test_srt_no_speech_is_empty():
    assert exports.build_srt({"segments": []}) == ""
    assert exports.build_srt({"segments": [{"start": 0, "end": 5, "text": "", "words": []}]}) == ""


def test_cli_srt_writes_file(tmp_path, capsys):
    t = tmp_path / "t.json"
    t.write_text(json.dumps(_transcript("Bună ziua.")), encoding="utf-8")
    out = tmp_path / "youtube.srt"
    assert exports.main(["srt", "--transcript", str(t), "--out", str(out), "--offset", "2"]) == 0
    assert json.loads(capsys.readouterr().out) == {"srt": str(out)}
    assert out.read_text(encoding="utf-8").startswith("1\n00:00:02,000 --> ")


def test_cli_srt_no_speech_writes_no_file(tmp_path, capsys):
    t = tmp_path / "t.json"
    t.write_text(json.dumps({"segments": []}), encoding="utf-8")
    out = tmp_path / "youtube.srt"
    assert exports.main(["srt", "--transcript", str(t), "--out", str(out)]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["srt"] is None and "vorbire" in res["reason"]
    assert not out.exists()


def test_cli_reels_srt_follows_snapped_segments_by_id(tmp_path, capsys):
    t = tmp_path / "t.json"
    t.write_text(json.dumps(_transcript("Unu. Doi. Trei. Patru.", step=1.0)), encoding="utf-8")
    seg = tmp_path / "snapped.json"
    seg.write_text(json.dumps({"segments": [{"id": 2, "start": 2.0, "end": 4.0},
                                            {"id": 1, "start": 0.0, "end": 2.0}]}), encoding="utf-8")
    reels = tmp_path / "reels"
    reels.mkdir()
    for n in (1, 2):
        (reels / ("short_%02d_ig.mp4" % n)).write_bytes(b"x")
    assert exports.main(["reels-srt", "--transcript", str(t), "--segments", str(seg),
                         "--reels-dir", str(reels)]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["srt"] == [str(reels / "short_01_ig.srt"), str(reels / "short_02_ig.srt")]
    assert _texts((reels / "short_01_ig.srt").read_text(encoding="utf-8")) == ["Unu.", "Doi."]
    assert _texts((reels / "short_02_ig.srt").read_text(encoding="utf-8")) == ["Trei.", "Patru."]


def _ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def _probe(path) -> dict:
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "stream=codec_type,codec_name,sample_rate:format=duration",
                          "-of", "json", str(path)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def test_cli_stems_voice_unchanged_and_picture_without_sound(tmp_path, capsys):
    video = tmp_path / "youtube.mp4"
    _ff("-f", "lavfi", "-i", "testsrc=size=320x240:rate=25:duration=2",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=2",
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(video))
    assert exports.main(["stems", "--video", str(video), "--out-dir", str(tmp_path), "--name", "youtube"]) == 0
    res = json.loads(capsys.readouterr().out)
    voice, silent = tmp_path / "youtube-voce.wav", tmp_path / "youtube-fara-sunet.mp4"
    assert res == {"voice": str(voice), "silent_video": str(silent), "warnings": []}
    v = _probe(voice)
    assert [s["codec_type"] for s in v["streams"]] == ["audio"]
    assert v["streams"][0]["sample_rate"] == "48000"
    assert abs(float(v["format"]["duration"]) - 2.0) < 0.1
    s = _probe(silent)
    assert [x["codec_type"] for x in s["streams"]] == ["video"]
    assert s["streams"][0]["codec_name"] == "h264"
    # unchanged volume: the voice file equals the video's own audio decoded with no filter
    ref = tmp_path / "ref.wav"
    _ff("-i", str(video), "-vn", "-c:a", "pcm_s16le", str(ref))
    assert voice.read_bytes() == ref.read_bytes()


def test_cli_stems_without_audio_warns(tmp_path, capsys):
    video = tmp_path / "mut.mp4"
    _ff("-f", "lavfi", "-i", "testsrc=size=320x240:rate=25:duration=1",
        "-pix_fmt", "yuv420p", "-c:v", "libx264", str(video))
    assert exports.main(["stems", "--video", str(video), "--out-dir", str(tmp_path), "--name", "mut"]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["voice"] is None
    assert res["silent_video"] == str(tmp_path / "mut-fara-sunet.mp4")
    assert res["warnings"] and not (tmp_path / "mut-voce.wav").exists()


def test_agent_runs_exports_in_monteaza_and_reels():
    text = AGENT.read_text(encoding="utf-8")
    assert "`SUNET_SEPARAT`" in text
    monteaza = text.split("## Comanda `monteaza`")[1].split("## Comanda `texte`")[0]
    reels = text.split("## Comanda `reels`")[1].split("## Dacă ceva nu merge")[0]
    assert ('exports.py" srt --transcript "$RUN_DIR/transcript-curat.json" '
            '--out "$RUN_DIR/youtube.srt" --offset') in monteaza
    assert 'exports.py" srt --transcript "$RUN_DIR/transcript-curat.json" --out "$RUN_DIR/curat.srt"' in monteaza
    assert 'exports.py" stems' in monteaza
    assert 'exports.py" reels-srt' in reels
    assert 'exports.py" stems' in reels


def test_skill_phrase_for_separate_sound():
    text = SKILL.read_text(encoding="utf-8")
    front = text.split("---")[1]
    assert "cu sunet separat" in front
    assert "`sunet_separat`" in text
    assert "SUNET_SEPARAT: <true|false>" in text
    assert "youtube.srt" in text


# --- correction after the 71998a1 checkpoint (D-11, additions 09:3x and (5)-(7))

def _section(text: str, start: str, end: str) -> str:
    return text.split(start)[1].split(end)[0]


def _monteaza(text: str) -> str:
    return _section(text, "## Comanda `monteaza`", "## Comanda `texte`")


def _reels(text: str) -> str:
    return _section(text, "## Comanda `reels`", "## Dacă ceva nu merge")


def _word(w, a, b):
    return {"word": w, "start": a, "end": b}


def test_srt_cue_ends_when_next_one_starts():
    tr = {"segments": [{"start": 0, "end": 2, "text": "Unu. Doi.",
                        "words": [_word("Unu.", 0.0, 1.5), _word("Doi.", 1.0, 2.0)]}]}
    assert _seconds(exports.build_srt(tr)) == [pytest.approx((0.0, 1.0)), pytest.approx((1.0, 2.0))]


def test_srt_reel_keeps_words_by_middle_and_cuts_times_at_edges():
    words = [_word("Salut", 0.0, 0.6), _word("bine", 0.8, 1.6), _word("ați", 1.8, 2.4),
             _word("venit", 2.5, 3.3), _word("azi", 3.4, 4.4)]
    tr = {"segments": [{"start": 0, "end": 4.4, "text": "", "words": words}]}
    srt = exports.build_srt(tr, start=1.0, end=3.0)
    assert _texts(srt) == ["bine ați venit"]
    assert _seconds(srt) == [pytest.approx((0.0, 2.0))]
    # "azi" starts inside the reel, but its middle (3.9 s) falls after the end
    srt = exports.build_srt(tr, start=1.0, end=3.8)
    assert _texts(srt) == ["bine ați venit"]
    assert _seconds(srt) == [pytest.approx((0.0, 2.3))]


def test_cli_reels_srt_reel_without_speech_gets_no_file(tmp_path, capsys):
    t = tmp_path / "t.json"
    t.write_text(json.dumps(_transcript("Unu. Doi.", step=1.0)), encoding="utf-8")
    seg = tmp_path / "snapped.json"
    seg.write_text(json.dumps({"segments": [{"id": 1, "start": 0.0, "end": 2.0},
                                            {"id": 2, "start": 5.0, "end": 8.0}]}), encoding="utf-8")
    reels = tmp_path / "reels"
    reels.mkdir()
    for n in (1, 2):
        (reels / ("short_%02d_ig.mp4" % n)).write_bytes(b"x")
    assert exports.main(["reels-srt", "--transcript", str(t), "--segments", str(seg),
                         "--reels-dir", str(reels)]) == 0
    res = json.loads(capsys.readouterr().out)
    assert res["srt"] == [str(reels / "short_01_ig.srt")]
    assert not (reels / "short_02_ig.srt").exists()
    assert len(res["warnings"]) == 1 and "short_02_ig" in res["warnings"][0]
    assert "vorbire" in res["warnings"][0]


def test_short_separate_sound_is_named_curat():
    agent = AGENT.read_text(encoding="utf-8")
    assert '--video "$RUN_DIR/curat.mp4" --name curat' in _monteaza(agent)
    skill = SKILL.read_text(encoding="utf-8")
    assert "`curat-voce.wav`" in skill and "`curat-fara-sunet.mp4`" in skill


def _video_with_audio(path):
    _ff("-f", "lavfi", "-i", "testsrc=size=320x240:rate=25:duration=1",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=1",
        "-pix_fmt", "yuv420p", "-c:v", "libx264", "-c:a", "aac", "-shortest", str(path))


def test_cli_stems_voice_failure_keeps_picture_and_removes_half_file(tmp_path, capsys, monkeypatch):
    video = tmp_path / "youtube.mp4"
    _video_with_audio(video)
    real = exports._ff

    def fake(args):
        out = Path(str(args[-1]))
        if out.name.endswith("-voce.wav"):
            out.write_bytes(b"RIFF half")      # ffmpeg stopped halfway, e.g. a full disk
            raise subprocess.CalledProcessError(1, "ffmpeg", stderr="No space left on device")
        return real(args)

    monkeypatch.setattr(exports, "_ff", fake)
    rc = exports.main(["stems", "--video", str(video), "--out-dir", str(tmp_path), "--name", "youtube"])
    res = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert res["voice"] is None
    assert not (tmp_path / "youtube-voce.wav").exists()
    assert res["silent_video"] == str(tmp_path / "youtube-fara-sunet.mp4")
    assert (tmp_path / "youtube-fara-sunet.mp4").stat().st_size > 0
    assert len(res["warnings"]) == 1
    assert res["warnings"][0].startswith("youtube-voce.wav lipsește: ")
    assert "No space left on device" in res["warnings"][0]


def _failing_write(monkeypatch, name=None):
    real = Path.write_text

    def fake(self, text, *a, **k):
        if name is None or self.name == name:
            real(self, text[:5], *a, **k)
            raise OSError(28, "No space left on device")
        return real(self, text, *a, **k)

    monkeypatch.setattr(Path, "write_text", fake)


def test_cli_srt_write_failure_leaves_no_half_file(tmp_path, capsys, monkeypatch):
    t = tmp_path / "t.json"
    t.write_text(json.dumps(_transcript("Bună ziua.")), encoding="utf-8")
    out = tmp_path / "youtube.srt"
    _failing_write(monkeypatch)
    rc = exports.main(["srt", "--transcript", str(t), "--out", str(out)])
    res = json.loads(capsys.readouterr().out)
    assert rc == 1 and "No space left" in res["error"]
    assert not out.exists()


def test_cli_reels_srt_one_failed_reel_does_not_stop_the_others(tmp_path, capsys, monkeypatch):
    t = tmp_path / "t.json"
    t.write_text(json.dumps(_transcript("Unu. Doi. Trei. Patru.", step=1.0)), encoding="utf-8")
    seg = tmp_path / "snapped.json"
    seg.write_text(json.dumps({"segments": [{"id": 1, "start": 0.0, "end": 2.0},
                                            {"id": 2, "start": 2.0, "end": 4.0}]}), encoding="utf-8")
    reels = tmp_path / "reels"
    reels.mkdir()
    for n in (1, 2):
        (reels / ("short_%02d_ig.mp4" % n)).write_bytes(b"x")
    _failing_write(monkeypatch, "short_01_ig.srt")
    rc = exports.main(["reels-srt", "--transcript", str(t), "--segments", str(seg),
                       "--reels-dir", str(reels)])
    res = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert res["srt"] == [str(reels / "short_02_ig.srt")]
    assert not (reels / "short_01_ig.srt").exists()
    assert len(res["warnings"]) == 1
    assert res["warnings"][0].startswith("short_01_ig.srt lipsește: ")


def test_agent_export_failure_is_a_warning_not_an_error():
    text = AGENT.read_text(encoding="utf-8")
    rules = _section(text, "## Reguli care nu se negociază", "## Intrarea")
    rule = [line for line in rules.splitlines() if "cod diferit de 0" in line]
    assert len(rule) == 1 and "`exports.py`" in rule[0]
    for part in (_monteaza(text), _reels(text)):
        assert "Dacă un apel `exports.py` iese cu cod 1, nu oprești comanda" in part
        assert "`<fișier> lipsește: <motivul, scurt>`" in part
        assert "treci la exportul următor" in part


def test_agent_monteaza_removes_old_exports_first():
    part = _monteaza(AGENT.read_text(encoding="utf-8"))
    rm = [line for line in part.splitlines() if line.strip().startswith("`rm -f ")]
    assert len(rm) == 1
    for name in ("youtube.srt", "curat.srt", "youtube-voce.wav", "youtube-fara-sunet.mp4",
                 "curat-voce.wav", "curat-fara-sunet.mp4"):
        assert '"$RUN_DIR/%s"' % name in rm[0]
    assert part.index(rm[0]) < part.index('exports.py" srt')


def test_skill_export_failure_keeps_the_run():
    text = SKILL.read_text(encoding="utf-8")
    sec = _section(text, "## Exporturi: subtitrări și sunet separat", "\n## ")
    assert "Dacă un export pică, montajul și reels-urile rămân" in sec
    assert "ce fișier lipsește" in sec
    assert "exporturile care lipsesc" in text
