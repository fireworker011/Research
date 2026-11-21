#!/usr/bin/env bash
# リッチメニューを Messaging API で登録し、デフォルトに付け替える。
# トークンは環境変数 LINE_CHANNEL_ACCESS_TOKEN だけを読む。このファイルには書かない。
# 一斉配信、Push、Broadcast は呼ばない。
# アカウントへの反映は、ナオミチが手元で実行するときだけ。リポジトリ作成時には実行していない。
set -euo pipefail

DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
TOKEN="${LINE_CHANNEL_ACCESS_TOKEN:-}"
if [[ -z "${TOKEN}" ]]; then
  echo "LINE_CHANNEL_ACCESS_TOKEN が空です。トークンはファイルに書かず、実行するときだけ環境変数に置いてください。" >&2
  exit 1
fi

JSON="${DIR}/richmenu.json"
IMAGE="${DIR}/richmenu.png"
if [[ ! -f "${JSON}" || ! -f "${IMAGE}" ]]; then
  echo "richmenu.json と richmenu.png を、このスクリプトと同じフォルダに置いてください。" >&2
  exit 1
fi

size=$(wc -c < "${IMAGE}" | tr -d ' ')
if (( size > 1048576 )); then
  echo "画像が1MBを超えています (${size} bytes)。PNGのまま1MB以下にしてから実行してください。" >&2
  exit 1
fi

case "${IMAGE}" in
  *.png) mime="image/png" ;;
  *.jpg | *.jpeg) mime="image/jpeg" ;;
  *)
    echo "画像は PNG か JPEG にしてください。" >&2
    exit 1
    ;;
esac

create_body=$(mktemp)
trap 'rm -f "${create_body}"' EXIT
http=$(curl -sS -o "${create_body}" -w "%{http_code}" \
  -X POST "https://api.line.me/v2/bot/richmenu" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  --data-binary @"${JSON}")
if [[ "${http}" != "200" ]]; then
  echo "メニューの作成に失敗しました。HTTP ${http}" >&2
  cat "${create_body}" >&2
  exit 1
fi

rich_id=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1], encoding="utf-8"))["richMenuId"])' "${create_body}")
rm -f "${create_body}"
trap - EXIT

upload_body=$(mktemp)
trap 'rm -f "${upload_body}"' EXIT
http=$(curl -sS -o "${upload_body}" -w "%{http_code}" \
  -X POST "https://api-data.line.me/v2/bot/richmenu/${rich_id}/content" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: ${mime}" \
  --data-binary @"${IMAGE}")
if [[ "${http}" != "200" ]]; then
  echo "画像のアップロードに失敗しました。HTTP ${http} richMenuId=${rich_id}" >&2
  cat "${upload_body}" >&2
  exit 1
fi
rm -f "${upload_body}"

default_body=$(mktemp)
http=$(curl -sS -o "${default_body}" -w "%{http_code}" \
  -X POST "https://api.line.me/v2/bot/user/all/richmenu/${rich_id}" \
  -H "Authorization: Bearer ${TOKEN}")
if [[ "${http}" != "200" ]]; then
  echo "デフォルトの付け替えに失敗しました。HTTP ${http} richMenuId=${rich_id}" >&2
  cat "${default_body}" >&2
  rm -f "${default_body}"
  exit 1
fi
rm -f "${default_body}"
trap - EXIT

echo "登録しました。richMenuId=${rich_id}"
echo "メッセージの配信はしていません。メニューを付け替えただけです。"
