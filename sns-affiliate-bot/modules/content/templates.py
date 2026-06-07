"""
各ジャンル × プラットフォーム × フック型のバズるテンプレートライブラリ。

リサーチ出典:
- TikTok 2026 Algorithm (Sprout Social / Hootsuite / Socialync)
- Instagram Reels Algorithm 2026 (Adam Mosseri confirmed signals)
- YouTube Shorts 2026 Best Practices (JoinBrands / Miraflow)
- 日本語バズパターン調査 (GOKKO Inc. / tenani.jp / Shopify JP)
"""

# ──────────────────────────────────────────────────────────────────────────────
# プラットフォーム別パラメータ
# ──────────────────────────────────────────────────────────────────────────────
PLATFORM_PARAMS = {
    "tiktok": {
        "display_name": "TikTok",
        "optimal_duration_sec": (21, 34),
        "scene_count": (5, 7),
        "sec_per_scene": (3, 5),
        "completion_target": 0.70,       # 70% 完走率がバズ閾値
        "top_signals": ["watch_time", "completion_rate", "shares", "comments"],
        "style_note": "テンポ速め・話し言葉・感情的・意外性重視",
        "posting_freq": "毎日〜週5本",
        "best_time_jst": "19:00-21:00",
    },
    "reels": {
        "display_name": "Instagram Reels",
        "optimal_duration_sec": (52, 78),
        "scene_count": (8, 12),
        "sec_per_scene": (5, 7),
        "completion_target": 0.65,
        "top_signals": ["dm_shares", "saves", "watch_time", "likes_per_reach"],
        "style_note": "ビジュアル重視・保存したくなる情報量・DM共有しやすい内容",
        "posting_freq": "週3〜5本",
        "best_time_jst": "20:00-22:00",
    },
    "shorts": {
        "display_name": "YouTube Shorts",
        "optimal_duration_sec": (28, 52),
        "scene_count": (6, 9),
        "sec_per_scene": (4, 6),
        "completion_target": 0.65,
        "top_signals": ["retention", "swipe_away_rate", "likes", "subscriptions"],
        "style_note": "検索ヒット性重視・情報密度高め・タイトルで内容が明確",
        "posting_freq": "週3〜5本",
        "best_time_jst": "12:00-14:00 / 20:00-22:00",
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# 5大フック型（全ジャンル共通）
# ──────────────────────────────────────────────────────────────────────────────
HOOK_TYPES = {
    "shock_fact": {
        "name": "衝撃事実型",
        "description": "常識を覆す数値・事実で掴む。完走率最高クラス。",
        "patterns": [
            "{topic}の90%は間違ってます",
            "{topic}を知らないのは損してます",
            "{topic}してると実は逆効果です",
            "プロが絶対やらない{topic}の失敗",
            "医師・専門家が警告する{topic}のNG",
        ],
    },
    "question": {
        "name": "疑問提起型",
        "description": "視聴者自身のことにさせる問いかけ。コメント誘発。",
        "patterns": [
            "あなたの{topic}、実は逆効果かもしれません",
            "なぜ{topic}を頑張っても結果が出ないのか",
            "{topic}してる人、それ本当に正しいですか？",
            "{topic}で失敗する人と成功する人の違い、わかりますか？",
            "あなたは{topic}について何割正解できますか？",
        ],
    },
    "before_after": {
        "name": "ビフォーアフター型",
        "description": "結果を先に見せてから理由・方法を語る。保存率高。",
        "patterns": [
            "{topic}を始めて{period}の変化がこれです",
            "{period}で{result}になれた{topic}の方法",
            "去年の私と今の私、{topic}で変わったこと",
            "{problem}だった私が{topic}で変われた話",
            "信じてもらえないけど{topic}でこうなりました",
        ],
    },
    "unexpected": {
        "name": "意外性型",
        "description": "予想を裏切る展開・意外な解法でスワイプを止める。",
        "patterns": [
            "100均の{item}が実は最強だった話",
            "まさかの{unexpected_method}で{result}できた",
            "誰も教えてくれなかった{topic}の裏技",
            "{expensive}じゃなくて{cheap}でよかった理由",
            "{common_belief}は実は嘘だった",
        ],
    },
    "empathy": {
        "name": "共感型",
        "description": "ターゲットの悩みに刺さる共感フック。DM共有されやすい。",
        "patterns": [
            "{problem}で悩んでる人、絶対に見てほしい",
            "{problem}あるある、わかる人いる？",
            "{problem}を経験した私だから言えること",
            "同じ{problem}で苦しんでる人へ",
            "{problem}の人が間違えがちなこと、全部解決します",
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# 5大コンテンツ構成（全プラットフォーム共通）
# ──────────────────────────────────────────────────────────────────────────────
CONTENT_FORMATS = {
    "delayed_reveal": {
        "name": "遅延開示型",
        "effect": "視聴完了率↑↑（最後まで見ないとわからない構造）",
        "structure": [
            "フック: 結果・答えをちらつかせる（でも見せない）",
            "展開1: 問題・背景の説明",
            "展開2: 解決のヒント（もったいぶる）",
            "展開3: 核心に近づく",
            "クライマックス: 答え・解決策の開示",
            "CTA: 保存・フォローを促す",
        ],
    },
    "controversy_loop": {
        "name": "論争ループ型",
        "effect": "コメント数↑↑・シェア↑（反論したくなる構造）",
        "structure": [
            "フック: 物議を醸す主張・断言",
            "展開1: 一般的な常識・反論を先に提示",
            "展開2: なぜその常識が間違いなのかの論拠",
            "展開3: 自分の主張の根拠・証拠",
            "まとめ: 「でも最終的には〇〇です」",
            "CTA: 「どう思う？コメントで教えて」",
        ],
    },
    "save_tutorial": {
        "name": "保存推奨チュートリアル型",
        "effect": "保存数↑↑・リプレイ↑（実用的な手順型）",
        "structure": [
            "フック: 「これ保存しておいて」宣言",
            "展開1: 必要なもの・準備",
            "展開2: ステップ1",
            "展開3: ステップ2",
            "展開4: ステップ3（最重要）",
            "結果: 完成・ビフォーアフター",
            "CTA: 「保存してあとで試してみて」",
        ],
    },
    "story_arc": {
        "name": "共感ストーリー型",
        "effect": "DMシェア↑↑・フォロー↑（感情移入させる物語）",
        "structure": [
            "フック: 共感できる悩み・状況の提示",
            "展開1: 「自分もそうだった」背景",
            "展開2: 転機・気づき",
            "展開3: 変化のプロセス",
            "クライマックス: 結果・現在の状態",
            "CTA: 「同じ経験した人はフォローして」",
        ],
    },
    "comparison": {
        "name": "比較検証型",
        "effect": "コメント↑・完走率↑（どっちが勝つか見たくなる）",
        "structure": [
            "フック: 「〇〇 vs △△、どっちが正解？」",
            "展開1: A案の紹介・実演",
            "展開2: B案の紹介・実演",
            "展開3: 比較結果（意外な勝者を演出）",
            "まとめ: 結論・おすすめ",
            "CTA: 「どっち派？コメントで」",
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# ジャンル別テンプレート
# ──────────────────────────────────────────────────────────────────────────────
GENRE_TEMPLATES = {

    "beauty": {
        "display_name": "美容・コスメ",
        "target": "20〜35歳女性、スキンケア・メイク・美肌に関心がある",
        "pain_points": [
            "毛穴・ニキビ・シミが気になる",
            "高い化粧品を使っても変化がない",
            "年齢とともに肌が変わってきた",
            "スキンケアの正しい順番・方法がわからない",
        ],
        "desires": [
            "お金をかけずにきれいになりたい",
            "プロみたいな肌になりたい",
            "若見えしたい",
            "毛穴レスな肌になりたい",
        ],
        "best_hooks": ["shock_fact", "before_after", "unexpected"],
        "best_formats": ["save_tutorial", "before_after", "comparison"],
        "best_platforms": ["reels", "tiktok"],
        "image_style": "clean beauty aesthetic, soft studio lighting, feminine, minimalist pastel",
        "hashtags_tiktok": ["#美容", "#スキンケア", "#コスメ", "#美肌", "#美容垢"],
        "hashtags_reels": ["#スキンケア", "#美容", "#コスメ", "#美肌", "#美白"],
        "hashtags_shorts": ["#スキンケア", "#美容", "#化粧品", "#美肌", "#コスメ"],
        "typical_hooks": [
            "このスキンケア順番、間違ってる人が多すぎます",
            "毛穴が消えたって言われる方法、ぜんぶ話します",
            "高い化粧品より効く100均アイテムを発見しました",
            "今すぐやめてほしい洗顔の間違い",
            "3ヶ月で肌が変わった話、聞いてほしい",
        ],
        "cta_patterns": [
            "詳しくはプロフィールのリンクをチェックしてね",
            "保存して後で試してみてください",
            "他にも美容情報発信してるのでフォローしてね",
        ],
    },

    "gadget": {
        "display_name": "ガジェット・テック",
        "target": "20〜40代男性中心、ガジェット・テクノロジーに関心",
        "pain_points": [
            "買って後悔したガジェットがある",
            "コスパのいい製品がわからない",
            "使いこなせていない機能がある",
            "新しい製品に乗り換えるべきか迷っている",
        ],
        "desires": [
            "生産性を上げたい",
            "コスパ最強のものを使いたい",
            "人より先に最新情報を知りたい",
            "生活を便利にしたい",
        ],
        "best_hooks": ["shock_fact", "unexpected", "question"],
        "best_formats": ["comparison", "save_tutorial", "delayed_reveal"],
        "best_platforms": ["tiktok", "shorts"],
        "image_style": "tech product showcase, dark background with accent lighting, high-tech minimal aesthetic",
        "hashtags_tiktok": ["#ガジェット", "#テック", "#iPhone", "#PC", "#便利グッズ"],
        "hashtags_reels": ["#ガジェット", "#テック", "#便利グッズ", "#iPhone", "#おすすめ"],
        "hashtags_shorts": ["#ガジェット", "#テック", "#便利グッズ", "#レビュー", "#おすすめ"],
        "typical_hooks": [
            "これを知らずにガジェット買ってたら損してます",
            "1万円以下なのに生産性が3倍になったアイテム",
            "Appleユーザーが気づいていない隠し機能があります",
            "ガジェットレビュアーが実際に使い続けてるものだけ紹介します",
            "買ってよかったガジェット vs 買って後悔したガジェット",
        ],
        "cta_patterns": [
            "商品リンクはプロフィールをチェックしてください",
            "保存して後で確認してみてください",
            "他にもガジェット情報発信中なのでフォローして",
        ],
    },

    "lifehack": {
        "display_name": "ライフハック・節約",
        "target": "20〜40代、時間・お金・生活の効率化に関心がある",
        "pain_points": [
            "時間が足りない、忙しい",
            "お金が貯まらない",
            "家事が面倒・時間がかかる",
            "もっと効率よく生きたい",
        ],
        "desires": [
            "時間を節約したい",
            "お金を節約したい",
            "生活をもっと楽にしたい",
            "知らなかった便利技を知りたい",
        ],
        "best_hooks": ["shock_fact", "unexpected", "empathy"],
        "best_formats": ["save_tutorial", "comparison", "story_arc"],
        "best_platforms": ["tiktok", "shorts", "reels"],
        "image_style": "clean organized home, lifestyle aesthetic, warm natural lighting, practical everyday items",
        "hashtags_tiktok": ["#ライフハック", "#節約", "#時短", "#便利", "#生活の知恵"],
        "hashtags_reels": ["#ライフハック", "#節約術", "#時短", "#便利グッズ", "#生活"],
        "hashtags_shorts": ["#ライフハック", "#節約", "#時短テク", "#便利", "#生活術"],
        "typical_hooks": [
            "これだけで月3万節約できます",
            "家事の時間を半分にする方法があります",
            "知らないと損する節約技5選",
            "100均で買えるのに高いやつより使える",
            "主婦が10年かけて気づいた家事の時短術",
        ],
        "cta_patterns": [
            "保存して実践してみてください",
            "他にも節約・時短情報を発信中なのでフォローして",
            "詳しいリストはプロフィールのリンクから",
        ],
    },

    "marriage": {
        "display_name": "婚活・恋愛",
        "target": "25〜38歳女性中心、マッチングアプリ・婚活に取り組んでいる",
        "pain_points": [
            "マッチングアプリで結果が出ない",
            "いい人に会えない",
            "告白や関係継続が難しい",
            "婚活疲れを感じている",
        ],
        "desires": [
            "理想のパートナーに出会いたい",
            "婚活を効率よく進めたい",
            "成功した人の方法を知りたい",
            "同じ境遇の人に共感したい",
        ],
        "best_hooks": ["empathy", "shock_fact", "before_after"],
        "best_formats": ["story_arc", "delayed_reveal", "save_tutorial"],
        "best_platforms": ["tiktok", "reels"],
        "image_style": "romantic soft aesthetic, couple silhouette, warm bokeh lighting, feminine pastel tones",
        "hashtags_tiktok": ["#婚活", "#マッチングアプリ", "#30代婚活", "#婚活女子", "#恋愛"],
        "hashtags_reels": ["#婚活", "#マッチングアプリ", "#婚活女子", "#恋愛", "#結婚"],
        "hashtags_shorts": ["#婚活", "#マッチングアプリ", "#恋愛", "#結婚", "#婚活女子"],
        "typical_hooks": [
            "マッチングアプリ3年やって気づいた本音を話します",
            "婚活で絶対やってはいけないこと、わかりますか？",
            "34歳でやっと結婚できた私が6年間失敗し続けた理由",
            "婚活で200人に会って気づいた出会いの真実",
            "婚活エージェントに言われた一言で人生が変わった話",
        ],
        "cta_patterns": [
            "詳しい婚活方法はプロフィールのリンクから",
            "同じ経験した人はフォローしてください",
            "保存して婚活の参考にしてください",
        ],
    },

    "sidehustle": {
        "display_name": "副業・マネー",
        "target": "20〜40代、収入増・副業開始に関心がある",
        "pain_points": [
            "収入が増えない",
            "副業を始めたいけど何をすれば良いかわからない",
            "本業が忙しくて時間がない",
            "詐欺的な副業情報に不信感がある",
        ],
        "desires": [
            "月収を増やしたい",
            "会社に依存しない収入が欲しい",
            "スキマ時間で稼ぎたい",
            "本当に稼げる方法を知りたい",
        ],
        "best_hooks": ["shock_fact", "before_after", "question"],
        "best_formats": ["delayed_reveal", "story_arc", "save_tutorial"],
        "best_platforms": ["tiktok", "shorts"],
        "image_style": "professional home office setup, financial success aesthetic, laptop and graphs, clean modern",
        "hashtags_tiktok": ["#副業", "#在宅ワーク", "#副業初心者", "#稼ぐ方法", "#マネー"],
        "hashtags_reels": ["#副業", "#在宅ワーク", "#副業おすすめ", "#お金", "#稼ぐ"],
        "hashtags_shorts": ["#副業", "#在宅ワーク", "#副業初心者", "#稼げる", "#マネー"],
        "typical_hooks": [
            "先月スマホだけで副業収入が〇万円になった話",
            "副業で失敗する人の共通点があります",
            "フォロワー100人でも月5万稼げる副業があります",
            "会社にバレずに副業する方法を教えます",
            "副業を3年やって気づいた本当に稼げる方法と稼げない方法",
        ],
        "cta_patterns": [
            "詳しい方法はプロフィールのリンクから",
            "他にも副業情報を発信中なのでフォローして",
            "保存して後で実践してみてください",
        ],
    },

    "diet": {
        "display_name": "ダイエット・健康",
        "target": "20〜40代女性中心、ダイエット・体型維持に取り組んでいる",
        "pain_points": [
            "痩せたいのにリバウンドする",
            "食事制限が続かない",
            "運動する時間がない",
            "年齢とともに太りやすくなった",
        ],
        "desires": [
            "理想の体型になりたい",
            "無理なく痩せたい",
            "食事を我慢せずに痩せたい",
            "リバウンドしない方法を知りたい",
        ],
        "best_hooks": ["before_after", "shock_fact", "unexpected"],
        "best_formats": ["story_arc", "save_tutorial", "comparison"],
        "best_platforms": ["reels", "tiktok"],
        "image_style": "healthy lifestyle aesthetic, fresh vegetables and fitness, bright natural light, aspirational",
        "hashtags_tiktok": ["#ダイエット", "#痩せる方法", "#ダイエット記録", "#糖質制限", "#ダイエット女子"],
        "hashtags_reels": ["#ダイエット", "#痩せた", "#ダイエット方法", "#食事管理", "#ダイエット記録"],
        "hashtags_shorts": ["#ダイエット", "#痩せる", "#ダイエット方法", "#健康", "#糖質制限"],
        "typical_hooks": [
            "3ヶ月で8kg痩せた方法、全部話します",
            "ダイエットで逆に太る食べ物があります",
            "運動ゼロで痩せた話、信じてもらえない",
            "食事制限なしで体重が落ちた理由がわかった",
            "リバウンドを繰り返してた私が変わったきっかけ",
        ],
        "cta_patterns": [
            "詳しい食事・運動プランはプロフィールのリンクから",
            "保存して実践してみてください",
            "他にもダイエット情報を発信中なのでフォローして",
        ],
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# ジャンル別アフィリエイト設定
# ──────────────────────────────────────────────────────────────────────────────
AFFILIATE_CONFIG = {
    "beauty":    {"platform": "楽天/Amazon", "category": "スキンケア・コスメ"},
    "gadget":    {"platform": "楽天/Amazon", "category": "ガジェット・電子機器"},
    "lifehack":  {"platform": "楽天/Amazon", "category": "便利グッズ・日用品"},
    "marriage":  {"platform": "A8.net",      "category": "婚活・結婚相談所"},
    "sidehustle":{"platform": "A8.net",      "category": "副業・投資スクール"},
    "diet":      {"platform": "楽天/Amazon", "category": "サプリ・ダイエット食品"},
}
