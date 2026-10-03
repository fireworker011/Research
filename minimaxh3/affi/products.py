"""This week's products. Facts are the 2026-10-03 runs. Unknowns stay 不明."""

from __future__ import annotations

from typing import Any

# Landing URLs are not copied into prompts or inbox jobs.
PRODUCTS: dict[str, dict[str, Any]] = {
    "kanetora": {
        "id": "kanetora",
        "genre": "pet_food",
        "pattern_id": "introduce",
        "display": "ドッグフードおさかな（金虎）",
        "a8_id": "s00000022193001",
        "a8_status": "提携中",
        "landing_url": "不明",
        "landing_note": "提携中。リンク文字列は台本フィクスチャにあり、inbox には入れない。",
        "names_in_video": ("おさかな", "金虎"),
        "fact": "原材料の先頭は魚介類（まぐろ、かつお、かつお節、かつおエキス）。出典は2026-09-30に保存した金虎の公開ページ。",
    },
    "orbis": {
        "id": "orbis",
        "genre": "beauty_skincare",
        "pattern_id": "buy_before",
        "display": "オルビスユー ドット",
        "a8_id": "s00000008657021",
        "a8_status": "提携中",
        "landing_url": "不明",
        "landing_note": "2026-10-03の実測は提携中のみ。リンク先URLの記録は無い。",
        "names_in_video": ("オルビス", "ユードット", "ユー ドット", "ORBIS", "orbis"),
        "fact": "シリーズのFAQは無香料。医薬部外品の効能（美白・シミ・ハリ・エイジング・浸透・有効成分）は言わない。",
    },
    "furbo": {
        "id": "furbo",
        "genre": "pet_camera",
        "pattern_id": "missing_on_camera",
        "display": "Furbo 360°ビュー",
        "a8_id": "s00000017737001",
        "a8_status": "提携中",
        "landing_url": "不明",
        "landing_note": "トップページから360°の商品ページへ転送されるかは不明。",
        "names_in_video": ("Furbo", "furbo", "ファーボ"),
        "fact": "公式商品ページの機能比較はカメラ単体で回転360°ビュー。死角ゼロ・自動追尾・おやつは言わない。",
    },
}

GENRES = ("beauty_skincare", "pet_food", "pet_camera")
PLATFORMS = ("youtube", "tiktok", "instagram")
