#!/usr/bin/env python3
"""AirTime reels: wrapper over the unmodified claude-shorts scripts.

Pipeline for `build`: snap_boundaries.py -> clip_NN.mp4 with ffmpeg -c copy ->
reframe.json -> render.mjs (cleaned captions) -> export.sh --platform instagram.

reframe.json format (read at claude-shorts a369fad, scripts/compute_reframe.py):
{
  "content_type": "talking-head",
  "clip_count": 1,
  "clips": {
    "clip_01.mp4": {
      "strategy": "face-track",              # vertical source: "full-frame"
      "source_resolution": "1920x1080",      # "WxH" of the clip
      "crop": {"x": 656, "y": 0, "w": 607, "h": 1080},
      "output_resolution": "1080x1920",
      "face_positions": [],
      "duration": 12.5,
      "crop_keyframes": [{"t": 0.0, "x": 800}]   # optional
    }
  }
}
Note: clips are cut with `ffmpeg -c copy` (as claude-shorts itself does), so a
cut snaps to the previous keyframe and may start slightly early; Task 10
measures the drift on real footage.
render.mjs reads clips[name].crop, .crop_keyframes (optional) and
.source_resolution. For a vertical source the crop is the whole frame:
{"x": 0, "y": 0, "w": W, "h": H}.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

FILLERS = ("ăă", "ăăă", "îî", "îîî", "mmm", "hmm", "ăm")
STYLES = ("bold", "bounce", "clean")
ORIENTATIONS = ("horizontal", "vertical")


class StepError(RuntimeError):
    def __init__(self, step: str, detail: str):
        super().__init__(f"{step}: {detail}")
        self.step = step
        self.detail = detail


# ------------------------------------------------------------ locations

def shorts_root() -> Path:
    candidates = []
    if os.environ.get("SHORTS_ROOT"):
        candidates.append(Path(os.environ["SHORTS_ROOT"]))
    if os.environ.get("CLAUDE_CONFIG_DIR"):
        candidates.append(Path(os.environ["CLAUDE_CONFIG_DIR"]) / "skills" / "shorts")
    candidates.append(Path.home() / ".claude" / "skills" / "shorts")
    for c in candidates:
        if c.exists():
            return c
    return candidates[-1]


def shorts_python() -> Path:
    paths = [Path.home() / ".video-skill" / "bin" / "python3",
             Path.home() / ".shorts-skill" / "bin" / "python3"]
    for p in paths:
        if p.exists():
            return p
    return paths[-1]


# ----------------------------------------------------------- subprocess

def run_step(step: str, args: list, cwd=None) -> str:
    try:
        r = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                           cwd=str(cwd) if cwd else None)
    except OSError as e:
        raise StepError(step, str(e))
    if r.returncode != 0:
        tail = "\n".join((r.stderr or r.stdout or "").strip().splitlines()[-15:])
        raise StepError(step, f"exit {r.returncode}: {tail}")
    return r.stdout


def probe(path) -> tuple:
    out = run_step("ffprobe", ["ffprobe", "-v", "error", "-select_streams", "v:0",
                               "-show_entries", "stream=width,height:format=duration",
                               "-of", "json", path])
    data = json.loads(out)
    st = data["streams"][0]
    return int(st["width"]), int(st["height"]), float(data.get("format", {}).get("duration", 0))


# ------------------------------------------------------------ transcribe

def transcribe(video, out, model) -> Path:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    run_step("transcribe", [shorts_python(), shorts_root() / "scripts" / "transcribe.py",
                            video, "--output", out, "--model", model])
    if not out.exists():
        raise StepError("transcribe", f"no output written at {out}")
    return out


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    return re.sub(r"[^\w]", "", text)


def clean_captions(transcript: dict, fillers=FILLERS) -> dict:
    drop = {_norm(f) for f in fillers}
    out = copy.deepcopy(transcript)
    out["captions"] = [c for c in out.get("captions") or []
                       if _norm(str(c.get("text", ""))) not in drop]
    return out


# --------------------------------------------------------------- reframe

def vertical_entry(w: int, h: int, duration: float) -> dict:
    return {
        "strategy": "full-frame",
        "source_resolution": f"{w}x{h}",
        "crop": {"x": 0, "y": 0, "w": w, "h": h},
        "output_resolution": "1080x1920",
        "face_positions": [],
        "duration": round(duration, 2),
    }


def write_vertical_reframe(clips_dir, out) -> Path:
    clips = {}
    for clip in sorted(Path(clips_dir).glob("clip_*.mp4")):
        w, h, dur = probe(clip)
        clips[clip.name] = vertical_entry(w, h, dur)
    data = {"content_type": "vertical", "clip_count": len(clips), "clips": clips}
    out = Path(out)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out


# ----------------------------------------------------------------- build

def build(curat, transcript_curat, approved, style, out_dir, orientation) -> list:
    if style not in STYLES:
        raise StepError("build", f"unknown style {style}")
    if orientation not in ORIENTATIONS:
        raise StepError("build", f"unknown orientation {orientation}")
    root = shorts_root()
    py = shorts_python()
    out_dir = Path(out_dir)
    work = out_dir / "work"
    clips_dir = work / "clips"
    render_dir = work / "render"
    clips_dir.mkdir(parents=True, exist_ok=True)
    render_dir.mkdir(parents=True, exist_ok=True)
    # stale files from an earlier run must never be mistaken for new results
    for stale in list(clips_dir.glob("clip_*.mp4")) + list(render_dir.glob("short_*.mp4")) \
            + list(out_dir.glob("short_*_ig.mp4")):
        stale.unlink()

    snapped = work / "snapped_segments.json"
    run_step("snap_boundaries", [py, root / "scripts" / "snap_boundaries.py",
                                 "--segments", approved, "--transcript", transcript_curat,
                                 "--input-video", curat, "--output", snapped])
    segments = json.loads(snapped.read_text(encoding="utf-8"))["segments"]

    for i, seg in enumerate(segments, 1):
        sid = seg.get("id", i)
        clip = clips_dir / f"clip_{int(sid):02d}.mp4"
        run_step("extract_clip", ["ffmpeg", "-y", "-ss", f"{float(seg['start']):.3f}",
                                  "-to", f"{float(seg['end']):.3f}", "-i", curat,
                                  "-c", "copy", clip])

    reframe = work / "reframe.json"
    if orientation == "horizontal":
        run_step("compute_reframe", [py, root / "scripts" / "compute_reframe.py",
                                     "--clips-dir", clips_dir, "--content-type", "talking-head",
                                     "--output", reframe])
    else:
        write_vertical_reframe(clips_dir, reframe)

    captions = work / "captions.json"
    cleaned = clean_captions(json.loads(Path(transcript_curat).read_text(encoding="utf-8")))
    captions.write_text(json.dumps(cleaned, ensure_ascii=False), encoding="utf-8")
    run_step("render", ["node", root / "remotion" / "render.mjs",
                        "--segments", snapped, "--reframe", reframe, "--captions", captions,
                        "--clips-dir", clips_dir, "--style", style, "--output-dir", render_dir],
             cwd=root / "remotion")
    rendered = sorted(render_dir.glob("short_*.mp4"))
    if len(rendered) != len(segments):
        raise StepError("render", f"expected {len(segments)} rendered reels, found {len(rendered)}")

    run_step("export", ["bash", root / "scripts" / "export.sh", "--input-dir", render_dir,
                        "--platform", "instagram", "--output-dir", out_dir, "--force"])
    exported = sorted(out_dir.glob("short_*_ig.mp4"))
    if len(exported) != len(segments):
        raise StepError("export", f"expected {len(segments)} exported reels, found {len(exported)}")
    return exported


# ------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="AirTime reels via claude-shorts")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcribe")
    t.add_argument("--video", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--model", default="large-v3")
    b = sub.add_parser("build")
    b.add_argument("--curat", required=True)
    b.add_argument("--transcript", required=True)
    b.add_argument("--approved", required=True)
    b.add_argument("--style", choices=STYLES, default="bold")
    b.add_argument("--orientation", choices=ORIENTATIONS, default="horizontal")
    b.add_argument("--out", required=True)
    args = p.parse_args(argv)
    try:
        if args.cmd == "transcribe":
            res = {"transcript": str(transcribe(args.video, args.out, args.model))}
        else:
            paths = build(args.curat, args.transcript, args.approved, args.style,
                          args.out, args.orientation)
            res = {"reels": [str(x) for x in paths]}
    except StepError as e:
        print(json.dumps({"error": str(e), "step": e.step}, ensure_ascii=False))
        return 1
    except (OSError, ValueError, KeyError, IndexError, TypeError) as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}, ensure_ascii=False))
        return 1
    print(json.dumps(res, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
