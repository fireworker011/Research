#!/usr/bin/env bash
# 下書きは mp4 を書き出さない。PCに渡すのは cuts-for-pc.md。
# 使い方: bash animatics/20261104-night/make.sh
# これは何も焼き込まない。終了コード 0 は「書き出さなかった」という意味。
set -euo pipefail
ROOT=$(cd "$(dirname "$0")" && pwd)
if [[ ! -f "$ROOT/cuts-for-pc.md" ]]; then
  echo "cuts-for-pc.md が無い" >&2
  exit 1
fi
echo "mp4は書き出していない。PCに渡すファイル: $ROOT/cuts-for-pc.md"
exit 0
