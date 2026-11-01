import os

if not globals().get("_H3_LOAD_ONLY"):
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
    if "release_runtime" not in globals() or "cancel_idle_timer" not in globals():
        raise RuntimeError("生成セルが未実行です。Drive の flush ができません。")
    cancel_idle_timer()
    print("合格のため、mp4 と制御 JSON を確認しました。Drive を flush してランタイムを削除します。")
    release_runtime()
