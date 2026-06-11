"""
generator.py - 直道・紀子キャラクター台本 & 画像生成プロンプト 自動生成エンジン

キャラクター設定:
  直道（なおみち）: 40代中盤・元清掃員。AI×ビジネス構造設計で脱出した努力家。泥臭い失敗談も包み隠さず話す。
  紀子（のりこ）:   直道のビジネスパートナー。冷静・論理的。仕組み化ロジックとA8案件への動線を提示。
"""

import os
import json
import logging
import re
from datetime import datetime
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
TRENDS_DIR = BASE_DIR / "data" / "trends"
OUTPUTS_DIR = BASE_DIR / "data" / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────
# キャラクター設定（システムプロンプト用）
# ──────────────────────────────────────────

CHARACTER_SYSTEM_PROMPT = """
あなたはYouTubeショート・縦型マンガ動画の台本作家です。以下のキャラクターで掛け合い台本を生成します。

【直道（なおみち）】
- 40代中盤の元清掃員。現場労働20年で体が限界に近づき、副業を模索し始めた
- AIツールとビジネス構造設計を独学で習得し、清掃業から月収50万超のデジタルビジネスへ転換
- 口調: 関西弁混じりの親しみやすい口語。「正直なあ...」「昔の俺はホンマにアホやった」など
- 感情豊か。失敗談を笑いに変えながらも、本音で語る泥臭さが視聴者に刺さる
- 弱みも見せる。でも諦めない姿勢が伝わる

【紀子（のりこ）】
- 直道のビジネスパートナー。元コンサルタント、現在フリーランス
- 冷静・論理的・的確。直道の感情論を数字とフレームワークで整理する
- 口調: 丁寧語だが歯切れよく「ポイントはここです」「つまり、構造として」など
- 直道の失敗を"鋭く"分析し、本質的な仕組みを提示する役割
- A8案件（転職・AIスクール・副業ツール等）への動線を自然に提示する

【関係性】
- 直道が感情・体験を語り、紀子がそれを構造化・解決策化する「感情×論理」のコンビ
- 掛け合いにより視聴者が「自分ごと」として引き込まれる
"""

# 画像生成プロンプトの品質呪文
IMAGE_QUALITY_SPELLS = {
    "positive_base": (
        "masterpiece, best quality, ultra-detailed, 8k wallpaper, "
        "anime style, cute characters, vibrant colors, clean lineart, "
        "professional illustration, dynamic composition"
    ),
    "negative_base": (
        "lowres, bad anatomy, bad hands, text, error, missing fingers, "
        "extra digit, fewer digits, cropped, worst quality, low quality, "
        "normal quality, jpeg artifacts, signature, watermark, username, blurry, "
        "bad proportions, deformed, ugly, duplicate, morbid, mutilated"
    ),
    "character_naomichi": (
        "middle-aged japanese man, 40s, slightly tired eyes but warm smile, "
        "work clothes or casual shirt, stocky build, kind expression"
    ),
    "character_noriko": (
        "japanese woman, 30s, professional suit or smart casual, "
        "glasses optional, confident posture, analytical expression"
    ),
}


class ContentGenerator:
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key and not demo_mode:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY が設定されていません。\n"
                "  デモ実行: python generator.py --demo"
            )
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    # ──────────────────────────────────────────
    # 1. パターンデータ読み込み
    # ──────────────────────────────────────────

    def load_pattern(self, pattern_path: Path | None = None) -> dict:
        """latest_pattern.json を読み込む"""
        if pattern_path is None:
            pattern_path = TRENDS_DIR / "latest_pattern.json"

        if not pattern_path.exists():
            raise FileNotFoundError(
                f"パターンファイルが見つかりません: {pattern_path}\n"
                "先に researcher.py を実行してください。"
            )

        with open(pattern_path, encoding="utf-8") as f:
            pattern = json.load(f)
        logger.info(f"パターン読み込み完了: {pattern_path}")
        return pattern

    # ──────────────────────────────────────────
    # 2. 台本 & 画像プロンプト生成
    # ──────────────────────────────────────────

    def _demo_script(self, pattern: dict) -> dict:
        """デモ用サンプル台本データ（APIキー不要）"""
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d%H%M")
        neg = IMAGE_QUALITY_SPELLS["negative_base"]
        qual = IMAGE_QUALITY_SPELLS["positive_base"]
        naomichi = IMAGE_QUALITY_SPELLS["character_naomichi"]
        noriko = IMAGE_QUALITY_SPELLS["character_noriko"]

        return {
            "content_id": ts,
            "title": "40代元清掃員がAIで月8万稼いだ3ステップ",
            "hook_text": "資格ゼロでも副業できた理由",
            "target_audience": "30〜50代の会社員・副業に興味があるが何から始めるか分からない人",
            "total_duration_seconds": 52,
            "scenes": [
                {
                    "scene_number": 1,
                    "duration_seconds": 5,
                    "speaker": "直道",
                    "emotion": "焦り・自己嫌悪",
                    "dialogue": "正直なあ…清掃の仕事しながら副業しようとして、3回失敗したんよ。",
                    "action": "汗をぬぐいながら苦笑いする。作業着姿。",
                    "screen_text": "副業3回失敗した男の話",
                    "image_prompt": {
                        "positive": f"{qual}, {naomichi}, janitor uniform, sweating, self-deprecating smile, messy break room background, warm indoor lighting, vertical composition",
                        "negative": neg,
                        "aspect_ratio": "9:16",
                        "style_note": "愛嬌あるアニメ風・汗のコミカル表現あり"
                    }
                },
                {
                    "scene_number": 2,
                    "duration_seconds": 8,
                    "speaker": "紀子",
                    "emotion": "冷静・分析的",
                    "dialogue": "直道さん、失敗した理由はシンプルです。『型』を知らずに動いていたから。",
                    "action": "ホワイトボードに「型」と大きく書きながら振り返る。",
                    "screen_text": "失敗の本当の原因",
                    "image_prompt": {
                        "positive": f"{qual}, {noriko}, professional setting, whiteboard with japanese text, pointer in hand, confident smile, clean modern office background",
                        "negative": neg,
                        "aspect_ratio": "9:16",
                        "style_note": "清潔感のあるビジネスシーン・論理的な表情"
                    }
                },
                {
                    "scene_number": 3,
                    "duration_seconds": 12,
                    "speaker": "直道",
                    "emotion": "熱量・共感",
                    "dialogue": "そう！リサーチ→型→自動化、この3ステップだけ。俺でも3ヶ月でできたんやから。",
                    "action": "指を3本立てながら熱く語る。目がキラキラしている。",
                    "screen_text": "3ステップだけ",
                    "image_prompt": {
                        "positive": f"{qual}, {naomichi}, casual shirt, three fingers raised, excited expression, bright eyes, home office background with laptop, motivational atmosphere",
                        "negative": neg,
                        "aspect_ratio": "9:16",
                        "style_note": "エネルギッシュな表情・明るい在宅環境"
                    }
                },
                {
                    "scene_number": 4,
                    "duration_seconds": 10,
                    "speaker": "紀子",
                    "emotion": "解説・真剣",
                    "dialogue": "特にAIツールと組み合わせると、作業時間が10分の1になります。具体的には概要欄のリンクで解説しています。",
                    "action": "スマートフォンを見せながら、画面を指差す。",
                    "screen_text": "作業時間→90%削減",
                    "image_prompt": {
                        "positive": f"{qual}, {noriko}, holding smartphone showing screen, pointing at phone display, informative expression, soft gradient background, clean composition",
                        "negative": neg,
                        "aspect_ratio": "9:16",
                        "style_note": "スマホ画面が見えるUI紹介シーン"
                    }
                },
                {
                    "scene_number": 5,
                    "duration_seconds": 7,
                    "speaker": "直道",
                    "emotion": "感謝・喜び",
                    "dialogue": "概要欄に無料チェックリストも入れてるから、まず自分のスキルを棚卸ししてみて！",
                    "action": "カメラに向かって親指を立てて笑顔。",
                    "screen_text": "👇概要欄を今すぐチェック",
                    "image_prompt": {
                        "positive": f"{qual}, {naomichi}, thumbs up gesture, big warm smile, direct eye contact with camera, bright background, encouraging atmosphere, close-up portrait",
                        "negative": neg,
                        "aspect_ratio": "9:16",
                        "style_note": "視聴者への語りかけ・フレンドリーな表情"
                    }
                },
                {
                    "scene_number": 6,
                    "duration_seconds": 10,
                    "speaker": "ナレーション",
                    "emotion": "締め・信頼感",
                    "dialogue": "直道と紀子が実践した副業の型は、概要欄の【無料診断】でチェックできます。",
                    "action": "二人が並んで微笑んでいるエンディングカット。",
                    "screen_text": "フォロー＆概要欄チェック！",
                    "image_prompt": {
                        "positive": f"{qual}, {naomichi} and {noriko}, side by side, both smiling warmly, team portrait, office background, professional yet friendly atmosphere, duo shot",
                        "negative": neg,
                        "aspect_ratio": "9:16",
                        "style_note": "エンディングカット・二人のキャラクターが並ぶ"
                    }
                }
            ],
            "affiliate_section": {
                "placement": "シーン4の後",
                "product_category": "転職・AIスクール・副業ツール（A8.net案件）",
                "natural_transition": "「紀子さんが実際に使ったAIスクール、概要欄にリンク貼っておきました」",
                "cta_text": "👇【無料】今すぐ副業適性チェック（A8案件リンク）\n📚 直道が使ったAIツール一覧はこちら\n🎁 登録特典：副業ロードマップPDF無料プレゼント",
                "hashtags": ["#AI副業", "#転職", "#副業初心者", "#在宅ワーク", "#SNSアフィリエイト", "#YouTubeショート", "#スキルアップ", "#仕組み収入"]
            },
            "thumbnail_concept": {
                "text_overlay": "元清掃員が3ヶ月で月＋8万",
                "image_prompt": f"{qual}, {naomichi}, shocked happy expression, money flying around, before-after composition, bold red japanese text overlay space, dramatic lighting, eye-catching thumbnail style",
                "color_scheme": "赤×黄×白のコントラスト強め。直道の表情を大きく"
            },
            "seo_metadata": {
                "youtube_title": "【副業】40代元清掃員がAIで月8万稼いだ3ステップを全公開",
                "description_template": "▼ 無料副業適性チェックはこちら\n[A8_LINK]\n\n直道が実践したAI副業の3ステップを解説。\n資格なし・スキルゼロから始められる方法です。\n\n▼ 関連動画\n• AIツール使い方入門\n• SNSマネタイズの始め方\n\n#AI副業 #転職 #副業初心者",
                "tags": ["AI副業", "副業初心者", "在宅ワーク", "転職", "SNSアフィリエイト", "ChatGPT副業", "スキルアップ", "仕組み収入", "YouTubeショート", "40代副業"]
            }
        }

    def generate_script(self, pattern: dict) -> dict:
        """
        トレンドパターンに基づき、直道・紀子の台本と画像プロンプトを生成
        """
        viral = pattern.get("viral_structure", {})
        keywords = pattern.get("trending_keywords", [])
        affiliate_angles = pattern.get("a8_affiliate_angles", [])
        formats = pattern.get("top_performing_formats", [])

        best_format = formats[0] if formats else {}
        affiliate_main = affiliate_angles[0] if affiliate_angles else {}

        prompt = f"""
{CHARACTER_SYSTEM_PROMPT}

【今回使用するトレンドパターン】
- トレンドキーワード: {', '.join(keywords[:6])}
- 最強フック型: {viral.get('hook', '')}
- 感情トリガー: {pattern.get('emotion_triggers', [])}
- 今週の推奨テーマ: {pattern.get('content_calendar_tip', 'AI副業で月5万を最速達成する方法')}
- 推奨フォーマット: {best_format.get('format_name', '失敗→逆転型')} - {best_format.get('why_it_works', '')}
- A8アフィリエイト訴求: {affiliate_main.get('category', '転職・AIスクール')} / {affiliate_main.get('angle', '')}

【生成要件】
以下のJSON形式で、縦型ショート動画（45〜60秒想定）の完全な制作パッケージを生成してください。
コードブロック（```json）で囲んでください。

```json
{{
  "content_id": "生成日時ベースのID（YYYYMMDDHHmm形式）",
  "title": "動画タイトル（30文字以内、SEO最適化済み）",
  "hook_text": "最初の3秒で表示するテキスト（インパクト重視、20文字以内）",
  "target_audience": "ターゲット視聴者の説明",
  "total_duration_seconds": 数値,
  "scenes": [
    {{
      "scene_number": 1,
      "duration_seconds": 数値,
      "speaker": "直道 or 紀子 or ナレーション",
      "emotion": "感情状態（例: 焦り、驚き、納得、熱量）",
      "dialogue": "セリフ（自然な口語体）",
      "action": "キャラクターの動作・表情の説明",
      "screen_text": "画面に表示するテキストオーバーレイ（あれば）",
      "image_prompt": {{
        "positive": "Stable Diffusion/Midjourney用 英語プロンプト（品質呪文込み）",
        "negative": "ネガティブプロンプト",
        "aspect_ratio": "9:16",
        "style_note": "スタイル補足（アニメ風、ビジネスシーン等）"
      }}
    }}
  ],
  "affiliate_section": {{
    "placement": "どのシーンの後に入れるか",
    "product_category": "商品カテゴリ",
    "natural_transition": "台本からアフィリエイトへの自然な橋渡しセリフ",
    "cta_text": "概要欄・ショッピングリンクへの誘導テキスト",
    "hashtags": ["#ハッシュタグ1", ...（8個）]
  }},
  "thumbnail_concept": {{
    "text_overlay": "サムネイルに入れる文字",
    "image_prompt": "サムネイル用画像生成プロンプト（英語）",
    "color_scheme": "カラースキームの説明"
  }},
  "seo_metadata": {{
    "youtube_title": "YouTube投稿用タイトル",
    "description_template": "概要欄テンプレート（アフィリエイトリンク挿入箇所を[A8_LINK]で示す）",
    "tags": ["タグ1", ...（10個）]
  }}
}}
```

【重要】
- 台本は直道と紀子の自然な掛け合いで構成（最低4シーン）
- 直道は1〜2個の具体的な失敗エピソードを短く語る
- 紀子は構造的解決策を提示し、自然にA8案件へ誘導
- 画像プロンプトは各シーンに必ず含め、品質呪文を標準装備
- 全体で視聴完了率を高める「引き」を各シーンに入れること
"""
        if self.demo_mode:
            logger.info("デモモード: サンプル台本を使用")
            return self._demo_script(pattern)

        logger.info("Claude で台本・画像プロンプト生成中...")
        message = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            system=CHARACTER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text

        # JSONブロックを抽出
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            script_data = json.loads(json_match.group(1))
        else:
            script_data = json.loads(response_text)

        # 画像品質呪文を確実に付与
        script_data = self._enhance_image_prompts(script_data)

        logger.info("台本生成完了")
        return script_data

    def _enhance_image_prompts(self, script_data: dict) -> dict:
        """各シーンの画像プロンプトに品質呪文を確実に付与"""
        quality_base = IMAGE_QUALITY_SPELLS["positive_base"]
        neg_base = IMAGE_QUALITY_SPELLS["negative_base"]

        for scene in script_data.get("scenes", []):
            ip = scene.get("image_prompt", {})
            if ip:
                pos = ip.get("positive", "")
                if quality_base.split(",")[0].strip() not in pos:
                    ip["positive"] = f"{quality_base}, {pos}"
                neg = ip.get("negative", "")
                if neg_base.split(",")[0].strip() not in neg:
                    ip["negative"] = f"{neg_base}, {neg}"

        # サムネイル用も強化
        thumb = script_data.get("thumbnail_concept", {})
        if thumb.get("image_prompt"):
            tp = thumb["image_prompt"]
            if quality_base.split(",")[0].strip() not in tp:
                thumb["image_prompt"] = f"{quality_base}, {tp}"

        return script_data

    # ──────────────────────────────────────────
    # 3. 出力フォーマット & 保存
    # ──────────────────────────────────────────

    def save_output(self, script_data: dict) -> dict[str, Path]:
        """生成結果をJSON・Markdownで保存"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        content_id = script_data.get("content_id", ts)

        output_dir = OUTPUTS_DIR / content_id
        output_dir.mkdir(parents=True, exist_ok=True)

        # JSON保存
        json_path = output_dir / "script_data.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(script_data, f, ensure_ascii=False, indent=2)

        # Markdown台本保存（制作チームが読みやすい形式）
        md_path = output_dir / "script_readable.md"
        md_content = self._format_markdown(script_data)
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(md_content)

        # 画像プロンプトのみ抽出して保存
        prompts_path = output_dir / "image_prompts.txt"
        prompts_content = self._extract_image_prompts(script_data)
        with open(prompts_path, "w", encoding="utf-8") as f:
            f.write(prompts_content)

        logger.info(f"出力完了: {output_dir}")
        return {"json": json_path, "markdown": md_path, "prompts": prompts_path, "dir": output_dir}

    def _format_markdown(self, data: dict) -> str:
        """人間が読みやすいMarkdown台本を生成"""
        lines = []
        lines.append(f"# {data.get('title', '無題')}")
        lines.append(f"\n**Content ID:** `{data.get('content_id', '')}`")
        lines.append(f"**ターゲット:** {data.get('target_audience', '')}")
        lines.append(f"**尺:** {data.get('total_duration_seconds', '?')}秒")
        lines.append(f"\n## フック（最初3秒）\n> {data.get('hook_text', '')}")

        lines.append("\n## 台本\n")
        for scene in data.get("scenes", []):
            spk = scene.get("speaker", "")
            emo = scene.get("emotion", "")
            dlg = scene.get("dialogue", "")
            act = scene.get("action", "")
            st = scene.get("screen_text", "")
            dur = scene.get("duration_seconds", "?")

            lines.append(f"### シーン {scene.get('scene_number', '?')} （{dur}秒）")
            lines.append(f"**{spk}** *[{emo}]*")
            lines.append(f"\n「{dlg}」")
            if act:
                lines.append(f"\n*（{act}）*")
            if st:
                lines.append(f"\n**テキストオーバーレイ:** `{st}`")

            ip = scene.get("image_prompt", {})
            if ip:
                lines.append(f"\n**🎨 画像プロンプト（Positive）:**")
                lines.append(f"```\n{ip.get('positive', '')}\n```")
                lines.append(f"**🚫 Negative:**")
                lines.append(f"```\n{ip.get('negative', '')}\n```")
            lines.append("")

        aff = data.get("affiliate_section", {})
        if aff:
            lines.append("## アフィリエイト導線")
            lines.append(f"- **商品カテゴリ:** {aff.get('product_category', '')}")
            lines.append(f"- **橋渡しセリフ:** 「{aff.get('natural_transition', '')}」")
            lines.append(f"- **CTA:** {aff.get('cta_text', '')}")
            lines.append(f"- **ハッシュタグ:** {' '.join(aff.get('hashtags', []))}")

        thumb = data.get("thumbnail_concept", {})
        if thumb:
            lines.append("\n## サムネイルコンセプト")
            lines.append(f"- **テキスト:** {thumb.get('text_overlay', '')}")
            lines.append(f"- **カラー:** {thumb.get('color_scheme', '')}")
            lines.append(f"- **プロンプト:**\n```\n{thumb.get('image_prompt', '')}\n```")

        seo = data.get("seo_metadata", {})
        if seo:
            lines.append("\n## SEOメタデータ")
            lines.append(f"**YouTube タイトル:** {seo.get('youtube_title', '')}")
            lines.append(f"\n**概要欄テンプレート:**\n```\n{seo.get('description_template', '')}\n```")
            lines.append(f"\n**タグ:** {', '.join(seo.get('tags', []))}")

        return "\n".join(lines)

    def _extract_image_prompts(self, data: dict) -> str:
        """全シーンの画像プロンプトをまとめて出力（SD/MJにコピペ可能形式）"""
        lines = [f"# 画像生成プロンプト集 - {data.get('title', '')}", ""]

        for scene in data.get("scenes", []):
            n = scene.get("scene_number", "?")
            spk = scene.get("speaker", "")
            ip = scene.get("image_prompt", {})
            if ip:
                lines.append(f"## Scene {n} ({spk})")
                lines.append(f"### Positive Prompt")
                lines.append(ip.get("positive", ""))
                lines.append(f"\n### Negative Prompt")
                lines.append(ip.get("negative", ""))
                lines.append(f"\n**Aspect Ratio:** {ip.get('aspect_ratio', '9:16')}")
                lines.append(f"**Style Note:** {ip.get('style_note', '')}")
                lines.append("")

        thumb = data.get("thumbnail_concept", {})
        if thumb and thumb.get("image_prompt"):
            lines.append("## サムネイル")
            lines.append(thumb["image_prompt"])

        return "\n".join(lines)

    # ──────────────────────────────────────────
    # 4. メイン実行フロー
    # ──────────────────────────────────────────

    def run(self, pattern_path: Path | None = None, demo: bool = False) -> dict:
        """フル生成パイプラインを実行"""
        if demo:
            self.demo_mode = True
        logger.info("=" * 60)
        logger.info("コンテンツ生成エンジン起動 - 直道＆紀子の台本生成")
        logger.info("=" * 60)

        pattern = self.load_pattern(pattern_path)
        script_data = self.generate_script(pattern)
        output_paths = self.save_output(script_data)

        logger.info("=" * 60)
        logger.info("生成完了!")
        logger.info(f"  台本JSON:     {output_paths['json']}")
        logger.info(f"  Markdown台本: {output_paths['markdown']}")
        logger.info(f"  画像プロンプト: {output_paths['prompts']}")
        logger.info("=" * 60)

        return {"script": script_data, "paths": {k: str(v) for k, v in output_paths.items()}}


# ──────────────────────────────────────────
# CLI エントリポイント
# ──────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="直道・紀子コンテンツ生成エンジン")
    parser.add_argument("--pattern", type=Path, default=None, help="パターンJSONファイルのパス")
    parser.add_argument("--demo", action="store_true", help="APIキー不要のデモモード")
    args = parser.parse_args()

    generator = ContentGenerator(demo_mode=args.demo)
    result = generator.run(pattern_path=args.pattern)
    script = result["script"]

    print(f"\n【生成完了】")
    print(f"タイトル: {script.get('title')}")
    print(f"フック: {script.get('hook_text')}")
    print(f"シーン数: {len(script.get('scenes', []))}")
    print(f"出力先: {result['paths']['dir']}")
