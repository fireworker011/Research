import os
import requests
from pathlib import Path


class VoiceVox:
    """
    VOICEVOX エンジン（ローカルHTTPサーバー）を使って日本語音声を生成する。
    事前に VOICEVOX アプリを起動して localhost:50021 で動かしておく必要がある。
    インストール: https://voicevox.hiroshiba.jp/
    """

    def __init__(self):
        self.base_url = os.getenv("VOICEVOX_URL", "http://localhost:50021")
        self.speaker_id = int(os.getenv("VOICEVOX_SPEAKER_ID", "1"))

    def is_available(self) -> bool:
        try:
            r = requests.get(f"{self.base_url}/version", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def synthesize(self, text: str, output_path: str) -> str:
        """
        テキストを音声ファイルに変換して output_path に保存する。
        戻り値: output_path
        """
        if not self.is_available():
            raise RuntimeError(
                "VOICEVOX が起動していません。\n"
                "VOICEVOX アプリを起動してから再実行してください。\n"
                "ダウンロード: https://voicevox.hiroshiba.jp/"
            )

        query_resp = requests.post(
            f"{self.base_url}/audio_query",
            params={"text": text, "speaker": self.speaker_id},
            timeout=30,
        )
        query_resp.raise_for_status()
        audio_query = query_resp.json()

        audio_query["speedScale"] = 1.1
        audio_query["intonationScale"] = 1.1

        synth_resp = requests.post(
            f"{self.base_url}/synthesis",
            params={"speaker": self.speaker_id},
            json=audio_query,
            timeout=60,
        )
        synth_resp.raise_for_status()

        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(synth_resp.content)

        return output_path

    def get_speakers(self) -> list:
        resp = requests.get(f"{self.base_url}/speakers", timeout=10)
        resp.raise_for_status()
        return resp.json()
