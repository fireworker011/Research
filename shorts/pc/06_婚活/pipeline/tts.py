"""
ナレーション音声生成 — Edge TTS (無料・APIキー不要)

ja-JP-NanamiNeural: 落ち着いた日本語女性音声(クライアント役)。
ja-JP-AoiNeural: もう1つの女性音声(カウンセラー役・毅然としたトーン)。
2026-07-25改修: ドラマ形式(2人芝居)に対応するため、シーンごとに
`speaker`フィールド(client/counselor)を指定すると声を出し分ける。
"""

from __future__ import annotations

import asyncio
from pathlib import Path

VOICES = {
    "client": "ja-JP-NanamiNeural",     # クライアント役(告白トーン)
    "counselor": "ja-JP-AoiNeural",     # カウンセラー役(毅然・落ち着いたプロトーン)
}
RATES = {
    "client": "+4%",
    "counselor": "+2%",
}
PITCHES = {
    "client": "-2Hz",
    "counselor": "-4Hz",
}

VOICE = VOICES["client"]   # 後方互換(speaker未指定時のデフォルト)
RATE = RATES["client"]
PITCH = PITCHES["client"]


async def _synth(text: str, out_path: Path, voice: str, rate: str, pitch: str) -> None:
    import edge_tts

    communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
    await communicate.save(str(out_path))


def generate_narration(text: str, out_path: Path, speaker: str = "client") -> Path:
    """ナレーション全文 → mp3(speaker: client/counselor)"""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    voice = VOICES.get(speaker, VOICE)
    rate = RATES.get(speaker, RATE)
    pitch = PITCHES.get(speaker, PITCH)
    asyncio.run(_synth(text, out_path, voice, rate, pitch))
    print(f"  ✅ 音声生成({speaker}): {out_path.name}")
    return out_path


def generate_scene_narrations(scenes: list[dict], out_dir: Path) -> list[Path]:
    """シーンごとに個別の音声ファイルを生成(尺合わせが正確になる)

    scene に "speaker" があればその声(client/counselor)を使う。
    なければ client 音声(デフォルト)。
    """
    paths = []
    for i, scene in enumerate(scenes, 1):
        p = out_dir / f"narration_{i:02d}.mp3"
        speaker = scene.get("speaker", "client")
        generate_narration(scene["narration"], p, speaker=speaker)
        paths.append(p)
    return paths
