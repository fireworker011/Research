"""One window for the H3 lanes that already exist.

This module names the lane, the LoRA, the kind of piece, and the prompt helper.
It does not write a new story, it does not queue Comfy, and it does not post.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from h3.live_remake import LIGHTNING_FILE, LIGHTNING_STEPS, MODEL_FILE, STEPS


class DeskError(Exception):
    """The request does not land on one lane."""


@dataclass(frozen=True)
class Lane:
    """One existing H3 lane. ``present`` is true only when this checkout can build it."""

    id: str
    when: str
    story: str
    prompt: str
    quality: str
    speed: str
    loras: str
    code: str
    present: bool
    words: tuple[str, ...]


# Facts taken from colab/h3_studio.py, colab/h3_sfw.py, h3/live_remake.py,
# and research/affi-templates/affi_av.py. This checkout builds live_remake only.
LANES: dict[str, Lane] = {
    "live_remake": Lane(
        id="live_remake",
        when="元動画の秒・位置・カメラを残し、渡した静止画の顔と衣装に差し替えるとき。",
        story="渡されたシートだけ。新しい話は書かない。動きの文が空なら blocked。",
        prompt="Ref2VA の6節。英語。日本語は <d>[Japanese] の中だけ。見た目は書かない。",
        quality=f"公式 {MODEL_FILE}。steps {STEPS}。横 1344x768、縦 768x1344。24fps。",
        speed=f"既定は LoRA なし。--lightning のときだけ {LIGHTNING_FILE}、steps {LIGHTNING_STEPS}。",
        loras="既定なし。4step は明示したときだけ。anime2real はここでは積まない。",
        code="h3/live_remake.py",
        present=True,
        words=("リメイク", "元動画", "live_remake"),
    ),
    "fast_motion": Lane(
        id="fast_motion",
        when="最初の静止画から縦の短い動きを出すとき。6秒か9秒。",
        story="アフィの短い動き。格闘の決めは combat_motion。",
        prompt="FL2VA。base-en の integrated_multimodal_description から。",
        quality="768x1344 が6秒（158フレーム）、640x1152 が9秒（226フレーム）。video shift 6。",
        speed="speed LoRA 1.0 が常に載る。steps 9。これが Turbo。",
        loras="speed 1.0。任意で action 0.6 と combat 0.7。prfight2 は付けない。charswap とは混ぜない。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("fast_motion", "縦の短さ", "スピード"),
    ),
    "combat_motion": Lane(
        id="combat_motion",
        when="格闘の1本。最後の絵まで含めて決めを出すとき。",
        story="戦闘の動き。アフィの日常台本には使わない。",
        prompt="FL2VA。finish のときだけ prfight2, prfin1。",
        quality="High-Mem。Turbo は切る。",
        speed="combat 1.0。speed や action とは同じサンプラーに積まない。",
        loras="H3_Combat_V2.safetensors 強さ 1.0。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("combat_motion", "格闘", "prfight2"),
    ),
    "swap_character": Lane(
        id="swap_character",
        when="動画の動きを残し、全身の静止画に差し替えるとき。",
        story="Hero シートがある既存の人物。新しい人物設定は書かない。",
        prompt="Ref2VA。Video が動き、Picture が全身。",
        quality="High-Mem。Turbo は切る。公式 API ではこの LoRA を読めない。",
        speed="LoRA は1枚だけ。",
        loras="charswap 1.0。他の LoRA と同じサンプラーに積まない。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("swap_character", "全身差替"),
    ),
    "swap_face": Lane(
        id="swap_face",
        when="同じ charswap で、顔と髪だけを静止画から取るとき。",
        story="服は元動画のまま。",
        prompt="Ref2VA。Picture は顔と髪。",
        quality="High-Mem。Turbo は切る。",
        speed="LoRA は1枚だけ。",
        loras="charswap 1.0。単独。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("swap_face", "顔と髪"),
    ),
    "swap_outfit": Lane(
        id="swap_outfit",
        when="同じ charswap で、服だけを静止画から取るとき。",
        story="顔は元動画のまま。",
        prompt="Ref2VA。Picture は服。",
        quality="High-Mem。Turbo は切る。",
        speed="LoRA は1枚だけ。",
        loras="charswap 1.0。単独。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("swap_outfit", "服だけ"),
    ),
    "real": Lane(
        id="real",
        when="描いた動画を、別ジョブの実写 LoRA で寄せるとき。リメイクシートではない。",
        story="元の動きの動画があるとき。シートのリメイクは live_remake。",
        prompt="Ref2VA。ref-en の6節。",
        quality="anime2real は charswap と同じサンプラーに積まない。",
        speed="LoRA は1枚だけ。",
        loras="Anime2Realsim__H3.safetensors 強さ 1.0。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("anime2real", "実写LoRA"),
    ),
    "text_scene": Lane(
        id="text_scene",
        when="静止画も動画も無く、文から1シーンを作るとき。",
        story="場所は Hero の place。空欄は書かない。",
        prompt="T2VA。base-en。英語。せりふの原文だけ残す。",
        quality="6秒、16:9、768P。LoRA なし。",
        speed="公式の T2VA。Turbo は載らない。",
        loras="なし。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("text_scene", "文から"),
    ),
    "orbit360": Lane(
        id="orbit360",
        when="同じ絵を首尾で回すとき。",
        story="1枚の絵。別の話は足さない。",
        prompt="FL2VA。",
        quality="LoRA のファイル名が未確定なので積まない。",
        speed="素の FL2VA。",
        loras="なし。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("orbit360", "首尾"),
    ),
    "two_pass": Lane(
        id="two_pass",
        when="1本目の mp4 を、2本目の Video 1 に渡すとき。",
        story="パスごとのジョブ。LoRA はパスごとに分ける。",
        prompt="各パスの形式に従う。",
        quality="LoRA の同時積みはパスの中でも排他のまま。",
        speed="パスごとの設定。",
        loras="パスごと。窓口の外で混ぜない。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("two_pass", "二段"),
    ),
    "join": Lane(
        id="join",
        when="できた6秒と9秒を、15秒以上になるまで切ってつなぐとき。",
        story="すでにあるクリップ。1本で15秒は生成しない。",
        prompt="プロンプトは各本のもの。つなぎは ffmpeg。",
        quality="1080x1920 に揃えて切る。",
        speed="生成はしない。",
        loras="なし。",
        code="colab/h3_sfw.py の join_ffmpeg",
        present=False,
        words=("join", "つなぎ"),
    ),
    "affi_template": Lane(
        id="affi_template",
        when="既存のバズ型台本を指すとき。buy_before、daily_food、daily_camera。",
        story="台本ファイルを指すだけ。書き換えない。",
        prompt="台本側が正。ここから新しい文は出さない。",
        quality="生成しない。",
        speed="生成しない。",
        loras="このジョブでは積まない。",
        code="colab/h3_sfw.py の TEMPLATES",
        present=False,
        words=("affi_template", "バズ型"),
    ),
    "longform_chunk": Lane(
        id="longform_chunk",
        when="5秒から8秒のチャンクを latent でつなぎ、1本の mp4 にするとき。",
        story="渡した文をチャンクに分ける。新しい話の追加はしない。",
        prompt="Comfy の H3 Continuum Sampler。公式 API では止め。",
        quality="既定チャンク 5秒。runtime は comfy だけ。",
        speed="チャンク生成。1本の長尺生成はしない。",
        loras="このジョブの計画では積まない。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("longform_chunk", "長尺チャンク"),
    ),
    "affi_chain": Lane(
        id="affi_chain",
        when="アフィ焼きで、連続の打撃だけを足すとき。オフなら通常の Turbo と Motion Repair。",
        story="既存のアフィ台本。百裂を載せるのはオンのときだけ。",
        prompt="焼き用の FL2VA。せりふ文字はプロンプトに入れない。",
        quality="通常は Turbo 1.0 と Motion Repair 0.6。",
        speed="オンのとき progressive_acceleration_slider_v1.0.safetensors 強さ 4。0未満は渡さない。",
        loras="百裂はオプトイン。オフの台本には載せない。",
        code="research/affi-templates/affi_av.py（cursor/affi-template-bake-44d6）",
        present=False,
        words=("affi_chain", "百裂"),
    ),
}


def lane(name: str) -> Lane:
    key = name.strip()
    if key not in LANES:
        raise DeskError("ジョブが無い: " + key)
    return LANES[key]


def choose(text: str) -> str:
    """One lane id. Several matches stop instead of guessing."""
    raw = " ".join(text.split())
    if not raw:
        raise DeskError("ジョブ名か、やりたいことを1つ書く")
    if raw in LANES:
        return raw
    hits = [item.id for item in LANES.values() if any(word in raw for word in item.words)]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise DeskError("窓口が決まらない。ジョブ名をそのまま書く")
    raise DeskError("窓口が一つに決まらない: " + ", ".join(hits))


def render(name: str | None = None) -> str:
    """Plain-text card for one lane, or the whole window."""
    chosen = list(LANES) if name is None else [choose(name)]
    blocks: list[str] = []
    for key in chosen:
        item = LANES[key]
        where = "このcheckout" if item.present else "別ブランチ"
        blocks.append(
            "\n".join(
                [
                    f"[{item.id}] {where}",
                    f"いつ: {item.when}",
                    f"話: {item.story}",
                    f"プロンプト: {item.prompt}",
                    f"画質: {item.quality}",
                    f"速度: {item.speed}",
                    f"LoRA: {item.loras}",
                    f"コード: {item.code}",
                    "生成: しない",
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(flag in args for flag in ("--generate", "--queue", "--publish")):
        print("DESK STOP: 生成と公開はこの窓口では走らない")
        return 1
    try:
        text = render(args[0] if args else None)
    except DeskError as exc:
        print(f"DESK STOP: {exc}")
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
