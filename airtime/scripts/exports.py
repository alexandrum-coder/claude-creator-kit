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
    """Write the file, or leave none: a half-written file is removed (D-11, point 6)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        path.write_text(text, encoding="utf-8")
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def _ff(args: list) -> None:
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *[str(a) for a in args]],
                   check=True, capture_output=True, text=True)


def _reason(e: BaseException) -> str:
    """The short reason for the warning line `<file> lipsește: <reason>`."""
    if isinstance(e, subprocess.CalledProcessError):
        lines = [x.strip() for x in (e.stderr or "").splitlines() if x.strip()]
        text = lines[-1] if lines else str(e)
    elif isinstance(e, OSError) and e.strerror:
        text = e.strerror
    else:
        text = str(e)
    return text[:200]


def _missing(path: Path, e: BaseException) -> str:
    return "%s lipsește: %s" % (path.name, _reason(e))


def _make(out: Path, args: list, warnings: list) -> str | None:
    """Run one ffmpeg export; on failure remove the half-written file and add a warning."""
    try:
        _ff(args)
        return str(out)
    except (subprocess.CalledProcessError, OSError) as e:
        out.unlink(missing_ok=True)
        warnings.append(_missing(out, e))
        return None


def _has_audio(video: Path) -> bool:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=index", "-of", "csv=p=0", str(video)],
                         check=True, capture_output=True, text=True).stdout
    return bool(out.strip())


def _probe_audio(path: Path) -> tuple[float, int]:
    """(duration of the file, sample rate of its first audio stream or 0)."""
    out = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                     "stream=codec_type,sample_rate:format=duration", "-of", "json", str(path)],
                                    check=True, capture_output=True, text=True).stdout)
    rate = next((int(s["sample_rate"]) for s in out.get("streams") or []
                 if s.get("codec_type") == "audio" and s.get("sample_rate")), 0)
    return float((out.get("format") or {}).get("duration") or 0), rate


def _voice_args(source: Path, voice: Path, start=None, end=None, intro=None) -> list:
    """ffmpeg arguments for the voice file. Without options: the source's sound as it is.

    start/end: only that stretch (a reel). intro: the intro's sound first, as in youtube.mp4
    (silence if the intro has none), then the source's sound (D-14 (20))."""
    if intro is not None:
        intro = Path(intro)
        dur, irate = _probe_audio(intro)
        rate = _probe_audio(source)[1] or irate or 48000
        fmt = "aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo" % rate
        head = ("[0:a]%s,atrim=0:%.6f[i]" % (fmt, dur) if irate
                else "anullsrc=r=%d:cl=stereo,atrim=0:%.6f[i]" % (rate, dur))
        graph = "%s;[1:a]%s[v];[i][v]concat=n=2:v=0:a=1[a]" % (head, fmt)
        return ["-i", intro, "-i", source, "-filter_complex", graph, "-map", "[a]", "-c:a", "pcm_s16le", voice]
    window = []
    if start is not None:
        window += ["-ss", "%.3f" % float(start)]
    if end is not None:
        window += ["-to", "%.3f" % float(end)]
    return window + ["-i", source, "-vn", "-c:a", "pcm_s16le", voice]


def stems(video, out_dir, name, voice_from=None, start=None, end=None, intro=None) -> dict:
    """Voice exactly as in the video (no filter) and the picture without sound (stream copy).

    With B-roll the voice comes from `voice_from` (the cut clip without B-roll), so it has no
    B-roll sound; the picture still comes from `video` (D-14 (17)).
    The two files are independent: if one fails, the other is still made (D-11, point 5).
    """
    video, out_dir = Path(video), Path(out_dir)
    source = Path(voice_from) if voice_from else video
    out_dir.mkdir(parents=True, exist_ok=True)
    voice = out_dir / ("%s-voce.wav" % name)
    silent = out_dir / ("%s-fara-sunet.mp4" % name)
    warnings = []
    if _has_audio(source):
        voice_path = _make(voice, _voice_args(source, voice, start, end, intro), warnings)
    else:
        warnings.append("%s nu are sunet; nu există fișier doar cu vocea." % source.name)
        voice_path = None
    silent_path = _make(silent, ["-i", video, "-an", "-c:v", "copy", "-movflags", "+faststart", silent],
                        warnings)
    return {"voice": voice_path, "silent_video": silent_path, "warnings": warnings}


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
        try:
            _write(out, text)
        except OSError as e:          # one reel failing does not stop the others (D-11, point 5)
            warnings.append(_missing(out, e))
            continue
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
    p.add_argument("--voice-from", help="vocea din acest fișier (clipul tăiat fără B-roll)")
    p.add_argument("--start", type=float)
    p.add_argument("--end", type=float)
    p.add_argument("--intro", help="sunetul intro-ului pus înaintea vocii (videoclipul YouTube)")
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
            _emit(stems(a.video, a.out_dir, a.name, a.voice_from, a.start, a.end, a.intro))
    except subprocess.CalledProcessError as e:
        _emit({"error": (e.stderr or str(e))[-800:], "step": a.cmd})
        return 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        _emit({"error": str(e), "step": a.cmd})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
