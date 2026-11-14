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
