# 再生成するカットだけ書く。例: CUTS = ["C2"] または CUTS = ["C2", "C4"]
# Drive の prompts.json を読み直してから、そのカットだけ同じ出力フォルダへ書く。
CUTS = ["C2"]

if not globals().get("_H3_LOAD_ONLY"):
    try:
        if "cancel_idle_timer" not in globals() or "regenerate_cuts" not in globals():
            raise RuntimeError("生成セルが未実行です。上から順に実行してください。")
        if "load_scene_prompts" not in globals() or "CONTROL_DIR" not in globals():
            raise RuntimeError("セットアップセルが未実行です。")
        cancel_idle_timer()
        loaded = load_scene_prompts(CONTROL_DIR)
        print(f"prompts.json を Drive から読み直しました: {CONTROL_DIR}/prompts.json")
        print("再生成: " + ", ".join(str(item) for item in CUTS))
        regenerate_cuts(CUTS, loaded)
    except Exception as exc:
        print(f"再生成に失敗しました: {exc}", flush=True)
        print("Drive を flush してランタイムを削除します。", flush=True)
        try:
            release_runtime()
        except Exception as release_exc:
            print(f"ランタイム削除に失敗しました: {release_exc}", flush=True)
        raise
