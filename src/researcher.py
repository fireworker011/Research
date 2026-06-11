"""
researcher.py - トレンド・バズ動画の自動リサーチ＆「伸びる型」分析エンジン

対象テーマ: AI副業 / 転職・スキルアップ / SNSマネタイズ
対象プラットフォーム: YouTubeショート / TikTok / Threads
"""

import os
import json
import time
import logging
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import anthropic
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent.parent
TRENDS_DIR = BASE_DIR / "data" / "trends"
TRENDS_DIR.mkdir(parents=True, exist_ok=True)

SEARCH_TOPICS = [
    "AI副業 2024 2025 YouTube ショート バズ",
    "転職 スキルアップ SNS 稼ぎ方 バズ動画",
    "SNSマネタイズ アフィリエイト 初心者 伸びる",
    "AIツール 副業 自動化 月収",
    "フリーランス スキル転換 AI活用 成功事例",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


class TrendResearcher:
    def __init__(self, demo_mode: bool = False):
        self.demo_mode = demo_mode
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key and not demo_mode:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY が設定されていません。\n"
                "  1) .env ファイルに ANTHROPIC_API_KEY=your_key を記載するか\n"
                "  2) 環境変数として export ANTHROPIC_API_KEY=your_key を実行してください。\n"
                "  ※デモ実行: python researcher.py --demo"
            )
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None
        self.raw_search_results: list[dict] = []

    # ──────────────────────────────────────────
    # 1. Web リサーチ層
    # ──────────────────────────────────────────

    def _duckduckgo_search(self, query: str, max_results: int = 5) -> list[dict]:
        """DuckDuckGo HTMLスクレイピングでキーワード検索結果を取得"""
        url = "https://html.duckduckgo.com/html/"
        try:
            resp = requests.post(
                url,
                data={"q": query, "kl": "jp-jp"},
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            results = []
            for r in soup.select(".result__body")[:max_results]:
                title_el = r.select_one(".result__title")
                snippet_el = r.select_one(".result__snippet")
                link_el = r.select_one(".result__url")
                results.append(
                    {
                        "title": title_el.get_text(strip=True) if title_el else "",
                        "snippet": snippet_el.get_text(strip=True) if snippet_el else "",
                        "url": link_el.get_text(strip=True) if link_el else "",
                    }
                )
            return results
        except Exception as e:
            logger.warning(f"DuckDuckGo検索失敗 ({query[:30]}...): {e}")
            return []

    def _scrape_youtube_search(self, keyword: str) -> list[dict]:
        """YouTube検索結果ページからタイトル・概要をスクレイピング"""
        url = f"https://www.youtube.com/results?search_query={requests.utils.quote(keyword)}&sp=EgIYAQ%3D%3D"
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            # 動画タイトルをテキストから正規表現で抽出
            titles = re.findall(r'"title":\{"runs":\[\{"text":"([^"]{10,80})"', resp.text)
            return [{"title": t, "source": "youtube_shorts"} for t in titles[:8]]
        except Exception as e:
            logger.warning(f"YouTube検索スクレイピング失敗: {e}")
            return []

    def gather_web_data(self) -> list[dict]:
        """全キーワードでWeb検索し生データを収集"""
        logger.info("Webリサーチ開始...")
        all_results = []

        for topic in SEARCH_TOPICS:
            logger.info(f"  検索中: {topic}")
            results = self._duckduckgo_search(topic)
            all_results.extend(results)
            time.sleep(1.5)  # 礼儀正しいスクレイピング

        # YouTubeショート追加検索
        yt_keywords = ["AI副業 ショート", "転職 スキルアップ ショート動画", "SNSアフィリエイト 稼ぎ方"]
        for kw in yt_keywords:
            yt_results = self._scrape_youtube_search(kw)
            all_results.extend(yt_results)
            time.sleep(1.0)

        self.raw_search_results = all_results
        logger.info(f"Web収集完了: {len(all_results)} 件")
        return all_results

    # ──────────────────────────────────────────
    # 2. Claude によるパターン分析
    # ──────────────────────────────────────────

    def _demo_pattern(self) -> dict:
        """デモ用サンプルパターンデータ（APIキー不要）"""
        return {
            "analyzed_at": datetime.now().isoformat(),
            "topic_cluster": "AI副業・SNSマネタイズ",
            "trending_keywords": [
                "AI副業", "月収50万", "転職不要", "在宅ワーク", "ChatGPT活用",
                "SNSアフィリエイト", "自動化収入", "スキルゼロ", "副業初心者", "仕組み収入"
            ],
            "viral_structure": {
                "hook": "【例1】『月5万稼ぐのに資格は一切いらなかった』\n【例2】『40代元清掃員が3ヶ月でやったこと』\n【例3】『AIを使えば作業時間が90%減る理由』",
                "problem_agitation": "【例1】『毎日残業して手取り22万…これが限界だと思ってた』\n【例2】『副業やろうとしたけど何から始めればいいか全くわからなかった』",
                "solution_reveal": "【例1】『紀子に教わったたった1つの【型】を使ったら全部変わった』\n【例2】『AIツール×A8案件の組み合わせが最速の答えだった』",
                "social_proof": "『3ヶ月で月収+8万・受講生127名が同じ結果』",
                "cta": "【例1】『概要欄に無料チェックリストを貼ったので今すぐチェック』\n【例2】『コメントに「AI」と書いてくれたら詳細を送ります』"
            },
            "emotion_triggers": ["焦り・危機感", "共感・あるある", "驚き・意外性", "希望・可能性", "信頼・実績"],
            "optimal_structure": {
                "duration_seconds": 50,
                "scene_count": 6,
                "pacing": "最初3秒でフック→10秒で問題共感→20秒で解決策→残りでCTA",
                "thumbnail_style": "赤文字インパクト + キャラクターのリアクション表情"
            },
            "top_performing_formats": [
                {
                    "format_name": "失敗→逆転型",
                    "description": "主人公の具体的な失敗談から始まり、転換点を経て逆転成功するストーリー",
                    "example_hook": "『清掃の仕事しながら副業挑戦して3回失敗した話』",
                    "why_it_works": "視聴者が自己投影しやすく、感情的な共鳴が高い。続きが気になる構造"
                },
                {
                    "format_name": "暴露・タブー破り型",
                    "description": "業界の常識や「実はこれって無駄だった」という視点で驚かせる",
                    "example_hook": "『AIスクールに40万払って気づいた正直な話』",
                    "why_it_works": "認知的不協和を起こし、視聴継続率が上がる"
                }
            ],
            "a8_affiliate_angles": [
                {
                    "category": "転職・キャリア支援",
                    "product_type": "転職エージェント・スクール",
                    "angle": "スキルなし・40代でも転換できた具体的ルートを提示",
                    "cta_phrase": "概要欄の【無料診断】で今のスキルが副業に使えるか3分でわかります"
                },
                {
                    "category": "AIスクール・オンライン学習",
                    "product_type": "AIビジネス講座",
                    "angle": "ゼロから3ヶ月でAI副業を始めるロードマップ付き",
                    "cta_phrase": "今なら入会金無料キャンペーン中。概要欄のリンクから"
                }
            ],
            "content_calendar_tip": "今週は『AIを使って副業を自動化する3ステップ』がホット。月曜・木曜の19〜21時投稿が最もリーチが伸びやすい。"
        }

    def analyze_patterns(self, raw_data: list[dict] | None = None) -> dict:
        """
        収集データをClaudeで分析し「伸びる型」を抽出。
        raw_dataが空でもClaudeの知識ベースで高品質な分析を行う。
        """
        if self.demo_mode:
            logger.info("デモモード: サンプルパターンを使用")
            return self._demo_pattern()

        if raw_data is None:
            raw_data = self.raw_search_results

        data_summary = "\n".join(
            f"- [{r.get('source', 'web')}] {r.get('title', '')} | {r.get('snippet', '')}"
            for r in raw_data[:30]
            if r.get("title")
        )

        if not data_summary.strip():
            data_summary = "(Web収集データなし - 知識ベースから最新トレンドを分析)"

        prompt = f"""
あなたはYouTubeショート・TikTok・Threadsのバズコンテンツ分析の専門家です。
以下のリサーチデータと、2024〜2025年の「AI副業」「転職・スキルアップ」「SNSマネタイズ」ジャンルの
バズトレンドに関するあなたの知識を統合して、「現在最もエンゲージメントが高い構成パターン」を分析してください。

【収集データ】
{data_summary}

【分析・出力要件】
以下のJSON形式で、実際に高いエンゲージメントを生む具体的なパターンを出力してください。
コードブロック（```json）で囲んでください。

```json
{{
  "analyzed_at": "{datetime.now().isoformat()}",
  "topic_cluster": "AI副業・SNSマネタイズ",
  "trending_keywords": ["キーワード1", "キーワード2", ...（10個）],
  "viral_structure": {{
    "hook": "最初3秒で使う衝撃フレーズのパターン（具体例3つ）",
    "problem_agitation": "視聴者の痛点を刺す問題提起の型（具体例2つ）",
    "solution_reveal": "解決策の見せ方・構造（具体例2つ）",
    "social_proof": "信頼性を高める実績・数値の見せ方",
    "cta": "行動喚起のパターン（具体例2つ）"
  }},
  "emotion_triggers": ["感情トリガー1", ...（5個）],
  "optimal_structure": {{
    "duration_seconds": 数値,
    "scene_count": 数値,
    "pacing": "テンポの説明",
    "thumbnail_style": "サムネイルスタイルの説明"
  }},
  "top_performing_formats": [
    {{
      "format_name": "フォーマット名",
      "description": "説明",
      "example_hook": "フックの例",
      "why_it_works": "なぜ伸びるか"
    }}
  ],
  "a8_affiliate_angles": [
    {{
      "category": "カテゴリ名",
      "product_type": "商品タイプ",
      "angle": "訴求アングル",
      "cta_phrase": "誘導フレーズ"
    }}
  ],
  "content_calendar_tip": "今週投稿すべきテーマの推奨"
}}
```
"""
        logger.info("Claudeでトレンドパターン分析中...")
        message = self.client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        response_text = message.content[0].text

        # JSONブロックを抽出
        json_match = re.search(r"```json\s*(.*?)\s*```", response_text, re.DOTALL)
        if json_match:
            pattern_data = json.loads(json_match.group(1))
        else:
            # フォールバック: テキスト全体をJSONとして試みる
            pattern_data = json.loads(response_text)

        logger.info("パターン分析完了")
        return pattern_data

    # ──────────────────────────────────────────
    # 3. 結果保存
    # ──────────────────────────────────────────

    def save_pattern(self, pattern: dict) -> Path:
        """最新パターンをJSONファイルに保存"""
        output_path = TRENDS_DIR / "latest_pattern.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(pattern, f, ensure_ascii=False, indent=2)
        logger.info(f"パターン保存完了: {output_path}")
        return output_path

    def save_raw_data(self, raw_data: list[dict]) -> Path:
        """生データをアーカイブ保存"""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = TRENDS_DIR / f"raw_{ts}.json"
        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(raw_data, f, ensure_ascii=False, indent=2)
        return archive_path

    # ──────────────────────────────────────────
    # 4. メイン実行フロー
    # ──────────────────────────────────────────

    def run(self, skip_web: bool = False, demo: bool = False) -> dict:
        """
        フルリサーチパイプラインを実行

        Args:
            skip_web: Trueならウェブスクレイピングをスキップ（Claudeの知識のみで分析）
        """
        logger.info("=" * 60)
        logger.info("YouTubeショート・SNSアフィリエイト トレンドリサーチ開始")
        logger.info("=" * 60)

        if demo or self.demo_mode:
            pattern = self._demo_pattern()
            output_path = self.save_pattern(pattern)
            logger.info(f"デモパターン保存: {output_path}")
            return pattern

        raw_data = []
        if not skip_web:
            raw_data = self.gather_web_data()
            self.save_raw_data(raw_data)
        else:
            logger.info("Webスクレイピングをスキップ（Claudeナレッジモード）")

        pattern = self.analyze_patterns(raw_data)
        output_path = self.save_pattern(pattern)

        logger.info("=" * 60)
        logger.info(f"リサーチ完了! 保存先: {output_path}")
        logger.info(f"トレンドキーワード: {pattern.get('trending_keywords', [])[:5]}")
        logger.info("=" * 60)

        return pattern


# ──────────────────────────────────────────
# CLI エントリポイント
# ──────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="SNSトレンドリサーチエンジン")
    parser.add_argument("--skip-web", action="store_true", help="Webスクレイピングをスキップ")
    parser.add_argument("--demo", action="store_true", help="APIキー不要のデモモード")
    args = parser.parse_args()

    researcher = TrendResearcher(demo_mode=args.demo)
    result = researcher.run(skip_web=args.skip_web or args.demo)

    print("\n【抽出された伸びる型サマリー】")
    viral = result.get("viral_structure", {})
    print(f"フック例: {viral.get('hook', 'N/A')}")
    print(f"感情トリガー: {result.get('emotion_triggers', [])}")
