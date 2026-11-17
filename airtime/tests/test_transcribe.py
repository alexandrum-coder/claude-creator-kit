"""F-1: Whisper hallucinations on silence are dropped by transcribe.py (PLAN, Note 2.28, D-93).

Measured on the real clips (scratch/upgrade/f1-probe.txt): "Thanks for watching!" on a clip without speech
(no_speech_prob 0.844, avg_logprob -0.979) and a repeated sentence at the end of a talking clip (0.958, -0.647);
real speech had no_speech_prob 0.608 or 0.132 and avg_logprob -0.314 or -0.267.
faster_whisper and the ffmpeg decode are faked: the AirTime venv has neither faster_whisper nor numpy.
"""
from __future__ import annotations

import json
import sys
import types
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import transcribe  # noqa: E402


@pytest.mark.parametrize("no_speech,logprob,keep", [
    (0.844, -0.979, False),     # Ddoec-ExBif: "Thanks for watching!"
    (0.958, -0.647, False),     # DWVpegyDPLS: the repeated last sentence
    (0.608, -0.314, True),      # real speech
    (0.132, -0.267, True),      # real speech
    (0.8, -0.9, True),          # no_speech_prob not above 0.8
    (0.95, -0.5, True),         # avg_logprob not below -0.5
    (0.95, -0.2, True),         # likely silence, but decoded with confidence
    (0.3, -1.5, True),          # low confidence alone is not enough
])
def test_keep_segment_thresholds(no_speech, logprob, keep):
    assert transcribe.keep_segment(no_speech, logprob) is keep


def _seg(start, end, text, no_speech, logprob):
    words = [types.SimpleNamespace(word=" " + w, start=start + i * 0.1, end=start + i * 0.1 + 0.1)
             for i, w in enumerate(text.split())]
    return types.SimpleNamespace(start=start, end=end, text=" " + text, words=words,
                                 no_speech_prob=no_speech, avg_logprob=logprob)


def _run(tmp_path, monkeypatch, segs):
    fake = types.ModuleType("faster_whisper")

    class WhisperModel:
        def __init__(self, *a, **k):
            pass

        def transcribe(self, audio, **k):
            return iter(segs), types.SimpleNamespace(language="ro", language_probability=0.9)

    fake.WhisperModel = WhisperModel
    monkeypatch.setitem(sys.modules, "faster_whisper", fake)
    monkeypatch.setattr(transcribe, "decode_audio", lambda p: [0.0] * (16000 * 19))
    video, out = tmp_path / "v.mp4", tmp_path / "t.json"
    video.write_bytes(b"x")
    monkeypatch.setattr(sys, "argv", ["transcribe.py", str(video), "--output", str(out)])
    assert transcribe.main() == 0
    return json.loads(out.read_text(encoding="utf-8"))


def test_hallucinated_segment_is_left_out_and_kept_as_a_trace(tmp_path, monkeypatch):
    t = _run(tmp_path, monkeypatch, [_seg(0.47, 3.03, "Bună sunt Irina", 0.608, -0.314),
                                      _seg(56.15, 58.15, "Mă mișc în continuare", 0.958, -0.647)])
    assert [s["text"] for s in t["segments"]] == ["Bună sunt Irina"]
    assert t["word_count"] == 3
    assert [c["text"] for c in t["captions"]] == [" Bună", " sunt", " Irina"]
    assert t["dropped_segments"] == [{"start": 56.15, "end": 58.15, "text": "Mă mișc în continuare",
                                      "no_speech_prob": 0.958, "avg_logprob": -0.647}]


def test_clip_with_only_hallucinations_has_no_words(tmp_path, monkeypatch):
    t = _run(tmp_path, monkeypatch, [_seg(0.0, 0.2, "Thanks for watching!", 0.844, -0.979)])
    assert t["segments"] == [] and t["captions"] == [] and t["word_count"] == 0
    assert [d["text"] for d in t["dropped_segments"]] == ["Thanks for watching!"]


def test_clean_transcript_has_an_empty_trace(tmp_path, monkeypatch):
    t = _run(tmp_path, monkeypatch, [_seg(0.47, 3.03, "Bună sunt Irina", 0.608, -0.314)])
    assert t["dropped_segments"] == [] and t["word_count"] == 3
