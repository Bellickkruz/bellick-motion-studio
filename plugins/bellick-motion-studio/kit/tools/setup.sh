#!/bin/bash
# Downloads the speech-recognition (Whisper small.en) and, with "voice", the Kokoro voice model from GitHub into ./models.
set -e
K="$(cd "$(dirname "$0")/.." && pwd)"; M="${KIT_MODELS:-$HOME/.motion-studio/models}"; mkdir -p "$M"; cd "$M"
get(){ for i in 1 2 3 4 5 6; do curl -sSL --retry 5 --retry-all-errors -C - -o "$2" "$1" && return 0; echo "retry $i for $2"; sleep 3; done; return 1; }
if [ ! -d sherpa-onnx-whisper-small.en ]; then
  get https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-whisper-small.en.tar.bz2 whisper.tar.bz2
  tar xjf whisper.tar.bz2 && rm whisper.tar.bz2
fi
if [ "$1" = "voice" ]; then
  [ -f kokoro-v1.0.onnx ] || get https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx kokoro-v1.0.onnx
  [ -f voices-v1.0.bin ] || get https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin voices-v1.0.bin
  cp "$K/tools/data/kokoro_config.json" .
fi
python3 -c "import onnxruntime, numpy; print('ok: onnxruntime + numpy present')"
ls "$M"
