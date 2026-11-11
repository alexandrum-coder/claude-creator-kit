#!/usr/bin/env bash
# Generează clipul de test AirTime: 75 s, 1920x1080, testsrc2, cu voce de sinteză în română.
#   make_test_clip.sh OUT_DIR        (scrie "Antrenament spate – test ședință.mov" în OUT_DIR)
# Structura audio: explicație, o frază reluată, pauză de 1,5 s, explicație, gol de 12 s cu zgomot
# (demonstrația), reacția de după. Cere ffmpeg, ffprobe și `say` (macOS).
set -eu

OUT_DIR="${1:?Folosire: make_test_clip.sh OUT_DIR}"
mkdir -p "$OUT_DIR"
OUT="$OUT_DIR/Antrenament spate – test ședință.mov"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT

VOICE=()
if say -v '?' 2>/dev/null | grep -q '^Ioana'; then VOICE=(-v Ioana); fi
speak() { say ${VOICE[@]+"${VOICE[@]}"} -o "$1" "$2"; }

speak "$TMP/a1.aiff" "Bună ziua. Astăzi lucrăm spatele. Începem cu o explicație scurtă despre postura corectă. Umerii stau jos, coloana rămâne dreaptă, iar privirea merge înainte."
speak "$TMP/a2.aiff" "Trageți coatele spre spate și strângeți omoplații."
speak "$TMP/a3.aiff" "Trageți coatele spre spate, hai încă o dată, și strângeți bine omoplații."
speak "$TMP/a4.aiff" "Respirația rămâne calmă pe tot parcursul exercițiului, fără blocaje."
speak "$TMP/a4b.aiff" "Greșeala cea mai frecventă este ridicarea umerilor spre urechi. Dacă o observați, coborâți umerii și reluați mișcarea de la început, cu greutatea pe călcâie."
speak "$TMP/a4c.aiff" "Pentru început alegeți o greutate mică. Contează controlul mișcării, nu cât de mare este greutatea, iar spatele trebuie să rămână neutru."
speak "$TMP/a5.aiff" "Acum urmează demonstrația. Urmăriți mișcarea și nu vorbim în timpul ei."
speak "$TMP/a6.aiff" "Foarte bine. Se simte lucrul în mușchii spatelui, iar la final spatele rămâne relaxat."

# Gol de 12 s cu zgomot (demonstrația) și pauză de 1,5 s.
ffmpeg -y -loglevel error -f lavfi -i "anoisesrc=d=12:c=brown:a=0.05:r=44100" "$TMP/noise.aiff"
ffmpeg -y -loglevel error -f lavfi -i "anullsrc=r=44100:cl=mono" -t 1.5 "$TMP/pause15.aiff"
ffmpeg -y -loglevel error -f lavfi -i "anullsrc=r=44100:cl=mono" -t 0.8 "$TMP/pause08.aiff"
ffmpeg -y -loglevel error -f lavfi -i "anullsrc=r=44100:cl=mono" -t 1.0 "$TMP/pause10.aiff"

speak "$TMP/a7.aiff" "Încheiem cu câteva respirații lungi. Inspirați pe nas, expirați pe gură și lăsați brațele libere pe lângă corp. Dacă exersați de trei ori pe săptămână, veți observa curând o postură mai bună, iar durerile de spate scad."
speak "$TMP/a8.aiff" "Vă mulțumesc că ați lucrat împreună cu mine și ne vedem la următorul antrenament."

ORDER=(a1 pause10 a2 pause08 a3 pause10 a4 pause10 a4b pause10 a4c pause15 a5 noise a6 pause10 a7 pause10 a8)
INPUTS=(); FILTER=""; i=0
for n in "${ORDER[@]}"; do
  INPUTS+=(-i "$TMP/$n.aiff")
  FILTER="$FILTER[$i:a]aresample=44100,aformat=sample_fmts=fltp:channel_layouts=mono[s$i];"
  i=$((i + 1))
done
for ((k = 0; k < i; k++)); do FILTER="$FILTER[s$k]"; done
FILTER="${FILTER}concat=n=$i:v=0:a=1,apad[a]"
ffmpeg -y -loglevel error ${INPUTS[@]+"${INPUTS[@]}"} -filter_complex "$FILTER" -map "[a]" -t 75 "$TMP/audio.wav"

DUR="$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$TMP/audio.wav")"
echo "audio: $DUR s"

# HEVC cu VideoToolbox dacă există, altfel H.264 (libx264).
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q hevc_videotoolbox; then
  VCODEC=(-c:v hevc_videotoolbox -tag:v hvc1 -b:v 4M); echo "codec: hevc_videotoolbox"
else
  VCODEC=(-c:v libx264 -preset veryfast -crf 23); echo "codec: libx264"
fi
ffmpeg -y -loglevel error -f lavfi -i "testsrc2=size=1920x1080:rate=30:duration=75" -i "$TMP/audio.wav" \
  -map 0:v -map 1:a "${VCODEC[@]}" -pix_fmt yuv420p -c:a aac -b:a 160k -t 75 "$OUT"
echo "clip: $OUT"
ffprobe -v error -show_entries stream=codec_name,width,height:format=duration -of default=nw=1 "$OUT"
