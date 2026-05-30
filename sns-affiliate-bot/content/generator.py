import json
import os
import random
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from ai.provider import AIProvider


class ContentGenerator:
    """
    ニッチ設定とAIプロバイダーを組み合わせてSNSコンテンツを生成する。
    AI_PROVIDER=template の場合はテンプレートをランダムに組み合わせて生成。
    AI_PROVIDER=claude/grok/openai の場合はAPIで高品質なテキストを生成。
    """

    VARIABLES = {
        "year": str(datetime.now().year),
        "n": ["3", "5", "7"],
        "count": ["3", "5", "7"],
        "multiplier": ["2", "3", "5", "10"],
        "category": ["プログラミング", "AI・DX", "データサイエンス", "クラウド"],
        "industry": ["IT", "DX", "AI", "フィンテック"],
        "skill": ["Python", "AI活用", "クラウド", "データ分析"],
        "period": ["半年", "1年", "2年"],
        "age": ["20", "30", "40"],
        "target": ["転職希望者", "副業志望", "スキルアップ中の社会人"],
        "result": ["年収100万UP", "未経験からエンジニア転職", "副業月10万達成"],
        "job": ["エンジニア", "マーケター", "ビジネスパーソン"],
        "benefit": ["作業時間を半分に削減できる", "スキルアップが加速する", "転職成功率が上がる"],
    }

    def __init__(self, niche_config: dict, ai_provider: Optional[AIProvider] = None):
        self.niche = niche_config
        self.ai = ai_provider or AIProvider()
        self.templates = niche_config.get("templates", {})
        self.hashtags = niche_config.get("hashtags", {})
        self.affiliate = niche_config.get("affiliate", {})

    def generate_threads_post(self, content_type: Optional[str] = None) -> dict:
        """Threadsに投稿するコンテンツを生成する。"""
        available = self.niche["content_types"]["threads"]
        content_type = content_type or random.choice(available)

        if self.ai.is_api_enabled():
            return self._threads_via_api(content_type)
        return self._threads_from_template(content_type)

    def generate_threads_video_script(self, content_type: Optional[str] = None) -> dict:
        """Threads動画（縦型ショート、30〜40秒）用の台本を生成する。"""
        available = self.niche["content_types"]["threads"]
        content_type = content_type or random.choice(available)

        if self.ai.is_api_enabled():
            return self._threads_video_via_api(content_type)
        return self._threads_video_from_template(content_type)

    def generate_youtube_script(self, content_type: Optional[str] = None) -> dict:
        """YouTube Shorts の台本・メタデータを生成する。"""
        available = self.niche["content_types"]["youtube"]
        content_type = content_type or random.choice(available)

        if self.ai.is_api_enabled():
            return self._youtube_via_api(content_type)
        return self._youtube_from_template(content_type)

    # ------------------------------------------------------------------ #
    #  テンプレートベース生成（追加コストゼロ）
    # ------------------------------------------------------------------ #

    def _threads_video_via_api(self, content_type: str) -> dict:
        product = random.choice(self.affiliate.get("products", [{}]))
        persona = self.niche.get("persona", {})
        prompt = (
            f"Threads縦型ショート動画（30〜40秒）の台本を日本語で作成してください。\n"
            f"ペルソナ: {persona.get('name', 'カズト')} - {persona.get('description', '')}\n"
            f"口調: {persona.get('tone', '口語体・実体験ベース・共感重視')}\n"
            f"投稿タイプ: {content_type}\n\n"
            f"以下のJSON形式だけを返してください（余分な説明は不要）:\n"
            f'{{\n'
            f'  "caption": "Threads投稿キャプション（フック+まとめ+CTA、200字以内）",\n'
            f'  "scenes": [\n'
            f'    {{"text": "冒頭フック（2〜3行、視聴者を引きつける問いかけ）", "duration_sec": 6}},\n'
            f'    {{"text": "ポイント1（具体的・数字を使う）", "duration_sec": 8}},\n'
            f'    {{"text": "ポイント2（実体験ベース）", "duration_sec": 8}},\n'
            f'    {{"text": "まとめ＆CTA（フォロー誘導）", "duration_sec": 7}}\n'
            f'  ]\n'
            f'}}\n'
        )
        raw = self.ai.generate(prompt)
        try:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(json_match.group()) if json_match else {}
        except Exception:
            data = {}

        hashtags = self._pick_hashtags(content_type)
        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))
        caption_base = data.get("caption", "")
        if affiliate_url and "{" not in affiliate_url:
            caption = f"{caption_base}\n\n{affiliate_url}\n\n{hashtags}"
        else:
            caption = f"{caption_base}\n\n{hashtags}"

        default_scenes = [
            {"text": "転職で失敗する人がやりがちなこと\n知らないと損します", "duration_sec": 6},
            {"text": "❌ 退職してから転職活動を始める\n→ 焦りで条件が下がりやすい", "duration_sec": 8},
            {"text": "✅ 在職中に転職エージェントに登録\n→ 比較して選べる余裕が生まれる", "duration_sec": 8},
            {"text": "フォローすると毎日転職ノウハウを配信！", "duration_sec": 7},
        ]
        return {
            "content_type": content_type,
            "caption": caption,
            "scenes": data.get("scenes", default_scenes),
            "image_keywords": self.niche["image_keywords"].get(content_type, ["business"]),
            "hashtags": hashtags,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    def _threads_video_from_template(self, content_type: str) -> dict:
        tmpl = self.templates.get("threads", {}).get(content_type, {})
        if not tmpl:
            content_type = "skill_list"
            tmpl = self.templates["threads"]["skill_list"]

        hook = self._fill(random.choice(tmpl.get("hooks", ["転職スキルを解説します"])))
        cta = tmpl.get("cta", "→ フォローして最新情報をGET！")
        product = random.choice(self.affiliate.get("products", [{}]))
        hashtags = self._pick_hashtags(content_type)
        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))

        body_items = self._get_video_body_items(content_type)
        scenes = [
            {"text": hook, "duration_sec": 6},
            *[{"text": item, "duration_sec": 8} for item in body_items],
            {"text": cta, "duration_sec": 6},
        ]

        if affiliate_url and "{" not in affiliate_url:
            caption = f"{hook}\n\n{cta}\n{affiliate_url}\n\n{hashtags}"
        else:
            caption = f"{hook}\n\n{cta}\n\n{hashtags}"

        return {
            "content_type": content_type,
            "caption": caption,
            "scenes": scenes,
            "image_keywords": self.niche["image_keywords"].get(content_type, ["business"]),
            "hashtags": hashtags,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    def _get_video_body_items(self, content_type: str, count: int = 2) -> list:
        if content_type == "skill_list":
            items = random.sample([
                "✅ ChatGPT・Claude の使いこなし",
                "✅ Python 基礎（データ分析に直結）",
                "✅ クラウド（AWS/GCP）の基礎知識",
                "✅ プロンプトエンジニアリング",
            ], min(count, 4))
        elif content_type == "career_tip":
            items = random.sample([
                "💡 転職エージェントは2〜3社使い比べる",
                "💡 在職中に動き始める（退職後は焦りで失敗しやすい）",
                "💡 給与交渉は内定後が鉄則",
            ], min(count, 3))
        elif content_type == "tool_recommendation":
            items = random.sample([
                "🔧 Claude Code ─ コードなしで自動化",
                "🔧 Notion AI ─ 議事録を瞬時に作成",
                "🔧 Perplexity ─ リサーチが10倍速に",
            ], min(count, 3))
        elif content_type == "market_insight":
            items = random.sample([
                "📊 AIエンジニア求人が前年比200%超え",
                "📊 AIスキルあり・なしで年収差が拡大",
                "📊 リモート可求人は依然として高水準",
            ], min(count, 3))
        else:
            items = [
                "⬛ 1年前：残業続きで余裕ゼロ",
                "✅ 今：AI活用で定時帰宅＋副収入",
            ][:count]
        return items

    def _threads_from_template(self, content_type: str) -> dict:
        tmpl = self.templates.get("threads", {}).get(content_type, {})
        if not tmpl:
            raise ValueError(f"テンプレートが見つかりません: threads/{content_type}")

        hook = self._fill(random.choice(tmpl.get("hooks", ["スキルアップ情報をお届けします"])))
        product = random.choice(self.affiliate.get("products", [{}]))

        body = self._build_threads_body(content_type, hook)
        hashtags = self._pick_hashtags(content_type)
        cta = tmpl.get("cta", "→ フォローして最新情報をGET！")
        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))

        # アフィリエイトURLが未設定の場合はリンクなしで投稿
        if affiliate_url and "{" not in affiliate_url:
            text = f"{hook}\n\n{body}\n\n{cta}\n{affiliate_url}\n\n{hashtags}"
        else:
            text = f"{hook}\n\n{body}\n\n{cta}\n\n{hashtags}"

        return {
            "content_type": content_type,
            "text": text,
            "hook": hook,
            "body": body,
            "cta": cta,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "hashtags": hashtags,
            "image_keywords": self.niche["image_keywords"].get(content_type, ["business"]),
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    def _build_threads_body(self, content_type: str, hook: str) -> str:
        n = int(self._extract_number(hook) or 3)
        if content_type == "skill_list":
            items = random.sample([
                "Python / データ分析",
                "ChatGPT・Claudeを使いこなす力",
                "クラウド（AWS / GCP）の基礎",
                "ノーコード・ローコード開発",
                "プロンプトエンジニアリング",
                "データ可視化（Tableau / Power BI）",
                "セキュリティの基本知識",
            ], min(n, 7))
            return "\n".join(f"✅ {i+1}. {item}" for i, item in enumerate(items))
        elif content_type == "career_tip":
            tips = random.sample([
                "自分の「強み」を言語化してから転職活動を始める",
                "転職エージェントを2〜3社使い比べる",
                "在職中に転職活動を始める（退職後は不利になりがち）",
                "給与交渉は内定後に行う",
                "業界を変える場合はスキルの棚卸しを先に",
            ], min(n, 5))
            return "\n".join(f"💡 {t}" for t in tips)
        elif content_type == "tool_recommendation":
            tools = random.sample([
                "Claude Code ─ コードを書かずに自動化",
                "Notion AI ─ 議事録・ドキュメントを自動生成",
                "Gamma ─ プレゼン資料を10分で作成",
                "Make（旧Integromat）─ ノーコード自動化",
                "Perplexity ─ リサーチを10倍速にするAI検索",
            ], min(n, 5))
            return "\n".join(f"🔧 {t}" for t in tools)
        elif content_type == "market_insight":
            insights = random.sample([
                "AIエンジニアの求人数が前年比200%超え",
                "40代転職者の年収UPケースが3年前の2倍に",
                "未経験からDX人材への転職成功率が上昇中",
                "リモート可の求人、依然として高水準を維持",
                "副業・複業OKの企業が大手でも急増",
                "AIスキルあり・なしで年収差が拡大している",
            ], min(n, 4))
            return "\n".join(f"📊 {item}" for item in insights)
        elif content_type == "personal_story":
            stories = random.sample([
                "1年前：残業続きで副業なんて考える余裕ゼロ",
                "半年前：Claude Codeに出会って仕組み化を開始",
                "3ヶ月前：定時で上がれる日が増え始めた",
                "1ヶ月前：初めて副業で収益が発生",
                "今：朝活でAI学習・仕事は効率化・夜は家族時間",
            ], min(n, 4))
            return "\n".join(f"{'⬛' if i == 0 else '🔶' if i < len(stories)-1 else '✅'} {s}"
                           for i, s in enumerate(stories))
        else:
            return "詳しくはプロフのリンクからご確認ください。"

    def _youtube_from_template(self, content_type: str) -> dict:
        tmpl = self.templates.get("youtube", {}).get(content_type, {})
        if not tmpl:
            raise ValueError(f"テンプレートが見つかりません: youtube/{content_type}")

        vars_filled = {k: (random.choice(v) if isinstance(v, list) else v)
                       for k, v in self.VARIABLES.items()}

        title = self._fill(tmpl.get("title_template", "スキルアップ動画"), vars_filled)
        hook_script = self._fill(tmpl.get("hook_script", "今日も有益な情報をお届けします。"), vars_filled)
        cta_script = tmpl.get("cta_script", "概要欄のリンクをチェックしてください！")
        duration = tmpl.get("target_duration_sec", 55)

        product = random.choice(self.affiliate.get("products", [{}]))
        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))

        scenes = self._build_youtube_scenes(content_type, hook_script, cta_script, vars_filled, duration)

        description = (
            f"{title}\n\n"
            f"▼ 詳細・無料相談はこちら\n{affiliate_url}\n\n"
            f"#転職 #スキルアップ #副業 #AI活用 #キャリア"
        )
        tags = ["転職", "スキルアップ", "副業", "AI活用", "キャリア", "エンジニア転職", "DX"]

        return {
            "content_type": content_type,
            "title": title,
            "description": description,
            "tags": tags,
            "scenes": scenes,
            "duration_sec": duration,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "image_keywords": self.niche["image_keywords"].get(content_type, ["career"]),
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    def _build_youtube_scenes(self, content_type, hook, cta, vars_filled, duration):
        n = int(vars_filled.get("n", "3"))
        scenes = [{"type": "hook", "text": hook, "duration_sec": 5}]

        if content_type == "skill_ranking":
            items = random.sample([
                ("Python", "データ分析・機械学習の必須言語"),
                ("ChatGPT/Claude活用", "生産性10倍のAI使いこなし"),
                ("AWS基礎", "クラウドエンジニアへの第一歩"),
                ("ノーコード開発", "プログラミング不要で自動化"),
                ("データ可視化", "Tableau / Power BIで説得力UP"),
                ("プロンプトエンジニアリング", "AIを自在に操るスキル"),
                ("セキュリティ基礎", "全ITエンジニア必須の知識"),
            ], min(n, 7))
            sec_each = max(6, (duration - 12) // len(items))
            for rank, (skill, desc) in enumerate(items, 1):
                scenes.append({
                    "type": "ranking_item",
                    "rank": rank,
                    "text": f"第{rank}位\n{skill}\n{desc}",
                    "duration_sec": sec_each,
                })
        elif content_type == "career_advice":
            tips = random.sample([
                "自分の強みを言語化する",
                "転職エージェントを複数活用",
                "在職中に行動を始める",
                "年収交渉は内定後に",
                "スキルの棚卸しを先に",
            ], min(n, 5))
            sec_each = max(7, (duration - 12) // len(tips))
            for i, tip in enumerate(tips, 1):
                scenes.append({
                    "type": "point",
                    "number": i,
                    "text": f"ポイント{i}\n{tip}",
                    "duration_sec": sec_each,
                })
        elif content_type == "tool_introduction":
            tools = random.sample([
                ("Claude Code", "コードなしで自動化"),
                ("Notion AI", "ドキュメントを瞬時に作成"),
                ("Gamma", "プレゼン資料を10分で完成"),
                ("Make", "ノーコード業務自動化"),
                ("Perplexity", "AIによる高速リサーチ"),
            ], min(n, 5))
            sec_each = max(7, (duration - 12) // len(tools))
            for i, (tool, desc) in enumerate(tools, 1):
                scenes.append({
                    "type": "tool",
                    "number": i,
                    "text": f"No.{i} {tool}\n{desc}",
                    "duration_sec": sec_each,
                })

        scenes.append({"type": "cta", "text": cta, "duration_sec": 7})
        return scenes

    # ------------------------------------------------------------------ #
    #  APIベース生成（将来: Grok / OpenAI Codex / Claude API）
    # ------------------------------------------------------------------ #

    def _threads_via_api(self, content_type: str) -> dict:
        tmpl = self.templates.get("threads", {}).get(content_type, {})
        product = random.choice(self.affiliate.get("products", [{}]))
        prompt = (
            f"SNS投稿を日本語で作成してください。\n"
            f"ジャンル: {self.niche['name']}\n"
            f"投稿タイプ: {content_type}\n"
            f"関連商品: {product.get('name', '')}\n"
            f"CTAメッセージ: {tmpl.get('cta', '詳細はプロフのリンクへ！')}\n\n"
            f"要件:\n"
            f"- 冒頭1行に強いフックを入れる\n"
            f"- 箇条書きリストを含める（3〜5項目）\n"
            f"- 最後にCTAを入れる\n"
            f"- 合計300文字以内\n"
            f"- Threadsらしい口語体で\n"
        )
        text = self.ai.generate(prompt)
        hashtags = self._pick_hashtags(content_type)
        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))

        return {
            "content_type": content_type,
            "text": f"{text}\n\n{affiliate_url}\n\n{hashtags}",
            "hashtags": hashtags,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "image_keywords": self.niche["image_keywords"].get(content_type, ["business"]),
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    def _youtube_via_api(self, content_type: str) -> dict:
        product = random.choice(self.affiliate.get("products", [{}]))
        prompt = (
            f"YouTube Shorts用の台本を日本語で作成してください。\n"
            f"ジャンル: {self.niche['name']}\n"
            f"動画タイプ: {content_type}\n"
            f"尺: 約55秒\n\n"
            f"JSON形式で返してください:\n"
            f'{{"title": "動画タイトル", "scenes": [{{"text": "台本テキスト", "duration_sec": 秒数}}]}}\n'
        )
        raw = self.ai.generate(prompt)
        try:
            import re
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(json_match.group()) if json_match else {}
        except Exception:
            data = {}

        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))
        return {
            "content_type": content_type,
            "title": data.get("title", f"【{datetime.now().year}年版】転職スキルガイド"),
            "description": f"詳細はこちら → {affiliate_url}\n#転職 #スキルアップ",
            "tags": ["転職", "スキルアップ", "AI活用", "副業"],
            "scenes": data.get("scenes", [{"text": "コンテンツを生成中...", "duration_sec": 55}]),
            "duration_sec": 55,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "image_keywords": self.niche["image_keywords"].get(content_type, ["career"]),
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    # ------------------------------------------------------------------ #
    #  ユーティリティ
    # ------------------------------------------------------------------ #

    def _fill(self, template: str, vars_override: Optional[dict] = None) -> str:
        variables = {k: (random.choice(v) if isinstance(v, list) else v)
                     for k, v in self.VARIABLES.items()}
        if vars_override:
            variables.update(vars_override)
        for key, value in variables.items():
            template = template.replace(f"{{{key}}}", str(value))
        return template

    def _extract_number(self, text: str) -> Optional[str]:
        match = re.search(r'(\d+)', text)
        return match.group(1) if match else None

    def _pick_hashtags(self, content_type: str) -> str:
        base = self.hashtags.get("base", [])
        extra = self.hashtags.get(content_type, [])
        tags = list(set(base + extra))
        random.shuffle(tags)
        return " ".join(tags[:8])
