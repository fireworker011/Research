"""
Content Generation Module — ScriptGenerator

リサーチ済みのバズるテンプレートを使い、LLM でジャンル別ショート動画台本を量産する。

出力 JSON は VideoGenerator.generate() に直接渡せる形式。

使い方:
  gen = ScriptGenerator()
  script = gen.generate(genre="beauty", platform="tiktok")
  # → VideoGenerator().generate(script)
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

from anthropic import Anthropic

from .templates import (
    AFFILIATE_CONFIG,
    CONTENT_FORMATS,
    GENRE_TEMPLATES,
    HOOK_TYPES,
    PLATFORM_PARAMS,
)

_MODEL = "claude-haiku-4-5-20251001"    # コスト効率重視（量産用）
_QUALITY_MODEL = "claude-sonnet-4-6"    # 高品質版（重要コンテンツ用）


class ScriptGenerator:
    """
    ジャンル × プラットフォーム × フック型から動画台本を自動生成する。

    Args:
        quality: "fast"（haiku・低コスト）or "high"（sonnet・高品質）
    """

    def __init__(self, quality: str = "fast"):
        self.client = Anthropic()
        self.model = _QUALITY_MODEL if quality == "high" else _MODEL

    def generate(
        self,
        genre: str,
        platform: str = "tiktok",
        hook_type: Optional[str] = None,
        content_format: Optional[str] = None,
        affiliate_url: Optional[str] = None,
    ) -> dict:
        """
        台本 JSON を生成して返す。

        Args:
            genre: "beauty" | "gadget" | "lifehack" | "marriage" | "sidehustle" | "diet"
            platform: "tiktok" | "reels" | "shorts"
            hook_type: None で自動選択（ジャンルベスト型から選ぶ）
            content_format: None で自動選択
            affiliate_url: 末尾 CTA に埋め込むアフィリエイト URL

        Returns: {
            "project_id": "...",
            "genre": "...",
            "platform": "...",
            "hook_type": "...",
            "content_format": "...",
            "scenes": [{"speech_text": "...", "image_prompt": "..."}, ...],
            "caption": "...",
            "hashtags": [...],
            "affiliate_url": "...",
            "created_at": "...",
        }
        """
        if genre not in GENRE_TEMPLATES:
            raise ValueError(f"未対応ジャンル: {genre}。選択肢: {list(GENRE_TEMPLATES.keys())}")
        if platform not in PLATFORM_PARAMS:
            raise ValueError(f"未対応プラットフォーム: {platform}。選択肢: {list(PLATFORM_PARAMS.keys())}")

        tmpl = GENRE_TEMPLATES[genre]
        plat = PLATFORM_PARAMS[platform]

        # フック型・コンテンツ構成を自動選択
        if hook_type is None:
            hook_type = random.choice(tmpl["best_hooks"])
        if content_format is None:
            content_format = random.choice(
                tmpl.get("best_formats", list(CONTENT_FORMATS.keys()))
            )

        hook_info = HOOK_TYPES[hook_type]
        fmt_info = CONTENT_FORMATS[content_format]

        # シーン数をプラットフォームに合わせて決定
        n_scenes = random.randint(*plat["scene_count"])

        # LLM プロンプトを構築して台本を生成
        prompt = self._build_prompt(
            tmpl, plat, hook_info, fmt_info, n_scenes, affiliate_url
        )
        raw = self._call_llm(prompt)

        # JSON パース・バリデーション
        parsed = self._parse_response(raw, genre, platform, n_scenes)

        # メタデータを付与
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        parsed.update({
            "project_id": f"{genre}_{platform}_{ts}",
            "genre": genre,
            "platform": platform,
            "hook_type": hook_type,
            "content_format": content_format,
            "affiliate_url": affiliate_url or "",
            "created_at": datetime.now().isoformat(),
        })

        return parsed

    def batch_generate(
        self,
        genre: str,
        platform: str = "tiktok",
        count: int = 7,
        affiliate_url: Optional[str] = None,
    ) -> list[dict]:
        """
        同一ジャンル × プラットフォームで count 本の台本を一括生成する。
        フック型・構成をローテーションして多様性を確保する。
        """
        tmpl = GENRE_TEMPLATES[genre]
        hook_cycle = tmpl["best_hooks"] * (count // len(tmpl["best_hooks"]) + 1)
        fmt_cycle = tmpl.get("best_formats", list(CONTENT_FORMATS.keys())) * (
            count // len(tmpl.get("best_formats", list(CONTENT_FORMATS.keys()))) + 1
        )
        results = []
        for i in range(count):
            script = self.generate(
                genre=genre,
                platform=platform,
                hook_type=hook_cycle[i],
                content_format=fmt_cycle[i],
                affiliate_url=affiliate_url,
            )
            results.append(script)
            print(f"  [{i+1}/{count}] {script['hook_type']} × {script['content_format']} 生成完了")
        return results

    # ── 内部メソッド ────────────────────────────────────────────────────────

    def _build_prompt(
        self,
        tmpl: dict,
        plat: dict,
        hook_info: dict,
        fmt_info: dict,
        n_scenes: int,
        affiliate_url: Optional[str],
    ) -> str:
        """LLM に渡すプロンプトを構築する。"""

        aff_instruction = ""
        if affiliate_url:
            aff_instruction = (
                f"\n最後のシーンの speech_text には必ず"
                f"「詳しくはプロフィールのリンクをチェックしてください」"
                f"というCTAを自然に含めてください。"
            )

        # 典型フック例を2つランダム選択
        sample_hooks = random.sample(tmpl["typical_hooks"], min(2, len(tmpl["typical_hooks"])))

        return f"""あなたはバズるショート動画の日本語台本専門ライターです。
以下の条件で、{plat["display_name"]} 向けの動画台本を1本生成してください。

## ジャンル情報
- ジャンル: {tmpl["display_name"]}
- ターゲット: {tmpl["target"]}
- ターゲットの悩み: {", ".join(tmpl["pain_points"][:3])}
- ターゲットの欲求: {", ".join(tmpl["desires"][:3])}

## 使用するバズの型
- フック型: {hook_info["name"]} — {hook_info["description"]}
  フックパターン例: {hook_info["patterns"][0]}
- コンテンツ構成: {fmt_info["name"]} — {fmt_info["effect"]}
  構成ガイド: {" → ".join(fmt_info["structure"])}

## プラットフォーム仕様
- プラットフォーム: {plat["display_name"]}
- 目標尺: {plat["optimal_duration_sec"][0]}〜{plat["optimal_duration_sec"][1]}秒
- シーン数: {n_scenes}シーン（各{plat["sec_per_scene"][0]}〜{plat["sec_per_scene"][1]}秒）
- スタイル: {plat["style_note"]}
- 重視するシグナル: {", ".join(plat["top_signals"][:3])}

## このジャンルで実際にバズったフック例（参考）
{chr(10).join(f"  ・{h}" for h in sample_hooks)}

## 台本の絶対ルール
1. 冒頭3秒で視聴者を掴む強烈なフックから始める
2. 1シーン = 1メッセージ（情報の詰め込みNG）
3. 話し言葉・口語体（書き言葉NG）
4. 具体的な数字・体験を入れる（「なんとなく」NG）
5. 3秒ごとに新しい情報・展開を作る
6. 最後は明確なCTA（フォロー/保存/リンク確認）
7. speech_text: 自然な日本語ナレーション（TTS で読まれる）
8. image_prompt: 英語のみ・テキスト禁止・背景イメージを描写{aff_instruction}

## image_prompt のルール（必須）
- 英語のみで記述すること
- 絶対にテキスト・文字・看板・ロゴを含めないこと
- 実写風・シネマティックな描写
- image_style のヒント: {tmpl["image_style"]}

## 出力フォーマット（純粋な JSON のみ、前後に説明文不要）

```json
{{
  "scenes": [
    {{
      "speech_text": "（日本語ナレーション、1シーン15〜40文字程度）",
      "image_prompt": "（英語のみ、no text, no letters を含めること）"
    }}
  ],
  "caption": "（投稿キャプション：フック1行+改行+フォローCTA+ハッシュタグ5個、100〜150字）",
  "hashtags": ["#...", "..."]
}}
```

{n_scenes}シーンで生成してください。JSONのみを出力し、前後に説明や```コードブロックマーカー```は不要です。"""

    def _call_llm(self, prompt: str) -> str:
        """Claude API を呼び出してレスポンスを返す。"""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()

    def _parse_response(
        self,
        raw: str,
        genre: str,
        platform: str,
        n_scenes: int,
    ) -> dict:
        """LLM レスポンスを JSON にパースし、バリデーションする。"""

        # コードブロックマーカーの除去
        text = raw
        for marker in ["```json", "```JSON", "```"]:
            text = text.replace(marker, "")
        text = text.strip()

        # JSON パース
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # JSON が途中で切れている場合のフォールバック
            data = self._fallback_parse(raw, genre, platform, n_scenes)

        # scenes のバリデーション
        scenes = data.get("scenes", [])
        validated_scenes = []
        for s in scenes:
            if not isinstance(s, dict):
                continue
            speech = s.get("speech_text", "").strip()
            img = s.get("image_prompt", "").strip()
            if speech and img:
                # image_prompt に日本語が混入していたら除去
                img_clean = _strip_japanese(img)
                if "no text" not in img_clean.lower():
                    img_clean += ", no text, no letters, no watermark"
                validated_scenes.append({
                    "speech_text": speech,
                    "image_prompt": img_clean,
                })

        if not validated_scenes:
            validated_scenes = _fallback_scenes(genre, n_scenes)

        # hashtags
        hashtags_key = f"hashtags_{platform}"
        tmpl = GENRE_TEMPLATES[genre]
        default_tags = tmpl.get(hashtags_key, tmpl.get("hashtags_tiktok", []))
        hashtags = data.get("hashtags", default_tags)[:5]

        # caption
        caption = data.get("caption", _default_caption(genre, platform))

        return {
            "scenes": validated_scenes,
            "caption": caption,
            "hashtags": hashtags,
        }

    def _fallback_parse(
        self, raw: str, genre: str, platform: str, n_scenes: int
    ) -> dict:
        """JSON パース失敗時のフォールバック。ジャンル固定サンプルを返す。"""
        tmpl = GENRE_TEMPLATES[genre]
        hooks = tmpl["typical_hooks"]
        return {
            "scenes": _fallback_scenes(genre, n_scenes),
            "caption": _default_caption(genre, platform),
            "hashtags": tmpl.get(f"hashtags_{platform}", tmpl.get("hashtags_tiktok", [])),
        }


# ── ヘルパー関数 ────────────────────────────────────────────────────────────

def _strip_japanese(text: str) -> str:
    """テキストから日本語文字（ひらがな・カタカナ・漢字）を除去する。"""
    import re
    return re.sub(r'[　-鿿＀-￯]', '', text).strip()


def _fallback_scenes(genre: str, n: int) -> list[dict]:
    """パース失敗時のフォールバックシーンリスト。"""
    tmpl = GENRE_TEMPLATES[genre]
    style = tmpl["image_style"]
    hooks = tmpl["typical_hooks"]
    ctas = tmpl["cta_patterns"]

    scenes = []
    for i in range(n):
        if i == 0:
            speech = hooks[0]
        elif i == n - 1:
            speech = ctas[0]
        else:
            speech = hooks[min(i, len(hooks) - 1)]
        scenes.append({
            "speech_text": speech,
            "image_prompt": f"{style}, cinematic, no text, no letters, no watermark",
        })
    return scenes


def _default_caption(genre: str, platform: str) -> str:
    tmpl = GENRE_TEMPLATES[genre]
    hook = tmpl["typical_hooks"][0]
    cta = tmpl["cta_patterns"][0]
    tags = " ".join(tmpl.get(f"hashtags_{platform}", tmpl.get("hashtags_tiktok", []))[:5])
    return f"{hook}\n\n{cta}\n\n{tags}"
