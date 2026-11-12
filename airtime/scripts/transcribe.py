#!/usr/bin/env python3
"""AirTime transcription without PyAV.

claude-shorts' scripts/transcribe.py passes a file path to faster-whisper, which then
calls av.open(..., metadata_errors="ignore"). PyAV 19 removed that argument, so on a
fresh install (faster-whisper 1.2.1 + the newest PyAV) transcription fails with
"av.open() got an unexpected keyword argument 'metadata_errors'". Here ffmpeg decodes
the audio to 16 kHz mono float32 and the numpy array goes straight to
WhisperModel.transcribe(); with an array faster-whisper never touches PyAV.

The output has the same format as claude-shorts/scripts/transcribe.py (segments with
word timestamps + Remotion captions), so snap_boundaries.py and render.mjs are unchanged.

Run with the claude-shorts Python (it has faster_whisper and numpy):
    ~/.shorts-skill/bin/python3 transcribe.py VIDEO --output OUT.json --model small [--language ro]
"""
import argparse
import json
import os
import subprocess
import sys
import time

SAMPLE_RATE = 16000


def decode_audio(path: str):
    import numpy as np
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-vn", "-ac", "1",
                        "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"], capture_output=True)
    if r.returncode != 0:
        detail = r.stderr.decode("utf-8", "replace")[-300:]
        raise RuntimeError(f"Audio extraction failed: {detail}")
    return np.frombuffer(r.stdout, dtype=np.float32).copy()


def main() -> int:
    ap = argparse.ArgumentParser(description="Transcribe with faster-whisper, without PyAV")
    ap.add_argument("input", help="input video or audio file")
    ap.add_argument("--output", required=True, help="output JSON file")
    ap.add_argument("--model", default="small", help="Whisper model size (default: small)")
    ap.add_argument("--language", default=None, help="language code, e.g. ro (default: detect)")
    a = ap.parse_args()

    if not os.path.isfile(a.input):
        print(json.dumps({"error": f"Input file not found: {a.input}"}))
        return 1
    t0 = time.time()
    try:
        audio = decode_audio(a.input)
    except RuntimeError as e:
        print(json.dumps({"error": str(e)}))
        return 1

    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device="cpu", compute_type="int8")
    segs, info = model.transcribe(audio, language=a.language, beam_size=5, word_timestamps=True,
                                  vad_filter=True,
                                  vad_parameters=dict(min_silence_duration_ms=500, speech_pad_ms=200))
    segments, captions = [], []
    for s in segs:
        d = {"start": round(s.start, 3), "end": round(s.end, 3), "text": s.text.strip(), "words": []}
        for w in s.words or []:
            d["words"].append({"word": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
            # faster-whisper keeps the leading space in w.word; Remotion captions expect it
            captions.append({"text": w.word, "startMs": int(w.start * 1000), "endMs": int(w.end * 1000)})
        segments.append(d)

    out = {
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(len(audio) / SAMPLE_RATE, 1),
        "word_count": sum(len(s["words"]) for s in segments),
        "model": a.model,
        "device": "cpu",
        "compute_type": "int8",
        "transcription_time_sec": round(time.time() - t0, 1),
        "segments": segments,
        "captions": captions,
    }
    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(json.dumps({"action": "transcribe", "output": a.output, "word_count": out["word_count"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
