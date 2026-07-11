"""
ナレーション音声生成 — Edge TTS (無料・APIキー不要)

ja-JP-NanamiNeural: 落ち着いた日本語女性音声。
「告白トーン」に寄せるため rate をやや遅めに設定。
"""

from __future__ import annotations

import asyncio
from pathlib import Path

VOICE = "ja-JP-NanamiNeural"
RATE = "+4%"    # ややテンポよく(2026-07改修: ゆっくり読みが離脱要因だったため)
PITCH = "-2Hz"  # 少し落ち着いたトーン


async def _synth(text: str, out_path: Path) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH)
    await communicate.save(str(out_path))


def generate_narration(text: str, out_path: Path) -> Path:
    """ナレーション全文 → mp3"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    asyncio.run(_synth(text, out_path))
    print(f"  ✅ 音声生成: {out_path.name}")
    return out_path


def generate_scene_narrations(scenes: list[dict], out_dir: Path) -> list[Path]:
    """シーンごとに個別の音声ファイルを生成(尺合わせが正確になる)"""
    paths = []
    for i, scene in enumerate(scenes, 1):
        p = out_dir / f"narration_{i:02d}.mp3"
        generate_narration(scene["narration"], p)
        paths.append(p)
    return paths
