"""VOICEVOX で話者ごとにナレーションを作る。"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
from voicevox_core.blocking import Onnxruntime, OpenJtalk, Synthesizer, VoiceModelFile

from irasutoya_short.audio import wav_bytes_to_float
from irasutoya_short.catalog import VOICES
from irasutoya_short.constants import BLOCKED_STYLE_IDS, SAMPLE_RATE

DEFAULT_ROOT = Path(os.environ.get("IRASUTOYA_VOICEVOX", Path.home() / ".cache/irasutoya-short/voicevox"))
NEEDED_VVMS = ("0.vvm", "4.vvm", "9.vvm")


def runtime_ready(root: Path | None = None) -> bool:
    root = root or DEFAULT_ROOT
    dict_dir = root / "dict/open_jtalk_dic_utf_8-1.11"
    ort = root / "onnxruntime/lib" / Onnxruntime.LIB_VERSIONED_FILENAME
    models = all((root / "models/vvms" / name).is_file() for name in NEEDED_VVMS)
    return dict_dir.is_dir() and ort.is_file() and models


def require_runtime(root: Path | None = None) -> Path:
    root = root or DEFAULT_ROOT
    if runtime_ready(root):
        return root
    raise RuntimeError(
        "VOICEVOX の実行ファイルがありません。"
        f" README の setup を実行して {root} に 0.vvm / 4.vvm / 9.vvm を置いてください。"
    )


class Speaker:
    def __init__(self, root: Path | None = None) -> None:
        self.root = require_runtime(root)
        ort_path = self.root / "onnxruntime/lib" / Onnxruntime.LIB_VERSIONED_FILENAME
        ort = Onnxruntime.load_once(filename=str(ort_path))
        dictionary = self.root / "dict/open_jtalk_dic_utf_8-1.11"
        self.synth = Synthesizer(ort, OpenJtalk(str(dictionary)))
        loaded: set[str] = set()
        for voice in VOICES.values():
            if voice["vvm"] in loaded:
                continue
            path = self.root / "models/vvms" / voice["vvm"]
            with VoiceModelFile.open(str(path)) as model:
                self.synth.load_voice_model(model)
            loaded.add(voice["vvm"])

    def speak(self, text: str, style_id: int, speed: float) -> np.ndarray:
        if style_id in BLOCKED_STYLE_IDS:
            raise ValueError(f"スタイル {style_id} は事前許可が必要な声なので使いません。")
        if not text.strip():
            return np.zeros(int(0.15 * SAMPLE_RATE), dtype=np.float32)
        query = self.synth.create_audio_query(text, style_id)
        query.speed_scale = float(speed)
        query.pre_phoneme_length = 0.06
        query.post_phoneme_length = 0.1
        wav = self.synth.synthesis(query, style_id)
        return wav_bytes_to_float(wav)
