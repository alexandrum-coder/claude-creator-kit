#!/usr/bin/env python3
"""AirTime montage: split a clip into speech/demo regions, propose cuts,
apply approved cuts with ffmpeg, remap the transcript.

Cuts are only proposals. Demonstration regions are never cut.
"""
from __future__ import annotations

import argparse
import functools
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

DEMO_GAP = 4.0
PAUSE_MIN = {"vorbit": 0.7, "culise": 1.0, "demonstratii": 1.2}
PAUSE_KEEP = 0.25
PHRASE_BREAK = 0.5
RETAKE_WINDOW = 15.0
RETAKE_WORDS = 3
HEAD_MARGIN = 0.5
TAIL_MARGIN = 1.0
EPS = 1e-6


# ---------------------------------------------------------------- words

def load_words(transcript: dict) -> list[dict]:
    words = []
    for seg in transcript.get("segments") or []:
        for w in seg.get("words") or []:
            text = w.get("text", w.get("word", ""))
            words.append({"text": str(text).strip(), "start": float(w["start"]), "end": float(w["end"])})
    words.sort(key=lambda w: (w["start"], w["end"]))
    return words


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", text)


def _phrases(words: list[dict]) -> list[list[dict]]:
    phrases: list[list[dict]] = []
    for w in words:
        if phrases and w["start"] - phrases[-1][-1]["end"] <= PHRASE_BREAK:
            phrases[-1].append(w)
        else:
            phrases.append([w])
    return phrases


# -------------------------------------------------------------- regions

def classify_regions(words: list[dict], duration: float, voiceover: bool) -> list[dict]:
    if voiceover:
        return [{"start": 0.0, "end": duration, "kind": "demo"}]
    regions: list[dict] = []
    cursor = 0.0
    for prev, nxt in zip(words, words[1:]):
        if nxt["start"] - prev["end"] >= DEMO_GAP:
            if prev["end"] > cursor:
                regions.append({"start": cursor, "end": prev["end"], "kind": "speech"})
            regions.append({"start": prev["end"], "end": nxt["start"], "kind": "demo"})
            cursor = nxt["start"]
    if duration > cursor or not regions:
        regions.append({"start": cursor, "end": duration, "kind": "speech"})
    return regions


# ----------------------------------------------------------------- cuts

def _text_between(words: list[dict], start: float, end: float) -> str:
    return " ".join(w["text"] for w in words if w["start"] >= start - EPS and w["end"] <= end + EPS)


def _clip_to_speech(start: float, end: float, regions: list[dict]):
    """Return (start, end) clipped to the speech region containing the span start, or None."""
    for r in regions:
        if r["kind"] == "speech" and r["start"] - EPS <= start < r["end"]:
            s, e = max(start, r["start"]), min(end, r["end"])
            return (s, e) if e - s > EPS else None
    return None


def propose_cuts(words, regions, duration, clip_type, voiceover, freeze=None) -> list[dict]:
    """Propose cuts. `freeze` is a list of (start, end) edge spans from freezedetect,
    used only with voiceover=True."""
    cuts: list[dict] = []

    def add(start, end, reason):
        cuts.append({"start": round(start, 3), "end": round(end, 3), "reason": reason,
                     "text": _text_between(words, start, end)})

    if voiceover or not words:
        for s, e in freeze or []:
            if e - s > EPS:
                add(max(0.0, s), min(duration, e), "capat")
        return _finish(cuts)

    taken: list[tuple[float, float]] = []

    def free(s, e):
        return not any(s < te and ts < e for ts, te in taken)

    # retakes: first phrase of a consecutive pair opening with the same 3 words
    phrases = _phrases(words)
    for a, b in zip(phrases, phrases[1:]):
        if len(a) < RETAKE_WORDS or len(b) < RETAKE_WORDS:
            continue
        if b[0]["start"] - a[-1]["end"] > RETAKE_WINDOW:
            continue
        if [_norm(w["text"]) for w in a[:RETAKE_WORDS]] != [_norm(w["text"]) for w in b[:RETAKE_WORDS]]:
            continue
        span = _clip_to_speech(a[0]["start"], b[0]["start"], regions)
        if span and free(*span):
            taken.append(span)
            add(span[0], span[1], "reluare")

    # pauses
    threshold = PAUSE_MIN[clip_type]
    for prev, nxt in zip(words, words[1:]):
        gap = nxt["start"] - prev["end"]
        if gap < threshold or gap >= DEMO_GAP:
            continue
        span = _clip_to_speech(prev["end"] + PAUSE_KEEP, nxt["start"] - PAUSE_KEEP, regions)
        if span and free(*span):
            taken.append(span)
            add(span[0], span[1], "pauza")

    # edges
    if words:
        head_end = words[0]["start"] - HEAD_MARGIN
        if head_end > EPS:
            add(0.0, head_end, "capat")
        tail_start = words[-1]["end"] + TAIL_MARGIN
        if duration - tail_start > EPS:
            add(tail_start, duration, "capat")
    return _finish(cuts)


def _finish(cuts: list[dict]) -> list[dict]:
    cuts.sort(key=lambda c: (c["start"], c["end"]))
    for i, c in enumerate(cuts, 1):
        c["id"] = i
    return [{"id": c["id"], "start": c["start"], "end": c["end"], "reason": c["reason"], "text": c["text"]}
            for c in cuts]


# --------------------------------------------------- keep intervals/remap

def keep_intervals(duration: float, cuts: list[dict]) -> list[tuple[float, float]]:
    spans = sorted((max(0.0, float(c["start"])), min(duration, float(c["end"]))) for c in cuts)
    keep: list[tuple[float, float]] = []
    cursor = 0.0
    for s, e in spans:
        if e <= s:
            continue
        if s > cursor + EPS:
            keep.append((cursor, s))
        cursor = max(cursor, e)
    if duration > cursor + EPS:
        keep.append((cursor, duration))
    return keep


def remap(t: float, keep) -> float | None:
    offset = 0.0
    for a, b in keep:
        if a - EPS <= t <= b + EPS:
            return offset + max(0.0, t - a)
        offset += b - a
    return None


def _remap_span(start: float, end: float, keep):
    """Remap a span whose midpoint lies in a keep interval, clamped to it; else None."""
    mid = (start + end) / 2.0
    offset = 0.0
    for a, b in keep:
        if a - EPS <= mid <= b + EPS:
            s, e = min(max(start, a), b), min(max(end, a), b)
            return offset + (s - a), offset + (e - a)
        offset += b - a
    return None


def remap_transcript(transcript: dict, keep) -> dict:
    def remap_words(words):
        out = []
        for w in words:
            span = _remap_span(float(w["start"]), float(w["end"]), keep)
            if span:
                nw = dict(w)
                nw["start"], nw["end"] = round(span[0], 3), round(span[1], 3)
                out.append(nw)
        return out

    result = dict(transcript)
    segments = []
    for seg in transcript.get("segments") or []:
        nseg = dict(seg)
        if seg.get("words"):
            words = remap_words(seg["words"])
            if not words:
                continue
            nseg["words"] = words
            nseg["start"], nseg["end"] = words[0]["start"], words[-1]["end"]
            if len(words) != len(seg["words"]):
                nseg["text"] = " ".join(str(w.get("word", w.get("text", ""))).strip() for w in words)
        else:
            span = _remap_span(float(seg["start"]), float(seg["end"]), keep)
            if not span:
                continue
            nseg["start"], nseg["end"] = round(span[0], 3), round(span[1], 3)
        segments.append(nseg)
    if "segments" in transcript:
        result["segments"] = segments
    if "words" in transcript:
        result["words"] = remap_words(transcript["words"] or [])
    if "captions" in transcript:
        caps = []
        for c in transcript["captions"] or []:
            span = _remap_span(c["startMs"] / 1000.0, c["endMs"] / 1000.0, keep)
            if span:
                nc = dict(c)
                nc["startMs"], nc["endMs"] = int(round(span[0] * 1000)), int(round(span[1] * 1000))
                caps.append(nc)
        result["captions"] = caps
    return result


# ---------------------------------------------------------------- ffmpeg

def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def probe_duration(video: str) -> float:
    r = _run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)])
    return float(r.stdout.strip())


def has_audio(video: str) -> bool:
    r = _run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
              "-of", "csv=p=0", str(video)])
    return bool(r.stdout.strip())


HDR_TRANSFERS = ("arib-std-b67", "smpte2084")  # HLG (iPhone HDR / Dolby Vision 8.4), PQ


def color_transfer(video: str) -> str:
    r = _run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
              "stream=color_transfer", "-of", "csv=p=0", str(video)])
    return r.stdout.strip().splitlines()[0].strip() if r.stdout.strip() else ""


def tonemap_filter(transfer: str) -> str:
    """zscale+tonemap chain from HDR (bt2020, HLG or PQ) to 8-bit bt709 SDR; "" for SDR input."""
    if transfer not in HDR_TRANSFERS:
        return ""
    return ("zscale=tin=%s:pin=bt2020:min=bt2020nc:t=linear:npl=100,format=gbrpf32le,"
            "zscale=p=bt709,tonemap=tonemap=hable:desat=0,"
            "zscale=t=bt709:m=bt709:r=tv,format=yuv420p" % transfer)


@functools.lru_cache(maxsize=None)
def has_filter(name: str) -> bool:
    """True if the local ffmpeg lists the filter (Homebrew's build has no zscale: no libzimg)."""
    try:
        r = _run(["ffmpeg", "-hide_banner", "-filters"])
    except (OSError, subprocess.CalledProcessError):
        return False
    return any(len(l.split()) > 1 and l.split()[1] == name for l in r.stdout.splitlines())


HDR_WARNING = ("Clipul e filmat în HDR, dar ffmpeg de pe acest calculator nu poate converti culorile. "
               "Culorile pot ieși spălate. Pe iPhone, la Configurări → Cameră → Formate, oprește "
               "„Video HDR” și filmează din nou, dacă diferența te deranjează.")


def parse_freeze_edges(stderr: str, duration: float, tol: float = 0.25) -> list[tuple[float, float]]:
    """Freeze spans touching the start or the end of the clip, from freezedetect output."""
    starts = [float(x) for x in re.findall(r"freeze_start:\s*([0-9.]+)", stderr)]
    ends = [float(x) for x in re.findall(r"freeze_end:\s*([0-9.]+)", stderr)]
    edges = []
    for i, s in enumerate(starts):
        e = ends[i] if i < len(ends) else duration  # unterminated freeze runs to the end
        if s <= tol or e >= duration - tol:
            edges.append((s, e))
    return edges


def freeze_edges(video: str, duration: float) -> list[tuple[float, float]]:
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vf",
                        "freezedetect=n=0.003:d=1", "-map", "0:v:0", "-an", "-f", "null", "-"],
                       capture_output=True, text=True)
    return parse_freeze_edges(r.stderr, duration)


def apply_cuts(video: str, cuts: list[dict], out: str) -> dict:
    duration = probe_duration(video)
    keep = keep_intervals(duration, cuts)
    if not keep:
        raise SystemExit("nothing left after cuts")
    audio = has_audio(video)
    parts, labels = [], ""
    for i, (a, b) in enumerate(keep):
        parts.append("[0:v]trim=start=%.6f:end=%.6f,setpts=PTS-STARTPTS[v%d]" % (a, b, i))
        labels += "[v%d]" % i
        if audio:
            parts.append("[0:a]atrim=start=%.6f:end=%.6f,asetpts=PTS-STARTPTS[a%d]" % (a, b, i))
            labels += "[a%d]" % i
    tonemap = tonemap_filter(color_transfer(video))
    warnings = []
    if tonemap and not has_filter("zscale"):
        tonemap = ""
        warnings.append(HDR_WARNING)
    vout = "[vc]" if tonemap else "[v]"
    parts.append("%sconcat=n=%d:v=1:a=%d%s%s" % (labels, len(keep), 1 if audio else 0, vout, "[a]" if audio else ""))
    if tonemap:
        # iPhone HDR: tone-map to SDR here, so curat.mp4 (and the intro, reels, Shorts after it) is bt709
        parts.append("[vc]%s[v]" % tonemap)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(video), "-filter_complex", ";".join(parts),
           "-map", "[v]"]
    if audio:
        cmd += ["-map", "[a]", "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p"]
    if tonemap:
        cmd += ["-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709"]
    cmd += ["-movflags", "+faststart", str(out)]
    _run(cmd)
    res = {"duration": duration, "keep": [[a, b] for a, b in keep]}
    if warnings:
        res["warnings"] = warnings
    return res


def extract_frame(video: str, t: float, out: Path) -> None:
    _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "%.3f" % t, "-i", str(video),
          "-frames:v", "1", "-q:v", "2", str(out)])


# ------------------------------------------------------------------- CLI

def _load_json(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str, data) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def cmd_propose(a) -> int:
    words = load_words(_load_json(a.transcript))
    duration = probe_duration(a.video)
    regions = classify_regions(words, duration, a.voiceover)
    freeze = None
    if a.voiceover or not words:
        if not words and not a.voiceover:
            print("Clipul nu are vorbire: propun doar tăieturi la capete.", file=sys.stderr)
        freeze = freeze_edges(a.video, duration)
    cuts = propose_cuts(words, regions, duration, a.clip_type, a.voiceover, freeze=freeze)
    frames = Path(a.frames_dir)
    frames.mkdir(parents=True, exist_ok=True)
    for c in cuts:
        extract_frame(a.video, (c["start"] + c["end"]) / 2.0, frames / ("cut_%s.jpg" % c["id"]))
    _write_json(a.out, {"duration": duration, "regions": regions, "cuts": cuts})
    return 0


def cmd_apply(a) -> int:
    data = _load_json(a.cuts)
    cuts = data["cuts"] if isinstance(data, dict) else data
    try:
        res = apply_cuts(a.video, cuts, a.out)
    except subprocess.CalledProcessError as e:
        print(json.dumps({"error": "ffmpeg a eșuat: %s" % (e.stderr or "")[-1500:].strip(), "step": "apply"},
                         ensure_ascii=False))
        return 1
    _write_json(a.map, res)
    if res.get("warnings"):
        print(json.dumps({"warnings": res["warnings"]}, ensure_ascii=False))
    return 0


def cmd_remap(a) -> int:
    m = _load_json(a.map)
    keep = [(float(s), float(e)) for s, e in m["keep"]]
    _write_json(a.out, remap_transcript(_load_json(a.transcript), keep))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="silences.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("propose")
    s.add_argument("--transcript", required=True)
    s.add_argument("--video", required=True)
    s.add_argument("--clip-type", required=True, choices=sorted(PAUSE_MIN))
    s.add_argument("--voiceover", action="store_true")
    s.add_argument("--out", required=True)
    s.add_argument("--frames-dir", required=True)
    s.set_defaults(fn=cmd_propose)
    s = sub.add_parser("apply")
    s.add_argument("--video", required=True)
    s.add_argument("--cuts", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--map", required=True)
    s.set_defaults(fn=cmd_apply)
    s = sub.add_parser("remap")
    s.add_argument("--transcript", required=True)
    s.add_argument("--map", required=True)
    s.add_argument("--out", required=True)
    s.set_defaults(fn=cmd_remap)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
