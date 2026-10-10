"""キャラと小物の検索クエリ。背景はここには置かない。"""

from __future__ import annotations

# 1制作物で使うイラストの定義。背景（部屋・夜・オフィス・集中線・チャット）はコード描画。
ASSET_CATALOG: dict[str, dict] = {
    "hero_trouble": {
        "kind": "person",
        "who": "hero",
        "queries": ["困っているサラリーマン", "頭を抱える会社員"],
        "needles": ["困", "抱え", "サラリー", "会社", "男性"],
        "gender": "男性",
    },
    "hero_angry": {
        "kind": "person",
        "who": "hero",
        "queries": ["怒っているサラリーマン", "怒る会社員 男性"],
        "needles": ["怒", "会社", "サラリー", "男性"],
        "gender": "男性",
    },
    "hero_tired": {
        "kind": "person",
        "who": "hero",
        "queries": ["疲れたサラリーマン", "残業している男性"],
        "needles": ["疲", "残業", "サラリー", "男性"],
        "gender": "男性",
    },
    "hero_smile": {
        "kind": "person",
        "who": "hero",
        "queries": ["ガッツポーズのサラリーマン", "喜ぶ会社員 男性"],
        "needles": ["ガッツ", "喜", "笑", "サラリー", "会社", "男性"],
        "gender": "男性",
    },
    "rival_smug": {
        "kind": "person",
        "who": "rival",
        "queries": ["ニヤニヤする男性会社員", "得意気な顔の男性"],
        "needles": ["ニヤ", "得意", "会社", "男性"],
        "gender": "男性",
    },
    "rival_pale": {
        "kind": "person",
        "who": "rival",
        "queries": ["青ざめる男性", "焦っている男性"],
        "needles": ["青ざ", "焦", "男性"],
        "gender": "男性",
    },
    "rival_bow": {
        "kind": "person",
        "who": "rival",
        "queries": ["謝る男性 お辞儀", "土下座する男性"],
        "needles": ["謝", "辞儀", "土下座", "男性"],
        "gender": "男性",
    },
    "boss_angry": {
        "kind": "person",
        "who": "boss",
        "queries": ["怒る上司", "激怒する部長"],
        "needles": ["上司", "部長", "怒", "男性"],
        "gender": "男性",
    },
    "mug": {
        "kind": "prop",
        "who": "",
        "queries": ["マグカップのイラスト", "コーヒーカップ 食器"],
        "needles": ["マグ", "カップ", "食器"],
        "gender": "",
    },
}

VOICES = {
    "narrator": {
        "key": "metan",
        "style_id": 2,
        "credit": "VOICEVOX:四国めたん",
        "vvm": "0.vvm",
    },
    "hero": {
        "key": "kotarou",
        "style_id": 12,
        "angry_style_id": 34,
        "credit": "VOICEVOX:白上虎太郎",
        "vvm": "9.vvm",
    },
    "rival": {
        "key": "takehiro",
        "style_id": 11,
        "credit": "VOICEVOX:玄野武宏",
        "vvm": "4.vvm",
    },
    "boss": {
        "key": "kenzaki",
        "style_id": 21,
        "credit": "VOICEVOX:剣崎雌雄",
        "vvm": "4.vvm",
    },
}
