"""Re-render the Imagine retrofit shorts and the kane videos that have picture.

Source audio is dropped. Narration, a 15% bed, and the last 2 seconds of PR
are added here. Nothing is posted.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
import sys
import urllib.parse
import urllib.request
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from finish_with_narration import (  # noqa: E402
    LINE_GAP_SEC,
    SR,
    FinishError,
    atempo,
    audio_stream_count,
    concat_pictures,
    duration_of,
    extract_muted_picture,
    mix_voice_and_bgm,
    mux,
    place_lines,
    probe,
    read_wav,
    resample,
    run,
    squeeze_internal_silence,
    trim_silence,
    write_bed,
    write_wav,
)

RETRO = Path("/tmp/pulls/retrofit/affiliate-shorts/v2/retrofit")
KANE = Path("/tmp/pulls/kane/affiliate-shorts/v2/kane")
OUT = Path("/workspace/affiliate-shorts/v3-fix")
FONT = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
VOICEVOX = "http://127.0.0.1:50021"
HIMARI = 14
MOCHIKO = 20


def parse_srt(text: str) -> list[dict]:
    cues = []
    blocks = re.split(r"\n\s*\n", text.strip())
    for block in blocks:
        lines = [line for line in block.splitlines() if line.strip() != ""]
        if len(lines) < 2:
            continue
        match = re.match(
            r"(\d+):(\d+):(\d+),(\d+)\s+-->\s+(\d+):(\d+):(\d+),(\d+)",
            lines[1] if "-->" in lines[1] else lines[0],
        )
        if match is None and len(lines) > 2:
            match = re.match(
                r"(\d+):(\d+):(\d+),(\d+)\s+-->\s+(\d+):(\d+):(\d+),(\d+)",
                lines[1],
            )
        if match is None:
            continue
        nums = [int(value) for value in match.groups()]
        start = nums[0] * 3600 + nums[1] * 60 + nums[2] + nums[3] / 1000
        end = nums[4] * 3600 + nums[5] * 60 + nums[6] + nums[7] / 1000
        body = lines[2:] if "-->" in lines[1] else lines[1:]
        if body and body[0].isdigit() and "-->" in lines[1]:
            body = lines[2:]
        cues.append({"start": start, "end": end, "lines": body})
    return cues


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3600000)
    m, ms = divmod(ms, 60000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(path: Path, cues: list[dict]) -> None:
    chunks = []
    for index, cue in enumerate(cues, start=1):
        chunks.append(
            f"{index}\n{srt_time(cue['start'])} --> {srt_time(cue['end'])}\n" + "\n".join(cue["lines"]) + "\n"
        )
    path.write_text("\n".join(chunks), encoding="utf-8")


def voicevox(text: str, speaker: int, speed: float, work: Path, name: str) -> np.ndarray:
    query_url = VOICEVOX + "/audio_query?text=" + urllib.parse.quote(text) + f"&speaker={speaker}"
    request = urllib.request.Request(query_url, data=b"", method="POST")
    query = json.load(urllib.request.urlopen(request))
    query["speedScale"] = speed
    query["pitchScale"] = 0.0
    query["intonationScale"] = 0.85
    query["volumeScale"] = 1.0
    query["prePhonemeLength"] = 0.05
    query["postPhonemeLength"] = 0.06
    synth = urllib.request.Request(
        f"{VOICEVOX}/synthesis?speaker={speaker}",
        data=json.dumps(query).encode(),
        headers={"Content-Type": "application/json"},
    )
    wav_path = work / f"{name}.wav"
    if not (wav_path.exists() and wav_path.stat().st_size > 1000):
        wav_path.write_bytes(urllib.request.urlopen(synth).read())
    samples, sr = read_wav(wav_path)
    trimmed = trim_silence(resample(samples, sr), SR)
    if speed >= 1.1:
        trimmed = squeeze_internal_silence(trimmed, SR)
    return trimmed


def add_yomi(path: Path) -> None:
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        parts = line.split(",")
        if len(parts) < 3 or not parts[0].strip() or parts[0].startswith("#"):
            continue
        surface, pron, accent = parts[0].strip(), parts[1].strip(), parts[2].strip()
        if not pron:
            continue
        accent_i = int(accent) if accent.isdigit() else 1
        if accent_i < 1:
            accent_i = 1
        url = (
            VOICEVOX
            + "/user_dict_word?surface="
            + urllib.parse.quote(surface)
            + "&pronunciation="
            + urllib.parse.quote(pron)
            + f"&accent_type={accent_i}"
        )
        request = urllib.request.Request(url, data=b"", method="POST")
        try:
            urllib.request.urlopen(request)
        except urllib.error.HTTPError:
            continue


class Amitaro:
    def __init__(self) -> None:
        from style_bert_vits2.constants import Languages
        from style_bert_vits2.nlp import bert_models
        from style_bert_vits2.tts_model import TTSModel

        self.languages = Languages
        model = bert_models.load_model(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
        model.float()
        bert_models.load_tokenizer(Languages.JP, "ku-nlp/deberta-v2-large-japanese-char-wwm")
        root = Path("/tmp/models/sbv2_amitaro/amitaro")
        self.model = TTSModel(
            root / "amitaro.safetensors",
            root / "config.json",
            root / "style_vectors.npy",
            device="cpu",
        )

    def speak(self, text: str) -> np.ndarray:
        cache = Path("/tmp/v3cache/amitaro")
        cache.mkdir(parents=True, exist_ok=True)
        cached = cache / (hashlib.sha1(text.encode("utf-8")).hexdigest()[:16] + ".wav")
        if cached.exists() and cached.stat().st_size > 1000:
            samples, sr = read_wav(cached)
            return trim_silence(resample(samples, sr), SR)
        sr, audio = self.model.infer(
            text,
            language=self.languages.JP,
            style="Neutral",
            length=0.95,
            sdp_ratio=0.2,
            line_split=False,
            pitch_scale=1.0,
            intonation_scale=1.0,
        )
        pcm = np.asarray(audio).astype(np.float32)
        if pcm.dtype == np.float32 and np.max(np.abs(pcm)) > 2:
            pcm = pcm / 32768.0
        if np.issubdtype(np.asarray(audio).dtype, np.integer):
            pcm = np.asarray(audio).astype(np.float32) / 32768.0
        trimmed = trim_silence(resample(pcm, SR), SR)
        write_wav(cached, trimmed)
        return trimmed


def fit_span(chunks: list[np.ndarray], span: float, work: Path) -> list[np.ndarray]:
    gap = 0.12
    total = sum(len(chunk) / SR for chunk in chunks) + gap * (len(chunks) - 1)
    limit = max(0.4, span - 0.05)
    if total <= limit:
        return chunks
    factor = total / limit
    return [atempo(chunk, SR, factor, work / f"fit{i}") for i, chunk in enumerate(chunks)]


def burn_and_panels(picture: Path, dst: Path, events: list[dict], fps: int) -> None:
    if not events:
        shutil.copy(picture, dst)
        return
    filters = []
    tmp = dst.parent / "_text"
    tmp.mkdir(parents=True, exist_ok=True)
    for index, event in enumerate(events):
        start = event["start"]
        end = event["end"]
        enable = f"enable='between(t\\,{start:.3f}\\,{end:.3f})'"
        if event["kind"] == "bar":
            y = event.get("y", 1500)
            filters.append(f"drawbox=x=40:y={y}:w=1000:h={event.get('h', 220)}:color={event['box']}:t=fill:{enable}")
            for line_i, line in enumerate(event["lines"]):
                text_path = tmp / f"{index}_{line_i}.txt"
                text_path.write_text(line, encoding="utf-8")
                filters.append(
                    "drawtext="
                    f"fontfile={FONT}:textfile={text_path}:fontsize={event.get('size', 52)}:"
                    f"fontcolor={event['color']}:x=(w-text_w)/2:y={y + 28 + line_i * 68}:{enable}"
                )
        elif event["kind"] == "panel":
            # Slides up over the last 2 seconds and hides the burned CTA line.
            filters.append(
                f"drawbox=x=0:y='if(lt(t-{start:.3f}\\,0.28)\\,h-((t-{start:.3f})/0.28)*h*0.42\\,h*0.58)':"
                f"w=1080:h=900:color={event['box']}:t=fill:{enable}"
            )
            for line_i, line in enumerate(event["lines"]):
                text_path = tmp / f"{index}_{line_i}.txt"
                text_path.write_text(line, encoding="utf-8")
                filters.append(
                    "drawtext="
                    f"fontfile={FONT}:textfile={text_path}:fontsize={event.get('size', 54)}:"
                    f"fontcolor={event['color']}:x=(w-text_w)/2:y={1180 + line_i * 90}:{enable}"
                )
    run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(picture),
            "-vf",
            ",".join(filters),
            "-an",
            "-r",
            str(fps),
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(dst),
        ]
    )


def render_card(path: Path, fps: int, kind: str, line: str, colors: tuple[tuple[int, int, int], tuple[int, int, int], tuple[int, int, int]]) -> None:
    bg, accent, ink = colors
    width, height = 1080, 1920
    frames = fps * 2
    font = ImageFont.truetype(FONT, 64, index=0)
    small = ImageFont.truetype(FONT, 36, index=0)
    raw = path.with_suffix(".rgb")
    with raw.open("wb") as handle:
        for frame_i in range(frames):
            t = frame_i / fps
            image = Image.new("RGB", (width, height), bg)
            draw = ImageDraw.Draw(image)
            if kind == "stamp":
                radius = int(150 + 70 * np.sin(t * 3.1))
                draw.ellipse((540 - radius, 760 - radius, 540 + radius, 760 + radius), outline=accent, width=14)
                draw.ellipse((500, 720, 580, 800), fill=accent)
            elif kind == "ribbon":
                shift = int((1 - min(1.0, t / 0.45)) * 400 + np.sin(t * 2.6) * 50)
                draw.polygon([(0, 980 + shift), (1080, 760 + shift), (1080, 980 + shift), (0, 1200 + shift)], fill=accent)
            elif kind == "spot":
                radius = int(60 + (t * 240) % 420)
                draw.ellipse((540 - radius, 900 - radius, 540 + radius, 900 + radius), outline=accent, width=10)
            elif kind == "pulse":
                for ring in range(3):
                    radius = int(80 + ((t * 1.4 + ring * 0.4) % 1.6) * 260)
                    draw.ellipse((540 - radius, 820 - radius, 540 + radius, 820 + radius), outline=accent, width=8)
            elif kind == "lamp":
                radius = int(120 + 80 * np.sin(t * 3.2))
                glow = Image.new("RGB", (width, height), bg)
                gdraw = ImageDraw.Draw(glow)
                gdraw.ellipse((540 - radius, 700 - radius, 540 + radius, 700 + radius), fill=accent)
                image = Image.blend(image, glow, 0.45)
                draw = ImageDraw.Draw(image)
            elif kind == "bounce":
                y = int(420 + abs(np.sin(t * 3.4)) * 80)
                draw.rounded_rectangle((160, y, 920, y + 520), radius=36, fill=accent)
            elif kind == "ticker":
                y = int(640 + (1 - min(1.0, t / 0.55)) * 220 + np.sin(t * 2.2) * 28)
                draw.rectangle((80, y, 1000, y + 280), fill=accent)
            elif kind == "receipt":
                y = int(1500 - min(1.0, t / 0.6) * 700 + np.sin(t * 2.4) * 18)
                draw.rectangle((180, y, 900, y + 640), fill=(247, 241, 222))
                draw.rectangle((180, y, 900, y + 16), fill=accent)
            else:
                raise FinishError(kind)
            # A bar keeps moving for the whole 2 seconds so the card is not a freeze.
            bar_x = int((frame_i * 7) % (width + 140)) - 140
            draw.rectangle((bar_x, height - 48, bar_x + 110, height - 28), fill=accent)
            alpha = min(1.0, max(0.0, (t - 0.15) / 0.25))
            if alpha > 0:
                layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
                odraw = ImageDraw.Draw(layer)
                odraw.text((540, 1240), line, font=font, fill=(*ink, int(255 * alpha)), anchor="mm")
                odraw.text((540, 1360), "#PR", font=small, fill=(*accent, int(255 * alpha)), anchor="mm")
                image = Image.alpha_composite(image.convert("RGBA"), layer).convert("RGB")
            pixels = np.asarray(image).astype(np.int16)
            grain = np.random.default_rng(frame_i).integers(-5, 6, size=pixels.shape, dtype=np.int16)
            image = Image.fromarray(np.clip(pixels + grain, 0, 255).astype(np.uint8))
            handle.write(image.tobytes())
    run(
        [
            "ffmpeg",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            "1080x1920",
            "-r",
            str(fps),
            "-i",
            str(raw),
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-pix_fmt",
            "yuv420p",
            str(path),
        ]
    )
    raw.unlink(missing_ok=True)


def thumbnail(src: Path, dest: Path, title: str, at: float, band: tuple[int, int, int], ink: tuple[int, int, int]) -> None:
    frame = dest.with_suffix(".jpg")
    run(["ffmpeg", "-y", "-ss", f"{at:.3f}", "-i", str(src), "-frames:v", "1", "-update", "1", str(frame)])
    image = Image.open(frame).convert("RGB").resize((1080, 1920), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT, 72, index=0)
    lines = []
    buf = ""
    for char in title:
        buf += char
        if len(buf) >= 9:
            lines.append(buf)
            buf = ""
    if buf:
        lines.append(buf)
    top = 120
    draw.rectangle((0, top - 20, 1080, top + 100 * len(lines) + 20), fill=band)
    for index, line in enumerate(lines):
        draw.text((540, top + 40 + index * 96), line, font=font, fill=ink, anchor="mm")
    image.save(dest, "PNG", optimize=True)
    frame.unlink(missing_ok=True)


def silence_hits(path: Path) -> int:
    result = subprocess_silence(path)
    return result


def subprocess_silence(path: Path) -> int:
    import subprocess

    result = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", "silencedetect=noise=-45dB:d=1.5", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    return result.stderr.count("silence_start")


def freeze_hits(path: Path) -> int:
    import subprocess

    result = subprocess.run(
        ["ffmpeg", "-i", str(path), "-vf", "freezedetect=n=-60dB:d=1.0", "-f", "null", "-"],
        capture_output=True,
        text=True,
    )
    return result.stderr.count("freeze_start")


def voice_onsets(samples: np.ndarray, sr: int) -> list[float]:
    loud = np.abs(samples) >= 0.02
    onsets = []
    prev = False
    for index, flag in enumerate(loud):
        if flag and not prev:
            onsets.append(index / sr)
        prev = bool(flag)
    return onsets


def check_sync(onsets: list[float], starts: list[float]) -> list[float]:
    deltas = []
    for start in starts:
        if not onsets:
            deltas.append(99.0)
            continue
        nearest = min(onsets, key=lambda item: abs(item - start))
        deltas.append(nearest - start)
    return deltas


def kenburns(kind: str, dur: float) -> str:
    if kind == "in":
        expr_x = f"(in_w-1080)*(0.25+0.5*t/{dur:.3f})"
        expr_y = f"(in_h-1920)*(0.25+0.5*t/{dur:.3f})"
    elif kind == "left":
        expr_x = f"(in_w-1080)*(0.8-0.6*t/{dur:.3f})"
        expr_y = "(in_h-1920)*0.45"
    else:
        expr_x = "(in_w-1080)*0.4"
        expr_y = f"(in_h-1920)*(0.15+0.7*t/{dur:.3f})"
    return (
        f"scale=1160:2062,crop=1080:1920:x='{expr_x}':y='{expr_y}',"
        "noise=alls=3:allf=t,setsar=1"
    )


def reset_work(work: Path) -> None:
    """Drop picture files but keep synthesized wavs so a re-render can reuse them."""
    stash = Path("/tmp/v3stash") / work.name
    if stash.exists():
        shutil.rmtree(stash)
    if work.exists():
        shutil.copytree(
            work,
            stash,
            ignore=shutil.ignore_patterns("*.mp4", "*.jpg", "*.rgb", "_text"),
        )
        shutil.rmtree(work)
    work.mkdir(parents=True, exist_ok=True)
    if not stash.exists():
        return
    for path in stash.rglob("*.wav"):
        dest = work / path.relative_to(stash)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)


def grab_frame(video: Path, t: float, dest: Path) -> None:
    run(
        [
            "ffmpeg",
            "-y",
            "-ss",
            f"{max(0.0, t):.3f}",
            "-i",
            str(video),
            "-frames:v",
            "1",
            "-update",
            "1",
            str(dest),
        ]
    )


def burned_caption_box(frame: Path) -> tuple[int, int] | None:
    """Find a thin white caption band baked into an Imagine frame."""
    image = np.asarray(Image.open(frame).convert("RGB"))
    center = image[:, 160:920]
    bright = center.max(axis=2)
    white = ((bright > 175) & (center.min(axis=2) > 120)).mean(axis=1)
    best: tuple[float, int, int] | None = None
    in_band = False
    start = 0
    for y, value in enumerate(white):
        if value > 0.025 and not in_band:
            start = y
            in_band = True
            continue
        if value <= 0.025 and in_band:
            height = y - start
            if 12 <= height <= 80 and 700 <= start <= 1450:
                peak = float(white[start:y].max())
                above = white[max(0, start - 40) : max(0, start - 5)]
                below = white[y + 5 : y + 40]
                nearby = np.concatenate([above, below]) if len(above) or len(below) else np.array([1.0])
                if peak >= 0.045 and float(nearby.mean()) < 0.02:
                    if best is None or peak > best[0]:
                        best = (peak, start, y)
            in_band = False
    if best is None:
        return None
    return best[1], best[2]


def subtitle_event(picture: Path, cue: dict, job: dict, work: Path, index: int, end: float) -> dict:
    frame = work / f"cap{index:02d}.jpg"
    grab_frame(picture, min(cue["start"] + 0.12, max(cue["start"], end - 0.05)), frame)
    found = burned_caption_box(frame)
    lines = cue["lines"]
    if found is None:
        y = int(job["bar_y"])
        height = 70 * len(lines) + 80
    else:
        y0, y1 = found
        y = max(80, y0 - 36)
        height = max(160, (y1 - y0) + 48 + 72 * len(lines))
    if y + height > 1880:
        y = max(80, 1880 - height)
    # Opaque. A translucent bar lets the Imagine caption show through.
    box = str(job["box"]).split("@", 1)[0]
    if box == "black":
        box = "0x14120F"
    return {
        "kind": "bar",
        "start": cue["start"],
        "end": end,
        "lines": lines,
        "box": box,
        "color": job["ink"],
        "y": y,
        "h": height,
        "size": job["size"],
    }


def render_retro(job: dict, speaker) -> dict:
    title = job["title"]
    work = Path("/tmp/v3work") / title
    reset_work(work)
    out = OUT / title
    out.mkdir(parents=True, exist_ok=True)
    src = RETRO / "src" / f"{title}.mp4"
    cues = parse_srt((RETRO / title / "subs.srt").read_text(encoding="utf-8"))
    fps = job["fps"]
    cut = job["cut"]
    if cut is not None:
        body_cues = [cue for cue in cues if cue["end"] <= cut + 0.03 and cue["start"] < cut - 0.02]
        body_end = cut
    else:
        body_cues = [cue for cue in cues if cue["end"] <= job["pr_at"] + 0.02 and "うちの子" not in "".join(cue["lines"])]
        body_end = job["pr_at"]
    spoken: list[tuple[float, np.ndarray]] = []
    new_cues = []
    for cue in body_cues:
        chunks = []
        for line in cue["lines"]:
            chunks.append(speaker(line) if not isinstance(speaker, Amitaro) else speaker.speak(line))
        chunks = fit_span(chunks, cue["end"] - cue["start"], work)
        cursor = cue["start"]
        for chunk in chunks:
            spoken.append((cursor, chunk))
            cursor += len(chunk) / SR + 0.12
        new_cues.append({"start": cue["start"], "end": cue["end"], "lines": cue["lines"]})
    pr_audio = speaker(job["pr_line"]) if not isinstance(speaker, Amitaro) else speaker.speak(job["pr_line"])
    pr_start = body_end
    if len(pr_audio) / SR > 1.85:
        pr_audio = atempo(pr_audio, SR, (len(pr_audio) / SR) / 1.8, work / "pr")
    spoken.append((pr_start + 0.08, pr_audio))
    total = body_end + 2.0
    new_cues.append({"start": pr_start, "end": total, "lines": [job["pr_line"], "#PR"]})
    picture = work / "picture.mp4"
    picture_end = body_end if cut is not None else body_end + 2.0
    extract_muted_picture(src, picture, end=picture_end, fps=fps)
    if job["card"] is None:
        base = picture
        events = [
            subtitle_event(picture, cue, job, work, index, cue["end"])
            for index, cue in enumerate(body_cues)
        ]
        events.append(
            {
                "kind": "panel",
                "start": pr_start,
                "end": total,
                "lines": [job["pr_line"], "#PR"],
                "box": job["panel"],
                "color": "white",
            }
        )
        burned = work / "burned.mp4"
        burn_and_panels(base, burned, events, fps)
        picture = burned
    else:
        card = work / "card.mp4"
        render_card(card, fps, job["card"], job["pr_line"], job["palette"])
        events = [
            subtitle_event(picture, cue, job, work, index, min(cue["end"], body_end))
            for index, cue in enumerate(body_cues)
        ]
        burned = work / "burned.mp4"
        burn_and_panels(picture, burned, events, fps)
        joined = work / "joined.mp4"
        concat_pictures([burned, card], joined, fps)
        picture = joined
    voice = work / "voice.wav"
    bed = work / "bed.wav"
    mix = work / "mix.wav"
    write_wav(voice, place_lines(spoken, total))
    write_bed(bed, total + 0.2, job["bed"])
    mix_voice_and_bgm(voice, bed, mix, total)
    final = out / "video.mp4"
    mux(picture, mix, final)
    write_srt(out / "subs.srt", new_cues)
    thumbnail(final, out / "thumbnail.png", job["thumb"], job["thumb_at"], job["thumb_band"], job["thumb_ink"])
    script = out / "script.md"
    script.write_text(job["script"] + "\n", encoding="utf-8")
    (out / "description.txt").write_text(job["description"].strip() + "\n", encoding="utf-8")
    return finish_report(final, voice, [cue["start"] for cue in new_cues if cue["start"] < pr_start or True], job)


def render_kane(number: str, meta: dict) -> dict:
    src_dir = KANE / number
    title = meta["title"]
    work = Path("/tmp/v3work") / f"kane-{number}"
    reset_work(work)
    out = OUT / title
    out.mkdir(parents=True, exist_ok=True)
    add_yomi(src_dir / "yomi.csv")
    cues = parse_srt((src_dir / "subs.srt").read_text(encoding="utf-8"))
    body = [cue for cue in cues if "#PR" not in "".join(cue["lines"])]
    spoken_chunks: list[list[np.ndarray]] = []
    for cue_i, cue in enumerate(body):
        chunks = []
        for line_i, line in enumerate(cue["lines"]):
            chunks.append(voicevox(line, HIMARI, 1.12, work, f"l{cue_i}_{line_i}"))
        spoken_chunks.append(chunks)
    scenes = []
    cursor = 0.0
    placed: list[tuple[float, np.ndarray]] = []
    new_cues = []
    for cue, chunks in zip(body, spoken_chunks):
        scene_start = cursor
        for chunk in chunks:
            placed.append((cursor, chunk))
            new_cues.append(
                {
                    "start": cursor,
                    "end": cursor + len(chunk) / SR,
                    "lines": [""],
                }
            )
            # fill line text below
            cursor += len(chunk) / SR + LINE_GAP_SEC
        scene_end = cursor
        scenes.append((cue["start"], cue["end"], scene_start, scene_end - scene_start))
    # rewrite cue texts in order
    flat_lines = [line for cue in body for line in cue["lines"]]
    for cue, line in zip(new_cues, flat_lines):
        cue["lines"] = [line]
        cue["end"] = cue["start"] + max(0.3, cue["end"] - cue["start"])
    body_dur = cursor
    total = body_dur + 2.0
    new_cues.append({"start": body_dur, "end": total, "lines": ["#PR", meta["pr"]]})
    parts = []
    src = src_dir / "video_noaudio.mp4"
    for index, (old_start, old_end, _new_start, new_dur) in enumerate(scenes):
        old_dur = max(0.1, old_end - old_start)
        factor = new_dur / old_dur
        part = work / f"part{index:02d}.mp4"
        vf = f"setpts={factor:.6f}*PTS,{kenburns(meta['move'], new_dur)}"
        extract_muted_picture(src, part, start=old_start, end=old_end, vf=vf, fps=30)
        # setpts is applied after trim inside extract. The trim filter already
        # resets PTS, then vf's setpts scales that. Duration follows the factor
        # only if we also limit the output. Force the length.
        fitted = work / f"fit{index:02d}.mp4"
        run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(part),
                "-an",
                "-vf",
                f"tpad=stop_mode=clone:stop_duration=0.4,fps=30,trim=duration={new_dur:.3f},setpts=PTS-STARTPTS,setsar=1,format=yuv420p",
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                str(fitted),
            ]
        )
        parts.append(fitted)
    card = work / "card.mp4"
    render_card(card, 30, meta["card"], meta["pr"], meta["palette"])
    parts.append(card)
    picture = work / "picture.mp4"
    concat_pictures(parts, picture, 30)
    voice = work / "voice.wav"
    bed = work / "bed.wav"
    mix = work / "mix.wav"
    write_wav(voice, place_lines(placed, total))
    write_bed(bed, total + 0.2, meta["bed"])
    mix_voice_and_bgm(voice, bed, mix, total)
    final = out / "video.mp4"
    mux(picture, mix, final)
    write_srt(out / "subs.srt", new_cues)
    thumbnail(final, out / "thumbnail.png", title, 0.4, meta["thumb_band"], meta["thumb_ink"])
    description = (src_dir / "description.txt").read_text(encoding="utf-8")
    description = description.replace("投稿はしない。\n", "").replace("投稿はしない。", "")
    description += (
        "\n話速: VOICEVOX:冥鳴ひまり speedScale 1.12（ピッチはそのまま）\n"
        f"BGM: この動画用に合成したオリジナル（{meta['bed_note']}）。他の曲の転用ではない。\n"
        "エンドカードの最後2秒に声は入れていない。商品URLは入れていない。\n"
    )
    (out / "description.txt").write_text(description, encoding="utf-8")
    narration = (src_dir / "narration.txt").read_text(encoding="utf-8").strip()
    (out / "script.md").write_text(
        f"# {title}\n\n"
        "読み上げは元の narration のまま。間だけを 0.16 秒に詰め、話速を 1.12 にした。\n"
        "絵は無音の video_noaudio を、声の長さに合わせてシーンごとに縮めた。\n"
        "ソース音声は元から無く、ナレーション以外の声は足していない。\n\n"
        + narration
        + "\n",
        encoding="utf-8",
    )
    starts = [cue["start"] for cue in new_cues if "#PR" not in "".join(cue["lines"])]
    return finish_report(final, voice, starts, {"title": title, "source_had_audio": False})


def finish_report(final: Path, voice: Path, starts: list[float], job: dict) -> dict:
    info = probe(final)
    video = next(stream for stream in info["streams"] if stream["codec_type"] == "video")
    samples, _ = read_wav(voice)
    deltas = check_sync(voice_onsets(samples, SR), starts)
    gaps = []
    onsets = voice_onsets(samples, SR)
    # gap between end of one run and start of the next is measured on the voice wav
    loud = np.abs(samples) >= 0.02
    runs = []
    in_run = False
    start_i = 0
    for index, flag in enumerate(loud):
        if flag and not in_run:
            start_i = index
            in_run = True
        elif not flag and in_run:
            runs.append((start_i / SR, index / SR))
            in_run = False
    if in_run:
        runs.append((start_i / SR, len(samples) / SR))
    for left, right in zip(runs, runs[1:]):
        gaps.append(right[0] - left[1])
    report = {
        "title": job["title"],
        "duration": round(float(info["format"]["duration"]), 3),
        "width": video.get("width"),
        "height": video.get("height"),
        "audio_streams": audio_stream_count(final),
        "silence_over_1_5s": subprocess_silence(final),
        "freeze_over_1s": freeze_hits(final),
        "sync_max_abs": round(max((abs(item) for item in deltas), default=0.0), 3),
        "voice_gap_max": round(max(gaps, default=0.0), 3),
        "source_audio_mapped": False,
    }
    (final.parent / "check.txt").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False), flush=True)
    return report


def retro_jobs() -> list[dict]:
    common_kon = (
        "声: VOICEVOX:もち子さん（ノーマル、speedScale 1.05、pitchScale 0）。\n"
        "BGM は声の約15%（振幅 0.15）。商品URLは入れていない。投稿していない。\n"
        "Imagine の元音声は消して、このナレーションだけを乗せている。\n"
    )
    return [
        {
            "title": "返信が遅い人を、好きになった理由",
            "fps": 30,
            "cut": 42.233,
            "pr_at": 42.233,
            "pr_line": "プロフィールを見直そう",
            "card": "ribbon",
            "palette": ((28, 36, 64), (196, 164, 106), (247, 241, 230)),
            "box": "black@0.62",
            "ink": "white",
            "panel": "0x1c2438@0.92",
            "bar_y": 1500,
            "size": 48,
            "bed": "piano_reply",
            "thumb": "返信が遅い人",
            "thumb_at": 1.0,
            "thumb_band": (28, 36, 64),
            "thumb_ink": (247, 241, 230),
            "script": (
                "# 返信が遅い人を、好きになった理由\n\n"
                "本編は 42.233 秒で切る。それ以降の焼き込み誘導は使わない。\n"
                "最後の 2 秒だけ「プロフィールを見直そう」と #PR。URL は無い。\n"
                + common_kon
            ),
            "description": (
                "既読のまま三日。待っていた中身は、相手の事情ではなかった。\n\n"
                "#PR\n"
                "広告を含みます。動画の中に商品URLは入れていません。\n"
                "声: VOICEVOX:もち子さん\n"
                "BGM: この動画用に合成したオリジナル（変ホの遅い和音）。\n"
            ),
        },
        {
            "title": "仮交際が、終わった夜",
            "fps": 30,
            "cut": 30.133,
            "pr_at": 30.133,
            "pr_line": "プロフィールを見直そう",
            "card": "spot",
            "palette": ((42, 32, 48), (214, 176, 122), (255, 248, 240)),
            "box": "0x2a2030@0.66",
            "ink": "0xFFF8F0",
            "panel": "0x2a2030@0.92",
            "bar_y": 1540,
            "size": 46,
            "bed": "piano_night",
            "thumb": "仮交際の夜",
            "thumb_at": 1.2,
            "thumb_band": (42, 32, 48),
            "thumb_ink": (255, 248, 240),
            "script": (
                "# 仮交際が、終わった夜\n\n"
                "本編は 30.133 秒で切る。それ以降の焼き込み誘導は使わない。\n"
                "最後の 2 秒だけ「プロフィールを見直そう」と #PR。URL は無い。\n"
                + common_kon
            ),
            "description": (
                "既読のまま夜が過ぎて、仮交際は相手の画面で終わっていた。\n\n"
                "#PR\n"
                "広告を含みます。動画の中に商品URLは入れていません。\n"
                "声: VOICEVOX:もち子さん\n"
                "BGM: この動画用に合成したオリジナル（イ短調の遅い和音）。\n"
            ),
        },
        {
            "title": "見守りカメラの夕方を見たら、水が減った順番が残っていた",
            "fps": 24,
            "cut": None,
            "pr_at": 11.0,
            "pr_line": "うちの子の留守中も見てみて",
            "card": None,
            "palette": ((40, 28, 18), (232, 164, 74), (255, 244, 220)),
            "box": "0x281c12@0.7",
            "ink": "0xFFF4DC",
            "panel": "0x281c12@0.88",
            "bar_y": 1460,
            "size": 44,
            "bed": "marimba_evening",
            "thumb": "水が減った順",
            "thumb_at": 1.0,
            "thumb_band": (40, 28, 18),
            "thumb_ink": (255, 244, 220),
            "script": (
                "# 見守りカメラの夕方を見たら、水が減った順番が残っていた\n\n"
                "皿の順番だけを読む。最後の 2 秒だけ「うちの子の留守中も見てみて」と #PR。\n"
                "URL は無い。Imagine の元音声は消している。\n"
                "声: Style-Bert-VITS2 あみたろ（Neutral、length 0.95、ピッチは 1.0）。\n"
                "クレジット: Style-BertVITS2モデル: あみたろ、あみたろの声素材工房 (https://amitaro.net/)\n"
            ),
            "description": (
                "夕方の皿は、水だけが先に減っていた。そのあとでご飯に戻っている。\n\n"
                "#PR\n"
                "広告を含みます。動画の中に商品URLは入れていません。\n"
                "声: Style-BertVITS2モデル: あみたろ、あみたろの声素材工房 (https://amitaro.net/)\n"
                "BGM: この動画用に合成したオリジナル（夕方の木琴）。\n"
            ),
        },
        {
            "title": "見守りカメラで留守番中を隠し撮りしたら、先輩が止めていた",
            "fps": 24,
            "cut": None,
            "pr_at": 10.0,
            "pr_line": "うちの子の留守中も見てみて",
            "card": None,
            "palette": ((24, 32, 28), (168, 196, 170), (236, 244, 236)),
            "box": "0x182018@0.72",
            "ink": "0xECF4EC",
            "panel": "0x182018@0.9",
            "bar_y": 1480,
            "size": 42,
            "bed": "box_hall",
            "thumb": "部屋の音",
            "thumb_at": 0.8,
            "thumb_band": (24, 32, 28),
            "thumb_ink": (236, 244, 236),
            "script": (
                "# 見守りカメラで留守番中を隠し撮りしたら、先輩が止めていた\n\n"
                "声は、ソファで丸くなり、部屋の音を聞いて、通路の前に出る、まで。\n"
                "2匹目には触れない。「隠し撮り」とは言わない。\n"
                "最後の 2 秒だけ「うちの子の留守中も見てみて」と #PR。URL は無い。\n"
                "Imagine の元音声は消している。\n"
                "声: Style-Bert-VITS2 あみたろ（Neutral、length 0.95、ピッチは 1.0）。\n"
                "クレジット: Style-BertVITS2モデル: あみたろ、あみたろの声素材工房 (https://amitaro.net/)\n"
            ),
            "description": (
                "ソファの上で丸くなって、部屋の音を聞いて、通路の前に出た。\n\n"
                "#PR\n"
                "広告を含みます。動画の中に商品URLは入れていません。\n"
                "声: Style-BertVITS2モデル: あみたろ、あみたろの声素材工房 (https://amitaro.net/)\n"
                "BGM: この動画用に合成したオリジナル（低い鐘）。\n"
            ),
        },
        {
            "title": "夜の見守りカメラを見たら、先輩が途中から隣に来ていた",
            "fps": 24,
            "cut": None,
            "pr_at": 13.0,
            "pr_line": "うちの子の留守中も見てみて",
            "card": None,
            "palette": ((18, 24, 42), (186, 198, 230), (232, 236, 248)),
            "box": "0x12182a@0.72",
            "ink": "0xE8ECF8",
            "panel": "0x12182a@0.9",
            "bar_y": 1500,
            "size": 44,
            "bed": "night_pad",
            "thumb": "隣に来た",
            "thumb_at": 1.0,
            "thumb_band": (18, 24, 42),
            "thumb_ink": (232, 236, 248),
            "script": (
                "# 夜の見守りカメラを見たら、先輩が途中から隣に来ていた\n\n"
                "匹数だけを足す。最後の 2 秒だけ「うちの子の留守中も見てみて」と #PR。\n"
                "URL は無い。Imagine の元音声は消している。\n"
                "声: Style-Bert-VITS2 あみたろ（Neutral、length 0.95、ピッチは 1.0）。\n"
                "クレジット: Style-BertVITS2モデル: あみたろ、あみたろの声素材工房 (https://amitaro.net/)\n"
            ),
            "description": (
                "夜のソファに一匹。右からもう一匹が入って、端を空けて隣で丸くなった。\n\n"
                "#PR\n"
                "広告を含みます。動画の中に商品URLは入れていません。\n"
                "声: Style-BertVITS2モデル: あみたろ、あみたろの声素材工房 (https://amitaro.net/)\n"
                "BGM: この動画用に合成したオリジナル（夜の低い和音）。\n"
            ),
        },
    ]


def main() -> None:
    reports = []
    print("retrofit", flush=True)
    amitaro = None
    for job in retro_jobs():
        if job["card"] is None:
            if amitaro is None:
                amitaro = Amitaro()
            speaker = amitaro
        else:
            serial = {"n": 0}

            def speaker(text: str, title=job["title"], serial=serial) -> np.ndarray:
                slot = Path("/tmp/v3work") / title / "vv"
                slot.mkdir(parents=True, exist_ok=True)
                serial["n"] += 1
                return voicevox(text, MOCHIKO, 1.05, slot, f"n{serial['n']:02d}")

        reports.append(render_retro(job, speaker))
    print("kane", flush=True)
    kane = {
        "01": {
            "title": "千分の五",
            "pr": "出典は説明欄",
            "card": "stamp",
            "palette": ((243, 230, 200), (180, 51, 42), (44, 36, 22)),
            "bed": "marimba_c",
            "bed_note": "ハ長調の木琴、104BPM前後",
            "move": "in",
            "thumb_band": (243, 230, 200),
            "thumb_ink": (180, 51, 42),
        },
        "02": {
            "title": "半分ずつ",
            "pr": "料率は公式",
            "card": "ticker",
            "palette": ((14, 26, 51), (228, 195, 106), (247, 241, 222)),
            "bed": "piano_eb",
            "bed_note": "変ホの遅いピアノ、66BPM前後",
            "move": "left",
            "thumb_band": (14, 26, 51),
            "thumb_ink": (228, 195, 106),
        },
        "03": {
            "title": "月十五万円まで",
            "pr": "上限の出典あり",
            "card": "receipt",
            "palette": ((231, 246, 241), (23, 33, 31), (23, 33, 31)),
            "bed": "guitar_g",
            "bed_note": "ト長調の撥弦、88BPM前後",
            "move": "down",
            "thumb_band": (231, 246, 241),
            "thumb_ink": (23, 33, 31),
        },
    }
    for number, meta in kane.items():
        reports.append(render_kane(number, meta))
    summary = OUT / "pipeline" / "render-report.json"
    summary.write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("done", len(reports))


if __name__ == "__main__":
    main()
