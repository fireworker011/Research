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
        if content_type in ("personal_story", "confession"):
            items = [
                "⬛ 半年前: 残業80h・副業収入ゼロ\nスクール月20万払えず断念",
                "🔶 転換点: Claude Code×Notion AIを使い始めた\n業務の40%が自動化",
                "✅ 今: 残業18h・副業月3.8万円\n同じ会社員でもここまで変われた",
            ][:count]
        elif content_type == "skill_list":
            items = random.sample([
                "✅ プロンプトエンジニアリング\n→ 業務報告書が30分→3分に",
                "✅ Notion AI\n→ 会議メモが自動で議事録に",
                "✅ Claude Code\n→ Excelマクロを自然言語で作成",
                "✅ Make（旧Integromat）\n→ 定型メール送信を完全自動化",
            ], min(count, 4))
        elif content_type == "career_tip":
            items = random.sample([
                "💡 在職中に動く\n→ 退職後は焦りで年収が下がりやすい",
                "💡 エージェント3社同時登録\n→ 比較できると交渉力が上がる",
                "💡 スキルの言語化を先に\n→ 面接で「何が強みか」即答できるか？",
            ], min(count, 3))
        elif content_type == "tool_recommendation":
            items = random.sample([
                "🔧 Claude Code\n→ コーディング不要で業務自動化",
                "🔧 Notion AI\n→ 議事録・報告書を瞬時に生成",
                "🔧 Perplexity\n→ 調査時間が10分の1に短縮",
            ], min(count, 3))
        elif content_type == "market_insight":
            items = random.sample([
                "📊 AIスキルあり・なしで年収差が拡大中\n同職種でも年収差100万超えの事例",
                "📊 プログラミング未経験→IT転職\n成功事例が3年前の2倍以上に",
                "📊 リモート可求人は高水準維持\nAIスキルがあれば全国どこからでも応募可",
            ], min(count, 3))
        else:
            items = [
                "⬛ ビフォー: 残業80h・副業収入ゼロ",
                "✅ アフター: 残業18h・副業月3.8万円",
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
        save_cta = random.choice(self._SAVE_CTA)
        if affiliate_url and "{" not in affiliate_url:
            text = f"{hook}\n\n{body}\n\n{cta}\n{affiliate_url}\n\n{save_cta}\n\n{hashtags}"
        else:
            text = f"{hook}\n\n{body}\n\n{cta}\n\n{save_cta}\n\n{hashtags}"

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
        bs = self.niche.get("persona", {}).get("backstory", {})
        before = bs.get("before", {})
        after = bs.get("after", {})

        niche_id = self.niche.get("id", "career")

        if content_type in ("personal_story", "confession"):
            if niche_id == "marriage":
                timeline = [
                    f"⬛ ビフォー: {before.get('age_start','28歳')}〜 {before.get('apps_tried','アプリ20社')}・{before.get('dates','出会い100人超')}で{before.get('result','全滅')}",
                    f"⬛ 原因: {before.get('mistake','プロフ・メッセージ・サービス選びが全部間違い')}",
                    f"🔶 転換点: {after.get('method','婚活エージェント＋プロフ改善＋メッセージ術')}を試した",
                    f"✅ 今: {after.get('result','運命の人と出会い1年後に入籍')}",
                ]
            else:
                timeline = [
                    f"⬛ ビフォー: {before.get('monthly_income','月収28万')}・{before.get('overtime','残業80時間')}",
                    f"⬛ 転換点: {before.get('turning_point','スクール月20万→断念→独学×AI')}",
                    f"🔶 3ヶ月後: 業務自動化が軌道に乗り始めた",
                    f"✅ 今: {after.get('overtime','残業18時間')}・副業{after.get('side_income','月3.8万円')}",
                    f"🎯 目標: {after.get('goal','副業月10万円')}",
                ]
            return "\n".join(timeline[:min(n, 4)])
        elif content_type == "skill_list":
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
        elif content_type == "app_comparison":
            items = random.sample([
                "📱 Pairs ─ 20〜30代に多い。カジュアル層も混在",
                "📱 with ─ 性格診断で相性重視。真剣度高め",
                "📱 Omiai ─ 結婚前提が明確。年齢層やや高め",
                "📱 Marrish ─ 審査制・真剣交際特化。マッチ率高い",
                "📱 婚活エージェント ─ プロサポート付き。コスパ最高",
            ], min(n, 3))
            return "\n".join(items)
        elif content_type == "advice":
            tips = random.sample([
                "💡 プロフ写真は必ずプロに撮ってもらう（自撮りとで5倍差が出る）",
                "💡 最初のメッセージは相手のプロフから1つ質問を拾う",
                "💡 3回デートしてもピンとこない相手とは会い続けない",
                "💡 複数のアプリを同時進行して比較する",
                "💡 婚活エージェントは無料相談だけでも受けてみる価値あり",
                "💡 断られてもダメだった理由を分析してから次に進む",
            ], min(n, 3))
            return "\n".join(tips)
        elif content_type == "paradox":
            if niche_id == "marriage":
                truths = random.sample([
                    "❌ よくある誤解：婚活がうまくいかないのは外見のせい\n✅ 本当の理由：プロフとメッセージの戦略の問題",
                    "❌ よくある誤解：いい人がいないからマッチしない\n✅ 本当の理由：アプリの選び方が間違っている",
                    "❌ よくある誤解：条件を下げれば出会える\n✅ 本当の理由：条件より「見せ方」の問題だった",
                    "❌ よくある誤解：たくさんの人に会えば誰かと続く\n✅ 本当の理由：質を上げないと数をこなしても変わらない",
                ], min(n, 3))
            else:
                truths = random.sample([
                    "❌ よくある誤解：副業が続かないのは稼げないから\n✅ 本当の理由：仕組みがないから続かない",
                    "❌ よくある誤解：転職失敗＝スキル不足\n✅ 本当の理由：動くタイミングと見せ方の問題",
                    "❌ よくある誤解：残業が減らないのは仕事量の問題\n✅ 本当の理由：自動化できていない業務がある",
                    "❌ よくある誤解：40代転職は「スペック勝負」\n✅ 本当の理由：経験の言語化と証明の問題",
                    "❌ よくある誤解：AIで副業するには知識が必要\n✅ 本当の理由：知識より先に始めた人が勝つ",
                ], min(n, 3))
            return "\n\n".join(truths)
        elif content_type == "comment_hook":
            # コメント欄リンク型: 本文にリンクなし→コメント欄へ誘導（Threadsリーチ最大化）
            if niche_id == "marriage":
                options = random.sample([
                    "今どのアプリを使っているか、コメントで教えてください👇\nアプリ20社試した私の体験談をお伝えします。",
                    "婚活中の30代女性に聞きたいことがあります。\n「出会えない原因」だと思っていること、コメントで教えてください。",
                    "マッチングアプリで「続かない」と思っている方へ。\n原因は3パターンに絞られます。コメント欄に詳細を貼っておきます👇",
                    "婚活エージェントと普通のアプリ、どちらか迷っている方へ。\n20社使った私の比較をコメント欄にまとめました👇",
                ], 1)
                return options[0]
            else:
                return "コメント欄に詳細をまとめました👇\n気になる方は「見た」とコメントしてください。"
        elif content_type == "fomo":
            if niche_id == "marriage":
                costs = random.sample([
                    "⏰ 1年先送り → 婚活市場での年齢ハンドルが上がる",
                    "⏰ 動いた人：半年後にパートナーと交際中",
                    "⏰ 待った人：半年後も「まだ準備中」のまま",
                    "💡 今すぐできること：マッチングアプリに1つだけ無料登録する",
                    "💡 今すぐできること：婚活エージェントの無料相談を予約する（30分）",
                ], min(n, 3))
            else:
                costs = random.sample([
                    f"⏰ 1ヶ月先送り → 副業収入を約{before.get('side_income','ゼロ')}のまま維持",
                    f"⏰ 半年先送り → {after.get('side_income','月3.8万円')}×6ヶ月＝約23万円を逃す",
                    "⏰ 動いた人：3ヶ月後に副業収入が発生",
                    "⏰ 待った人：3ヶ月後も「準備中」のまま",
                    "💡 今すぐできること：転職エージェントに1社だけ無料登録する",
                    "💡 今すぐできること：Claude Freeで業務の1つを試しに自動化してみる",
                ], min(n, 3))
            return "\n".join(costs)
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
    #  APIベース生成（Claude API）
    # ------------------------------------------------------------------ #

    def _persona_context(self) -> str:
        """ペルソナのバックストーリーをプロンプト用テキストに変換する。ニッチ非依存。"""
        p = self.niche.get("persona", {})
        bs = p.get("backstory", {})
        before = bs.get("before", {})
        after = bs.get("after", {})
        name = p.get("name", "")
        age = p.get("age", "")
        situation = p.get("situation", "")

        before_lines = "、".join(f"{v}" for v in before.values() if v) if before else "（未設定）"
        after_lines = "、".join(f"{v}" for v in after.values() if v) if after else "（未設定）"

        return (
            f"【あなたは「{name}」として一人称で投稿します】\n"
            f"・{age}歳・{situation}\n"
            f"・ビフォー: {before_lines}\n"
            f"・アフター: {after_lines}\n"
            f"・核心メッセージ: {bs.get('key_moment', '')}\n"
            f"・口調: {p.get('tone', '口語体・実体験ベース・共感重視')}\n"
        )

    # 保存促進CTA（Threadsアルゴリズム対策: 保存率向上でリーチ増加）
    _SAVE_CTA = [
        "保存してあとで読んでね📌",
        "同じ状況の人に届けてほしい🔁",
        "迷ってる人、これ保存しておいて📌",
    ]

    _TYPE_PROMPT: dict = {
        "paradox": (
            "【逆説フック型の構成】\n"
            "① 「●●じゃなくて●●だ」という逆説の主張から始める\n"
            "   例：「副業で一番ヤバいのは稼げないことじゃなくて続かないことです」\n"
            "   例：「転職で失敗する本当の原因、スキルがないことじゃありませんでした」\n"
            "② なぜそう言えるか→自分の失敗体験（具体的数字で）\n"
            "③ 本質的な解決策（仕組み・習慣レベルの話）\n"
            "④ 「あなたはどちらに当てはまりますか？」の問いかけ\n"
            "⑤ CTA\n\n"
            "【絶対禁止】告白フックで始めないこと。逆説命題から入ること。\n"
        ),
        "fomo": (
            "【損失フレーム・先送り心理型の構成】\n"
            "① 先送り行動そのものを問いかけで描写する\n"
            "   例：「調べるだけで1年経ってませんか？」\n"
            "   例：「もう少し準備してから、と言い続けて何年ですか？」\n"
            "② 先送りのコスト（機会損失）を数字で可視化する\n"
            "   例：「1年先送りすると、副業収入45万円を逃す計算になります」\n"
            "③ 「動いた人」vs「待った人」の具体的な差を示す\n"
            "④ 「今すぐできる1つのこと」を示してハードルを下げる\n"
            "⑤ CTA\n\n"
            "【絶対禁止】抽象的な「頑張れ」系の励まし。数字と行動を具体的に。\n"
        ),
    }

    def _threads_via_api(self, content_type: str) -> dict:
        product = random.choice(self.affiliate.get("products", [{}]))
        cta_line = product.get("cta", "詳細はプロフのリンクへ！")

        type_supplement = self._TYPE_PROMPT.get(content_type, (
            "【必須の投稿構造・この順番で書く】\n"
            "① 告白・弱さの暴露で始める\n"
            "   「正直に言います」「恥ずかしい話をします」「信じてもらえないかもしれませんが」\n"
            "   「ずっと言えなかった」「1年前の僕は誰にも言えなかったんですが」等を必ず使う\n"
            "② ビフォー→アフターを具体的数字で\n"
            "   例：月収28万→副業+3.8万、残業80h→18h、スクール月20万→無料AIで代替\n"
            "③ 再現可能な解決策を2〜3ステップで簡潔に\n"
            "④ 「あなたも同じ状況ですか？」「同じ悩みの人に届けたい」等の問いかけ\n"
            "⑤ CTA: 「{cta_line}」\n"
        )).replace("{cta_line}", cta_line)

        prompt = (
            f"{self._persona_context()}\n"
            f"投稿タイプ: {content_type}\n"
            f"紹介商品: {product.get('name','')}（{product.get('description','')}）\n\n"
            f"{type_supplement}\n"
            f"CTA（必ず末尾に入れる）: 「{cta_line}」\n\n"
            f"【全タイプ共通・絶対禁止】\n"
            f"・「○選」「○つ」で始まるリスト型タイトル\n"
            f"・「年収UP」「市場価値向上」「スキルアップ」等の抽象ワード単独使用\n"
            f"・情報メディアのような文体・箇条書きのみの構成\n"
            f"・嘘の数字や過大な主張\n\n"
            f"文字数: 250〜380字。口語体で、読んだ人が「自分のことだ」と感じる文章に。\n"
            f"本文のみを返してください（ハッシュタグ・説明文は不要）。"
        )
        text = self.ai.generate(prompt)
        hashtags = self._pick_hashtags(content_type)
        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))

        if affiliate_url and "{" not in affiliate_url:
            full_text = f"{text}\n\n{affiliate_url}\n\n{hashtags}"
        else:
            full_text = f"{text}\n\n{hashtags}"

        return {
            "content_type": content_type,
            "text": full_text,
            "hashtags": hashtags,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "image_keywords": self.niche["image_keywords"].get(content_type, ["business"]),
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    def _youtube_via_api(self, content_type: str) -> dict:
        product = random.choice(self.affiliate.get("products", [{}]))
        tmpl = self.templates.get("youtube", {}).get(content_type, {})

        prompt = (
            f"{self._persona_context()}\n"
            f"YouTube Shorts（55秒）の台本を作成してください。\n"
            f"動画タイプ: {content_type}\n"
            f"関連商品: {product.get('name', '')}\n\n"
            f"【構成】告白（弱さ+数字）→ 転換点 → 解決策 → CTA\n"
            f"1シーン目は「正直に言います」系で始めること。\n\n"
            f"以下のJSON形式だけを返してください（余分な説明不要）:\n"
            f'{{"title": "実体験・数字を含むタイトル", '
            f'"scenes": [{{"text": "シーンテキスト", "duration_sec": 秒数}}]}}\n'
        )
        raw = self.ai.generate(prompt)
        try:
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            data = json.loads(json_match.group()) if json_match else {}
        except Exception:
            data = {}

        affiliate_url = product.get("url_template", "").replace("{A8_ID}", os.getenv("A8_AFFILIATE_ID", ""))
        default_title = tmpl.get("title_template", "【実録】40代会社員がAIで残業80h→18hになった話")
        default_scenes = [
            {"text": "正直に言います\n半年前の僕は残業80時間\n副業収入ゼロでした", "duration_sec": 8},
            {"text": "転換点はプログラミングスクール断念\n月20万払えなかった日", "duration_sec": 10},
            {"text": "Claude Code×Notion AIで\n業務を自動化→副業月3.8万円\n残業も18時間に", "duration_sec": 12},
            {"text": "同じ状況の人に届けたい\n詳しい方法は概要欄から", "duration_sec": 8},
        ]

        return {
            "content_type": content_type,
            "title": data.get("title", default_title),
            "description": f"詳細はプロフのリンクから\n#AI副業 #40代副業 #副業",
            "tags": ["AI副業", "40代副業", "副業", "転職", "AI活用"],
            "scenes": data.get("scenes", default_scenes),
            "duration_sec": 55,
            "affiliate_product_id": product.get("id", ""),
            "affiliate_url": affiliate_url,
            "image_keywords": self.niche["image_keywords"].get(content_type, ["career"]),
            "niche": self.niche["id"],
            "generated_at": datetime.now().isoformat(),
        }

    def _threads_video_via_api(self, content_type: str) -> dict:
        product = random.choice(self.affiliate.get("products", [{}]))

        prompt = (
            f"{self._persona_context()}\n"
            f"Threads縦型ショート動画（30〜40秒）の台本を作成してください。\n"
            f"投稿タイプ: {content_type}\n\n"
            f"【シーン構成（必須）】\n"
            f"シーン1（6秒）: 「正直に言います」系で始まる告白＋具体的数字\n"
            f"シーン2（8秒）: ビフォーの状況（数字で）\n"
            f"シーン3（8秒）: アフターの数字＋方法\n"
            f"シーン4（7秒）: 「あなたも？」の問いかけ＋「プロフのリンクへ」CTA\n\n"
            f"以下のJSON形式だけを返してください:\n"
            f'{{\n'
            f'  "caption": "200字以内の告白スタイルキャプション",\n'
            f'  "scenes": [\n'
            f'    {{"text": "シーン1（2〜3行）", "duration_sec": 6}},\n'
            f'    {{"text": "シーン2（2〜3行）", "duration_sec": 8}},\n'
            f'    {{"text": "シーン3（2〜3行）", "duration_sec": 8}},\n'
            f'    {{"text": "シーン4（2〜3行）", "duration_sec": 7}}\n'
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
            {"text": "正直に言います\n残業80h→18hになりました\nAIだけが理由です", "duration_sec": 6},
            {"text": "半年前\n月収28万・副業ゼロ\nスクール月20万払えず断念", "duration_sec": 8},
            {"text": "今\n副業月3.8万円\nClaude Code×Notion AIで実現", "duration_sec": 8},
            {"text": "同じ状況の人に届け\nプロフのリンクに方法まとめています", "duration_sec": 7},
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
        # Threadsはハッシュタグ3〜5個がアルゴリズム最適
        return " ".join(tags[:4])
