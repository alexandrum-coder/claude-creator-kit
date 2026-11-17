#!/usr/bin/env python3
"""AirTime sfx: the two sound effects of the montage, generated with ffmpeg, never downloaded (PLAN, P2).

    sfx.py DIR       writes DIR/sfx_whoosh.wav and DIR/sfx_pop.wav and prints their paths as JSON

whoosh: pink noise with a fixed seed, band-passed at 1.8 kHz, sin(pi*t/0.35) envelope, 0.35 s. The sweep of
the plan is approximated by the envelope (PLAN, Nota 2.14, D-41).
pop: a 900 Hz sine with an exp(-40 t) decay, 0.08 s.
Both are 48 kHz mono pcm_s16le written with -bitexact, so two runs give the same bytes.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RATE = 48000
SOURCES = {
    "whoosh": "anoisesrc=d=0.35:c=pink:r=%d:a=0.9:seed=7,bandpass=f=1800:width_type=o:width=1.5,"
              "volume='sin(PI*t/0.35)':eval=frame,volume=2.4" % RATE,   # band-passing leaves -13.5 dBFS
    "pop": "aevalsrc='0.5*sin(2*PI*900*t)*exp(-40*t)':s=%d:d=0.08" % RATE,
}


def generate(folder) -> dict:
    """Write the effects into folder (created if needed); returns {kind: path}."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    out = {}
    for kind, src in SOURCES.items():
        path = folder / ("sfx_%s.wav" % kind)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", src, "-ac", "1",
                        "-ar", str(RATE), "-c:a", "pcm_s16le", "-fflags", "+bitexact", "-flags:a", "+bitexact",
                        "-map_metadata", "-1", str(path)], check=True, capture_output=True, text=True)
        out[kind] = path
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if len(argv) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    print(json.dumps({k: str(v) for k, v in generate(argv[0]).items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
