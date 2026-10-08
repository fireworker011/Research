"""Source reproduction: ranges, speech, prompts, finishing, and measurement. No H3 render."""

from __future__ import annotations

import json
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parents[1] / "h3-runner"))

import affi_bake as bake
import affi_finish
import affi_match
import affi_media
import affi_speech
from h3_runner.ffmpeg_join import join_command
from h3_runner.planner import choose_short_edges
from h3_runner.slice_media import slice_argv

_CJK = re.compile(r"[ぁ-んァ-ン一-龥]")
_DIALOGUE = re.compile(r"<d>\[Japanese\] .*?</d>")
_NO_PROBES = {"cuts": None, "silences": None, "turns": None, "music": None}
needs_ffmpeg = pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg が無い")


def _outside_dialogue(prompt: str) -> str:
    return _DIALOGUE.sub("", prompt)


def _fake(tmp_path: Path, name: str = "source.mp4") -> Path:
    path = tmp_path / name
    path.write_bytes(b"not-a-real-video")
    return path


def _word(start: float, end: float, text: str, prob: float = 0.9) -> dict:
    return {"start_s": start, "end_s": end, "text": text, "prob": prob}


def test_the_canvas_table_matches_the_planner() -> None:
    for aspect in ("9:16", "16:9"):
        for frames in range(124, 346, 17):
            assert choose_short_edges("ref2va", frames, aspect)[0] == bake.ref2va_short_edge(frames / 24)
    assert bake.ref2va_steps("quality")[0] == (124, 512)
    assert bake.ref2va_steps("fewer")[0] == (345, 288)


def test_range_boundaries_land_in_silence_and_stay_out_of_words() -> None:
    lines = [
        {"start_s": 0.5, "end_s": 4.6, "text": "a", "words": [_word(0.5, 2.0, " a"), _word(2.1, 4.6, " b")]},
        {"start_s": 5.6, "end_s": 9.9, "text": "c", "words": [_word(5.6, 9.9, " c")]},
    ]
    silences = [(4.7, 5.5), (10.0, 10.8)]
    spans, edge = affi_media.plan_spans(16.0, steps=bake.ref2va_steps("quality"), silences=silences, lines=lines)
    assert spans[0][0] == 0.0 and spans[-1][1] == 16.0
    for (_a, b), (c, _d) in zip(spans, spans[1:]):
        assert b == c
        assert any(start <= b <= end for start, end in silences)
    for start, end in spans:
        assert 5.0 - 1e-6 <= end - start <= 14.375 + 1e-6
    assert edge == 448


def test_fewer_ranges_trade_the_canvas_for_count() -> None:
    quality, q_edge = affi_media.plan_spans(45.0, steps=bake.ref2va_steps("quality"))
    fewer, f_edge = affi_media.plan_spans(45.0, steps=bake.ref2va_steps("fewer"))
    assert len(quality) == 9 and q_edge == 512
    assert len(fewer) == 4 and f_edge == 288
    assert sum(b - a for a, b in fewer) == pytest.approx(45.0, abs=0.002)


def test_a_cut_is_preferred_when_there_is_no_reading() -> None:
    whole, _edge = affi_media.plan_spans(12.0, steps=bake.ref2va_steps("fewer"), cuts=[6.5], silences=[(0.0, 12.0)])
    assert whole == [(0.0, 12.0)]
    spans, _edge = affi_media.plan_spans(20.0, steps=bake.ref2va_steps("fewer"), cuts=[9.5], silences=[(0.0, 20.0)])
    assert spans == [(0.0, 9.5), (9.5, 20.0)]


def test_measured_lines_reach_only_the_range_that_hears_them(tmp_path: Path) -> None:
    source = _fake(tmp_path)
    speech = [
        {"start_s": 1.0, "end_s": 2.0, "text": "こんにちは"},
        {"start_s": 9.0, "end_s": 10.0, "text": "またね"},
    ]
    job = bake.plan_reproduce(video=str(source), duration_s=16, speech=speech, analysis=_NO_PROBES)
    assert job["status"] == "ready"
    owners = {}
    for clip in job["clips"]:
        prompt = clip["prompt"]
        for word in ("こんにちは", "またね"):
            if word in prompt:
                owners.setdefault(word, []).append(clip["id"])
        assert "lip-synced" not in prompt.casefold()
        assert not _CJK.search(_outside_dialogue(prompt))
        assert "(S2)" not in prompt
    assert len(owners["こんにちは"]) == 1 and len(owners["またね"]) == 1
    first = job["clips"][0]["prompt"]
    assert "At 00:01.000, (S1) says: <d>[Japanese] こんにちは.</d> The mouth forms that one line and no other words." in first
    assert "When a line ends, the mouth closes until the next line." in first
    assert "Each line is spoken by the mouth that <Video 1> shows speaking at that moment." in first
    path = bake.write_reproduce(job, tmp_path / "spoken")
    captions = json.loads((path.parent / "captions.json").read_text(encoding="utf-8"))
    assert [row["text"] for row in captions] == ["こんにちは.", "またね."]
    assert [(row["start_s"], row["end_s"]) for row in captions] == [(1.0, 2.0), (9.0, 10.0)]
    assert all(row["burn"] is False and row["speaker"] == "S1" for row in captions)
    assert "口はその文だけを作る" in job["speech_note"]


def test_a_line_at_the_first_frame_has_no_time(tmp_path: Path) -> None:
    job = bake.plan_reproduce(
        video=str(_fake(tmp_path)),
        duration_s=8,
        speech=[{"start_s": 0.0, "end_s": 1.0, "text": "はい"}],
        analysis=_NO_PROBES,
    )
    prompt = job["clips"][0]["prompt"]
    assert "From the first frame, (S1) says: <d>[Japanese] はい.</d>" in prompt
    assert "At 00:00.000" not in prompt
    assert "[Shot 2]" not in prompt


def test_measured_cuts_become_shots_and_a_line_across_a_cut_carries_over(tmp_path: Path) -> None:
    words = [_word(2.0, 2.6, "今日は"), _word(2.7, 3.4, "いい"), _word(3.5, 4.0, "天気")]
    job = bake.plan_reproduce(
        video=str(_fake(tmp_path)),
        duration_s=8,
        speech=[{"start_s": 2.0, "end_s": 4.0, "text": "今日はいい天気", "words": words}],
        analysis={**_NO_PROBES, "cuts": [3.0]},
    )
    prompt = job["clips"][0]["prompt"]
    assert "[Shot 2] At 00:03.000, <Video 1> cuts to its next framing" in prompt
    assert "<d>[Japanese] 今日は <scenetrans></d> The line continues seamlessly across the cut." in prompt
    assert "(S1)'s line carries over from the previous shot: <d>[Japanese] <scenetrans> いい天気.</d>" in prompt
    shot_two = prompt[prompt.index("[Shot 2]") :]
    assert "今日は <scenetrans>" not in shot_two
    assert not _CJK.search(_outside_dialogue(prompt))


def test_no_measured_cut_holds_one_shot(tmp_path: Path) -> None:
    job = bake.plan_reproduce(video=str(_fake(tmp_path)), duration_s=8, speech=[], analysis={**_NO_PROBES, "cuts": []})
    prompt = job["clips"][0]["prompt"]
    assert "<Video 1> has no cut in this range, so the target video holds one continuous shot." in prompt
    assert "When <Video 1> cuts" not in prompt


def test_a_line_cut_by_the_range_end_is_split_by_word_time() -> None:
    words = [_word(7.0, 7.6, " see"), _word(7.7, 8.4, " you"), _word(8.5, 9.0, " soon")]
    lines = [{"start_s": 7.0, "end_s": 9.0, "text": "see you soon", "words": words, "speaker": "S1"}]
    head = affi_speech.lines_in_span(lines, 0.0, 8.0)
    tail = affi_speech.lines_in_span(lines, 8.0, 16.0)
    assert head[0]["text"] == "see" and head[0]["tail_cut"] and not head[0]["head_cut"]
    assert tail[0]["text"] == "you soon." and tail[0]["head_cut"] and not tail[0]["tail_cut"]
    first = bake.reproduce_prompt(has_image=False, start_s=0.0, end_s=8.0, lines=lines, speech_known=True, cuts=[])
    second = bake.reproduce_prompt(has_image=False, start_s=8.0, end_s=16.0, lines=lines, speech_known=True, cuts=[])
    assert "<d>[English] see<cutoff></d> The line is cut off by the end of this video." in first
    assert "From the first frame, (S1) is already mid-line and continues: <d>[English] you soon.</d>" in second


def test_low_confidence_words_are_unclear_and_an_unclear_line_is_left_to_the_soundtrack(tmp_path: Path) -> None:
    words = [_word(1.0, 1.4, "こん"), _word(1.4, 1.8, "に", prob=0.2), _word(1.8, 2.2, "ちは")]
    murmur = [_word(4.0, 4.5, "む", prob=0.1)]
    job = bake.plan_reproduce(
        video=str(_fake(tmp_path)),
        duration_s=8,
        speech=[
            {"start_s": 1.0, "end_s": 2.2, "text": "", "words": words},
            {"start_s": 4.0, "end_s": 4.5, "text": "", "words": murmur},
        ],
        analysis=_NO_PROBES,
    )
    prompt = job["clips"][0]["prompt"]
    assert "<d>[Japanese] こん[unclear]ちは.</d>" in prompt
    assert "From 00:04.000 to 00:04.500, the mouth that <Video 1> shows speaking shapes the speech heard in its soundtrack, and no words are added." in prompt
    path = bake.write_reproduce(job, tmp_path / "unclear")
    captions = json.loads((path.parent / "captions.json").read_text(encoding="utf-8"))
    assert [row["text"] for row in captions] == ["こん[unclear]ちは."]
    assert captions[0]["unclear"] is True


def test_a_line_read_without_words_leaves_only_the_window_on_the_other_side() -> None:
    lines = [
        {"start_s": 0.0, "end_s": 1.0, "text": "前"},
        {"start_s": 7.5, "end_s": 8.5, "text": "またぐ"},
    ]
    inside = affi_speech.lines_in_span(lines, 8.0, 16.0)
    assert [row["text"] for row in inside] == ["またぐ."]
    assert inside[0]["start_s"] == 0.0
    before = affi_speech.lines_in_span(lines, 0.0, 8.0)
    assert [row["text"] for row in before] == ["前.", ""]
    assert before[1]["unread"] is True
    assert (before[1]["start_s"], before[1]["end_s"]) == (7.5, 8.0)


def test_speaker_install_keeps_the_hub_that_accepts_the_model_card(tmp_path: Path) -> None:
    site = tmp_path / "affi-speaker"
    argv = affi_media.speaker_install_argv(site)
    assert "--target" in argv and str(site) in argv
    assert "--upgrade" in argv
    assert "pyannote.audio==3.3.2" in argv
    assert "huggingface_hub==0.36.0" in argv
    assert affi_media.SPEAKER_MODEL == "pyannote/speaker-diarization-3.1"
    assert affi_media.SPEAKER_SEGMENTATION == "pyannote/segmentation-3.0"
    lines = affi_media.speaker_gate_lines()
    assert any(affi_media.SPEAKER_MODEL in line for line in lines)
    assert any(affi_media.SPEAKER_SEGMENTATION in line for line in lines)
    assert affi_media.speaker_site_ready(site) is False
    (site / "pyannote" / "audio").mkdir(parents=True)
    assert affi_media.speaker_site_ready(site) is False
    (site / "pyannote_audio-3.3.2.dist-info").mkdir()
    (site / "huggingface_hub-0.36.0.dist-info").mkdir()
    assert affi_media.speaker_site_ready(site) is True
    text = Path(affi_media.__file__).with_name("affi_speaker.py").read_text(encoding="utf-8")
    assert "use_auth_token" in text
    assert "pyannote/segmentation-3.0" in text


def test_speaker_turns_number_speakers_in_the_order_heard(tmp_path: Path) -> None:
    job = bake.plan_reproduce(
        video=str(_fake(tmp_path)),
        duration_s=8,
        speech=[
            {"start_s": 1.0, "end_s": 2.0, "text": "はい"},
            {"start_s": 3.0, "end_s": 4.0, "text": "いいえ"},
            {"start_s": 5.0, "end_s": 6.0, "text": "そう"},
        ],
        analysis={**_NO_PROBES, "turns": [
            {"start_s": 0.9, "end_s": 2.1, "speaker": "SPEAKER_07"},
            {"start_s": 2.9, "end_s": 4.1, "speaker": "SPEAKER_02"},
            {"start_s": 4.9, "end_s": 6.1, "speaker": "SPEAKER_07"},
        ]},
    )
    assert job["speakers"] == 2
    prompt = job["clips"][0]["prompt"]
    assert "At 00:01.000, (S1) says: <d>[Japanese] はい.</d>" in prompt
    assert "At 00:03.000, (S2) says: <d>[Japanese] いいえ.</d>" in prompt
    assert "At 00:05.000, (S1) says: <d>[Japanese] そう.</d>" in prompt
    assert not any("1人として並べた" in note for note in job["notes"])
    lone = bake.plan_reproduce(
        video=str(_fake(tmp_path, "lone.mp4")),
        duration_s=8,
        speech=[{"start_s": 1.0, "end_s": 2.0, "text": "はい"}],
        analysis=_NO_PROBES,
    )
    assert any("1人として並べた" in note for note in lone["notes"])
    assert affi_media.parse_turns([{"start_s": 1, "end_s": 1, "speaker": "x"}]) == []


def test_a_sidecar_speaker_is_kept(tmp_path: Path) -> None:
    source = _fake(tmp_path)
    affi_speech.speech_sidecar(source).write_text(
        json.dumps(
            [
                {"start_s": 1.0, "end_s": 2.0, "text": "こんにちは", "speaker": "女性"},
                {"start_s": 3.0, "end_s": 4.0, "text": "どうも", "speaker": "男性"},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    job = bake.plan_reproduce(video=str(source), duration_s=8, analysis=_NO_PROBES)
    prompt = job["clips"][0]["prompt"]
    assert "(S1) says: <d>[Japanese] こんにちは.</d>" in prompt
    assert "(S2) says: <d>[Japanese] どうも.</d>" in prompt
    assert "女性" not in prompt and "男性" not in prompt


def test_measured_instruments_join_the_music_line(tmp_path: Path) -> None:
    job = bake.plan_reproduce(
        video=str(_fake(tmp_path)),
        duration_s=8,
        speech=[],
        analysis={**_NO_PROBES, "music": [["piano", "string section"]]},
    )
    assert "The instruments heard in that soundtrack include piano and string section." in job["clips"][0]["prompt"]
    assert affi_media.labels_from_scores({"Piano": 0.8, "Guitar": 0.1, "Speech": 0.9, "Violin, fiddle": 0.4}) == ["piano", "violin"]


def test_measured_silence_does_not_form_words(tmp_path: Path) -> None:
    job = bake.plan_reproduce(video=str(_fake(tmp_path)), duration_s=8, speech=[], analysis=_NO_PROBES)
    prompt = job["clips"][0]["prompt"]
    assert job["speech_known"] is True
    assert "<d>" not in prompt
    assert "No one speaks. Mouths do not form words." in prompt
    assert "発話は無い" in job["speech_note"]
    assert "No new logo, watermark, or account name is drawn." in prompt


def test_a_banned_line_never_enters_the_prompt(tmp_path: Path) -> None:
    job = bake.plan_reproduce(
        video=str(_fake(tmp_path)),
        duration_s=8,
        speech=[{"start_s": 1.0, "end_s": 2.0, "text": "すず丸"}],
        analysis=_NO_PROBES,
    )
    prompt = job["clips"][0]["prompt"]
    assert "すず丸" not in prompt
    assert "すず丸" not in json.dumps(job["speech"], ensure_ascii=False)
    assert "<d>" not in prompt
    assert "Mouths do not form words." in prompt
    assert "実在や未成年の指定はせりふから外した。" in job["speech_note"]


def test_a_speech_sidecar_is_the_mouth_line(tmp_path: Path) -> None:
    source = _fake(tmp_path)
    affi_speech.speech_sidecar(source).write_text(
        json.dumps([{"start_s": 1.0, "end_s": 2.0, "text": "こんにちは"}], ensure_ascii=False),
        encoding="utf-8",
    )
    job = bake.plan_reproduce(video=str(source), duration_s=8, analysis=_NO_PROBES)
    assert "<d>[Japanese] こんにちは.</d>" in job["clips"][0]["prompt"]
    assert "speech.json" in job["speech_note"]
    shown = bake._run_repro(str(source), "", "9:16", tmp_path / "shown", duration_s=8, analysis=_NO_PROBES)
    assert "口はその文だけを作る" in shown
    assert "短辺 384" in shown
    assert "画質優先" in shown


def test_sentences_are_finished_the_way_the_guide_asks() -> None:
    assert affi_speech.finish_sentence("こんにちは") == "こんにちは."
    assert affi_speech.finish_sentence("え？") == "え?"
    assert affi_speech.finish_sentence("〜やあ") == "やあ."
    assert affi_speech.finish_sentence("まだ", complete=False) == "まだ"
    assert affi_speech.dialogue_tag("hello") == "<d>[English] hello.</d>"
    assert affi_speech.words_text([_word(0, 1, " a", 0.1), _word(1, 2, " b", 0.2), _word(2, 3, " c")]) == "[unclear] c"


def test_cut_and_silence_logs_parse() -> None:
    log = "[scdet @ 0x1] lavfi.scd.score: 15.6, lavfi.scd.time: 2\n[scdet @ 0x1] lavfi.scd.score: 30, lavfi.scd.time: 4.5\n"
    assert affi_media.parse_cuts(log) == [2.0, 4.5]
    silent = "silence_start: 0.99\nsilence_end: 2.5 | silence_duration: 1.5\nsilence_start: 3.9\n"
    assert affi_media.parse_silences(silent, 4.0) == [(0.99, 2.5), (3.9, 4.0)]


def test_template_captions_burn_where_the_template_says(tmp_path: Path) -> None:
    drama = bake.bake_reference("yako.shiawasekon", fill="template")
    path = bake.write_job(drama, tmp_path / "drama")
    ass = (path.parent / "captions.ass").read_text(encoding="utf-8")
    assert ass.count("Dialogue:") == 3
    assert "ここで会うね" in ass
    style = affi_finish.caption_style(drama["subtitle_spec"], height=1920)
    assert style["alignment"] == 2 and style["margin_v"] == round(1920 * 0.325)
    assert style["outline_colour"] == affi_finish.BLACK and style["bold"] is True
    lines = bake.finish_lines(path.parent)
    assert len(lines) == 2
    master = shlex.split(lines[0])
    parts = [(path.parent / "clips" / f"{clip['id']}.mp4", float(clip["trim_s"])) for clip in drama["clips"]]
    assert master == join_command(parts, path.parent / "story.mov", width=1080, height=1920, audio="pcm")
    finish = shlex.split(lines[1])
    assert any(part.startswith("[0:v]ass=filename=") for part in finish)
    assert finish[-1] == str(path.parent / "story.mp4")
    beauty = bake.bake_reference("the.care.logic", fill="template")
    bare = bake.write_job(beauty, tmp_path / "beauty")
    assert not (bare.parent / "captions.ass").exists()
    assert "copy" in shlex.split(bake.finish_lines(bare.parent)[1])
    talk = affi_finish.caption_style(bake.bake_reference("nuts0629", mode="talk", fill="template")["subtitle_spec"], height=1920)
    assert talk["alignment"] == 5 and talk["outline_colour"] == affi_finish.WHITE
    assert talk["colours"] == [affi_finish.COLOURS["青"], affi_finish.COLOURS["ピンク"], affi_finish.COLOURS["黄"]]


def test_beauty_title_card_and_name_mark(tmp_path: Path) -> None:
    job = bake.bake_reference("the.care.logic", fill="template", title="乾燥の朝", logo="わたしの店")
    assert job["overlay"] == {"title": "乾燥の朝", "cover_end_s": 0.07, "logo": "わたしの店"}
    assert all("乾燥の朝" not in clip["prompt"] and "わたしの店" not in clip["prompt"] for clip in job["clips"])
    path = bake.write_job(job, tmp_path / "beauty")
    ass = (path.parent / "captions.ass").read_text(encoding="utf-8")
    assert "Dialogue: 3,0:00:00.00,0:00:00.07,Title,,0,0,0,,乾燥の朝" in ass
    assert "Dialogue: 4,0:00:00.00,0:00:30.00,Logo,,0,0,0,,わたしの店" in ass
    other = bake.bake_reference("junjun_ranran", fill="template", title="題", logo="名")
    assert other["overlay"]["title"] == "" and other["overlay"]["logo"] == ""
    assert any("美容の型だけ" in note for note in other["notes"])
    with pytest.raises(ValueError):
        bake.bake_reference("the.care.logic", fill="template", logo="the.care.logic")


def test_an_own_music_file_replaces_the_template_music(tmp_path: Path) -> None:
    missing = bake.bake_reference("yako.shiawasekon", fill="template", bgm=str(tmp_path / "gone.wav"))
    assert missing["status"] == "blocked"
    assert any("曲のファイルが無い" in reason for reason in missing["blocked"])
    song = tmp_path / "song.wav"
    song.write_bytes(b"RIFF")
    job = bake.bake_reference("yako.shiawasekon", fill="template", bgm=str(song))
    assert job["status"] == "ready"
    assert all(clip["prompt"].rstrip().endswith("non_diegetic_music: N/A") for clip in job["clips"])
    assert "自分の曲" in job["performance"]["bgm"]["summary"]
    path = bake.write_job(job, tmp_path / "drama")
    finish = shlex.split(bake.finish_lines(path.parent)[1])
    assert str(song) in finish
    graph = finish[finish.index("-filter_complex") + 1]
    assert f"[1:a]volume={affi_finish.BGM_VOLUME:g}[bgm]" in graph
    assert "amix=inputs=2:duration=first:normalize=0" in graph


def test_baked_clips_are_skipped_and_restored_only_when_unchanged(tmp_path: Path) -> None:
    job = bake.plan_reproduce(video=str(_fake(tmp_path)), duration_s=16, speech=[], analysis=_NO_PROBES)
    root = tmp_path / "affi-bake" / "repro"
    path = bake.write_reproduce(job, root)
    commands = path.parent / "commands.txt"
    lines, _note = bake.commands_to_run(commands, first_only=False, skip_done=True)
    first_out = bake._out_of(lines[0])
    first_out.parent.mkdir(parents=True, exist_ok=True)
    first_out.write_bytes(b"mp4")
    assert bake.commands_to_run(commands, first_only=False, skip_done=True)[0] == lines
    bake.mark_done(lines[0])
    rest, note = bake.commands_to_run(commands, first_only=True, skip_done=True)
    assert rest == [lines[1]]
    assert "焼いてある 1 本は飛ばします" in note
    assert not bake.all_clips_made(path.parent)
    drive = tmp_path / "drive"
    bake.publish_job_dir(path.parent, drive_root=drive)
    shutil.rmtree(root / "clips")
    assert bake.restore_done_clips(commands, drive_root=drive) == [first_out]
    assert first_out.read_bytes() == b"mp4"
    (path.parent / "prompts" / "01.txt").write_text("changed", encoding="utf-8")
    assert bake.commands_to_run(commands, first_only=True, skip_done=True)[0] == [lines[0]]
    for line in lines:
        out = bake._out_of(line)
        out.write_bytes(b"mp4")
    assert bake.all_clips_made(path.parent)


def test_sound_offset_cuts_and_text_are_measured() -> None:
    rate = affi_match.RATE
    clock = np.zeros(rate * 3, dtype=np.float32)
    for start in (0.4, 1.1, 2.0):
        clock[int(start * rate) : int((start + 0.05) * rate)] = 0.8
    later = np.concatenate([np.zeros(int(0.12 * rate), dtype=np.float32), clock])[: len(clock)]
    lag, corr = affi_match.audio_offset(clock, later)
    assert lag == pytest.approx(120, abs=10)
    assert corr > 0.9
    same, same_corr = affi_match.audio_offset(clock, clock)
    assert same == 0 and same_corr == pytest.approx(1.0, abs=1e-3)
    assert affi_match.audio_offset(np.zeros(rate), clock[:rate]) == (None, None)
    cuts = affi_match.match_cuts([1.0, 2.0, 3.0], [1.04, 2.5])
    assert cuts == {"source": 3, "generated": 2, "matched": 1, "mean_offset_ms": 40.0}
    assert affi_match.char_error_rate("こんにちは.", "こんにちわ") == 0.2
    assert affi_match.char_error_rate("", "x") is None
    text = affi_match.summary_text("01", {"sound": {"lag_ms": 12.0, "correlation": 0.97}, "cuts": cuts, "speech": None})
    assert "音のずれ 12ms" in text and "3 本のうち 1 本" in text and affi_match.LIP_NOTE in text


def _clip_with_beeps(path: Path, seconds: float, beeps: list[float], *, colour: str = "black", rate: int = 24) -> None:
    expr = "+".join(f"between(t,{b:.3f},{b + 0.05:.3f})" for b in beeps) or "0"
    subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            f"color=c={colour}:s=288x512:d={seconds}:r={rate}",
            "-f",
            "lavfi",
            "-i",
            f"aevalsrc='0.8*sin(2*PI*1000*t)*({expr})':s=32000:d={seconds}",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-c:a",
            "aac",
            "-shortest",
            str(path),
        ],
        check=True,
    )


def _first_beep(path: Path, start: float = 0.0, end: float | None = None) -> float:
    samples = affi_media._decode_mono(path, 16000, start, end) if end is not None else affi_media._decode_mono(path, 16000)
    loud = np.flatnonzero(np.abs(samples) > 0.3)
    return float(loud[0]) / 16000


@needs_ffmpeg
def test_join_master_and_mp4_keep_the_sound_on_its_frame(tmp_path: Path) -> None:
    first = tmp_path / "clips" / "01.mp4"
    second = tmp_path / "clips" / "02.mp4"
    first.parent.mkdir()
    _clip_with_beeps(first, 5.5, [1.0])
    _clip_with_beeps(second, 5.5, [0.5])
    parts = [(first, 5.0), (second, 5.0)]
    master = tmp_path / "story.mov"
    subprocess.run(bake.delivery_join_argv(parts, master, width=288, height=512), check=True, capture_output=True)
    final = tmp_path / "story.mp4"
    subprocess.run(affi_finish.finish_argv(master, final), check=True, capture_output=True)
    probe = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name", "-of", "csv=p=0", str(master)], text=True
    )
    assert "pcm_s16le" in probe
    assert _first_beep(master) == pytest.approx(1.0, abs=0.002)
    assert _first_beep(final) == pytest.approx(1.0, abs=0.002)
    assert _first_beep(final, 5.0, 10.0) == pytest.approx(0.5, abs=0.002)


@needs_ffmpeg
def test_a_reference_range_is_exact_and_held_in_silence(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    _clip_with_beeps(source, 12.0, [3.2, 8.0], rate=30)
    dest = tmp_path / "ref.mov"
    subprocess.run(slice_argv(source, 3.0, 8.0, dest, pad_s=0.167), check=True, capture_output=True)
    info = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "stream=codec_name,r_frame_rate,nb_frames", "-of", "csv=p=0", str(dest)],
        text=True,
    )
    assert "24/1" in info and "pcm_s16le" in info
    assert _first_beep(dest) == pytest.approx(0.2, abs=0.002)
    tail = affi_media._decode_mono(dest, 16000, 5.0, 5.167)
    assert float(np.abs(tail).max()) < 0.01


@needs_ffmpeg
def test_probes_and_measurement_on_real_files(tmp_path: Path) -> None:
    red = tmp_path / "red.mp4"
    blue = tmp_path / "blue.mp4"
    _clip_with_beeps(red, 3.0, [0.5], colour="red")
    _clip_with_beeps(blue, 3.0, [], colour="blue")
    joined = tmp_path / "cut.mov"
    subprocess.run(bake.delivery_join_argv([(red, 3.0), (blue, 3.0)], joined, width=288, height=512), check=True, capture_output=True)
    assert affi_media.detect_cuts(joined) == [3.0]
    silences = affi_media.detect_silences(joined, 6.0)
    assert silences and silences[0][0] == pytest.approx(0.0, abs=0.01)
    assert any(start <= 1.0 and end >= 2.9 for start, end in silences)
    report = affi_match.measure_clip(joined, 0.0, 6.0, joined, source_cuts=[3.0])
    assert report["sound"]["lag_ms"] == 0
    assert report["sound"]["correlation"] == pytest.approx(1.0, abs=1e-3)
    assert report["cuts"]["matched"] == 1
    assert report["speech"] is None


@needs_ffmpeg
def test_captions_are_drawn_by_libass(tmp_path: Path) -> None:
    clip = tmp_path / "black.mov"
    _clip_with_beeps(clip, 2.0, [])
    ass = tmp_path / "captions.ass"
    style = affi_finish.caption_style({"place": "画面の下から約30%"}, height=512)
    ass.write_text(
        affi_finish.ass_document(
            width=288,
            height=512,
            captions=[{"start_s": 0.0, "end_s": 2.0, "text": "HELLO", "burn": True}],
            style=style,
        ),
        encoding="utf-8",
    )
    out = tmp_path / "drawn.mp4"
    subprocess.run(affi_finish.finish_argv(clip, out, ass_path=ass), check=True, capture_output=True)
    raw = subprocess.check_output(
        ["ffmpeg", "-v", "error", "-ss", "1.0", "-i", str(out), "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    )
    frame = np.frombuffer(raw, dtype=np.uint8).reshape(512, 288)
    band = frame[512 - int(512 * 0.30) - 40 : 512 - int(512 * 0.30) + 5]
    assert band.max() > 200
    assert frame[:100].max() < 40
