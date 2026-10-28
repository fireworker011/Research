"""One window for the H3 lanes that already exist.

The card leads with the function name and the concrete change when that lane
is selected. It does not write a new story, it does not queue Comfy, and it
does not post.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

from h3.live_remake import LIGHTNING_FILE, LIGHTNING_STEPS, MODEL_FILE, STEPS
from h3.reproduce import main as reproduce_main


class DeskError(Exception):
    """The request does not land on one lane."""


@dataclass(frozen=True)
class Lane:
    """One existing H3 lane. ``present`` is true only when this checkout can build it."""

    id: str
    title: str
    effect: str
    give: str
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
        title="元動画の顔と衣装を、渡した静止画に合わせる",
        effect=(
            f"秒・カット位置・カメラは元動画のまま残る。顔と衣装は渡した静止画に寄る。"
            f"動きの文が空の区間は blocked になり、その区間のプロンプトは空のまま。"
            f"既定は steps {STEPS}、LoRA なし、本体は {MODEL_FILE}。"
            f"横は 1344x768、縦は 768x1344、24fps。参照画像は 9 枚まで。"
            f"--lightning を付けると steps が {STEPS} から {LIGHTNING_STEPS} になり、"
            f"{LIGHTNING_FILE} が強さ 1 で載る。"
        ),
        give="動きの英文が入ったシート、人物と場所の静止画、元動画。",
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
    "reproduce": Lane(
        id="reproduce",
        title="渡した動画を測って、完全再現のプロンプトと LoRA の採否を書く",
        effect=(
            "ローカルの動画を ffprobe とシーン検出で測り、範囲ごとに Ref2VA の6節を書く。"
            "秒・カット・カメラは測った値だけ。見ていない動作の文は足さない。"
            "動画だけなら見た目もその動画。人物の静止画を役つきで渡すと、顔と衣装だけ静止画、動きとカメラは動画。"
            "既定の LoRA は空。speed、combat、charswap、anime2real、百裂は採否に出して、載せない。"
            f"--lightning のときだけ {LIGHTNING_FILE} が強さ 1、steps {LIGHTNING_STEPS}。"
            "リンクだけでは映像を測れず、プロンプトは出さない。"
        ),
        give="動画ファイル1本。または役を付けた静止画。動きの英文は任意。リンクだけは測れない。",
        when="動画のリンクか素材を渡して、完全再現の H3 プロンプトと、必要な LoRA を出したいとき。",
        story="測った範囲だけ。新しい話は書かない。渡した英文がある範囲だけ、その文を足す。",
        prompt="Ref2VA の6節。英語。日本語は <d>[Japanese] の中だけ。見ていない動作は書かない。",
        quality=f"公式 {MODEL_FILE}。steps {STEPS}。横 1344x768、縦 768x1344。24fps。",
        speed=f"既定は LoRA なし、steps {STEPS}。--lightning のときだけ steps {LIGHTNING_STEPS}。",
        loras="既定なし。採否の一覧に、載せない LoRA のファイル名と理由を書く。",
        code="h3/reproduce.py",
        present=True,
        words=("完全再現", "reproduce", "丸投げ"),
    ),
    "fast_motion": Lane(
        id="fast_motion",
        title="最初の静止画から、縦の短い動きを出す",
        effect=(
            "最初の1枚から縦動画の計画になる。最後の絵は受け付けない。"
            "6秒を選ぶと 768x1344、158フレーム（実尺 6.583秒）。"
            "9秒を選ぶと 640x1152、226フレーム（実尺 9.417秒）。"
            "speed LoRA が常に強さ 1.0 で載り、steps は 9、video shift は 6。"
            "action を足すと Motion Repair V2 が強さ 0.6 でその上に載る。"
            "combat を足すと Combat V2 が強さ 0.7 で載る。格闘トリガー prfight2 は付かない。"
            "High-Mem。公式 API では止まる。"
        ),
        give="最初の静止画。尺は 6 か 9。任意で action と combat。",
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
        title="最初の絵と最後の絵で、格闘の1本にする",
        effect=(
            "最初の絵から始まり、終端で最後の絵の構図に着く FL2VA になる。"
            "Combat V2 が強さ 1.0 で1枚だけ載る。Turbo と Motion Repair は同じサンプラーに積まない。"
            "finish を切っているときはプロンプトのトリガーが prfight2。"
            "finish を入れるとトリガーが prfight2, prfin1 になり、決めの語が付く。強さは 1.0 のまま。"
            "尺は 4 秒から 5 秒、既定 5 秒。縦 768x1344、24fps、768P。"
            "High-Mem。公式 API では止まる。"
        ),
        give="最初の静止画と最後の静止画。finish は決めの語を足すスイッチ。",
        when="格闘の1本。最後の絵まで含めて決めを出すとき。",
        story="戦闘の動き。アフィの日常台本には使わない。",
        prompt="FL2VA。finish のときだけ prfight2, prfin1。",
        quality="High-Mem。Turbo は切る。縦 768x1344。既定 5 秒。",
        speed="combat 1.0。speed や action とは同じサンプラーに積まない。",
        loras="H3_Combat_V2.safetensors 強さ 1.0。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("combat_motion", "格闘", "prfight2"),
    ),
    "swap_character": Lane(
        id="swap_character",
        title="動画の動きを残し、全身を静止画に差し替える",
        effect=(
            "動きは Video のまま。全身・顔・髪・服は Picture の静止画に置き換わる。"
            "charswap が強さ 1.0 で1枚だけ載る。Turbo は切れる。"
            "尺は 4 秒から 5 秒、既定 5 秒。縦 768x1344。"
            "High-Mem。公式 API ではこの LoRA を読めず止まる。"
        ),
        give="動きの動画と、全身の静止画。Hero シートが要る。",
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
        title="動画の服と動きを残し、顔と髪だけ差し替える",
        effect=(
            "顔と髪だけが Picture の静止画になる。服と動きは Video のまま。"
            "載る LoRA は swap_character と同じ charswap 強さ 1.0 の1枚。"
            "Turbo は切れる。尺は 4 秒から 5 秒、既定 5 秒。縦 768x1344。"
            "High-Mem。公式 API では止まる。"
        ),
        give="動きの動画と、顔と髪の静止画。Hero シートが要る。",
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
        title="動画の顔と動きを残し、服だけ差し替える",
        effect=(
            "服だけが Picture の静止画になる。顔と動きは Video のまま。"
            "載る LoRA は同じ charswap 強さ 1.0 の1枚。Turbo は切れる。"
            "尺は 4 秒から 5 秒、既定 5 秒。縦 768x1344。"
            "High-Mem。公式 API では止まる。"
        ),
        give="動きの動画と、服の静止画。Hero シートが要る。",
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
        title="描いた動画を、実写寄せの LoRA に通す",
        effect=(
            "Anime2Realsim が強さ 1.0 で1枚だけ載る。他の LoRA と同じサンプラーには積めない。"
            "動画を渡すと Ref2VA になり、見た目は Picture、動きは Video。"
            "静止画だけなら、その1枚を首尾に置いた FL2VA になる。"
            "lumireal を入れるとプロンプトに LumiReal が書かれる。"
            "尺は 4 秒から 5 秒、既定 5 秒。縦 768x1344。High-Mem。公式 API では止まる。"
            "シートのリメイクは live_remake。こちらは別ジョブ。"
        ),
        give="見た目の静止画。動きを残すなら、その動画も。",
        when="描いた動画を、別ジョブの実写 LoRA で寄せるとき。リメイクシートではない。",
        story="元の動きの動画があるとき。シートのリメイクは live_remake。",
        prompt="Ref2VA。ref-en の6節。静止画だけなら FL2VA。",
        quality="anime2real は charswap と同じサンプラーに積まない。High-Mem。",
        speed="LoRA は1枚だけ。強さ 1.0。",
        loras="Anime2Realsim__H3.safetensors 強さ 1.0。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("anime2real", "実写LoRA"),
    ),
    "text_scene": Lane(
        id="text_scene",
        title="静止画なしで、文から1シーンのプロンプトを作る",
        effect=(
            "静止画も動画も使わない。英語の action 1本から T2VA の3節ができる。LoRA は付かない。"
            "1本の計画は縦 768x1344、既定 5 秒（4 秒から 5 秒）。"
            "7本バッチは各 6 秒、横 1344x768、16:9、768P。こちらも LoRA は付かない。"
            "場所は Hero の place。空欄は文に出ない。"
        ),
        give="英語の action 1本。せりふがあるなら「」の中の日本語1つ。",
        when="静止画も動画も無く、文から1シーンを作るとき。",
        story="場所は Hero の place。空欄は書かない。",
        prompt="T2VA。base-en。英語。せりふの原文だけ残す。",
        quality="1本は縦 768x1344、既定 5 秒。7本バッチは 6 秒、横 1344x768。LoRA なし。",
        speed="公式の T2VA。Turbo のファイルは載らない。",
        loras="なし。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("text_scene", "文から"),
    ),
    "orbit360": Lane(
        id="orbit360",
        title="同じ1枚を一周させて、最初の構図に戻す",
        effect=(
            "同じ絵が最初と最後に置かれる。被写体が一周して、最初のポーズと構図に戻る FL2VA になる。"
            "カメラはその周りを小さい幅でゆっくり回る、とプロンプトに書かれる。"
            "LoRA のファイル名が未確定なので、LoRA は付かない。"
            "尺は 4 秒から 5 秒、既定 5 秒。"
        ),
        give="同じ静止画1枚。別の最後の絵は受け付けない。",
        when="同じ絵を首尾で回すとき。",
        story="1枚の絵。別の話は足さない。",
        prompt="FL2VA。",
        quality="LoRA のファイル名が未確定なので積まない。既定 5 秒。",
        speed="素の FL2VA。",
        loras="なし。",
        code="colab/h3_studio.py（cursor/h3-continuum-chunk-0ff5）",
        present=False,
        words=("orbit360", "首尾"),
    ),
    "two_pass": Lane(
        id="two_pass",
        title="1本目の動画を、2本目の参照動画に渡す",
        effect=(
            "A の mp4 が B の Video 1 になる。LoRA はパスごとに分かれる。"
            "A が差し替えで B が real のとき、A は charswap 1.0、B は anime2real 1.0。"
            "同じサンプラーに charswap 強さ 0.5 で重ねる指定は使わない。"
            "その並びのとき、B のプロンプトに LumiReal が書かれる。"
            "B に渡せるのは swap か real。"
        ),
        give="A と B のジョブを2つ。B は動画を受け取るジョブ。",
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
        title="できた短いクリップを切って、15秒以上につなぐ",
        effect=(
            "生成は走らない。出来ている 6 秒指定と 9 秒指定のクリップを、指定した秒で切って 1080x1920 でつなぐ。"
            "合計は 15 秒以上。1本の H3 生成で 15 秒は出せない。"
            "6秒指定の生成物は 158 フレーム（6.583秒）、9秒指定は 226 フレーム（9.417秒）なので、つなぐときに指定秒へ切る。"
        ),
        give="すでに出来ている 6 秒と 9 秒の mp4。並びの合計が 15 秒以上。",
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
        title="既存のバズ型台本を、名前で指す",
        effect=(
            "台本は増えない。名前で既存ファイルを指すだけ。"
            "buy_before は悩み・不一致を先に出す型。"
            "daily_food は日常の同じ子（犬のごはん）。"
            "daily_camera は日常の同じ子（見守り）。"
            "このジョブでは LoRA を積まず、生成もしない。"
        ),
        give="buy_before、daily_food、daily_camera のどれか。",
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
        title="長い文を短いチャンクに分け、latent で1本につなぐ",
        effect=(
            "渡した英語が 5 秒から 8 秒のチャンクに分かれる。既定のチャンクは 5 秒。最大 16 個。"
            "チャンク同士は latent continuity でつながり、最後に Assemble で mp4 が1本になる計画になる。"
            "総尺は 5 秒以上。LoRA は付かない。"
            "runtime を api にすると止まる。使うサンプラーは Comfy の H3 Continuum Sampler。"
        ),
        give="英語の action と、5 秒以上の総尺。チャンク秒は 5 から 8。",
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
        title="アフィ焼きに、打撃が後ろほど速くなるスライダーを足す",
        effect=(
            "オフのときは Turbo 強さ 1.0（steps 9、video shift 6）と Motion Repair 強さ 0.6 だけ。"
            "オンにすると、その2枚に progressive_acceleration_slider_v1.0.safetensors が強さ 4 で足される。"
            "連続の打撃が、後ろの打撃ほど速くなる。"
            "カードの範囲は -8 から 8。0 未満は渡さない。"
            "せりふの文字は焼きのプロンプトに入らない。"
        ),
        give="既存のアフィ台本。百裂はオンにしたときだけ。",
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
                    f"機能: {item.title}",
                    f"入れると: {item.effect}",
                    f"渡すもの: {item.give}",
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
    if args and args[0] == "reproduce":
        return reproduce_main(args[1:])
    try:
        text = render(args[0] if args else None)
    except DeskError as exc:
        print(f"DESK STOP: {exc}")
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
