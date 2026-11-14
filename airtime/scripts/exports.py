#!/usr/bin/env python3
"""AirTime exports after editing (D-11): .srt subtitles, voice-only .wav, picture-only .mp4.

  exports.py srt --transcript T --out F [--offset S] [--start A --end B]
  exports.py reels-srt --transcript T --segments reels/work/snapped_segments.json --reels-dir reels
  exports.py stems --video V --out-dir D --name N

Each command prints one JSON object. On failure: {"error", "step"} and exit 1.
Standard library and ffmpeg only.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

MAX_LINE = 42          # characters per subtitle line
MAX_LINES = 2          # lines per subtitle
SENTENCE_END = ".?!…"
PAUSE = ",;:"
EPS = 1e-6
NO_SPEECH = "Clipul nu are vorbire; nu există subtitrări."


def _words(transcript: dict) -> list[dict]:
    out = []
    for seg in transcript.get("segments") or []:
        for w in seg.get("words") or []:
            text = str(w.get("word", w.get("text", ""))).strip()
            if text:
                out.append({"word": text, "start": float(w["start"]), "end": float(w["end"])})
    return out


def _wrap(words: list[str]) -> list[str]:
    lines, cur = [], ""
    for w in words:
        if cur and len(cur) + 1 + len(w) > MAX_LINE:
            lines.append(cur)
            cur = w
        else:
            cur = "%s %s" % (cur, w) if cur else w
    if cur:
        lines.append(cur)
    return lines


def _stamp(t: float) -> str:
    ms = max(0, int(round(t * 1000)))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return "%02d:%02d:%02d,%03d" % (h, m, s, ms)


def cues(words: list[dict]) -> list[list[dict]]:
    """Group words into subtitles of at most 2 lines x 42 characters (D-11)."""
    groups, cur = [], []
    for w in words:
        if cur and len(_wrap([x["word"] for x in cur + [w]])) > MAX_LINES:
            groups.append(cur)
            cur = []
        cur.append(w)
        tail = w["word"][-1:]
        if tail in SENTENCE_END:
            groups.append(cur)
            cur = []
        elif tail in PAUSE and len(" ".join(x["word"] for x in cur)) >= MAX_LINE:
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def build_srt(transcript: dict, offset: float = 0.0, start: float | None = None,
              end: float | None = None) -> str:
    """SRT text for the transcript, or "" when nobody speaks.

    start/end keep the words whose middle falls in the window, with times relative to start
    (a reel); offset shifts every time (the intro before youtube.mp4).
    """
    words = _words(transcript)
    base = 0.0 if start is None else float(start)
    if start is not None or end is not None:
        lo = base
        hi = float("inf") if end is None else float(end)
        kept = []
        for w in words:
            mid = (w["start"] + w["end"]) / 2.0
            if lo - EPS <= mid <= hi + EPS:
                kept.append(dict(w, start=max(w["start"], lo), end=min(w["end"], hi)))
        words = kept
    groups = cues(words)
    blocks = []
    for i, g in enumerate(groups):
        a = g[0]["start"]
        b = g[-1]["end"]
        if i + 1 < len(groups):
            b = min(b, groups[i + 1][0]["start"])
        a, b = a - base + offset, b - base + offset
        text = "\n".join(_wrap([x["word"] for x in g]))
        blocks.append("%d\n%s --> %s\n%s\n" % (i + 1, _stamp(a), _stamp(b), text))
    return "\n".join(blocks)


def _load(path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ff(args: list) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *[str(a) for a in args]],
                   check=True, capture_output=True, text=True)


def _has_audio(video: Path) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=index", "-of", "csv=p=0", str(video)],
                         check=True, capture_output=True, text=True).stdout
    return bool(out.strip())


def stems(video, out_dir, name) -> dict:
    """Voice exactly as in the video (no filter) and the picture without sound (stream copy)."""
    video, out_dir = Path(video), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    voice = out_dir / ("%s-voce.wav" % name)
    silent = out_dir / ("%s-fara-sunet.mp4" % name)
    warnings = []
    if _has_audio(video):
        _ff(["-i", video, "-vn", "-c:a", "pcm_s16le", voice])
        voice_path = str(voice)
    else:
        warnings.append("%s nu are sunet; nu există fișier doar cu vocea." % video.name)
        voice_path = None
    _ff(["-i", video, "-an", "-c:v", "copy", "-movflags", "+faststart", silent])
    return {"voice": voice_path, "silent_video": str(silent), "warnings": warnings}


def reels_srt(transcript, segments, reels_dir) -> dict:
    tr = _load(transcript)
    segs = sorted(_load(segments).get("segments") or [], key=lambda s: int(s.get("id", 0)))
    reels_dir = Path(reels_dir)
    files = sorted(reels_dir.glob("short_*_ig.mp4"))
    if len(files) != len(segs):
        raise ValueError("%d reels, dar %d segmente" % (len(files), len(segs)))
    written, warnings = [], []
    for f, s in zip(files, segs):
        text = build_srt(tr, start=float(s["start"]), end=float(s["end"]))
        if not text:
            warnings.append("%s: %s" % (f.name, NO_SPEECH))
            continue
        out = f.with_suffix(".srt")
        _write(out, text)
        written.append(str(out))
    res = {"srt": written}
    if warnings:
        res["warnings"] = warnings
    return res


def _emit(obj: dict) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("srt")
    p.add_argument("--transcript", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--offset", type=float, default=0.0)
    p.add_argument("--start", type=float)
    p.add_argument("--end", type=float)
    p = sub.add_parser("reels-srt")
    p.add_argument("--transcript", required=True)
    p.add_argument("--segments", required=True)
    p.add_argument("--reels-dir", required=True)
    p = sub.add_parser("stems")
    p.add_argument("--video", required=True)
    p.add_argument("--out-dir", required=True)
    p.add_argument("--name", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "srt":
            text = build_srt(_load(a.transcript), offset=a.offset, start=a.start, end=a.end)
            if not text:
                _emit({"srt": None, "reason": NO_SPEECH})
            else:
                _write(Path(a.out), text)
                _emit({"srt": a.out})
        elif a.cmd == "reels-srt":
            _emit(reels_srt(a.transcript, a.segments, a.reels_dir))
        else:
            _emit(stems(a.video, a.out_dir, a.name))
    except subprocess.CalledProcessError as e:
        _emit({"error": (e.stderr or str(e))[-800:], "step": a.cmd})
        return 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        _emit({"error": str(e), "step": a.cmd})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
