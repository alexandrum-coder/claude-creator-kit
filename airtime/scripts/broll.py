#!/usr/bin/env python3
"""AirTime B-roll (D-14): short clips laid over the cut clip while the coach talks.

    broll.py vorbit   --dir DIR
    broll.py cadre    --dir DIR --frames-dir F --out broll-clipuri.json [--exclude VIDEO]
    broll.py verifica --broll broll-propus.json --cuts cuts-aprobate.json --video VIDEO --dir DIR
    broll.py aplica   --video curat-fara-broll.mp4 --broll broll-aprobat.json --map map.json --dir DIR --out curat.mp4

A table row is {id, t0, src, src_in, dur, volum, cuvinte, motiv}. t0 is on the ORIGINAL clip;
`aplica` places it on the cut clip through the real cuts in map.json (D-14 (16)).
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from silences import (EPS, HDR_WARNING, color_transfer, has_filter, keep_intervals, probe_duration,
                      remap, tonemap_filter)
from compose import _fps_text, _probe_full

VIDEO_EXT = (".mp4", ".mov", ".m4v")
MIN_CLIP = 3.0      # a B-roll clip shorter than this is not used (D-14 (14))
DUR_MIN, DUR_MAX = 3.0, 5.0
GAP = 15.0          # from the end of one insert to the start of the next (D-14 (8), (21))
HEAD = 5.0          # nothing in the first 5 s of the cut clip (D-14 (9))
FADE = 0.25
VOLUM = 0.2         # B-roll sound: about a fifth, under the voice (D-14 (3))


def _run(args: list) -> subprocess.CompletedProcess:
    return subprocess.run([str(a) for a in args], check=True, capture_output=True, text=True)


def list_clips(folder) -> list[Path]:
    return sorted((p for p in Path(folder).iterdir()
                   if p.is_file() and not p.name.startswith(".") and p.suffix.lower() in VIDEO_EXT),
                  key=lambda p: p.name.lower())


def speaker(folder) -> Path | None:
    """The spoken clip in a single folder: the longest clip with sound (the coach confirms it)."""
    best = None
    for p in list_clips(folder):
        info = _probe_full(p)
        if info["has_audio"] and (best is None or info["duration"] > best[1]):
            best = (p, info["duration"])
    return best[0] if best else None


def cadre(folder, frames_dir, exclude=None) -> dict:
    frames_dir = Path(frames_dir)
    frames_dir.mkdir(parents=True, exist_ok=True)
    skip = Path(exclude).resolve() if exclude else None
    clips, skipped = [], []
    for p in list_clips(folder):
        if skip is not None and p.resolve() == skip:
            continue
        info = _probe_full(p)
        if info["duration"] < MIN_CLIP:
            skipped.append({"src": p.name, "duration": round(info["duration"], 2),
                            "reason": "mai scurt de 3 s, nu se folosește"})
            continue
        frames = []
        for k, frac in enumerate((0.25, 0.5, 0.75), 1):
            out = frames_dir / ("%s_%d.jpg" % (p.stem, k))
            _run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "%.3f" % (info["duration"] * frac), "-i", p,
                  "-frames:v", "1", "-q:v", "3", "-vf", "scale=480:-2", out])
            frames.append(str(out))
        clips.append({"src": p.name, "duration": round(info["duration"], 3), "has_audio": info["has_audio"],
                      "frames": frames})
    return {"clips": clips, "skipped": skipped}


# ------------------------------------------------------------ table rules

def _rows(data) -> list[dict]:
    return list(data.get("broll") or []) if isinstance(data, dict) else list(data or [])


def normalize(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        r = dict(r)
        if r.get("volum") is None:
            r["volum"] = VOLUM
        r["src_in"] = float(r.get("src_in") or 0.0)
        out.append(r)
    return out


def _inside_cut(t: float, cuts: list[dict]) -> bool:
    return any(float(c["start"]) + EPS < t < float(c["end"]) - EPS for c in cuts)


def verifica(rows, cuts, duration, clips: dict) -> list[str]:
    """Errors for a table, on the cut clip computed from the approved cuts (approximate, D-14 (16)).

    The real cuts only shrink (snap_cuts), so after map.json a moment can only move later:
    the 5 s and 15 s rules checked here still hold at `aplica`."""
    keep = keep_intervals(duration, cuts)
    cut_len = sum(b - a for a, b in keep)
    errors, seen, placed = [], set(), []
    for r in normalize(rows):
        rid = "rândul %s" % r.get("id", "?")
        src, dur, src_in, t0 = r.get("src"), float(r.get("dur", 0)), r["src_in"], float(r.get("t0", 0))
        if not DUR_MIN - EPS <= dur <= DUR_MAX + EPS:
            errors.append("%s: durata %.1f s, trebuie între 3 și 5 s" % (rid, dur))
        if not 0.0 <= float(r["volum"]) <= 1.0:
            errors.append("%s: volumul %s, trebuie între 0 și 1" % (rid, r["volum"]))
        if src not in clips:
            errors.append("%s: clipul %s nu e în dosarul B-roll" % (rid, src))
        elif clips[src] < MIN_CLIP:
            errors.append("%s: clipul %s e mai scurt de 3 s" % (rid, src))
        elif src_in < 0 or src_in + dur > clips[src] + EPS:
            errors.append("%s: %s are %.1f s, nu ajunge de la %.1f s cât %.1f s" % (rid, src, clips[src], src_in, dur))
        if src in seen:
            errors.append("%s: clipul %s e folosit de două ori" % (rid, src))
        seen.add(src)
        t = remap(t0, keep)
        if t is None or _inside_cut(t0, cuts):
            errors.append("%s: momentul %.1f s cade într-o tăietură" % (rid, t0))
            continue
        if t < HEAD - EPS:
            errors.append("%s: în primele 5 s ale clipului tăiat" % rid)
        if t + dur > cut_len + EPS:
            errors.append("%s: trece de sfârșitul clipului tăiat" % rid)
        placed.append((t, t + dur, rid))
    placed.sort()
    for (a0, a1, _), (b0, _, rid) in zip(placed, placed[1:]):
        if b0 - a1 < GAP - EPS:
            errors.append("%s: la %.1f s după B-roll-ul dinainte, trebuie cel puțin 15 s" % (rid, b0 - a1))
    return errors


def place(rows, keep) -> list[dict]:
    """Rows with `t` on the cut clip, from t0 on the original through the keep intervals."""
    out = []
    for r in normalize(rows):
        t = remap(float(r["t0"]), keep)
        if t is not None:
            out.append(dict(r, t=t))
    return sorted(out, key=lambda r: r["t"])


# ------------------------------------------------------------ overlay

def build_filtergraph(main: dict, inserts: list[dict]):
    """Input 0 = cut clip without B-roll, input i+1 = inserts[i] (with t, src_in, dur, volum, has_audio, tonemap)."""
    w, h, fps = main["width"], main["height"], _fps_text(main["fps"])
    rate = main.get("sample_rate") or 48000
    parts, last, mixes = [], "0:v", []
    for i, ins in enumerate(inserts):
        k, t, d = i + 1, float(ins["t"]), float(ins["dur"])
        tm = (ins.get("tonemap") or "") + "," if ins.get("tonemap") else ""
        parts.append("[%d:v]trim=start=%.3f:end=%.3f,setpts=PTS-STARTPTS,%s"
                     "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,fps=%s,setsar=1,format=yuva420p,"
                     "fade=t=in:st=0:d=%s:alpha=1,fade=t=out:st=%.3f:d=%s:alpha=1,setpts=PTS+%.3f/TB[b%d]"
                     % (k, ins["src_in"], ins["src_in"] + d, tm, w, h, w, h, fps, FADE, d - FADE, FADE, t, i))
        parts.append("[%s][b%d]overlay=eof_action=pass:enable='between(t,%.3f,%.3f)'[v%d]" % (last, i, t, t + d, i))
        last = "v%d" % i
        if main["has_audio"] and ins.get("has_audio") and float(ins["volum"]) > 0:
            ms = int(round(t * 1000))
            parts.append("[%d:a]atrim=start=%.3f:end=%.3f,asetpts=PTS-STARTPTS,aresample=%d,"
                         "aformat=sample_fmts=fltp:channel_layouts=stereo,volume=%.3f,"
                         "afade=t=in:st=0:d=%s,afade=t=out:st=%.3f:d=%s,adelay=%d:all=1[s%d]"
                         % (k, ins["src_in"], ins["src_in"] + d, rate, float(ins["volum"]), FADE, d - FADE,
                            FADE, ms, i))
            mixes.append("[s%d]" % i)
    maps = {"video": "[%s]" % last, "audio": None}
    if main["has_audio"]:
        if mixes:
            parts.append("[0:a]aresample=%d,aformat=sample_fmts=fltp:channel_layouts=stereo[m]" % rate)
            parts.append("[m]%samix=inputs=%d:duration=first:normalize=0[a]" % ("".join(mixes), len(mixes) + 1))
            maps["audio"] = "[a]"
        else:
            maps["audio"] = "0:a"
    return ";".join(parts), maps


def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def aplica(video, table, map_json, folder, out) -> dict:
    video, folder, out = Path(video), Path(folder), Path(out)
    keep = [(float(a), float(b)) for a, b in _load(map_json)["keep"]]
    rows = place(_rows(_load(table)), keep)
    if not rows:
        raise ValueError("tabelul B-roll e gol")
    main = _probe_full(video)
    warnings, inserts = [], []
    for r in rows:
        src = folder / r["src"]
        info = _probe_full(src)
        tm = tonemap_filter(color_transfer(src))
        if tm and not has_filter("zscale"):
            tm = ""
            if HDR_WARNING not in warnings:
                warnings.append(HDR_WARNING)
        inserts.append(dict(r, file=src, has_audio=info["has_audio"], tonemap=tm))
    graph, maps = build_filtergraph(main, inserts)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", video]
    for ins in inserts:
        cmd += ["-i", ins["file"]]
    cmd += ["-filter_complex", graph, "-map", maps["video"]]
    if maps["audio"]:
        cmd += ["-map", maps["audio"], "-c:a", "aac"]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out]
    out.parent.mkdir(parents=True, exist_ok=True)
    _run(cmd)
    res = {"inserts": len(inserts), "curat": str(out)}
    if warnings:
        res["warnings"] = warnings
    return res


# ------------------------------------------------------------ CLI

def _emit(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="broll.py", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("vorbit")
    p.add_argument("--dir", required=True)
    p = sub.add_parser("cadre")
    p.add_argument("--dir", required=True)
    p.add_argument("--frames-dir", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--exclude")
    p = sub.add_parser("verifica")
    p.add_argument("--broll", required=True)
    p.add_argument("--cuts", required=True)
    p.add_argument("--video", required=True)
    p.add_argument("--dir", required=True)
    p = sub.add_parser("aplica")
    p.add_argument("--video", required=True)
    p.add_argument("--broll", required=True)
    p.add_argument("--map", required=True)
    p.add_argument("--dir", required=True)
    p.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        if a.cmd == "vorbit":
            v = speaker(a.dir)
            _emit({"video": str(v) if v else None})
        elif a.cmd == "cadre":
            res = cadre(a.dir, a.frames_dir, a.exclude)
            Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
            _emit({"clips": len(res["clips"]), "skipped": [s["src"] for s in res["skipped"]], "out": a.out})
        elif a.cmd == "verifica":
            cuts = _load(a.cuts)
            cuts = cuts["cuts"] if isinstance(cuts, dict) else cuts
            clips = {p.name: _probe_full(p)["duration"] for p in list_clips(a.dir)}
            errors = verifica(_rows(_load(a.broll)), cuts, probe_duration(a.video), clips)
            if errors:
                _emit({"errors": errors})
                return 2
            _emit({"ok": True})
        else:
            _emit(aplica(a.video, a.broll, a.map, a.dir, a.out))
    except subprocess.CalledProcessError as e:
        _emit({"error": "ffmpeg a eșuat: %s" % (e.stderr or "")[-800:].strip(), "step": a.cmd})
        return 1
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        _emit({"error": str(e), "step": a.cmd})
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
