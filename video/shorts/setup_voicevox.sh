#!/usr/bin/env bash
# VOICEVOX engine の Linux CPU 版を 127.0.0.1:50021 で起動し、生存を確認する。
# 公式の Linux CPU 版。docker があるときは cpu イメージを使う。
# 有料契約はしない。投稿はしない。
set -euo pipefail

PORT=50021
BASE="http://127.0.0.1:${PORT}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CACHE="${VOICEVOX_CACHE:-/tmp/voicevox-engine}"
VERSION="0.26.1"
ASSET="voicevox_engine-linux-cpu-x64-${VERSION}.7z.001"
URL="https://github.com/VOICEVOX/voicevox_engine/releases/download/${VERSION}/${ASSET}"
FFMPEG_URL="https://github.com/FFmpeg-Builds/FFmpeg-Builds/releases/download/autobuild-2026-11-09-12-42/ffmpeg-n8.1.3-34-ga35157abb9-linux64-gpl-8.1.tar.xz"
FFMPEG_DIR="${FFMPEG_DIR:-/tmp/ffmpeg-static}"

install_ffmpeg() {
  local bin="${FFMPEG_DIR}/ffmpeg"
  if [[ -x "$bin" ]]; then
    echo "PASS ffmpeg $("$bin" -version | head -1)"
    echo "URL ${FFMPEG_URL}"
    return 0
  fi
  mkdir -p "$FFMPEG_DIR"
  echo "静的ビルドを取る: ${FFMPEG_URL}"
  curl -fL --retry 3 -o "${FFMPEG_DIR}/ffmpeg.tar.xz" "$FFMPEG_URL"
  tar -xJf "${FFMPEG_DIR}/ffmpeg.tar.xz" -C "$FFMPEG_DIR"
  local found
  found="$(find "$FFMPEG_DIR" -type f -path '*/bin/ffmpeg' | head -1)"
  local probe
  probe="$(find "$FFMPEG_DIR" -type f -path '*/bin/ffprobe' | head -1)"
  ln -sfn "$found" "${FFMPEG_DIR}/ffmpeg"
  ln -sfn "$probe" "${FFMPEG_DIR}/ffprobe"
  echo "PASS ffmpeg $("${FFMPEG_DIR}/ffmpeg" -version | head -1)"
  echo "URL ${FFMPEG_URL}"
}

install_ffmpeg

health() {
  curl -fsS --max-time 3 "${BASE}/version" 2>/dev/null || true
}

if [[ -n "$(health)" ]]; then
  echo "PASS 生存確認 ${BASE}/version $(health)"
  exit 0
fi

if command -v docker >/dev/null 2>&1; then
  docker rm -f voicevox-engine >/dev/null 2>&1 || true
  docker run -d --name voicevox-engine --rm -p "127.0.0.1:${PORT}:50021" voicevox/voicevox_engine:cpu-latest
else
  mkdir -p "$CACHE"
  archive="${CACHE}/${ASSET}"
  if [[ ! -f "$archive" ]]; then
    echo "公式の Linux CPU 版を取る: ${URL}"
    curl -fL --retry 3 -o "$archive" "$URL"
  fi
  if [[ ! -x "${CACHE}/run" && ! -x "${CACHE}/voicevox_engine/run" ]]; then
    (cd "$CACHE" && 7z x -y "$archive")
  fi
  run=""
  if [[ -x "${CACHE}/run" ]]; then
    run="${CACHE}/run"
  else
    run="$(find "$CACHE" -type f -name run -perm -u+x | head -1 || true)"
  fi
  if [[ -z "$run" ]]; then
    echo "FAIL 展開後に run が無い"
    exit 1
  fi
  nohup "$run" --host 127.0.0.1 --port "$PORT" >"${CACHE}/engine.log" 2>&1 &
  echo $! >"${CACHE}/engine.pid"
fi

for _ in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if [[ -n "$(health)" ]]; then
    echo "PASS 生存確認 ${BASE}/version $(health)"
    exit 0
  fi
  sleep 3
done

echo "FAIL 50021 が応答しない"
exit 1
