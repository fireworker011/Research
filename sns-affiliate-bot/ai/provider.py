import os
from typing import Optional


class AIProvider:
    """
    プラガブルAIプロバイダー。
    AI_PROVIDER 環境変数で切り替え可能:
      template  : APIなし・テンプレートのみ（デフォルト・追加コストゼロ）
      claude    : Anthropic Claude API（ANTHROPIC_API_KEY 必要）
      grok      : xAI Grok API（XAI_API_KEY 必要）
      openai    : OpenAI API（OPENAI_API_KEY 必要）
    """

    SUPPORTED = ("template", "claude", "grok", "openai")

    def __init__(self, provider: Optional[str] = None):
        self.provider = provider or os.getenv("AI_PROVIDER", "template")
        if self.provider not in self.SUPPORTED:
            raise ValueError(f"AI_PROVIDER must be one of {self.SUPPORTED}")

    def generate(self, prompt: str, system: str = "あなたは日本語で回答するSNSマーケティングの専門家です。") -> str:
        """テキストを生成して返す。templateモードは NotImplementedError を送出する。"""
        if self.provider == "claude":
            return self._claude(prompt, system)
        elif self.provider == "grok":
            return self._grok(prompt, system)
        elif self.provider == "openai":
            return self._openai(prompt, system)
        else:
            raise NotImplementedError(
                "AI_PROVIDER=template の場合は generator.py のテンプレート生成を使用してください"
            )

    def is_api_enabled(self) -> bool:
        return self.provider != "template"

    def _claude(self, prompt: str, system: str) -> str:
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic が必要です")
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY が .env に設定されていません")
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

    def _grok(self, prompt: str, system: str) -> str:
        """xAI Grok API（OpenAI互換）"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai が必要です")
        api_key = os.getenv("XAI_API_KEY")
        if not api_key:
            raise EnvironmentError("XAI_API_KEY が .env に設定されていません")
        client = OpenAI(api_key=api_key, base_url="https://api.x.ai/v1")
        response = client.chat.completions.create(
            model="grok-3",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content

    def _openai(self, prompt: str, system: str) -> str:
        """OpenAI API（Codex含む）"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai が必要です")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY が .env に設定されていません")
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content
