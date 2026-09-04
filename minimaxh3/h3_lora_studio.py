"""Colab helper for stacking MiniMax H3 LoRAs.

SFW: turbo + one quality LoRA. Adult: act + optional helper + optional thin turbo.
Cinema replaces helper. CoachBate anal stays turbo off.
Larry and LightX2V never stack. Adults 21+ only. Never print API keys.
Fal H3 Max cannot take LoRAs — this is local Comfy FL2VA only.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

STUDIO_ROOT = Path(__file__).resolve().parents[1] / "h3-lora-studio"
if not STUDIO_ROOT.is_dir():
    STUDIO_ROOT = Path("/content/h3-lora-studio")

OPTIONAL_IDS = {
    "astro-nsfw-h3": 0.35,
    "tiddies-realism-slider": 1.2,
    "h3-realism-people": 1.0,
    "photoreal-h3-still": 1.0,
}

SITUATION_DOWNLOAD = {
    "vanilla": [],
    "sfw_daily": ["larry-v4", "cinema-dy"],
    "sfw_preview": ["minimax-h3-turbo-fl2v-4step", "cinema-dy"],
    "sfw_audio": ["minimax-h3-turbo-fl2v-8step", "cinema-dy"],
    "sfw_r2v": ["minimax-h3-turbo-ref2v-4step", "cinema-dy"],
    "anal_closeup": ["synth-pussy-h3", "larry-v4", "cinema-dy"],
    "anal_penetration": ["anal-penetration-coachbate", "synth-pussy-h3"],
    "futa_blowjob": ["blowjob-h3", "penis-lora-h3", "larry-v4"],
    "oral": ["blowjob-h3", "penis-lora-h3", "larry-v4"],
    "general_sex": ["hmnsfw-aio-v25", "minimax-h3-turbo-fl2v-4step"],
    "preview": ["hmnsfw-aio-v25", "minimax-h3-turbo-fl2v-4step"],
    "riding": ["hmnsfw-aio-v25", "minimax-h3-turbo-fl2v-4step"],
}

SITUATION_JA = {
    "普通（エロなし）": "vanilla",
    "日常（速い＋綺麗）": "sfw_daily",
    "最速プレビュー（エロなし）": "sfw_preview",
    "音も残す（エロなし）": "sfw_audio",
    "アナル挿入（画質）": "anal_penetration",
    "アナル挿入": "anal_penetration",
    "アナル舐め・指": "anal_closeup",
    "穴アップ（舐め・指）": "anal_closeup",
    "フェラ": "oral",
    "ふたなりフェラ": "futa_blowjob",
    "汎用エロ": "general_sex",
    "試し打ち": "preview",
    "騎乗位": "riding",
    "vanilla": "vanilla",
    "sfw_daily": "sfw_daily",
    "sfw_preview": "sfw_preview",
    "sfw_audio": "sfw_audio",
    "sfw_r2v": "sfw_r2v",
    "anal_closeup": "anal_closeup",
    "anal_penetration": "anal_penetration",
    "futa_blowjob": "futa_blowjob",
    "oral": "oral",
    "general_sex": "general_sex",
    "preview": "preview",
    "riding": "riding",
}

MODE_JA = {
    "テキストから（写真なし）": "t2v",
    "写真から（1枚必要）": "i2v",
    "t2v": "t2v",
    "i2v": "i2v",
}

SITUATION_HELP = {
    "vanilla": "専用 I2V / T2V ノートと同じ。LightX2V 4step だけ。画質 LoRA なし。",
    "sfw_daily": "日常・会話・商品・風景。Larry v4 1.0 + シネマ 0.65 / 8step。エロ用は入れない。",
    "sfw_preview": "エロなしの最速プレビュー。LightX2V 4step 1.0 + シネマ 0.4。当たりは日常で焼き直す。",
    "sfw_audio": "音を残して速く。LightX2V 8step 1.0 + シネマ 0.4。歌・日本語は日常（Larry）の方が安定。",
    "sfw_r2v": "顔固定 R2V。LightX2V Ref2VA 4step + シネマ 0.5。FL2VA 用 Turbo は積まない。このノートでは選ばない。",
    "anal_closeup": "舐め・指。穴の見え方 0.7 + Larry 0.5 + シネマ 0.4。行為は1本だけ。",
    "anal_penetration": "アナル挿入の本線。CoachBate 0.85 + 穴の見え方 0.55。Turbo なし。12〜20 step。",
    "futa_blowjob": "ふたなりフェラ。フェラ + 竿 + Larry 0.7。AIO とふたなり部品は足さない。",
    "oral": "フェラ本線。フェラ 0.75 + 竿 0.7 + Larry 0.7。",
    "general_sex": "汎用エロ。AIO 0.75 + LightX2V 0.5 / 12 step。穴が曖昧でいいとき。",
    "preview": "試し打ち。AIO 0.7 + LightX2V 4step。当たりだけ本線で焼き直す。",
    "riding": "騎乗は汎用エロと同じ薄い積み。",
}

LORA_JA = {
    "synth-pussy-h3": "穴の見え方",
    "anal-penetration-coachbate": "アナル挿入",
    "hmnsfw-aio-v25": "総合えっち",
    "futa-h3-v51": "ふたなり",
    "penis-lora-h3": "竿",
    "blowjob-h3": "フェラ",
    "riding-pose-i2v": "騎乗のポーズ",
    "h3-realism-people": "肌のリアルさ",
    "tiddies-realism-slider": "胸の大きさ",
    "larry-v4": "Larry v4",
    "cinema-dy": "シネマ質感",
    "astro-cinema-h3": "映画レンズ",
    "minimax-h3-turbo-fl2v-4step": "LightX2V 4step",
    "minimax-h3-turbo-fl2v-8step": "LightX2V 8step",
    "minimax-h3-turbo-ref2v-4step": "LightX2V Ref2VA",
    "photoreal-h3-still": "静止画用の写実",
}

SFW_SITUATIONS = {"sfw_daily", "sfw_preview", "sfw_audio", "sfw_r2v"}


def resolve_situation(name: str) -> str:
    key = str(name or "").strip()
    if key in SITUATION_JA:
        return SITUATION_JA[key]
    raise SystemExit(
        "シーンの名前が分かりません。フォームのリストから選んでください。"
        f" 入力: {name}"
    )


def resolve_mode(name: str) -> str:
    key = str(name or "").strip()
    if key in MODE_JA:
        return MODE_JA[key]
    raise SystemExit("作り方は「テキストから（写真なし）」か「写真から（1枚必要）」を選んでください。")


def friendly_lora(lora_id: str) -> str:
    return LORA_JA.get(str(lora_id), str(lora_id))


def is_vanilla(situation: str) -> bool:
    return resolve_situation(situation) == "vanilla"


def explain_choice(situation: str, mode: str) -> str:
    sid = resolve_situation(situation)
    mid = resolve_mode(mode)
    how = "テキストから動画（写真は使いません）" if mid == "t2v" else "写真1枚から動画（Drive の input に jpg）"
    if sid == "vanilla":
        return (
            f"シーン: {situation}\n"
            f"作り方: {how}\n"
            f"説明: {SITUATION_HELP[sid]}\n"
            "えっち用の部品は使いません。速いモード（Turbo）を使います。"
        )
    parts = "、".join(friendly_lora(x) for x in SITUATION_DOWNLOAD[sid])
    cap = (
        "重ね上限は Turbo1 + 画質1。エロ用は入れません。"
        if sid in SFW_SITUATIONS
        else "重ね上限は 行為1 + ヘルパー1 + Turbo1。Fal には載せません。"
    )
    return (
        f"シーン: {situation}\n"
        f"作り方: {how}\n"
        f"説明: {SITUATION_HELP[sid]}\n"
        f"使う部品: {parts}\n"
        + cap
    )


def civitai_token(form_value: str = "") -> str:
    """Read Civitai API key. Form paste first, then Colab secret, then env. Never print it."""
    pasted = str(form_value or "").strip()
    if pasted:
        return pasted
    for getter in (_colab_userdata_token, lambda: os.environ.get("CIVITAI_API_TOKEN") or ""):
        try:
            raw = getter()
        except Exception:
            raw = ""
        token = str(raw or "").strip()
        if token:
            return token
    return ""


def _colab_userdata_token() -> str:
    from google.colab import userdata  # type: ignore

    return str(userdata.get("CIVITAI_API_TOKEN") or "")


def missing_civitai_files(
    jobs: list[tuple[str, Path, dict[str, Any]]],
    *,
    min_bytes: int = 1_000_000,
) -> list[str]:
    names: list[str] = []
    for _url, dest, row in jobs:
        if str(row.get("source") or "") != "civitai":
            continue
        if dest.is_file() and dest.stat().st_size > min_bytes:
            continue
        names.append(dest.name)
    return names


def civitai_token_help() -> str:
    return (
        "Civitai の API キーが空です。シークレットは使わなくて大丈夫です。\n"
        "1. https://civitai.com/user/account を開く（ログイン）\n"
        "2. 下のほうの API Keys → Add API key → 作った文字列をコピー\n"
        "3. ②セルの「CivitaiのAPIキー」欄に貼る\n"
        "4. ②をもう一度実行\n"
        "キー自体は画面に出しません。ノートを保存・共有する前に欄を空に戻してください。"
    )


def load_catalog(studio_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(studio_root or STUDIO_ROOT)
    path = root / "catalog" / "loras.json"
    return json.loads(path.read_text(encoding="utf-8"))


def catalog_by_id(catalog: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = catalog or load_catalog()
    return {str(row["id"]): row for row in data.get("loras") or [] if row.get("id")}


def civitai_download_url(row: dict[str, Any]) -> str:
    version = int(row["civitai_version_id"])
    file_id = int(row["civitai_file_id"])
    return f"https://civitai.com/api/download/models/{version}?fileId={file_id}"


def download_jobs_for(
    ids: list[str],
    lora_dir: Path | str,
    *,
    catalog: dict[str, Any] | None = None,
) -> list[tuple[str, Path, dict[str, Any]]]:
    index = catalog_by_id(catalog)
    dest_dir = Path(lora_dir)
    jobs: list[tuple[str, Path, dict[str, Any]]] = []
    seen: set[str] = set()
    for lid in ids:
        if lid in seen:
            continue
        seen.add(lid)
        row = index.get(lid)
        if row is None:
            raise SystemExit(f"unknown LoRA id: {lid}")
        dest = dest_dir / str(row["filename"])
        source = str(row.get("source") or "hf")
        if source == "civitai":
            url = civitai_download_url(row)
        elif row.get("repo") and not str(row["repo"]).startswith("civitai:"):
            url = (
                "https://huggingface.co/"
                + str(row["repo"])
                + "/resolve/main/"
                + str(row.get("file") or row["filename"])
            )
        else:
            continue
        jobs.append((url, dest, row))
    return jobs


def fetch_weight(
    url: str,
    dest: Path,
    *,
    token: str = "",
    auth: str = "",
    min_bytes: int = 1_000_000,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file() and dest.stat().st_size > min_bytes:
        print(f"skip {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")
        return
    tmp = dest.with_name(dest.name + ".part")
    headers = {"User-Agent": "h3-lora-studio/colab"}
    if auth == "civitai" and token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=600) as resp, open(tmp, "wb") as out:
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                out.write(chunk)
    except urllib.error.HTTPError as exc:
        if tmp.exists():
            tmp.unlink()
        if exc.code in {401, 403}:
            raise SystemExit(
                f"Civitai が {exc.code} を返した: {dest.name}。\n"
                + civitai_token_help()
            ) from exc
        raise SystemExit(f"DL 失敗 {exc.code}: {dest.name}") from exc
    if not tmp.is_file() or tmp.stat().st_size < min_bytes:
        if tmp.exists():
            tmp.unlink()
        raise SystemExit(f"DL 失敗（小さい）: {dest.name}")
    tmp.replace(dest)
    print(f"saved {dest.name} ({dest.stat().st_size / 1e6:.1f} MB)")


def inject_lora_stack(
    g: dict[str, Any],
    stack: list[dict[str, Any]],
    *,
    steps: int | None = None,
    sampler: dict[str, Any] | None = None,
    unet_node: str = "1",
) -> dict[str, Any]:
    """Chain LoraLoaderModelOnly. Sampler comes from the situation plan."""
    if g.get("2", {}).get("class_type") == "LoraLoaderModelOnly":
        del g["2"]
    prev = unet_node
    last = unet_node
    for i, item in enumerate(stack, start=1):
        name = str(item.get("filename") or item.get("lora_name") or "")
        if not name:
            raise ValueError("stack item needs filename")
        nid = str(200 + i)
        g[nid] = {
            "class_type": "LoraLoaderModelOnly",
            "inputs": {
                "model": [prev, 0],
                "lora_name": name,
                "strength_model": float(item.get("strength_model", item.get("strength", 1.0))),
            },
        }
        prev = nid
        last = nid
    model = [last, 0] if stack else [unet_node, 0]
    plan = sampler or {
        "sampler_name": "res_multistep",
        "scheduler": "beta",
        "steps": max(int(steps or 16), 16),
    }
    if "22" in g:
        g["22"]["inputs"]["sampler_name"] = str(plan.get("sampler_name") or "res_multistep")
    if "23" in g:
        g["23"]["inputs"]["model"] = model
        g["23"]["inputs"]["scheduler"] = str(plan.get("scheduler") or "beta")
        g["23"]["inputs"]["steps"] = int(plan.get("steps") or steps or 16)
    if "24" in g:
        g["24"]["inputs"]["model"] = model
    return g


def merge_optional(
    stack: list[dict[str, Any]],
    *,
    extras: list[str],
    catalog: dict[str, Any] | None = None,
    mode: str = "t2v",
) -> list[dict[str, Any]]:
    """Extras stay off. Three quality LoRAs collapse hole, shaft, and face."""
    del catalog, mode
    if extras:
        print("上級の追加部品は重ね上限（行為1+ヘルパー1+Turbo1）のため無視します。")
    return list(stack)


def situation_ids(situation: str) -> list[str]:
    if situation not in SITUATION_DOWNLOAD:
        raise SystemExit(f"unknown situation: {situation}")
    return list(SITUATION_DOWNLOAD[situation])


BLANK_PROMPTS = {"", "（シーン）", "(シーン)", "シーン", "scene", "auto", "おすすめ"}
I2V_CUSTOM_LOCK = (
    "For the target video, at 0.00 seconds into the target video, "
    "<Picture 1> (from [Shot 1]) is fully referenced.\n\n"
    "subject_definitions:\n"
    "<Subject 1> Adult, clearly over 21, same face body and hair as <Picture 1>.\n\n"
)


def is_blank_prompt(text: str | None) -> bool:
    return str(text or "").strip() in BLANK_PROMPTS


def apply_user_prompt(user_text: str | None, *, mode: str, default_prompt: str = "") -> tuple[str, bool]:
    """Empty → default scene. Custom I2V gets a Picture 1 lock if the user omitted it."""
    raw = str(user_text or "").strip()
    if is_blank_prompt(raw):
        return str(default_prompt or ""), False
    if str(mode).lower() == "i2v" and "Picture 1" not in raw:
        wrapped = (
            I2V_CUSTOM_LOCK
            + "integrated_multimodal_description: "
            + raw
            + " Identity of (S1) stays locked to <Picture 1>. Photoreal. No freeze frame.\n"
            "overall_soundscape: Natural ambient sound.\n"
            "All performers are consenting adults 21 years or older."
        )
        return wrapped, True
    return raw, True


def prepend_triggers(prompt: str, stack: list[dict[str, Any]]) -> str:
    triggers = []
    low = prompt.lower()
    for item in stack:
        trig = str(item.get("trigger") or "").strip()
        if trig and trig.lower() not in low:
            triggers.append(trig)
    if not triggers:
        return prompt
    return ", ".join(triggers) + "\n" + prompt


def assert_no_secret_text(text: str) -> None:
    blob = text.lower()
    if "civitai_api_token=" in blob or "xai_api_key=" in blob:
        raise SystemExit("refusing to print API keys")


def studio_sys_path(studio_root: Path | str | None = None) -> None:
    root = Path(studio_root or STUDIO_ROOT)
    scripts = root / "scripts"
    if str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
