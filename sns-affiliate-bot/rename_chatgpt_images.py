"""
ChatGPTからダウンロードした画像を scene1.png〜scene7.png にリネーム

ファイル名末尾の (1)〜(7) をscene番号として対応付ける。

使い方:
  python rename_chatgpt_images.py 10
  → C:\\Users\\ys734\\Desktop\\pet10_images\\ 内の画像をリネーム

  python rename_chatgpt_images.py 10 --src C:\\Users\\ys734\\Downloads
  → Downloadsフォルダから探してリネーム
"""

import re
import sys
import shutil
from pathlib import Path

DEFAULT_BASE = Path(r"C:\Users\ys734\Desktop")


def find_and_rename(src_dir: Path, dst_dir: Path):
    dst_dir.mkdir(parents=True, exist_ok=True)

    # (1)〜(7) を含む画像ファイルを探す
    pattern = re.compile(r'\((\d)\)\s*\.(png|jpg|jpeg|webp)$', re.IGNORECASE)
    found = {}

    for f in src_dir.iterdir():
        m = pattern.search(f.name)
        if m:
            num = int(m.group(1))
            if 1 <= num <= 7:
                found[num] = f

    if not found:
        print(f"❌ (1)〜(7) を含む画像が見つかりません: {src_dir}")
        return

    print(f"✅ {len(found)}件 検出")
    for num in sorted(found):
        src = found[num]
        dst = dst_dir / f"scene{num}.png"
        shutil.copy2(src, dst)
        print(f"  ({num}) {src.name}  →  {dst.name}")

    missing = [i for i in range(1, 8) if i not in found]
    if missing:
        print(f"\n⚠️ 未検出: scene{missing} → ChatGPTで再生成してください")
    else:
        print(f"\n✅ 全7枚 完了: {dst_dir}")


def main():
    args = sys.argv[1:]

    if not args:
        print("使い方: python rename_chatgpt_images.py <動画番号>")
        print("  例: python rename_chatgpt_images.py 10")
        return

    num = args[0]
    dst_dir = DEFAULT_BASE / f"pet{num}_images"

    # --src オプションで探索先を変更可能
    if "--src" in args:
        idx = args.index("--src")
        src_dir = Path(args[idx + 1])
    else:
        src_dir = dst_dir  # デフォルトはpetN_imagesフォルダ自身

    print("=" * 50)
    print(f"ChatGPT画像 リネーム — 動画{num}")
    print(f"探索先: {src_dir}")
    print(f"出力先: {dst_dir}")
    print("=" * 50)

    find_and_rename(src_dir, dst_dir)


if __name__ == "__main__":
    main()
