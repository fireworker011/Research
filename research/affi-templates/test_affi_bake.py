"""Bake jobs keep the template clock. They do not render video."""

from __future__ import annotations

import ast
import json
import re
import shlex
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parents[2]))

import affi_av
import affi_bake as bake
import affi_genre_templates as genre
import affi_reference as ref
import affi_speech

_CJK = re.compile(r"[ぁ-んァ-ン一-龥]")
_DIALOGUE = re.compile(r"<d>\[Japanese\] .*?</d>")


def _ids(job: dict) -> list[str]:
    return [cut["id"] for cut in job["cuts"]]


def test_genre_handles_match_the_table() -> None:
    assert bake.GENRE_HANDLES == genre.REFERENCE_HANDLES


def test_account_menu_names_one_account() -> None:
    assert [handle for _label, handle in bake.ACCOUNT_CHOICES] == list(bake.GENRE_HANDLES.values())
    handle, mode = bake.resolve_account("美容：材料のキャラ（the.care.logic）", "ダンス")
    assert handle == "the.care.logic"
    assert mode is None
    text = bake.describe_account(handle, mode)
    assert text.startswith("再現するのはこの1件です。")
    assert f"話: {bake.STORIES['the.care.logic']}" in text
    assert "ジャンル: 美容スキンケア" in text
    assert "アカウント: the.care.logic" in text
    assert "選ぶ欄: 材料のキャラ、場所、口調" in text
    assert "使わない見た目" not in text
    assert "ドッグフードだけ" in text
    assert "nuts0629" not in text

    handle, mode = bake.resolve_account("ドッグフード：犬（nuts0629）", "会話")
    assert (handle, mode) == ("nuts0629", "talk")
    talk = bake.describe_account(handle, mode)
    assert f"話: {bake.STORIES['nuts0629']}" in talk
    assert "ジャンル: ドッグフード" in talk
    assert "型: 会話" in talk
    assert "足りない秒は足さない" in talk


def test_dance_is_one_ten_second_clip_and_text_bakes_without_a_still(tmp_path: Path) -> None:
    job = bake.bake_reference("nuts0629", mode="dance", theme="夕方の散歩")
    assert job["duration_s"] == 10
    assert job["aspect"] == "9:16"
    assert job["canvas"] == "720x1280"
    assert [cut["duration_s"] for cut in job["cuts"]] == [10]
    assert [(clip["trim_s"], clip["request_s"]) for clip in job["clips"]] == [(10, 10)]
    assert job["status"] == "ready"
    assert job["task"] == "t2va"
    assert job["blocked"] == []
    assert "Picture 1" not in job["clips"][0]["prompt"]
    assert job["clips"][0]["prompt"].startswith("integrated_multimodal_description:")
    assert job["generates_video"] is False
    assert job["posts"] is False
    text_path = bake.write_job(job, tmp_path / "text")
    text_command = json.loads(text_path.read_text(encoding="utf-8"))["commands"][2]
    assert "--task t2va" in text_command
    assert "--image" not in text_command
    missing = bake.bake_reference("nuts0629", mode="dance", theme="夕方の散歩", image=str(tmp_path / "missing.jpg"))
    assert missing["status"] == "blocked"
    assert any("静止画" in reason for reason in missing["blocked"])
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    ready = bake.bake_reference("nuts0629", mode="dance", theme="夕方の散歩", image=str(still))
    assert ready["status"] == "ready"
    assert ready["blocked"] == []
    path = bake.write_job(ready, tmp_path / "job")
    saved = json.loads(path.read_text(encoding="utf-8"))
    command = saved["commands"][2]
    assert "python3 h3-runner/run_h3.py" in command
    assert "--task fl2va" in command
    assert f"--image {still}" in command
    assert f"{affi_av.TURBO_FILENAME}:1.0" in command
    assert f"{affi_av.REPAIR_FILENAME}:0.6" in command
    assert "--steps 9" in command
    assert "--video-shift 6" in command
    assert "Combat" not in command
    assert "Larry" not in command
    assert "すず丸" not in path.read_text(encoding="utf-8")
    captions = json.loads((tmp_path / "job" / "captions.json").read_text(encoding="utf-8"))
    assert captions[0]["text"] == ""
    assert captions[0]["burn"] is False
    assert ready["performance"]["bgm"]["prompt"] == "N/A"
    assert ready["performance"]["bgm"]["summary"] == "曲名は入力のまま。元の曲はコピーしない。"


def test_interview_stays_one_generation_and_blocks_without_lines(tmp_path: Path) -> None:
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    job = bake.bake_reference(
        "nuts0629",
        mode="interview",
        theme="夕方の散歩",
        image=str(still),
    )
    assert job["duration_s"] == 8
    assert job["aspect"] == "16:9"
    assert _ids(job) == ["ask", "answer"]
    assert len(job["clips"]) == 1
    assert job["clips"][0]["trim_s"] == 8
    assert job["clips"][0]["cut_ids"] == ["ask", "answer"]
    assert job["status"] == "blocked"
    assert any("台詞" in reason for reason in job["blocked"])


def test_asmr_repeats_four_cuts_of_eight_seconds() -> None:
    job = bake.bake_reference("nuts0629", mode="asmr", theme="夕方の散歩")
    assert job["duration_s"] == 32
    assert [cut["duration_s"] for cut in job["cuts"]] == [8, 8, 8, 8]
    assert [clip["trim_s"] for clip in job["clips"]] == [8, 8, 8, 8]
    assert sum(clip["trim_s"] for clip in job["clips"]) == 32


def test_talk_makes_only_the_written_seconds() -> None:
    job = bake.bake_reference("nuts0629", mode="talk", theme="夕方の散歩", lines=["どっちが先"])
    assert job["template_duration_s"] == 37
    assert job["duration_s"] == 19
    assert job["cuts"][0]["end_s"] == 19
    assert sum(clip["trim_s"] for clip in job["clips"]) == 19
    assert all(bake._accepts(clip["request_s"]) for clip in job["clips"])
    assert job["status"] == "ready"
    assert any("19–37 秒は区間が無いので作らない" in note for note in job["notes"])
    assert job["performance"]["motion"]["template_coverage"] == "型に書いてある動作は全部入っている"
    assert job["performance"]["bgm"]["summary"] == "BGMはあると型にある。楽器は不明なので曲は足さない。"


def test_beauty_is_three_ten_second_cuts_without_the_cover() -> None:
    job = bake.bake_reference("the.care.logic", theme="夕方の散歩")
    assert job["duration_s"] == 30
    assert _ids(job) == ["problem", "action", "result"]
    assert [clip["trim_s"] for clip in job["clips"]] == [10, 10, 10]
    assert job["aspect"] == "9:16"
    assert all(job["look"]["en"] in clip["prompt"] for clip in job["clips"])
    assert all(job["look"]["ja"] not in clip["prompt"] for clip in job["clips"])
    assert all("夕方の散歩" not in clip["prompt"] for clip in job["clips"])
    assert all("Do not draw writing on the picture." in clip["prompt"] for clip in job["clips"])
    assert all("画面の文字は" not in clip["prompt"] for clip in job["clips"])
    assert job["performance"]["motion"]["template_coverage"] == "型に書いてある動作は全部入っている"
    assert job["performance"]["captions"]["summary"] == "声と同じ文。型は字幕を焼かない。"


def test_long_templates_keep_their_runtime_and_split_only_for_h3() -> None:
    cats = bake.bake_reference("junjun_ranran", theme="夕方の散歩")
    assert cats["duration_s"] == 45
    assert _ids(cats) == ["hook", "argument", "punch"]
    assert sum(clip["trim_s"] for clip in cats["clips"]) == 45
    hook = cats["clips"][0]
    assert hook["trim_s"] == 3
    assert hook["request_s"] == 5
    assert all(bake._accepts(clip["request_s"]) for clip in cats["clips"])

    drama = bake.bake_reference("yako.shiawasekon", theme="夕方の散歩")
    assert drama["duration_s"] == 60
    assert sum(clip["trim_s"] for clip in drama["clips"]) == 60
    assert all(5 <= clip["request_s"] <= 15 for clip in drama["clips"])
    assert all(bake._accepts(clip["request_s"]) for clip in drama["clips"])


def test_look_is_the_same_on_every_clip_and_likeness_stops() -> None:
    job = bake.bake_genre("見守りカメラ", theme="夕方の散歩")
    assert all(job["look"]["ja"] not in clip["prompt"] for clip in job["clips"])
    assert all(job["look"]["en"] in clip["prompt"] for clip in job["clips"])
    assert job["source"] == "genre"
    assert job["seconds_from"] == "reference-template"
    assert job["duration_s"] == 45
    try:
        bake.bake_reference("nuts0629", mode="dance", theme="すず丸のまね")
    except ValueError as exc:
        assert "すず丸" in str(exc)
    else:
        raise AssertionError("likeness was accepted")


def test_genre_table_does_not_change_the_cut_clock() -> None:
    job = bake.bake_genre("ドッグフード", theme="夕方の散歩")
    before = [cut["duration_s"] for cut in job["cuts"]]
    bake.annotate_table(
        job,
        duration_band="31〜60秒",
        opening_type="その他",
        main_subject="動物",
        face_shown="なし",
        basis="伸びてる群の傾向",
        account_confidence="弱い",
        homage={"first_3_seconds": "同じ子", "borrow": ["同じ子を最初から出す"], "do_not_copy": ["すず丸本人"]},
    )
    assert [cut["duration_s"] for cut in job["cuts"]] == before
    assert job["genre_table"]["duration_band"] == "31〜60秒"
    assert job["duration_s"] == 8
    assert "すず丸" not in job["clips"][0]["prompt"]


def test_h3_acceptance_matches_the_runner_when_it_is_installed() -> None:
    from h3_runner.official import diffusers_accepts, frames_for_seconds

    for seconds in (5, 8, 10, 13.5, 14, 15):
        assert bake._accepts(seconds) is bool(diffusers_accepts(frames_for_seconds(seconds)))


def _cell_source(cell: dict) -> str:
    return "".join(cell["source"])


def test_story_form_defaults_match_the_story() -> None:
    known = set(ref.catalog()["defaults"])
    seen: set[str] = set()
    for sections in bake.STORY_FORMS.values():
        for _title, fields in sections:
            for label, key, default in fields:
                assert label.isidentifier()
                assert key in known
                assert default in bake._options_for(key)
                seen.add(ref._field_id(key))
    assert seen == set(ref.catalog()["fields"])

    cats = bake.look_from_form(
        {
            label: default
            for _title, fields in bake.STORY_FORMS["junjun_ranran"]
            for label, _key, default in fields
        }
    )
    block = ref.look_block("junjun_ranran", cats)
    assert "マンチカン" in block["ja"]
    assert "スコティッシュフォールド" in block["ja"]
    assert "柴" not in block["ja"]
    drama = {
        label: default
        for _title, fields in bake.STORY_FORMS["yako.shiawasekon"]
        for label, _key, default in fields
    }
    yako = ref.look_block("yako.shiawasekon", bake.look_from_form(drama))
    assert "カフェ" in yako["ja"]
    assert "30代" in yako["ja"]
    custom = bake.look_from_form({"犬の衣装": "緑のバンダナ"})
    assert custom["animal_outfit"] == "その他（直接入力）"
    assert custom["animal_outfit_text"] == "緑のバンダナ"
    assert "緑のバンダナ" in ref.look_block("nuts0629", custom)["ja"]
    try:
        bake.look_from_form({"無い欄": "犬"})
    except KeyError as exc:
        assert "無い欄" in str(exc)
    else:
        raise AssertionError("unknown form label was accepted")
    try:
        bake.look_from_form({"犬の衣装": "その他（直接入力）"})
    except ValueError as exc:
        assert "犬の衣装" in str(exc)
    else:
        raise AssertionError("empty other-text was accepted")


def test_form_status_and_story_check_stay_on_one_account() -> None:
    assert bake.form_status(None, "nuts0629").startswith("先に")
    assert bake.form_status("nuts0629", "nuts0629") == ""
    skipped = bake.form_status("the.care.logic", "nuts0629")
    assert "美容：材料のキャラ" in skipped
    assert "この欄は使いません" in skipped

    cats = bake.story_check("junjun_ranran")
    assert "F2" in cats
    assert "F1" not in cats
    assert "F3" not in cats
    assert "最初のセリフ" in cats
    assert "冒頭の文字の表紙" not in cats
    assert "字幕:" not in cats
    beauty = bake.story_check("the.care.logic")
    assert "制作可否テストは無い" in beauty
    assert "冒頭の文字の表紙" in beauty
    assert "F1" not in beauty
    dog = bake.story_check("nuts0629", "dance")
    assert "F3" in dog
    assert "これは焼くジョブではない。" in dog
    assert "日本語の口パク" not in dog


def test_reference_notebook_is_one_japanese_form_per_story() -> None:
    disk = json.loads((ROOT / "affi.ipynb").read_text(encoding="utf-8"))
    built = bake.reference_notebook()
    disk_src = [_cell_source(cell) for cell in disk["cells"]]
    built_src = [_cell_source(cell) for cell in built["cells"]]
    assert disk_src == built_src
    blob = "\n".join(disk_src)
    assert "animal_species" not in blob
    assert "THEME" not in blob
    for sentence in bake.STORIES.values():
        assert sentence in blob
    for label, _handle in bake.ACCOUNT_CHOICES:
        assert label in blob
    assert blob.count("look_from_form") == 4
    assert "静止画" in blob
    code = [_cell_source(cell) for cell in disk["cells"] if cell["cell_type"] == "code"]
    assert len(code) == 8
    assert "すべてのセルを実行" in blob
    assert "押しません" in blob
    assert "読み込み" in blob
    assert "実行" in blob
    assert "#@title 焼く" in blob
    assert "publish_job_dir" in blob
    assert "マウントしたアカウントのマイドライブ" in blob
    assert "fireworker06" not in blob
    assert "最初の1本だけ" in blob
    assert "重みが無いとき落とす" in blob
    assert "この場で焼く" not in blob
    assert "orbis01" not in blob
    for src in code:
        ast.parse(src)
    bake_src = next(src for src in code if "#@title 焼く" in src)
    assert bake_src.index("if not 焼く") < bake_src.index("google.colab")
    quiet: dict = {}
    exec(bake_src, quiet)
    assert quiet["焼く"] is False
    assert quiet["最初の1本だけ"] is False
    assert "残っている範囲を続けて焼いて" in bake_src
    assert quiet["重みが無いとき落とす"] is False

    forms = [src for src in code if "look_from_form" in src]
    ns: dict = {"HANDLE": "junjun_ranran", "MODE": None}
    for src in forms:
        exec(src, ns)
    look = ns["look"]
    assert look["animal_species"] == "猫"
    assert look["animal_breed"] == "マンチカン"
    assert look["animal2_species"] == "猫"
    assert look["animal2_breed"] == "スコティッシュフォールド"
    assert look["animal2_coat"] == "白の短毛"
    assert "mascot_subject" not in look

    beauty_ns: dict = {"HANDLE": "the.care.logic", "MODE": None}
    for src in forms:
        exec(src, beauty_ns)
    assert beauty_ns["look"]["mascot_subject"] == "茶葉"
    assert "animal_species" not in beauty_ns["look"]

    picker = next(src for src in code if "resolve_account" in src)
    picked: dict = {}
    exec(picker, picked)
    assert picked["HANDLE"] == "nuts0629"
    assert picked["MODE"] == "interview"
    assert "affi_av.py" in blob
    assert "run_choice" in blob
    assert "手入力で I2V" in blob
    assert "テンプレ" in blob
    assert "オマージュ" in blob
    assert "元の型のまま" in blob
    assert "元動画を再現" in blob
    assert "transformer_ref" in blob
    assert "affi_speech.py" in blob
    assert "faster-whisper" in blob
    assert "台詞の文字はプロンプトに写しません" not in blob
    loader = next(src for src in code if "#@title 読み込み" in src)
    for name in ("affi_media.py", "affi_speech.py", "affi_speaker.py", "affi_finish.py", "affi_match.py"):
        assert loader.index(f'"{name}",') < loader.index('"affi_bake.py",')
    assert picked["範囲の切り方"] == bake.SPLIT_CHOICES[0][0]
    assert picked["題字"] == "" and picked["ロゴ"] == "" and picked["曲"] == ""
    assert "speaker_install_argv" in blob
    run_src = next(src for src in code if "#@title 実行" in src)
    assert 'HF_TOKEN = "" #@param {type:"string"}' in run_src
    assert "https://huggingface.co/settings/tokens" in run_src
    assert "このセルの HF_TOKEN 欄が空なので話者は分けない。" in run_src
    assert "同意済みなら、そのトークンを欄に貼るだけでよい。" in run_src
    assert "speaker_gate_lines" not in run_src
    assert 'globals().get("HF_TOKEN")' in bake_src
    assert "skip_done=True" in bake_src
    assert "measure_repro_clip" in bake_src
    assert "all_clips_made" in bake_src
    assert "not 最初の1本だけ" not in bake_src
    for name in ("reference_check.ipynb", "affi_genre_templates.ipynb"):
        moved = json.loads((ROOT / name).read_text(encoding="utf-8"))
        moved_src = "\n".join(_cell_source(cell) for cell in moved["cells"])
        assert moved_src == _cell_source(bake.moved_notebook()["cells"][0])
        assert bake.NOTEBOOK_URL in moved_src
        assert "affi.ipynb" in moved_src


def _outside_dialogue(prompt: str) -> str:
    return _DIALOGUE.sub("", prompt)


def test_a_job_without_a_look_uses_that_storys_defaults() -> None:
    cats = bake.bake_reference("junjun_ranran", theme="夕方の散歩", lines=["いち", "に", "さん"])
    prompt = cats["clips"][0]["prompt"]
    assert "Munchkin" in prompt
    assert "Scottish Fold" in prompt
    assert "Shiba" not in prompt
    drama = bake.bake_reference("yako.shiawasekon", theme="夕方の散歩", lines=["はじめ", "なか", "おわり"])
    assert "a cafe" in drama["clips"][0]["prompt"]
    assert "thirties" in drama["clips"][0]["prompt"]


def test_every_template_beat_has_english_motion() -> None:
    for handle in bake.GENRE_HANDLES.values():
        item = ref.template_for(handle)
        timelines = []
        if item.get("modes"):
            timelines.extend(block["timeline"] for block in item["modes"].values())
        if item.get("timeline"):
            timelines.append(item["timeline"])
        for timeline in timelines:
            for beat in timeline:
                if beat.get("optional"):
                    continue
                key = (handle, str(beat["id"]))
                assert key in affi_av.MOTION_EN
                assert key in affi_av.ON_SCREEN


def test_prompt_keeps_japanese_inside_the_spoken_line() -> None:
    job = bake.bake_reference("the.care.logic", theme="夕方の散歩", lines=["悩んでる", "なでた", "笑った"])
    assert job["theme"] == "夕方の散歩"
    for clip, line in zip(job["clips"], ["悩んでる", "なでた", "笑った"]):
        prompt = clip["prompt"]
        assert job["look"]["en"] in prompt
        assert job["look"]["ja"] not in prompt
        assert "夕方の散歩" not in prompt
        assert "lip-synced" not in prompt.casefold()
        assert clip["motion_ja"][0]["picture"] not in prompt
        assert clip["motion_ja"][0]["picture"] == next(cut["picture"] for cut in job["cuts"] if cut["id"] == clip["motion_ja"][0]["id"])
        assert clip["motion_ja"][0]["camera"] == next(cut["camera"] for cut in job["cuts"] if cut["id"] == clip["motion_ja"][0]["id"])
        assert f"<d>[Japanese] {line}</d>" in prompt
        assert not _CJK.search(_outside_dialogue(prompt))
        assert "higher-pitched" in prompt
        assert "200 to 330 Hz" in prompt
    mascot = next(row for row in job["performance"]["voices"] if row["id"] == "mascot")
    assert "low" not in mascot["voice_en"]
    assert all(row["burn"] is False for row in job["performance"]["captions"]["rows"])
    assert [row["text"] for row in job["performance"]["captions"]["rows"]] == ["悩んでる", "なでた", "笑った"]


def test_placeholder_line_is_not_spoken() -> None:
    job = bake.bake_reference("the.care.logic", theme="夕方の散歩")
    assert all("<d>" not in clip["prompt"] for clip in job["clips"])
    assert all("台詞は入力" not in clip["prompt"] for clip in job["clips"])
    assert all(row["text"] == "" for row in job["performance"]["captions"]["rows"])


def test_interview_speaks_both_lines_once_and_adds_no_song() -> None:
    job = bake.bake_reference("nuts0629", mode="interview", theme="夕方の散歩", lines=["質問です", "わんわん"])
    assert len(job["clips"]) == 1
    prompt = job["clips"][0]["prompt"]
    assert prompt.count("質問です") == 1
    assert prompt.count("わんわん") == 1
    assert "A microphone is visible." in prompt
    assert "a high voice, estimated in the template" in prompt
    assert "non_diegetic_music: N/A" in prompt
    assert job["performance"]["bgm"]["summary"] == "型は曲なし。BGMは足さない。"
    rows = {row["id"]: row for row in job["performance"]["captions"]["rows"]}
    assert rows["ask"]["text"] == "質問です"
    assert rows["ask"]["start_s"] == 0
    assert rows["ask"]["end_s"] == 4
    assert rows["answer"]["text"] == "わんわん"
    assert rows["answer"]["end_s"] == 8
    assert rows["ask"]["burn"] is False
    assert rows["answer"]["burn"] is False


def test_split_line_is_spoken_once_and_the_caption_follows_that_piece() -> None:
    cats = bake.bake_reference("junjun_ranran", theme="夕方の散歩", lines=["いち", "に", "さん"])
    hook = next(clip for clip in cats["clips"] if clip["cut_ids"] == ["hook"])
    assert hook["prompt"].count("いち") == 1
    assert "does not name which role speaks it" in hook["prompt"]
    assert "the retorting cat (S1)" not in hook["prompt"]
    arguments = [clip for clip in cats["clips"] if clip["cut_ids"] == ["argument"]]
    assert len(arguments) == 2
    assert arguments[0]["prompt"].count("に") == 1
    assert "に" not in arguments[1]["prompt"]
    assert "The spoken line is not repeated." in arguments[1]["prompt"]
    punches = [clip for clip in cats["clips"] if clip["cut_ids"] == ["punch"]]
    assert len(punches) == 2
    assert punches[0]["prompt"].count("さん") == 1
    assert "さん" not in punches[1]["prompt"]
    rows = {row["id"]: row for row in cats["performance"]["captions"]["rows"]}
    assert rows["hook"]["text"] == "いち"
    assert rows["hook"]["burn"] is True
    assert (rows["hook"]["start_s"], rows["hook"]["end_s"]) == (0, 3)
    assert rows["argument"]["text"] == "に"
    assert (rows["argument"]["start_s"], rows["argument"]["end_s"]) == (arguments[0]["start_s"], arguments[0]["end_s"])
    assert rows["punch"]["text"] == "さん"
    assert (rows["punch"]["start_s"], rows["punch"]["end_s"]) == (punches[0]["start_s"], punches[0]["end_s"])
    assert cats["performance"]["motion"]["template_coverage"] == "型に書いてある動作は全部入っている"
    assert cats["performance"]["motion"]["source_video"] == "元動画の一致率は測っていない"
    assert cats["performance"]["bgm"]["prompt"] == "N/A"
    assert cats["performance"]["bgm"]["summary"] == "BGMは型が不明。足さない。"
    for clip in cats["clips"]:
        for row in clip["motion_ja"]:
            cut = next(item for item in cats["cuts"] if item["id"] == row["id"])
            assert row["picture"] == cut["picture"]
            assert row["camera"] == cut["camera"]


def test_piano_is_the_only_copied_music_and_captions_burn() -> None:
    drama = bake.bake_reference("yako.shiawasekon", theme="夕方の散歩", lines=["はじめ", "なか", "おわり"])
    assert all("Sparse piano notes at a slow tempo." in clip["prompt"] for clip in drama["clips"])
    assert all("Emotional piano solo" not in clip["prompt"] for clip in drama["clips"])
    assert drama["performance"]["bgm"]["summary"] == "ピアノ。曲名はコピーしない。"
    assert all(row["burn"] and row["text"] for row in drama["performance"]["captions"]["rows"])
    middles = [clip for clip in drama["clips"] if clip["cut_ids"] == ["middle"]]
    assert middles
    assert middles[0]["prompt"].count("なか") == 1
    assert all("なか" not in clip["prompt"] for clip in middles[1:])


def test_custom_japanese_look_is_not_read_aloud() -> None:
    look = bake.look_from_form({"犬の衣装": "緑のバンダナ"})
    job = bake.bake_reference("nuts0629", mode="dance", theme="夕方の散歩", look=look)
    assert "緑のバンダナ" in job["look"]["ja"]
    assert "緑のバンダナ" not in job["clips"][0]["prompt"]
    assert "Untranslated look notes stay on the still and are not spoken." in job["clips"][0]["prompt"]
    assert not _CJK.search(_outside_dialogue(job["clips"][0]["prompt"]))


def test_fills_supply_the_theme_and_leave_out_the_source_lines(tmp_path: Path) -> None:
    banned = ("飼い主に言いたいことはありますか", "感謝感謝", "本能寺", "すず丸")
    seen: set[tuple[str, str | None, str]] = set()
    for handle in bake.GENRE_HANDLES.values():
        modes: list[str | None] = ["interview", "asmr", "dance", "talk"] if handle == "nuts0629" else [None]
        for mode in modes:
            themes = set()
            for label, fill in bake.FILL_CHOICES:
                job = bake.bake_reference(handle, mode=mode, fill=fill)
                seen.add((handle, mode, fill))
                themes.add(job["theme"])
                assert job["fill"]["label"] == label
                assert job["fill"]["note"] == bake._FILL_NOTE
                assert "テーマは入力" not in job["blocked"]
                assert job["theme"] not in "".join(clip["prompt"] for clip in job["clips"])
                if job["clips"]:
                    assert job["subject_en"] in job["clips"][0]["prompt"]
                    assert not _CJK.search(job["subject_en"])
                for cut in job["cuts"]:
                    if cut["needs_line"]:
                        assert cut["line"] != bake.PLACEHOLDER_LINE
                        spoken = "".join(
                            clip["prompt"]
                            for clip in job["clips"]
                            if cut["id"] in clip["cut_ids"] and clip["part_index"] == 0
                        )
                        if job["clips"]:
                            assert f"<d>[Japanese] {cut['line']}</d>" in spoken
                blob = json.dumps(job, ensure_ascii=False)
                for word in banned:
                    assert word not in blob
            assert len(themes) == 3
    assert len(seen) == (3 + 4) * 3
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    ready = bake.bake_reference("nuts0629", mode="dance", fill="source", image=str(still))
    assert ready["status"] == "ready"
    assert ready["blocked"] == []
    talk = bake.bake_reference("nuts0629", mode="talk", fill="template")
    assert talk["status"] == "ready"
    assert talk["duration_s"] == 19
    assert talk["clips"]
    assert any("足さない" in note for note in talk["notes"])


def test_manual_i2v_keeps_the_typed_prompt_and_does_not_render(tmp_path: Path) -> None:
    wrapped = affi_av.i2v_prompt("The dog turns its head.")
    assert wrapped.startswith(affi_av.I2VA_HEADER)
    assert wrapped.count(affi_av.I2VA_HEADER) == 1
    assert "The dog turns its head." in wrapped
    assert "non_diegetic_music: N/A" in wrapped
    full = affi_av.I2VA_HEADER + "\n\nintegrated_multimodal_description: already written.\n"
    assert affi_av.i2v_prompt(full) == full if full.endswith("\n") else full + "\n"
    assert affi_av.i2v_prompt(full).count(affi_av.I2VA_HEADER) == 1
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    job = bake.plan_i2v(image=str(still), prompt="The dog turns its head.", duration_s="10", aspect="9:16")
    assert job["status"] == "ready"
    assert job["task"] == "i2va"
    plain = bake.plan_i2v(image="", prompt="The dog turns its head.", duration_s="10", aspect="9:16")
    assert plain["status"] == "ready"
    assert plain["task"] == "t2va"
    assert plain["prompt"].startswith("integrated_multimodal_description:")
    assert "Picture" not in plain["prompt"]
    assert "<Picture" not in plain["prompt"]
    assert job["generates_video"] is False
    assert job["posts"] is False
    path = bake.write_i2v(job, tmp_path / "i2v")
    command = (tmp_path / "i2v" / "commands.txt").read_text(encoding="utf-8")
    assert "--task i2va" in command
    assert f"--image {still}" in command
    assert "--steps 9" in command
    assert f"{affi_av.TURBO_FILENAME}:1.0" in command
    assert job["argv"][job["argv"].index("--task") + 1] == "i2va"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["generates_video"] is False
    empty = bake.plan_i2v(image=str(still), prompt="  ", duration_s=10)
    assert empty["status"] == "blocked"
    assert any("プロンプト" in reason for reason in empty["blocked"])
    try:
        bake.plan_i2v(image=str(still), prompt="すず丸が振り向く", duration_s=10)
    except ValueError as exc:
        assert "すず丸" in str(exc)
    else:
        raise AssertionError("likeness was accepted")
    try:
        bake.plan_i2v(image=str(still), prompt="The dog turns its head.", duration_s=15)
    except ValueError as exc:
        assert "秒" in str(exc)
    else:
        raise AssertionError("15 seconds was accepted")


def test_one_choice_runs_the_table_or_one_job_or_i2v(tmp_path: Path) -> None:
    table = bake.run_choice(
        "表を見る",
        data_dir=ROOT / "data" / "2026-10-07",
        table_out=tmp_path / "templates",
    )
    assert "美容スキンケア" in table
    assert "ジョブはここでは書きません" in table
    assert "mp4" not in table
    assert (tmp_path / "templates" / "compare.md").is_file()
    missing = bake.run_choice("表を見る", data_dir=tmp_path / "missing")
    assert "読み込み" in missing

    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    job_text = bake.run_choice(
        "話でジョブを書く",
        handle="the.care.logic",
        fill_label="テンプレ",
        image=str(still),
        out_dir=tmp_path / "jobs",
    )
    assert "夕方の乾燥" in job_text
    assert "ready" in job_text
    assert "見た目は初期値です" in job_text
    assert "型に書いてある動作は全部入っている" in job_text
    assert "mp4 は焼いていない" in job_text
    other = bake.default_look("junjun_ranran")
    ignored = bake.run_choice(
        "話でジョブを書く",
        handle="nuts0629",
        mode="dance",
        fill_label="元の型のまま",
        look=other,
        image=str(still),
        out_dir=tmp_path / "jobs",
    )
    assert "見た目は初期値です" in ignored
    assert "ready" in ignored
    assert bake.look_is_for("nuts0629", bake.default_look("nuts0629"))
    assert not bake.look_is_for("nuts0629", other)

    typed = bake.run_choice(
        "自分の文で1本",
        image=str(still),
        prompt="The dog turns its head.",
        duration_s="10",
        aspect="9:16",
        out_dir=tmp_path / "jobs",
    )
    assert "手入力で I2V" in typed
    assert "ready" in typed
    assert "--task i2va" in typed
    assert "mp4 は焼いていない" in typed
    assert bake.next_step("表を見る").startswith("次は「実行」")
    assert bake.next_step("話でジョブを書く").startswith("次は「実行」")
    assert bake.next_step("自分の文で1本").startswith("次は「実行」")
    assert "元動画" in bake.next_step("元動画を再現")


def test_bite_mentions_the_mouth_and_does_not_invent_the_chew() -> None:
    job = bake.bake_reference("nuts0629", mode="asmr", theme="夕方の散歩")
    assert "Mouth movement is visible. The template does not say whether chewing is audible." in job["clips"][0]["prompt"]
    assert "<d>" not in job["clips"][0]["prompt"]
    assert job["performance"]["bgm"]["summary"] == "音源名は型が不明。元の音はコピーしない。"


def test_commands_to_run_uses_the_written_job_and_stops_when_blocked(tmp_path: Path) -> None:
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    bake.run_choice(
        "話でジョブを書く",
        handle="the.care.logic",
        fill_label="テンプレ",
        image=str(still),
        out_dir=tmp_path,
    )
    path = bake.commands_file("話でジョブを書く", handle="the.care.logic", out_dir=tmp_path)
    assert path is not None and path.is_file()
    one, note = bake.commands_to_run(path, first_only=True)
    assert len(one) == 1
    assert "run_h3.py" in one[0]
    assert "--task" in one[0]
    assert "fl2va" in one[0]
    assert "残りは" in note
    every, all_note = bake.commands_to_run(path, first_only=False)
    assert len(every) > 1
    assert all_note == f"{len(every)} 本焼きます。"
    first_out = bake._out_of(every[0])
    assert first_out is not None
    first_out.parent.mkdir(parents=True, exist_ok=True)
    first_out.write_bytes(b"mp4")
    bake.mark_done(every[0])
    rest, rest_note = bake.commands_to_run(path, first_only=False, skip_done=True)
    assert rest == every[1:]
    assert "飛ばします" in rest_note
    assert f"{len(rest)} 本焼きます。" in rest_note
    for line in every[1:]:
        out = bake._out_of(line)
        assert out is not None
        out.write_bytes(b"mp4")
        bake.mark_done(line)
    none, done_note = bake.commands_to_run(path, first_only=False, skip_done=True)
    assert none == []
    assert "このあとつなぐ" in done_note

    bake.run_choice(
        "話でジョブを書く",
        handle="nuts0629",
        mode="talk",
        fill_label="テンプレ",
        image=str(tmp_path / "gone.jpg"),
        out_dir=tmp_path,
    )
    blocked = bake.commands_file("話でジョブを書く", handle="nuts0629", mode="talk", out_dir=tmp_path)
    assert blocked is not None
    empty, message = bake.commands_to_run(blocked, first_only=True)
    assert empty == []
    assert "止まっているので焼かない" in message
    assert "静止画" in message

    missing, missing_note = bake.commands_to_run(tmp_path / "nope.txt", first_only=True)
    assert missing == []
    assert "実行" in missing_note

    bake.run_choice(
        "自分の文で1本",
        image=str(still),
        prompt="The dog turns its head.",
        duration_s="10",
        out_dir=tmp_path,
    )
    typed = bake.commands_file("自分の文で1本", out_dir=tmp_path)
    assert typed is not None
    i2v_lines, i2v_note = bake.commands_to_run(typed, first_only=True)
    assert len(i2v_lines) == 1
    assert "i2va" in i2v_lines[0]
    assert "最初の1本だけ焼きます。" in i2v_note
    text_job = bake.plan_i2v(image="", prompt="The dog turns its head.", duration_s="10")
    bake.write_i2v(text_job, tmp_path / "text-clip")
    text_lines, _text_note = bake.commands_to_run(tmp_path / "text-clip" / "commands.txt", first_only=True)
    assert "--task t2va" in text_lines[0]
    assert "--image" not in text_lines[0]
    blank = bake.plan_i2v(image="", prompt="  ", duration_s=10)
    bake.write_i2v(blank, tmp_path / "blank")
    none, blank_note = bake.commands_to_run(tmp_path / "blank" / "commands.txt", first_only=True)
    assert none == []
    assert "プロンプトが空" in blank_note
    assert "T2V。プロンプトは手入力" not in blank_note
    cache = tmp_path / "h3-weights"
    prepared = bake.prepare_command(i2v_lines[0], cache)
    assert "--prepare-weights" in prepared
    assert f"--cache-dir {cache}" in prepared
    again = bake.prepare_command(prepared, cache)
    assert again.split().count("--prepare-weights") == 1
    assert again.split().count("--cache-dir") == 1

    absent = bake.missing_weight_files(cache)
    assert any(item.endswith("modular_model_index.json") for item in absent)
    assert any(item.endswith(affi_av.TURBO_FILENAME) for item in absent)
    assert any(item.endswith(affi_av.REPAIR_FILENAME) for item in absent)
    marker = cache / "MiniMax-H3" / "modular_model_index.json"
    marker.parent.mkdir(parents=True)
    marker.write_text("{}", encoding="utf-8")
    for name in (affi_av.TURBO_FILENAME, affi_av.REPAIR_FILENAME):
        (cache / "loras" / name).parent.mkdir(parents=True, exist_ok=True)
        (cache / "loras" / name).write_bytes(b"x")
    assert bake.missing_weight_files(cache) == []
    assert bake.commands_file("表を見る", out_dir=tmp_path) is None


def test_run_logged_shows_the_child_text(capsys, tmp_path: Path) -> None:
    code = bake.run_logged(
        [sys.executable, "-c", "import sys; print('visible-line'); sys.exit(1)"],
        tmp_path,
    )
    assert code == 1
    assert "visible-line" in capsys.readouterr().out


def test_a_finished_clip_is_copied_onto_drive(tmp_path: Path) -> None:
    job = tmp_path / "affi-bake" / "junjun_ranran"
    clip = job / "clips" / "01-hook.mp4"
    clip.parent.mkdir(parents=True)
    clip.write_bytes(b"mp4-bytes")
    (job / "job.json").write_text("{}\n", encoding="utf-8")
    (job / "clips" / "01-hook.request.json").write_text("{}\n", encoding="utf-8")
    saved = bake.publish_job_dir(job, drive_root=tmp_path / "drive")
    assert (saved / "job.json").read_text(encoding="utf-8") == "{}\n"
    assert (saved / "clips" / "01-hook.mp4").read_bytes() == b"mp4-bytes"
    assert saved == tmp_path / "drive" / "junjun_ranran"


def test_a_source_video_becomes_ref2va_slices_without_fl2v_lora(tmp_path: Path) -> None:
    source = tmp_path / "source-secret.mp4"
    source.write_bytes(b"not-a-real-video")
    job = bake.plan_reproduce(video=str(source), duration_s=45, aspect="9:16")
    assert job["status"] == "ready"
    assert job["task"] == "ref2va"
    assert job["duration_s"] == 45
    assert job["video_shift"] == 12
    assert job["steps"] == 50
    covered = 0.0
    for clip in job["clips"]:
        span = clip["end_s"] - clip["start_s"]
        assert 5 <= span <= 15
        assert bake._accepts(clip["request_s"])
        covered += span
        assert "<d>" not in clip["prompt"]
        assert "Mouths do not form words." not in clip["prompt"]
        assert "shapes the words heard in the soundtrack of <Video 1>" in clip["prompt"]
        assert "lip-synced" not in clip["prompt"].casefold()
        assert "source-secret" not in clip["prompt"]
        assert "<Picture 1>" not in clip["prompt"]
        for header in (
            "subject_definitions:",
            "summary:",
            "retention_analysis:",
            "detailed_description:",
            "overall_soundscape:",
            "non_diegetic_music:",
        ):
            assert header in clip["prompt"]
        assert clip["prompt"].index("subject_definitions:") < clip["prompt"].index("non_diegetic_music:")
        assert "<Video 1>" in clip["prompt"]
        assert "fully_preserved" in clip["prompt"]
    assert abs(covered - 45) < 0.02
    assert job["speech"] == []
    assert job["speech_known"] is False
    assert "文は足さない" in job["speech_note"]
    assert job["cuts"] is None
    assert any("カットは測っていない" in note for note in job["notes"])
    assert all("When <Video 1> cuts, the target video cuts at that same moment" in clip["prompt"] for clip in job["clips"])
    assert job["short_edge"] == 512
    path = bake.write_reproduce(job, tmp_path / "repro")
    commands = (path.parent / "commands.txt").read_text(encoding="utf-8")
    assert "status=ready" in commands
    assert "--task ref2va" in commands
    assert "--lora" not in commands
    assert affi_av.TURBO_FILENAME not in commands
    assert "ffmpeg" not in commands
    assert "--video-shift 12" in commands
    assert "--steps 50" in commands
    assert "--image" not in commands
    lines, note = bake.commands_to_run(path.parent / "commands.txt", first_only=True)
    assert len(lines) == 1
    assert "--video" in lines[0]
    assert "--video-start" in lines[0]
    assert "最初の1本だけ" in note
    join = bake.join_line(path.parent)
    assert join is not None
    assert join.startswith("ffmpeg ")
    from h3_runner.ffmpeg_join import join_command

    parts = [(path.parent / "clips" / f"{clip['id']}.mp4", float(clip["trim_s"])) for clip in job["clips"]]
    assert shlex.split(join) == join_command(parts, path.parent / "source.mov", width=1080, height=1920, audio="pcm")
    finish = bake.finish_lines(path.parent)
    assert len(finish) == 2
    last = shlex.split(finish[1])
    assert last[last.index("-i") + 1] == str(path.parent / "source.mov")
    assert last[-1] == str(path.parent / "source.mp4")
    assert last[last.index("-c:v") + 1] == "copy"
    assert last[last.index("-c:a") + 1] == "aac"
    assert not (path.parent / "captions.ass").exists()
    still = tmp_path / "still.jpg"
    still.write_bytes(b"jpeg")
    with_still = bake.plan_reproduce(video=str(source), image=str(still), duration_s=8)
    assert with_still["status"] == "ready"
    assert len(with_still["clips"]) == 1
    assert "<Picture 1>" in with_still["clips"][0]["prompt"]
    wrote = bake.write_reproduce(with_still, tmp_path / "with-still")
    still_cmd = (wrote.parent / "commands.txt").read_text(encoding="utf-8")
    assert "--image" in still_cmd
    shown = bake.run_choice("元動画を再現", video=str(source), out_dir=tmp_path / "probed")
    assert "秒数が測れない" in shown
    assert "ready" not in shown
    assert "一致率は、焼いたあとに範囲ごとに測る" in shown
    assert bake.commands_file("元動画を再現", out_dir=tmp_path / "probed") == tmp_path / "probed" / "repro" / "commands.txt"


def test_a_missing_source_video_does_not_invent_a_length(tmp_path: Path) -> None:
    missing = bake.plan_reproduce(video=str(tmp_path / "gone.mp4"))
    assert missing["status"] == "blocked"
    assert missing["clips"] == []
    assert missing["duration_s"] is None
    assert any("ファイルが無い" in reason for reason in missing["blocked"])


def test_a_file_under_five_seconds_is_held_to_five_and_cut_back(tmp_path: Path) -> None:
    short = tmp_path / "short.mp4"
    short.write_bytes(b"x")
    under = bake.plan_reproduce(video=str(short), duration_s=4)
    assert under["status"] == "ready"
    assert len(under["clips"]) == 1
    clip = under["clips"][0]
    assert (clip["start_s"], clip["end_s"], clip["trim_s"], clip["request_s"]) == (0.0, 4.0, 4.0, 5.0)
    assert clip["pad_s"] == round(124 / 24 - 4.0, 3)
    assert "From 00:04.000, <Video 1> holds its last frame in silence." in clip["prompt"]
    assert any("5秒まで止め絵と無音で生成し、元の秒に戻す" in note for note in under["notes"])
    path = bake.write_reproduce(under, tmp_path / "short-job")
    lines, _note = bake.commands_to_run(path.parent / "commands.txt", first_only=True)
    assert "--duration 5" in lines[0]
    assert "--video-end 4" in lines[0]
    assert "trim=duration=4.000" in bake.join_line(path.parent)


def test_repro_weights_are_transformer_ref_and_not_the_fl2v_stack(tmp_path: Path) -> None:
    cache = tmp_path / "h3-weights"
    missing = bake.missing_weight_files(cache, "元動画を再現")
    assert any(item.endswith("transformer_ref") for item in missing)
    assert all(affi_av.TURBO_FILENAME not in item for item in missing)
    assert all(affi_av.REPAIR_FILENAME not in item for item in missing)


