"""
main.py - YouTubeショッピング・SNSアフィリエイト自動化システム
フルパイプライン実行エントリポイント
"""

import sys
import argparse
import logging
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_pipeline(
    skip_web: bool = False,
    pattern_only: bool = False,
    generate_only: bool = False,
    demo: bool = False,
):
    """フルパイプライン実行"""

    if not generate_only:
        logger.info("STEP 1/2: トレンドリサーチ開始")
        from researcher import TrendResearcher
        researcher = TrendResearcher(demo_mode=demo)
        pattern = researcher.run(skip_web=skip_web or demo)
        logger.info("STEP 1/2: リサーチ完了\n")
    else:
        logger.info("STEP 1/2: スキップ（--generate-only モード）")

    if not pattern_only:
        logger.info("STEP 2/2: コンテンツ生成開始")
        from generator import ContentGenerator
        generator = ContentGenerator(demo_mode=demo)
        result = generator.run()
        logger.info("STEP 2/2: 生成完了\n")

        print("\n" + "=" * 60)
        print("✅ 全工程完了！出力サマリー")
        print("=" * 60)
        script = result["script"]
        print(f"動画タイトル : {script.get('title')}")
        print(f"フック       : {script.get('hook_text')}")
        print(f"尺           : {script.get('total_duration_seconds')}秒")
        print(f"シーン数     : {len(script.get('scenes', []))}")
        print(f"\n出力ディレクトリ: {result['paths']['dir']}")
        print(f"  - script_data.json     : 完全データ")
        print(f"  - script_readable.md   : 読みやすい台本")
        print(f"  - image_prompts.txt    : 画像プロンプト集")
        print("=" * 60)
        return result

    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="YouTubeショッピング・SNSアフィリエイト自動化システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py                    # フルパイプライン（Web検索 + 生成）
  python main.py --skip-web         # Web検索スキップ（Claude知識のみ）★推奨
  python main.py --pattern-only     # リサーチのみ（生成スキップ）
  python main.py --generate-only    # 生成のみ（既存パターン使用）
        """,
    )
    parser.add_argument("--skip-web", action="store_true", help="Webスクレイピングをスキップ")
    parser.add_argument("--pattern-only", action="store_true", help="リサーチのみ実行")
    parser.add_argument("--generate-only", action="store_true", help="生成のみ実行")
    parser.add_argument("--demo", action="store_true", help="APIキー不要のデモモード（構造確認用）")
    args = parser.parse_args()

    run_pipeline(
        skip_web=args.skip_web,
        pattern_only=args.pattern_only,
        generate_only=args.generate_only,
        demo=args.demo,
    )
