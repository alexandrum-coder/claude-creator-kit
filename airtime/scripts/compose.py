#!/usr/bin/env python3
"""AirTime compose: put the branded intro in front of the cut clip, lay the
chapter and list overlays on top, and encode the final youtube.mp4.

    compose.py --curat curat.mp4 --render render.json --out youtube.mp4
    compose.py probe FILE

render.json is the JSON printed by render.mjs: {intro, overlays: [{file, t}]}.
Paths in it are relative to the render.json's own folder. Overlay times are
relative to the cut clip; they are shifted by the intro duration here.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

AUDIO_LAYOUT = "stereo"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, check=True, capture_output=True, text=True)


def _rate(text: str) -> float:
    num, _, den = (text or "0/1").partition("/")
    try:
        d = float(den) if den else 1.0
        return float(num) / d if d else 0.0
    except ValueError:
        return 0.0


def _probe_full(path) -> dict:
    r = _run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)])
    data = json.loads(r.stdout)
    streams = data.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise ValueError("no video stream in %s" % path)
    width, height = int(video["width"]), int(video["height"])
    rotation = 0
    for sd in video.get("side_data_list") or []:
        if "rotation" in sd:
            rotation = int(round(float(sd["rotation"])))
    rotation = rotation or int(float((video.get("tags") or {}).get("rotate", 0) or 0))
    if rotation % 180 != 0:
        width, height = height, width
    fps = _rate(video.get("avg_frame_rate", "")) or _rate(video.get("r_frame_rate", ""))
    duration = float((data.get("format") or {}).get("duration") or video.get("duration") or 0)
    sample_rate = next((int(s["sample_rate"]) for s in streams
                        if s.get("codec_type") == "audio" and s.get("sample_rate")), 0)
    return {
        "width": width,
        "height": height,
        "fps": fps,
        "duration": duration,
        "has_audio": any(s.get("codec_type") == "audio" for s in streams),
        "sample_rate": sample_rate,
    }


def probe(path) -> dict:
    """{width, height, fps, duration, has_audio} of a media file (display size, rotation applied)."""
    info = _probe_full(path)
    info.pop("sample_rate")
    return info


def _fps_text(fps: float) -> str:
    return ("%.3f" % fps).rstrip("0").rstrip(".")


def build_filtergraph(src: dict, intro: dict, overlays: list[dict], intro_duration: float):
    """Filtergraph (string) and output maps. Input 0 = cut clip, 1 = intro, 2.. = overlays."""
    w, h, fps = src["width"], src["height"], _fps_text(src["fps"])
    rate = src.get("sample_rate") or 48000
    parts = [
        "[0:v]fps=%s,setsar=1,format=yuv420p[sv]" % fps,
        "[1:v]scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2,"
        "fps=%s,setsar=1,format=yuv420p[iv]" % (w, h, w, h, fps),
    ]
    fmt = "aformat=sample_fmts=fltp:channel_layouts=%s" % AUDIO_LAYOUT
    if src["has_audio"]:
        parts.append("[0:a]aresample=%d,%s[sa]" % (rate, fmt))
    else:
        parts.append("anullsrc=r=%d:cl=%s,atrim=0:%.3f[sa]" % (rate, AUDIO_LAYOUT, src["duration"]))
    if intro["has_audio"]:
        parts.append("[1:a]aresample=%d,%s,atrim=0:%.3f[ia]" % (rate, fmt, intro_duration))
    else:
        parts.append("anullsrc=r=%d:cl=%s,atrim=0:%.3f[ia]" % (rate, AUDIO_LAYOUT, intro_duration))
    parts.append("[iv][ia][sv][sa]concat=n=2:v=1:a=1[cv][ca]")
    last = "cv"
    for i, ov in enumerate(overlays):
        k = i + 2
        at = float(ov["t"]) + intro_duration
        parts.append("[%d:v]scale=%d:%d,format=yuva420p,setpts=PTS-STARTPTS+%.3f/TB[o%d]" % (k, w, h, at, i))
        parts.append("[%s][o%d]overlay=eof_action=pass:format=auto[v%d]" % (last, i, i))
        last = "v%d" % i
    return ";".join(parts), {"video": "[%s]" % last, "audio": "[ca]"}


def _load_render(render_json: Path) -> tuple[Path, list[dict]]:
    spec = json.loads(Path(render_json).read_text(encoding="utf-8"))
    base = Path(render_json).resolve().parent

    def resolve(p: str) -> Path:
        q = Path(p)
        return q if q.is_absolute() else base / q

    overlays = [{"file": resolve(o["file"]), "t": float(o["t"])} for o in spec.get("overlays") or []]
    return resolve(spec["intro"]), sorted(overlays, key=lambda o: o["t"])


def compose(curat, render_json, out) -> Path:
    curat, out = Path(curat), Path(out)
    intro_path, overlays = _load_render(Path(render_json))
    src = _probe_full(curat)
    intro = _probe_full(intro_path)
    graph, maps = build_filtergraph(src, intro, overlays, intro["duration"])
    # Frame colour properties win over the encoder flags below, so set them in the graph too.
    graph += ";%ssetparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709[vout]" % maps["video"]
    maps = dict(maps, video="[vout]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(curat), "-i", str(intro_path)]
    for ov in overlays:
        cmd += ["-i", str(ov["file"])]
    cmd += ["-filter_complex", graph, "-map", maps["video"], "-map", maps["audio"],
            "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
            # youtube.mp4 is SDR: tag it bt709 explicitly, or ffmpeg copies a tag from one of the
            # inputs (an HLG curat.mp4 left untouched without zscale ended up as iec61966-2-1).
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        _run(cmd)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("ffmpeg a esuat:\n%s" % (e.stderr or "")[-1500:]) from e
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "probe":
        ap = argparse.ArgumentParser(prog="compose.py probe")
        ap.add_argument("file")
        a = ap.parse_args(argv[1:])
        print(json.dumps(probe(a.file), ensure_ascii=False))
        return 0
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--curat", required=True)
    ap.add_argument("--render", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        compose(a.curat, a.render, a.out)
    except (RuntimeError, OSError, ValueError, KeyError, subprocess.CalledProcessError) as e:
        print("Eroare: %s" % e, file=sys.stderr)
        return 1
    print(a.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
