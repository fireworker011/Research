import os

from google.colab import runtime

if not globals().get("GENERATION_DONE"):
    raise RuntimeError(
        "生成が終わっていないので、ランタイムは切断しません。失敗したセルの出力を確認してください。"
    )
paths = list(globals().get("OUTPUT_MP4S") or []) + list(globals().get("OUTPUT_JSONS") or [])
if not paths:
    raise RuntimeError("出力パスが空なので、ランタイムは切断しません。")
for path in paths:
    if not os.path.isfile(path) or os.path.getsize(path) == 0:
        raise RuntimeError(f"出力が無いので、ランタイムは切断しません: {path}")
print("mp4 と制御 JSON を確認しました。ランタイムを切断して削除します。")
runtime.unassign()
