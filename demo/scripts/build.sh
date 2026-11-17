#!/usr/bin/env bash
# Reproduce el video de ejemplo (Taskflow) de principio a fin.
# Uso:  cd demo && bash scripts/build.sh
set -euo pipefail
cd "$(dirname "$0")/.."

# 1. Dependencias
pip install -q kokoro-onnx soundfile numpy scipy pillow
command -v ffmpeg >/dev/null || { echo "Falta ffmpeg"; exit 1; }

# 2. Modelo de voz Kokoro (Apache 2.0)
mkdir -p models build
BASE=https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0
[ -f models/kokoro-v1.0.int8.onnx ] || curl -sSL -o models/kokoro-v1.0.int8.onnx $BASE/kokoro-v1.0.int8.onnx
[ -f models/voices-v1.0.bin ]       || curl -sSL -o models/voices-v1.0.bin       $BASE/voices-v1.0.bin

# 3. Grabación de pantalla sintética (app ficticia, con errores a propósito)
python3 scripts/make_recording.py

# 4. Portada, steps y cierre (necesita la fuente Inter instalada)
python3 scripts/compose.py

# 5. Unión con transiciones + 1,5 s congelados al final
ffmpeg -loglevel error -y -i build/cover.mp4 -i build/step1.mp4 -i build/step2.mp4 -i build/step3.mp4 -i build/closing.mp4 \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.45:offset=2.55[a];\
[a][2:v]xfade=transition=smoothleft:duration=0.6:offset=15.7[b];\
[b][3:v]xfade=transition=smoothleft:duration=0.6:offset=26.25[c];\
[c][4:v]xfade=transition=fade:duration=0.5:offset=36.95,tpad=stop_mode=clone:stop_duration=1.5,format=yuv420p[v]" \
  -map "[v]" -r 30 -c:v libx264 -preset slow -crf 20 build/video.mp4

# 6. Voz y música
python3 scripts/voice.py
python3 scripts/music.py
ffmpeg -loglevel error -y -i build/music.wav -af loudnorm=I=-22:TP=-2:LRA=11 -ar 44100 build/music22.wav

# 7. Mezcla final (música -22 LUFS, voz -16 LUFS, sidechain)
ffmpeg -loglevel error -y -i build/video.mp4 -i build/music22.wav -i build/voice.wav -filter_complex \
  "[2:a]aresample=44100,apad,loudnorm=I=-16:TP=-1.5:LRA=11,asplit=2[v1][v2];[1:a][v1]sidechaincompress=threshold=0.03:ratio=4:attack=60:release=500:makeup=1[m];[m][v2]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.9[a]" \
  -map 0:v -map "[a]" -c:v libx264 -crf 20 -c:a aac -b:a 192k -shortest build/final.mp4

echo "Listo: demo/build/final.mp4"
