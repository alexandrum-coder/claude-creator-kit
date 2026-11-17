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

# A reel that renders longer than this is stuck (e.g. Remotion hanging while it unzips
# Chrome Headless Shell); fail loudly instead of waiting forever.
RENDER_TIMEOUT_PER_REEL = 600

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

def run_step(step: str, args: list, cwd=None, timeout=None) -> str:
    try:
        r = subprocess.run([str(a) for a in args], capture_output=True, text=True,
                           cwd=str(cwd) if cwd else None, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise StepError(step, f"nu a terminat în {timeout // 60} minute; procesul pare blocat "
                              "(la randare: Chrome Headless Shell, vezi AIRTIME-INSTALL.md#probleme)")
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

def transcribe(video, out, model, language=None) -> Path:
    """AirTime's own transcribe.py (no PyAV) with the claude-shorts Python."""
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    args = [shorts_python(), Path(__file__).with_name("transcribe.py"),
            video, "--output", out, "--model", model]
    if language:
        args += ["--language", language]
    run_step("transcribe", args)
    if not out.exists():
        raise StepError("transcribe", f"no output written at {out}")
    return out


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFC", text.lower())
    return re.sub(r"[^\w]", "", text)


def has_words(transcript: dict) -> bool:
    return any(seg.get("words") for seg in transcript.get("segments") or [])


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


def center_entry(w: int, h: int, duration: float) -> dict:
    """Same crop as claude-shorts compute_crop_center: 9:16, full height, centred."""
    crop_w = min(int(h * 9 / 16), w)
    return {
        "strategy": "center",
        "source_resolution": f"{w}x{h}",
        "crop": {"x": (w - crop_w) // 2, "y": 0, "w": crop_w, "h": h},
        "output_resolution": "1080x1920",
        "face_positions": [],
        "duration": round(duration, 2),
    }


def write_center_reframe(clips_dir, out) -> Path:
    """Fallback when compute_reframe fails (e.g. a mediapipe without mp.solutions)."""
    clips = {}
    for clip in sorted(Path(clips_dir).glob("clip_*.mp4")):
        w, h, dur = probe(clip)
        clips[clip.name] = center_entry(w, h, dur)
    data = {"content_type": "talking-head", "clip_count": len(clips), "clips": clips}
    out = Path(out)
    out.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return out


# ---------------------------------------------------------------- export

def export_reels(root, render_dir, out_dir, expected: int) -> list:
    """Run claude-shorts export.sh. At a369fad it ends with GNU `paste -sd ','`, which BSD
    paste on macOS rejects: the script writes every short_*_ig.mp4 and then exits 1. A failed
    export is accepted only when exactly `expected` non-empty files exist and each one probes."""
    out_dir = Path(out_dir)
    try:
        run_step("export", ["bash", Path(root) / "scripts" / "export.sh", "--input-dir", render_dir,
                            "--platform", "instagram", "--output-dir", out_dir, "--force"])
        failed = None
    except StepError as e:
        failed = e
    exported = sorted(out_dir.glob("short_*_ig.mp4"))
    if failed is not None:
        if len(exported) != expected or any(p.stat().st_size == 0 for p in exported):
            raise failed
        for p in exported:
            try:
                if probe(p)[2] <= 0:
                    raise failed
            except StepError:
                raise failed
        # nothing for the coach to act on: logged on stderr, not added to `warnings`
        print(f"export: export.sh failed after writing all {expected} files ({failed.detail.splitlines()[0]}); "
              "files probed and kept", file=sys.stderr)
    if len(exported) != expected:
        raise StepError("export", f"expected {expected} exported reels, found {len(exported)}")
    return exported


# ----------------------------------------------------------------- build

def build(curat, transcript_curat, approved, style, out_dir, orientation, warnings=None, cta_word=None) -> list:
    if warnings is None:
        warnings = []
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
    if has_words(json.loads(Path(transcript_curat).read_text(encoding="utf-8"))):
        run_step("snap_boundaries", [py, root / "scripts" / "snap_boundaries.py",
                                     "--segments", approved, "--transcript", transcript_curat,
                                     "--input-video", curat, "--output", snapped])
    else:
        # no speech: snap_boundaries.py exits 1 without word timestamps; keep the approved times
        snapped.write_text(Path(approved).read_text(encoding="utf-8"), encoding="utf-8")
    segments = json.loads(snapped.read_text(encoding="utf-8"))["segments"]
    # D-86: impact times are counted from the approved start; follow the start snap_boundaries moved
    if any(seg.get("impact") is not None for seg in segments):
        import reels_fx
        starts = {int(s.get("id", i)): s.get("start")
                  for i, s in enumerate(json.loads(Path(approved).read_text(encoding="utf-8"))["segments"], 1)}
        for i, seg in enumerate(segments, 1):
            sid = int(seg.get("id", i))
            if seg.get("impact") is None or starts.get(sid) is None:
                continue
            delta = float(starts[sid]) - float(seg["start"])
            seg["impact"] = reels_fx.shift_impact(seg["impact"], delta, float(seg["end"]) - float(seg["start"]),
                                                  warnings, sid)
            if seg["impact"] == [] and delta:
                del seg["impact"]

    for i, seg in enumerate(segments, 1):
        sid = seg.get("id", i)
        clip = clips_dir / f"clip_{int(sid):02d}.mp4"
        if seg.get("pushin") is not None:
            # element 2 (PLAN, D-39): cut into clips_src/, zoom into clips/; reels.py globs clips/clip_*.mp4
            import montaj
            import reels_fx
            try:
                scale = montaj.pushin_scale(seg["pushin"])
            except ValueError as e:
                raise StepError("pushin", f"segmentul {sid}: {e}")
            raw = work / "clips_src" / clip.name
            raw.parent.mkdir(parents=True, exist_ok=True)
            run_step("extract_clip", ["ffmpeg", "-y", "-ss", f"{float(seg['start']):.3f}",
                                      "-to", f"{float(seg['end']):.3f}", "-i", curat, "-c", "copy", raw])
            run_step("pushin", reels_fx.pushin_args(raw, clip, scale, reels_fx.probe(raw, run_step)))
            continue
        run_step("extract_clip", ["ffmpeg", "-y", "-ss", f"{float(seg['start']):.3f}",
                                  "-to", f"{float(seg['end']):.3f}", "-i", curat,
                                  "-c", "copy", clip])

    reframe = work / "reframe.json"
    if orientation == "horizontal":
        try:
            run_step("compute_reframe", [py, root / "scripts" / "compute_reframe.py",
                                         "--clips-dir", clips_dir, "--content-type", "talking-head",
                                         "--output", reframe])
        except StepError:
            write_center_reframe(clips_dir, reframe)
            warnings.append("Urmărirea feței nu a mers; reels-urile folosesc cadrul din centru.")
    else:
        write_vertical_reframe(clips_dir, reframe)

    captions = work / "captions.json"
    cleaned = clean_captions(json.loads(Path(transcript_curat).read_text(encoding="utf-8")))
    captions.write_text(json.dumps(cleaned, ensure_ascii=False), encoding="utf-8")
    run_step("render", ["node", root / "remotion" / "render.mjs",
                        "--segments", snapped, "--reframe", reframe, "--captions", captions,
                        "--clips-dir", clips_dir, "--style", style, "--output-dir", render_dir],
             cwd=root / "remotion", timeout=RENDER_TIMEOUT_PER_REEL * max(1, len(segments)))
    rendered = sorted(render_dir.glob("short_*.mp4"))
    if len(rendered) != len(segments):
        raise StepError("render", f"expected {len(segments)} rendered reels, found {len(rendered)}")

    listed = [(i, seg) for i, seg in enumerate(segments, 1) if seg.get("list") is not None]
    with_cta = [(i, seg) for i, seg in enumerate(segments, 1) if seg.get("cta") is not None]
    with_impact = [(i, seg) for i, seg in enumerate(segments, 1) if seg.get("impact") is not None]
    with_hook = [(i, seg) for i, seg in enumerate(segments, 1) if seg.get("result_hook") is not None]
    if listed or with_cta or with_impact or with_hook:
        import airtime_config
        import reels_fx
        remotion_dir = airtime_config.home() / "remotion"
        # element 4 (PLAN, D-52): the CTA word of each segment, decided before the list gives way to it
        cta_words = {}
        for i, seg in with_cta:
            sid = int(seg.get("id", i))
            try:
                word = reels_fx.resolve_cta_word(seg["cta"], cta_word, warnings, sid)
            except ValueError as e:
                raise StepError("cta", f"segmentul {sid}: {e}")
            if word is not None:
                cta_words[sid] = word
        # element 3 (PLAN, D-48): numbered list over short_NN.mp4, between render and export
        words = [w for s in json.loads(Path(transcript_curat).read_text(encoding="utf-8")).get("segments") or []
                 for w in s.get("words") or []] if listed else []
        for i, seg in listed:
            sid = int(seg.get("id", i))
            try:
                reels_fx.apply_list(seg, sid, render_dir / f"short_{sid:02d}.mp4", words, work, run_step,
                                    warnings, remotion_dir, cta=seg["cta"] if sid in cta_words else None)
            except reels_fx.CtaError as e:
                raise StepError("cta", f"segmentul {sid}: {e}")
            except ValueError as e:
                raise StepError("list", f"segmentul {sid}: {e}")
        # element 4 (PLAN, D-54): the CTA keyword from from_s to the last frame
        for i, seg in with_cta:
            sid = int(seg.get("id", i))
            if sid not in cta_words:
                continue
            try:
                reels_fx.apply_cta(seg, sid, render_dir / f"short_{sid:02d}.mp4", cta_words[sid], work, run_step,
                                   remotion_dir)
            except ValueError as e:
                raise StepError("cta", f"segmentul {sid}: {e}")
        # element 5 (PLAN, D-62, D-63): impact captions, a difference blend after the list and the CTA
        for i, seg in with_impact:
            sid = int(seg.get("id", i))
            try:
                reels_fx.apply_impact(seg, sid, render_dir / f"short_{sid:02d}.mp4", work, run_step, remotion_dir)
            except ValueError as e:
                raise StepError("impact", f"segmentul {sid}: {e}")
        # element 7 (PLAN, D-67, D-70): the result hook is the last pass, so the reel opens on its finished ending
        for i, seg in with_hook:
            sid = int(seg.get("id", i))
            try:
                reels_fx.apply_hook(seg, sid, render_dir / f"short_{sid:02d}.mp4", work, run_step)
            except ValueError as e:
                raise StepError("result_hook", f"segmentul {sid}: {e}")

    return export_reels(root, render_dir, out_dir, len(segments))


# ------------------------------------------------------------------- CLI

def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="AirTime reels via claude-shorts")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("transcribe")
    t.add_argument("--video", required=True)
    t.add_argument("--out", required=True)
    t.add_argument("--model", default="medium")
    t.add_argument("--language", default=None)
    b = sub.add_parser("build")
    b.add_argument("--curat", required=True)
    b.add_argument("--transcript", required=True)
    b.add_argument("--approved", required=True)
    b.add_argument("--style", choices=STYLES, default="bold")
    b.add_argument("--orientation", choices=ORIENTATIONS, default="horizontal")
    b.add_argument("--out", required=True)
    b.add_argument("--cta-word", default=None,
                   help="CTA word for segments whose cta has no word (the first profile keyword)")
    args = p.parse_args(argv)
    try:
        if args.cmd == "transcribe":
            res = {"transcript": str(transcribe(args.video, args.out, args.model, args.language))}
        else:
            warnings = []
            paths = build(args.curat, args.transcript, args.approved, args.style,
                          args.out, args.orientation, warnings=warnings, cta_word=args.cta_word)
            res = {"reels": [str(x) for x in paths]}
            if warnings:
                res["warnings"] = warnings
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
