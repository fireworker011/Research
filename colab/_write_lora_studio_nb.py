#!/usr/bin/env python3
"""Write a beginner-friendly MiniMax H3 LoRA studio Colab."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from h3_lora_studio import (  # noqa: E402
    ANTHOLOGY_LABEL,
    CHAIN_PACK_ORDER,
    STORY_ORDER,
    STORY_PLAY_DEDICATED,
    chain_pack_labels,
    story_play_label,
    story_play_labels,
)

ROOT = Path(__file__).resolve().parents[1]
OUTS = [
    ROOT / "minimax_h3_lora_studio.ipynb",
    ROOT / "minimaxh3" / "minimax_h3_lora_studio.ipynb",
    ROOT / "h3-lora-studio" / "minimax_h3_lora_studio.ipynb",
]

# ③ の並び: SFW → 専用11話×5再生 → 名前付きパック×5再生 → 短編集（参照） → 行為シーン
SFW_LABELS = ["日常（速い＋綺麗）", "最速プレビュー（エロなし）", "音も残す（エロなし）", "普通（エロなし）"]
ACT_LABELS = [
    "アナル挿入（画質）", "アナル舐め・指", "アナル指入れ", "フェラ（女体）", "ふたなりフェラ", "セックス（女体）",
    "アナルセックス（女体）", "騎乗位（女体）", "後背位（女体）", "正常位POV（女体）", "後射精（女体）", "顔射（女体）",
    "中出し（女体）", "口内射精（女体）", "指入れ", "オナニー", "足コキ", "絶頂", "汎用エロ（女体）", "試し打ち",
    "レズビアンクンニ", "性器を広げる", "レズ＋広げる",
]
DEFAULT_SCENE = story_play_label("commute-120s", STORY_PLAY_DEDICATED)  # 登校（専用）
SCENE_OPTIONS_3 = SFW_LABELS + story_play_labels() + chain_pack_labels() + [ANTHOLOGY_LABEL] + ACT_LABELS
# ② は話ごとに1つ（専用）で足りる。ダウンロードは story id 単位。短編集も入れる。
SCENE_OPTIONS_2 = (
    SFW_LABELS
    + [story_play_label(sid, STORY_PLAY_DEDICATED) for sid in STORY_ORDER + CHAIN_PACK_ORDER]
    + [ANTHOLOGY_LABEL]
    + ACT_LABELS
)
STORY_ID_LIST = list(STORY_ORDER) + list(CHAIN_PACK_ORDER) + ["shorts-immoral"]


def _options(rows: list[str]) -> str:
    return json.dumps(rows, ensure_ascii=False)


MD0 = r"""# MiniMax H3 で動画を作る（速い＋綺麗 / えっち）

写真なしの文章から、または写真1枚から、短い動画を作ります。

**18歳未満は使えません。出演者は全員 21歳以上の設定です。**

このノートは Google Colab の画面の中で完結します。難しいソフトの画面は開きません。

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_lora_studio.ipynb)

## やること（3つだけ）

1. **①** を実行 → Google Drive の許可を出す
2. **②** を実行 → 初回だけ待ちます（部品のダウンロード。2回目は速い）
3. **③** でシーンを選んで実行 → 下に動画が出る

③の初期値はこの版の準備どおり **登校（専用）** ＋ **テキストから（写真なし）**。シネマ質感とえっち部品を取るので **②の「CivitaiのAPIキー」を貼って**、上から順に ▶ を押す。**普通（エロなし）だけ**（専用ノートと同じ LightX2V）ならキーは空でOK。

## 今の準備（この版）

専用11話（帰宅〜縁側）と、名前付きパック13本（訪問販売・定期検診・終点、建前パックのカフェ・車内販売・赤信号・ヨガ・背中流し・カラオケ・ランドリー・講義机・キャンプ・花火）が入っています。どちらも③で **（専用）/（つなぐ）/（つなぐ修）/（参照つなぐ）/（参照つなぐ修）** の5つから選べます。**短編集（参照）** は15秒完結×複数・つなぎなし。画像サイズは JSON の canvas で決まる（専用11話は 16:9 か 9:16、パックと短編集は 9:16 576×1024）ので、文章に大きさは書かなくてよい。**写真が無くても動画は作れます**（T2V。参照モードだけ `input/cast/` の8枚が必須）。登校の試験jpgは品質が足りないので、③を「テキストから」のままにすると Drive の `input/commute-120s/` があっても使いません。キャスト8枚は `input/cast/`（`sayaka-bust` / `sayaka-full` / `rei-bust` / `rei-full` / `aya-bust` / `aya-full` / `madoka-bust` / `madoka-full`）。Imagine 2.0 でも使える。**参照つなぐ・参照つなぐ修・短編集（参照）** ではこの8枚を **R2V の identity 参照**にする（I2V の最初のコマではない。FL2VA と Ref2VA は混ぜない）。

## 120秒は混ぜない（普通のつなぐ / 専用5パターン / 名前付きパック5パターン / 短編集）

| 種類 | ③での選び方 | 何が起きるか |
|---|---|---|
| **普通のつなぐ** | やりたいシーンは日常・フェラなど普通の1シーン ＋ 長さの作り方「つなぐ 120秒」 | 1本目はテキストまたは写真。2本目以降は**最後のコマから I2V**。同じ場所・人・服・カメラ。文章欄が1本目。つなぎ欄は続きの拍。カット割りは書かない |
| **専用（専用）** | 「登校（専用）」など | **カット編集**。JSON のまま。各本は独立。最後のコマからは続けない。長さの作り方・つなぎ欄・秒数は無視 |
| **専用（つなぐ）** | 「登校（つなぐ）」など | 同じ JSON を**最後のコマから I2V** で繋ぐ。文は直さない（1本目も長回しに直さない。③合わせも掛けない）。Picture 1 のロックだけ足す |
| **専用（つなぐ修）** | 「登校（つなぐ修）」など | 最後のコマから I2V ＋ 1本目を長回しに直す。「最終シーン合わせ」オンなら最後の本だけ合わせる |
| **専用（参照つなぐ）** | 「登校（参照つなぐ）」など | 1本目は `input/cast/` を **R2V 参照**（上半身＋全身。最初のコマではない）。文はそのまま。2本目以降は最後のコマから I2V。③のテキストから／写真ファイルは無視 |
| **専用（参照つなぐ修）** | 「登校（参照つなぐ修）」など | 参照つなぐ ＋ 1本目を長回しに直す。③オンなら最後の本だけ合わせる |
| **名前付きパック（専用 / つなぐ / つなぐ修 / 参照つなぐ / 参照つなぐ修）** | 「訪問販売（つなぐ修）」「カフェ（参照つなぐ）」「花火（専用）」など | 専用ストーリーではないが再生は同じ5つ。JSON の本ごとの部品はそのまま |
| **短編集（参照）** | 「短編集（参照）」 | 15秒完結の濃厚日常インモラル×複数。**つなぎなし・連結なし**。各本は人物写真を **R2V 参照**。文と部品は自動（R2V 安全な LoRA だけ） |

専用は 11話 × 5 ＝ 55行、パックは 13本 × 5 ＝ 65行、短編集は1行。旧名「登校120秒（専用）」なども同じ意味（専用＝カット）で残っています。旧名「訪問販売60秒（つなぐ）」「定期検診100秒（つなぐ）」「終点40秒（つなぐ）」は前と同じ動き（＝つなぐ修）です。普通のつなぐ側の文は、切れ目なく続きやすい長回しに直してから送ります（1本目は途中の動きで終わる。2本目以降は最後のコマから再開しない）。最初の T2V→I2V のつなぎ（1本目→2本目）は文を直しません（Picture 1 のロックだけ）。

## 準備（最初の1回）

1. 上の **Open in Colab** を開く
2. 右上の **ランタイム → ランタイムのタイプを変更 → GPU を A100**
3. **Civitai の API キー**（シネマ質感とえっち用。**普通（エロなし）だけなら不要**）
   - https://civitai.com/user/account を開く → 下の **API Keys** → **Add API key** → コピー
   - **②の「CivitaiのAPIキー」欄に貼る**（このノートのフォーム。左の鍵マークは使わなくてよい）
   - キーは画面に出ません。ノートを保存する前に欄を空に戻す
4. メニュー **ランタイム → すべてのセルを実行** でも、①②③を順に押しても同じ

できた動画は Google Drive の  
`マイドライブ / minimax-h3-comfyui / output`

このフォルダは、普通の I2V / T2V ノートと**同じ**です。土台（FL2VA）と速いモード（Turbo）を共用します。ノートを別々に開いても、同じ Colab の③で「普通（エロなし）」を選んでも大丈夫です。同時に2つのノートを動かさないでください。

写真から作るときは、同じ Drive の `input` フォルダに jpg を置いてから ③ を実行。

普通の専用ノート:
- [I2V（写真から・エロなし）](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_i2v_phone.ipynb)
- [T2V（文章から・エロなし）](https://colab.research.google.com/github/fireworker011/Research/blob/cursor/minimax-h3-motion-identity-e959/minimax_h3_t2v_phone.ipynb)

## シーンの選び方（③で選ぶ）

| ③で選ぶ名前 | どんな動画 | 自動で入る部品 |
|---|---|---|
| 日常（速い＋綺麗） | 会話・商品・風景 | Larry v4 1.0 + シネマ 0.65 / 8step |
| 最速プレビュー（エロなし） | 量産プレビュー | LightX2V 4step 1.0 + シネマ 0.4 |
| 音も残す（エロなし） | 音を残して速く | LightX2V 8step 1.0 + シネマ 0.4 |
| 普通（エロなし） | 専用 I2V / T2V と同じ | LightX2V 4step だけ。画質 LoRA なし |
| 帰宅（専用 / つなぐ / つなぐ修） | 玄関フェラ→トイレクンニ寄り→口内。10×12 | クンニ LoRA は寄り1本。入室・退出は歩行部品。576×1024 |
| 洗い物（専用 / つなぐ / つなぐ修） | シンク洗い物＋プリン。アヤが床で口。10×12 | サヤカはシンク固定。レイは椅子で竿。入室と着席は別本。フェラは60秒以降。口内は CUMOUF |
| 登校（専用 / つなぐ / つなぐ修） | 朝〜大学正門。10秒×12本。16:9。**今はテキストから** | 1本1場所。セリフは口元3本。フェラは玄関と路地の寄り。授業は授業。写真は任意 |
| 授業（専用 / つなぐ / つなぐ修） | 授業〜昼。10秒×10本＝100秒。16:9 | 家とサヤカなし。机のシコはオナニー寄り。クンニは寄り1本。口内は CUMOUF。セリフは「ヒルだよ」だけ。セックスは屋上 |
| 屋上（専用 / つなぐ / つなぐ修） | 屋上挿入〜家の門。10秒×10本。16:9 | 1本1場所。セリフは口元2本。セックスは横クローズ。玄関はおかえり |
| おかえり（専用 / つなぐ / つなぐ修） | 家の門〜玄関ジュボ〜廊下。10秒×12本。16:9 | 屋上の続き。セリフは口元3本。フェラは玄関の寄り。口内は CUMOUF。夜風呂は風呂。食卓は洗い物 |
| 風呂（専用 / つなぐ / つなぐ修） | 夜風呂。支度と洗体〜洗い場で根元まで。10秒×12本。16:9 | セリフは口元3本。フェラは洗い場の寄り。口内は CUMOUF。ご飯〜食卓は食卓 |
| 食卓（専用 / つなぐ / つなぐ修） | 風呂上がり〜食卓。配膳と食事〜テーブル下で根元まで。10秒×12本。16:9 | セリフは口元3本。フェラはテーブル下の寄り。口内は CUMOUF。夜の布団は布団 |
| 布団（専用 / つなぐ / つなぐ修） | 食卓から布団。片付けと布団〜横になったまま根元まで。10秒×12本。16:9 | セリフは口元2本。フェラは布団の寄り。口内は CUMOUF。仰向けにアナルは入れない。休日午前は休日 |
| 休日（専用 / つなぐ / つなぐ修） | 休日午前。家から出ない。二度寝・テレビ・洗濯〜ソファでもう入っている、抜いたあと根元まで。10秒×12本。16:9 | セリフは口元2本。セックスは AIO 横クローズ。フェラは床の寄り。口内は CUMOUF。午後の縁側は縁側 |
| 縁側（専用 / つなぐ / つなぐ修） | 休日午後。縁側と二回戦。竿役はマドカ。昼残り・縁側・庭の風〜縁側でもう入っている、抜いたあとアヤがマドカを根元まで。10秒×12本。16:9 | セリフは口元2本。セックスは AIO 横クローズ。フェラは縁側の寄り。口内は CUMOUF。レイは入れない |
| 訪問販売（専用 / つなぐ / つなぐ修） | 玄関の水売り。口はアヤ、竿は5人目の販売員（25・短め黒髪・中乳・20cm・玉なし・根元にマンコ）。対面20秒。ジュボ15秒。8本＝85秒。9:16 | 名前付きパック。対面→おミズ（放尿を飲む）→ジュボ→口内。セリフはカタカナ。旧名「訪問販売60秒（つなぐ）」＝つなぐ修 |
| 定期検診（専用 / つなぐ / つなぐ修） | 家の玄関。医師（32・結い髪・中乳・竿なし・聴診器）がレイ（20cm）を訪問検診。対面30秒。ベロチューとジュボは無言15秒。9本＝100秒。9:16 | 名前付きパック。対面→キスと胸→カクニン→口内。診察室ではない。台詞はカタカナ |
| 終点（専用 / つなぐ / つなぐ修） | 終点の車内。車掌（29・短髪・中乳・竿なし・ホイッスル）が寝ているレイを起こす。10秒×4本。9:16 | 名前付きパック。声では起きない。ジュボで起きる。口内 CUMOUF のあと車掌に戻る。台詞はカタカナ |
| カフェ（専用 / つなぐ / つなぐ修） | 夏のカフェ。客アヤ、店員（25・お団子・中乳・20cm・トレイ）。おミズ＝放尿、ミルク＝ジュボと口内。コーヒーは本物。10秒×10本。9:16 | 建前パック。台詞はカタカナ、1本に2行まで。行為は無言・寄り。最後はベロチュー |
| 車内販売（専用 / つなぐ / つなぐ修） | 電車の車内販売。客レイ（自分の20cmは使わない）、販売員（26・短め黒髪・中乳・20cm・ワゴン）。おチャ＝放尿、ミルクコーヒー＝ジュボと口内。10秒×8本。9:16 | 建前パック。台詞はカタカナ |
| 赤信号（専用 / つなぐ / つなぐ修） | 信号待ちの車。運転レイ（両手はハンドル）、口アヤ。ジュボ→口内→アオになった。放尿なし。10秒×5本。9:16 | 建前パック。車は動かない |
| ヨガ（専用 / つなぐ / つなぐ修） | ヨガ教室。講師（29・お団子・中乳・20cm）、生徒アヤ。四つん這いでもう入っている。10秒×5本。9:16 | 建前パック。後背位 LoRA。ジュボなし・放尿なし |
| 背中流し（専用 / つなぐ / つなぐ修） | 風呂場。サヤカ（竿なし）がマドカ（20cm）を洗う。背中→マンコ舐め→アガリユ＝放尿。10秒×6本。9:16 | 建前パック。クンニ LoRA。マドカの竿は舐めない。ジュボなし |
| カラオケ（専用 / つなぐ / つなぐ修） | カラオケ。歌うマドカ（20cm・マイク）、口アヤ。歌のあいだジュボ、最後の音で口内、点数。10秒×5本。9:16 | 建前パック。放尿なし |
| ランドリー（専用 / つなぐ / つなぐ修） | 夜のコインランドリー。竿レイ、受けアヤ。洗濯機の上でもう入っている。あと何分。10秒×5本。9:16 | 建前パック。AIO 横クローズ。ジュボなし・放尿なし |
| 講義机（専用 / つなぐ / つなぐ修） | 大学の講義。先生（36・眼鏡・結い髪・中乳・20cm・チョーク）、アヤが教卓の下でジュボ→口内。上の声は授業。10秒×5本。9:16 | 建前パック。授業（専用11話）とは別。放尿なし |
| キャンプ（専用 / つなぐ / つなぐ修） | 夜のキャンプ。レイがアヤのマンコを舐めるだけ。虫よけ。レイの20cmは使わない。10秒×5本。9:16 | 建前パック。クンニ LoRA。ジュボなし・放尿なし |
| 花火（専用 / つなぐ / つなぐ修 / 参照つなぐ / 参照つなぐ修） | 川べりの花火。竿マドカ、受けサヤカ。立ったまま後ろから入っている。顔は花火。10秒×5本。9:16 | 建前パック。AIO。ジュボなし・放尿なし |
| 短編集（参照） | 15秒完結の濃厚日常インモラル×12。玄関ジュボ・シンク口内・路地・トイレクンニ・屋上挿入・洗い場・食卓下・布団・ソファ・縁側マドカ・訪問おミズ・ヨガ後背。つなぎなし | 各本 R2V（フェラは blowjob＋Ref2VA turbo、他は AfterMidnight）。FL2VA の竿/穴は載せない。人物写真必須 |
| アナル挿入（画質） | 穴のアップで挿入。遅いが綺麗 | ThumbInButt 0.85 + 竿 0.7 + 穴の見え方 0.55 / 16step。Turbo なし |
| アナル舐め・指 | 舐め・指のアップ。動きの本線はアナル指入れ | 穴の見え方 0.7 + Larry 0.5 + シネマ 0.4 |
| アナル指入れ | 自分の親指をアナルへ。指入れ（膣）とは別 | ThumbInButt 0.85 + 穴の見え方 0.55 + Larry 0.5 / 8step。写真からが本線 |
| フェラ（女体） | 女がふたなりにフェラ。竿＋根元のマンコが見える。男なし | フェラ 0.8 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step |
| ふたなりフェラ | ふたなりがフェラされる。竿＋穴＋フェラ。男なし | フェラ 0.75 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 6step |
| セックス（女体） | ふたなり＋女。男なし。描写は文章欄 | 総合えっち 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step |
| アナルセックス（女体） | アナル本線。後ろから、穴が膣より上に見える構図 | ThumbInButt 0.85 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。写真からが本線 |
| 騎乗位（女体） | 騎乗。総合えっちは積まない | 騎乗 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし |
| 後背位（女体） | 後ろから前後の突き | 後背位 0.8 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし |
| 正常位POV（女体） | 挿入側の視点。横からの正常位はセックス（女体） | POV挿入 0.85 + 竿 0.7 + Larry 0.5 / 8step |
| 後射精（女体） | 外に出す射精。中出し・顔射とは別 | 射精 0.9 + 竿 0.7 + Larry 0.5 / 8step |
| 顔射（女体） | 顔にかける。後射精・口内とは別 | 顔射 0.8 + 竿 0.7 + Larry 0.5 / 8step。写真からが本線 |
| 中出し（女体） | 膣の中に出す。後射精・顔射とは別 | Final Thrust 0.85 + 竿 0.7 + 穴の見え方 0.55 / 12step。Turbo なし。写真からが本線 |
| 口内射精（女体） | 口の中で出す。顔射・フェラ本線とは別 | CUMOUF 0.5 + 竿 0.7 + 穴の見え方 0.55 + Larry 0.5 / 8step。写真からが本線 |
| 指入れ | 膣への指の出し入れ。オナニー LoRA は積まない。アナルはアナル指入れ | 指 0.85 + 穴の見え方 0.55 + Larry 0.5 / 8step |
| オナニー | 潮吹き。指入れ LoRA は積まない | オナニー 0.8 + 穴の見え方 0.55 + Larry 0.5 / 12step |
| 足コキ | 両足で竿 | Type D 0.85 + 竿 0.7 + Larry 0.5 / 8step |
| 絶頂 | 女体の絶頂反応。射精ではない | 絶頂 0.8 + 穴の見え方 0.55 + Larry 0.5 / 8step |
| 汎用エロ（女体） | ふたなり＋女。男なし | AIO 0.8 + Larry 0.5 / 12step |
| 試し打ち | エロの量産プレビュー | AIO 0.7 + LightX2V 4step。当たりは本線で焼き直し |
| レズビアンクンニ | 全裸の出会い→キス→クンニ | クンニ 0.8 + 穴の見え方 0.55 + Larry 0.5 |
| 性器を広げる | 広げて見せるクローズ | 広げる 0.75 + 穴の見え方 0.55 + Larry 0.5 |
| レズ＋広げる | クンニに広げるを足す | クンニ 0.8 + 広げる 0.6 + Larry 0.5。穴の見え方は外す |

**ふたなりの既定:** 竿＋マンコ、金玉なし（フェラの参考画と同じ）。アヤとサヤカは竿なしのまま。
**台詞:** 「」の中はカタカナ（ひらがな・助詞はそのまま）。読み間違え防止。漢字は使わない。
**速さ:** 本線は Larry 8step。試し打ち・最速プレビューだけ LightX2V 4step。秒数は 4〜15（1本）。20〜120秒の「つなぐ」は同じカットを最後のコマで繋ぐ（10秒ずつ。1本で伸ばさない）。20秒は 10×2、120秒は 10×12。2〜12本目の文は③のつなぎ欄。空なら前の続き。「登校（専用）」などはカット割りで、つなぐとは別。「登校（つなぐ）」「登校（つなぐ修）」は同じ JSON を最後のコマで繋ぐ再生。
**最終シーン合わせ（③のチェック）:** 普通のつなぐと「つなぐ修」は**最後の本だけ**を選んだシーンに合わせて直す（最初の T2V→I2V のつなぎは触らない）。専用（カット）は**写真から**の本だけ「この本の静止画・独立カット・前の最後のコマから続けない」の1行を足す（JSON の部品はそのまま）。「つなぐ」（文そのまま）ではチェックしても何もしない。
**エロなしの重ね:** Turbo1 + 画質1。速さ用と画質用を分ける。Larry と LightX2V は同時に積まない。
**エロの重ね:** 行為1 + ヘルパー0〜2 + Turbo0〜1。体位 LoRA は総合えっちの代わり（同時に積まない）。シネマを足すならヘルパーを落とす。挿入ショットに Turbo は切る。Fal には載せない。
**エロの空欄:** 全員 21歳以上の全裸のごく普通の若い成人女性（女かふたなり）。男は出さない。行為の細かい描写は③の文章欄で足す。
**アナル系（ThumbInButt）のコツ:** 専用のアナルセックス LoRA は無いので、「物をアナルに入れる」を覚えた ThumbInButt を竿と組む。**穴が膣より上に見える構図**（四つん這い・後ろから）でないと膣に入る。挿入側の手は腰に置く（親指に置き換わるのを防ぐ）。写真からが本線。写真は後ろから穴が見えるもの。文章欄に書くなら「(S2) inserts her penis in (S1)'s anus」の形で、男・his は書かない。

**プロンプトは任意。** 空ならシーンのおすすめ文。自分の文を③の欄に貼ってもよい。写真からのときは顔ロック（Picture 1）を自動で足します。禁止語は Drive の `forbidden.json` だけ。未成年ロックは外せません。

上級の追加部品（リアル寄せ・胸など）は重ね上限のため無視します。
"""

MD1 = r"""## ① Google Drive をつなぐ

下のセルを実行すると、許可のポップアップが出ます。**許可** を押してください。

フォームは触らなくて大丈夫です。GPU が A100 でないとここで止まります。
"""

CELL1 = r'''#@title ① Drive の許可を出す（ここは触らなくてOK）
print("① Google Drive につないでいます…")

from google.colab import drive
import os

DRIVE_ROOT = "/content/drive/MyDrive/minimax-h3-comfyui"  #@param {type:"string"}
COMFY_DIR = "/content/ComfyUI"

drive.mount("/content/drive")

DRIVE_MODELS = f"{DRIVE_ROOT}/models"
for sub in ["diffusion_models", "text_encoders", "vae", "loras"]:
    os.makedirs(f"{DRIVE_MODELS}/{sub}", exist_ok=True)
os.makedirs(f"{DRIVE_ROOT}/output", exist_ok=True)
os.makedirs(f"{DRIVE_ROOT}/input", exist_ok=True)
# pip / HuggingFace / torch / Triton は Colab の消えるディスクではなく Drive に置く
for sub in ["cache/hf/hub", "cache/hf/transformers", "cache/torch/inductor", "cache/triton", "cache/pip", "cache/xdg"]:
    os.makedirs(f"{DRIVE_ROOT}/{sub}", exist_ok=True)
os.environ["HF_HOME"] = f"{DRIVE_ROOT}/cache/hf"
os.environ["HUGGINGFACE_HUB_CACHE"] = f"{DRIVE_ROOT}/cache/hf/hub"
os.environ["HF_HUB_CACHE"] = f"{DRIVE_ROOT}/cache/hf/hub"
os.environ["TRANSFORMERS_CACHE"] = f"{DRIVE_ROOT}/cache/hf/transformers"
os.environ["TORCH_HOME"] = f"{DRIVE_ROOT}/cache/torch"
os.environ["TORCHINDUCTOR_CACHE_DIR"] = f"{DRIVE_ROOT}/cache/torch/inductor"
os.environ["TRITON_CACHE_DIR"] = f"{DRIVE_ROOT}/cache/triton"
os.environ["PIP_CACHE_DIR"] = f"{DRIVE_ROOT}/cache/pip"
os.environ["XDG_CACHE_HOME"] = f"{DRIVE_ROOT}/cache/xdg"
os.environ["CUDA_MODULE_LOADING"] = "EAGER"
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

with open("/content/h3_paths.env", "w") as f:
    f.write(f"DRIVE_ROOT={DRIVE_ROOT}\n")
    f.write(f"DRIVE_MODELS={DRIVE_MODELS}\n")
    f.write(f"COMFY_DIR={COMFY_DIR}\n")

import torch
if not torch.cuda.is_available():
    raise SystemExit("GPU がオフです。上のメニュー「ランタイム」→「ランタイムのタイプを変更」→ GPU を A100 にして、①からやり直してください。")
props = torch.cuda.get_device_properties(0)
vram = props.total_memory / 1024 ** 3
print("つながった Drive:", DRIVE_ROOT)
print("動画の保存先:", f"{DRIVE_ROOT}/output")
print("写真を置く場所:", f"{DRIVE_ROOT}/input")
print("部品の保存先:", DRIVE_MODELS)
print("キャッシュ（pip/torch）:", f"{DRIVE_ROOT}/cache")
print("GPU:", torch.cuda.get_device_name(0), "メモリ:", round(vram, 1), "GB")
if vram < 20:
    raise SystemExit("メモリが足りません。GPU を A100 にしてください。")
print()
print("① 完了。次は②を実行してください。初回は待ちます。")
'''

MD2 = r"""## ② 部品を用意する（初回だけ長い）

下のセルで、動画の土台と部品を **Google Drive に保存**します。生成のときは Drive を直接読まず、ローカル SSD に載せてから GPU に入れます（初回③で GPU が遊んで見えた原因は Drive FUSE の mmap）。

- **初めて** … 20〜40分かかることがあります。途中で止まっても、もう一度押せば続きから入ります
- **同じランタイムで2回目** … Drive にあるファイルは飛ばす。ローカルに既にあればコピーも飛ばす。pip も飛ばす
- **ランタイム切断後** … Drive の土台は飛ばす（40GB の再取得はしない）。ローカルへコピー＋GPU 載せ＋Comfy 起動で数分
- pip / torch / Triton のキャッシュも Drive の `cache/`。Colab の消えるディスクには置かない
- 初めてなら「よく使う部品を全部入れる」は **オンのまま**（ディスクへ保存。再生中に全部を同時積みはしない）
- 土台と速いモード（Turbo）は必ず入れます。えっち用ノートと普通ノートで共用します

**Civitai の API キー** は、えっち用の部品を取るときだけ。**普通（エロなし）だけなら空でOK。** 左の鍵（シークレット）は使わなくて大丈夫です。

1. [civitai.com のアカウント画面](https://civitai.com/user/account) を開く
2. **API Keys** → **Add API key** でキーを作ってコピー
3. ②の **CivitaiのAPIキー** 欄に貼って実行

401 / 403 が出たら、キーの貼り忘れです。欄に貼って②をもう一度。キー自体は画面に出ません。
"""

CELL2 = r'''#@title ② 土台と部品を入れる（初回は待つ）
print("② 準備を始めています…")

#@markdown ### Civitai の API キー（ここに貼る。シークレット不要）
#@markdown 取り方: [civitai.com/user/account](https://civitai.com/user/account) → API Keys → Add API key
CivitaiのAPIキー = ""  #@param {type:"string"}
#@markdown **よく使う部品を全部入れる（初めてならオンのまま）**
よく使う部品を全部入れる = True  #@param {type:"boolean"}
#@markdown 全部オフにするなら、今使うシーンだけ（専用は話ごとに1つ。ダウンロードは話単位）:
今使うシーン = "__DEFAULT_SCENE__"  #@param __SCENE_OPTIONS_2__

import json, os, shutil, subprocess, sys, time, urllib.request
from pathlib import Path

env = {}
with open("/content/h3_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
DRIVE_ROOT = Path(env["DRIVE_ROOT"])
DRIVE_MODELS = Path(env["DRIVE_MODELS"])
COMFY_DIR = Path(env["COMFY_DIR"])
PORT = 8188
BRANCH = "cursor/h3-cast-ref-shorts-f112"
FETCH_REV = "h3-20260907-audio-2"
RAW = f"https://raw.githubusercontent.com/fireworker011/Research/{BRANCH}"
STUDIO = Path("/content/h3-lora-studio")

def sh(cmd, **kw):
    return subprocess.run(cmd, check=False, **kw)

def fetch_text(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        f"{url}?rev={FETCH_REV}",
        headers={"Cache-Control": "no-cache", "Pragma": "no-cache"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            dest.write_bytes(resp.read())
        return dest.is_file() and dest.stat().st_size > 100
    except Exception:
        print("ファイル取得に失敗:", dest.name)
        return False

print("説明書を取っています…")
helpers = [
    "colab/h3_r2v_core.py",
    "colab/h3_motion_graphics.py",
    "colab/h3_i2v_phone.py",
    "colab/h3_t2v.py",
    "colab/h3_lora_studio.py",
]
studio_files = [
    "h3-lora-studio/catalog/loras.json",
    "h3-lora-studio/catalog/forbidden.json",
    "h3-lora-studio/scripts/select_loras.py",
    "h3-lora-studio/profiles/anal_closeup.json",
    "h3-lora-studio/profiles/anal_fingering.json",
    "h3-lora-studio/profiles/anal_penetration.json",
    "h3-lora-studio/profiles/futa_blowjob.json",
    "h3-lora-studio/profiles/futa_sex.json",
    "h3-lora-studio/profiles/futa_anal.json",
    "h3-lora-studio/profiles/oral.json",
    "h3-lora-studio/profiles/general_sex.json",
    "h3-lora-studio/profiles/lesbian_cunnilingus.json",
    "h3-lora-studio/profiles/lesbian_spread.json",
    "h3-lora-studio/profiles/pussy_spread.json",
    "h3-lora-studio/profiles/preview.json",
    "h3-lora-studio/profiles/riding.json",
    "h3-lora-studio/profiles/doggy.json",
    "h3-lora-studio/profiles/missionary_pov.json",
    "h3-lora-studio/profiles/after_ejaculation.json",
    "h3-lora-studio/profiles/facial.json",
    "h3-lora-studio/profiles/creampie.json",
    "h3-lora-studio/profiles/oral_creampie.json",
    "h3-lora-studio/profiles/fingering.json",
    "h3-lora-studio/profiles/masturbation.json",
    "h3-lora-studio/profiles/footjob.json",
    "h3-lora-studio/profiles/remote_orgasm.json",
    "h3-lora-studio/profiles/sfw_daily.json",
    "h3-lora-studio/profiles/sfw_preview.json",
    "h3-lora-studio/profiles/sfw_audio.json",
    "h3-lora-studio/profiles/sfw_r2v.json",
    "h3-lora-studio/profiles/futa_visible.json",
    "h3-lora-studio/profiles/futa_masturbation.json",
    "h3-lora-studio/profiles/cunnilingus_futa.json",
    "h3-lora-studio/stories/homecoming-90s.json",
    "h3-lora-studio/stories/dishes-90s.json",
    "h3-lora-studio/stories/commute-120s.json",
    "h3-lora-studio/stories/lecture-120s.json",
    "h3-lora-studio/stories/rooftop-100s.json",
    "h3-lora-studio/stories/okaeri-120s.json",
    "h3-lora-studio/stories/bath-120s.json",
    "h3-lora-studio/stories/dinner-120s.json",
    "h3-lora-studio/stories/futon-120s.json",
    "h3-lora-studio/stories/sunday-120s.json",
    "h3-lora-studio/stories/engawa-120s.json",
    "h3-lora-studio/stories/sales-visit-60s.json",
    "h3-lora-studio/stories/checkup-100s.json",
    "h3-lora-studio/stories/last-stop-40s.json",
    "h3-lora-studio/stories/cafe-100s.json",
    "h3-lora-studio/stories/train-sales-80s.json",
    "h3-lora-studio/stories/red-light-50s.json",
    "h3-lora-studio/stories/yoga-50s.json",
    "h3-lora-studio/stories/back-wash-60s.json",
    "h3-lora-studio/stories/karaoke-50s.json",
    "h3-lora-studio/stories/laundromat-50s.json",
    "h3-lora-studio/stories/lecture-desk-50s.json",
    "h3-lora-studio/stories/camp-50s.json",
    "h3-lora-studio/stories/fireworks-50s.json",
]
for rel in helpers:
    dest = Path("/content") / Path(rel).name
    if not fetch_text(f"{RAW}/{rel}", dest):
        raise SystemExit("説明書の取得に失敗しました。ネットを確認して②をもう一度。")
    shutil.copy2(dest, DRIVE_ROOT / dest.name)
for rel in studio_files:
    dest = Path("/content") / rel
    if not fetch_text(f"{RAW}/{rel}", dest):
        raise SystemExit("シーン設定の取得に失敗しました。②をもう一度。")
drive_fb = DRIVE_ROOT / "forbidden.json"
git_fb = Path("/content/h3-lora-studio/catalog/forbidden.json")
if not (drive_fb.is_file() and drive_fb.stat().st_size > 20):
    shutil.copy2(git_fb, drive_fb)
    print("禁止語ファイルを作りました:", drive_fb)
else:
    print("禁止語ファイル:", drive_fb)
shutil.copy2(drive_fb, git_fb)
try:
    fb = json.loads(drive_fb.read_text(encoding="utf-8"))
    extra_now = [str(x).strip() for x in (fb.get("extra") or []) if str(x).strip()]
    print("extra:", ", ".join(extra_now) or "（空）")
    print("足す・消すのは extra だけ。minors を消しても未成年ロックは残ります。")
except Exception:
    raise SystemExit("禁止語ファイルが壊れています。Drive の forbidden.json を直してください。")

sel = Path("/content/h3-lora-studio/scripts/select_loras.py")
if "MAX_HELPERS" not in sel.read_text(encoding="utf-8"):
    raise SystemExit("設定の取り直しに失敗しました。②をもう一度実行してください。")
print("設定の版:", FETCH_REV)

sys.path.insert(0, "/content")
sys.path.insert(0, "/content/h3-lora-studio/scripts")
for name in ("select_loras", "h3_lora_studio", "h3_i2v_phone", "h3_t2v", "h3_r2v_core", "h3_motion_graphics"):
    sys.modules.pop(name, None)
from h3_i2v_phone import i2v_download_jobs
from h3_r2v_core import r2v_download_jobs
from h3_lora_studio import (
    SITUATION_HELP, civitai_token, civitai_token_help, civitai_download_fallbacks,
    download_jobs_for, fetch_weight, load_catalog, missing_civitai_files,
    resolve_situation, situation_ids, comfy_alive, wait_comfy_ready,
    apply_drive_cache_env, prepare_local_model_roots, stage_models_to_local,
    model_dir_is_drive_link, link_model_dirs_to_drive, warmup_h3_engine,
    clear_warmup_stamp,
)
apply_drive_cache_env(DRIVE_ROOT)

print("今のシーン:", 今使うシーン)
print(SITUATION_HELP[resolve_situation(今使うシーン)])
print()

if not (COMFY_DIR / "main.py").is_file():
    print("動画ソフトを入れています…")
    sh(["git", "clone", "--depth", "1", "https://github.com/Comfy-Org/ComfyUI.git", str(COMFY_DIR)])
else:
    print("動画ソフトはすでにあります。更新はしません。")
req = COMFY_DIR / "requirements.txt"
pip_stamp = Path("/content/.h3_pip_ok")
pip_cache = Path(os.environ.get("PIP_CACHE_DIR") or (DRIVE_ROOT / "cache" / "pip"))
pip_cache.mkdir(parents=True, exist_ok=True)
if pip_stamp.is_file():
    print("Python 部品は前回入れ済み。飛ばします。")
elif req.is_file():
    print("Python 部品を入れています（このランタイムの初回だけ。wheel は Drive の cache/pip）…")
    sh([sys.executable, "-m", "pip", "install", "-q", "-r", str(req), "--cache-dir", str(pip_cache)])
    pip_stamp.write_text("ok", encoding="utf-8")

def link_dir(link_path: Path, target: Path):
    target.mkdir(parents=True, exist_ok=True)
    if link_path.is_symlink() or link_path.is_file():
        link_path.unlink()
    elif link_path.is_dir():
        shutil.rmtree(link_path)
    link_path.symlink_to(target)

models_root = COMFY_DIR / "models"
models_root.mkdir(parents=True, exist_ok=True)
# input / output は Drive のまま（写真と完成動画）。重みは FUSE mmap しない。
link_dir(COMFY_DIR / "output", DRIVE_ROOT / "output")
link_dir(COMFY_DIR / "input", DRIVE_ROOT / "input")
if comfy_alive(PORT) and model_dir_is_drive_link(COMFY_DIR):
    print("エンジンが Drive 直読みのままなので、一度止めてローカルに載せ直します…")
    subprocess.run(["fuser", "-k", f"{PORT}/tcp"], check=False, capture_output=True)
    time.sleep(2)
    clear_warmup_stamp(COMFY_DIR)
broke_link = prepare_local_model_roots(COMFY_DIR)
if broke_link:
    print("モデルフォルダをローカル SSD に切り替えました。")

print("大きな土台を入れています（すでにあれば飛ばします）…")
for url, dest in i2v_download_jobs(DRIVE_MODELS):
    if "turbo" in dest.name.lower():
        print("  速いモード（Turbo）も入れます。普通の I2V / T2V と共用します:", dest.name)
    fetch_weight(url, dest)
print("参照用の土台（R2V / ref2va）も入れます。FL2VA とは混ぜません…")
for url, dest in r2v_download_jobs(DRIVE_MODELS):
    print("  参照:", dest.name)
    fetch_weight(url, dest)

sid = resolve_situation(今使うシーン)
ids = situation_ids(sid)
if よく使う部品を全部入れる:
    ids = []
    for key in ("sfw_daily", "sfw_preview", "sfw_audio", "anal_closeup", "anal_fingering", "anal_penetration", "futa_blowjob", "futa_sex", "futa_anal", "oral", "general_sex", "preview", "lesbian_cunnilingus", "pussy_spread", "lesbian_spread", "riding", "doggy", "missionary_pov", "after_ejaculation", "facial", "creampie", "oral_creampie", "fingering", "masturbation", "footjob", "remote_orgasm", "futa_visible", "futa_masturbation", "cunnilingus_futa", *__STORY_ID_LIST__):
        ids.extend(situation_ids(key))
    print("よく使う部品を全部ディスクへ入れます。再生は今の本の LoRA だけ載せます。")
else:
    print("今のシーン用だけ入れます:", 今使うシーン)

catalog = load_catalog(STUDIO)
# Civitai API をここで読む。名前は CIVITAI_API_TOKEN。値は print しない。
token = civitai_token(CivitaiのAPIキー)
if token:
    os.environ["CIVITAI_API_TOKEN"] = token
print("Civitai API:", "読み込み済み（値は出しません）" if token else "空")
jobs = download_jobs_for(ids, DRIVE_MODELS / "loras", catalog=catalog)
need = missing_civitai_files(jobs)
if need and not token:
    raise SystemExit(civitai_token_help())
skipped = []
for url, dest, row in jobs:
    auth = "civitai" if str(row.get("source")) == "civitai" else ""
    fallbacks = civitai_download_fallbacks(row) if auth else None
    if not fetch_weight(url, dest, token=token, auth=auth, fallback_urls=fallbacks):
        skipped.append(dest.name)
        if dest.name == "H3_anal_penetration_v1.safetensors":
            print("アナル挿入の専用部品は Civitai 有料のことがあります。③では総合えっちで代用します。Drive の models/loras に置けば専用になります。")
if skipped:
    print("一部スキップ:", ", ".join(skipped))
    print("今のシーンに不要なら③へ。必要なら Drive の models/loras に置いてください。②をもう一度回すだけでは取れないことがあります。")

print("Drive の重みをローカル SSD に載せます（FUSE mmap だと初回の GPU が遊ります）…")
staged = stage_models_to_local(DRIVE_MODELS, COMFY_DIR / "models")
if staged.get("copied"):
    print("コピーしたファイル:", len(staged["copied"]), "（", round(staged.get("bytes") or 0) / 1e9, "GB）")
if staged.get("skipped"):
    print("ローカル済み:", len(staged["skipped"]))
if staged.get("drive_direct"):
    print("空きが足りないので Drive 直読みに戻します。")
    if comfy_alive(PORT):
        subprocess.run(["fuser", "-k", f"{PORT}/tcp"], check=False, capture_output=True)
        time.sleep(2)
        clear_warmup_stamp(COMFY_DIR)
    link_model_dirs_to_drive(COMFY_DIR, DRIVE_MODELS)

os.environ.setdefault("PYTORCH_CUDA_ALLOC_CONF", "expandable_segments:True")

if comfy_alive(PORT):
    print("動画エンジンはすでに起動しています。部品の準備を待ちます…")
    if not wait_comfy_ready(PORT, seconds=180):
        raise SystemExit("エンジンの準備が終わりません。ランタイムを再起動して①からやり直してください。")
else:
    print("動画エンジンを起動しています…")
    log = Path("/content/comfyui.log")
    log_f = open(log, "w", buffering=1)
    cmd = [sys.executable, "main.py", "--listen", "127.0.0.1", "--port", str(PORT),
           "--highvram", "--disable-auto-launch", "--enable-cors-header"]
    subprocess.Popen(cmd, cwd=str(COMFY_DIR), stdout=log_f, stderr=subprocess.STDOUT, start_new_session=True)
    if not wait_comfy_ready(PORT, seconds=180):
        print(log.read_text(errors="replace")[-2000:])
        raise SystemExit("起動に失敗しました。ランタイムを再起動して①からやり直してください。")
    print("起動できました")

diff = list((COMFY_DIR / "models" / "diffusion_models").glob("*fl2va*"))
unet_name = diff[0].name if diff else ""
if unet_name:
    warmup_h3_engine(COMFY_DIR, PORT, unet_name)

print()
print("② 完了。次は③でシーンを選んで実行してください。1本目から GPU 本体の計算に入ります。")
'''

MD3 = r"""## ③ 動画を作る

**シーン** と **作り方** を選んで実行します。**プロンプトは任意**（空ならおすすめ文）。

| 作り方 | 必要なもの |
|---|---|
| テキストから（写真なし） | なし。専用も JSON の文だけ。16:9 の話は横のまま。Drive に試験jpgがあっても使わない |
| 写真から（1枚必要） | Drive の `input` または専用フォルダの jpg。顔を固定したいとき |

自分の文を書くときは、出演者は「21歳以上の成人」と書いてください。未成年の表現は拒否されます。写真からのときに Picture 1 を書かなくても、顔ロックは自動で足します。

**専用の3パターン（同じ話・同じ JSON）:** `登校（専用）` ＝ カット（最後のコマから続けない）。`登校（つなぐ）` ＝ 文を直さず最後のコマから I2V（Picture 1 ロックだけ）。`登校（つなぐ修）` ＝ 最後のコマから I2V ＋ 1本目を長回しに直す。初期値は `登校（専用）`。旧名 `登校120秒（専用）` も専用。

**最終シーン合わせ（チェック）:** 普通のつなぐと「つなぐ修」は最後の本だけ選んだシーンに合わせる（最初の T2V→I2V のつなぎは触らない）。専用（カット）は写真からの本だけ「この本の静止画・独立カット」の1行を足す。「つなぐ」（文そのまま）では何もしない。

**禁止語:** Drive の `minimax-h3-comfyui/forbidden.json` だけ。`extra` を足す・消す。③に欄は無い。編集したら③を再実行。ロリ・ショタ・child・21歳未満・アフィURLは消せません。

おすすめ文の例（空欄のときに自動で近い内容になります）:

- **日常（速い＋綺麗）** … Larry + シネマ。8step
- **最速プレビュー（エロなし）** … LightX2V 4step。当たりは日常で焼き直し
- **音も残す（エロなし）** … LightX2V 8step
- **普通（エロなし）** … 専用 I2V / T2V ノートと同じおすすめ文
- **帰宅（専用 / つなぐ / つなぐ修）** … 10秒×12本。1本1場所。セリフは口元の1本だけ（リップシンク）。クンニ LoRA は寄り1本。行為は口元・舌・竿の寄り。写真は `input/homecoming-90s/` の 01〜12（`11-lick.jpg` は舌と穴の寄り）
- **洗い物（専用 / つなぐ / つなぐ修）** … 10秒×12本。1本1場所。サヤカはシンク固定。セリフは口元の2本だけ。フェラは口元の寄り。口内は CUMOUF。写真は `input/dishes-90s/` の 01〜12（任意。01〜09は従来のまま）
- **登校（専用 / つなぐ / つなぐ修）** … 第1話。朝〜大学正門。10秒×12本＝120秒。16:9。1本1場所。セリフは口元3本（イってらっしゃい／チコクするよ／ほしい。カタカナ）。フェラは玄関と路地の寄り。授業は授業。**今の準備はテキストから。** `input/commute-120s/` の試験jpgは③がテキストからなら使わない。Imagine 後に写真からへ。旧名「登校120秒（専用）」も専用
- **授業（専用 / つなぐ / つなぐ修）** … 第2話。授業〜昼。10秒×10本＝100秒。16:9。家とサヤカは出さない。机のシコはオナニー寄り。クンニ LoRA は寄り1本。根元はフェラ。口内は CUMOUF。セリフは口元の「ヒルだよ」だけ。セックスは屋上。写真は `input/lecture-120s/` の 01〜10（16:9。無い本はテキストから）
- **屋上（専用 / つなぐ / つなぐ修）** … 第3話。屋上で挿入（もう入っている）〜家の門。10秒×10本＝100秒。16:9。1本1場所。セリフは口元2本（ほしい／帰ろ）。セックスは AIO 横クローズ。歩く本にセックス部品なし。玄関はおかえり。サヤカなし。写真は `input/rooftop-100s/` の 01〜10（16:9）。全話同じ追従ルール（10秒・1場所・口パクは顔寄り・行為は LoRA のカメラ）
- **おかえり（専用 / つなぐ / つなぐ修）** … 第4話。家の門〜玄関ジュボ〜廊下。10秒×12本＝120秒。16:9。屋上の続き。セリフは口元3本（ただいま／おかえり／手洗って）。フェラは玄関の寄り。口内は CUMOUF。夜風呂は風呂。食卓のプリンは洗い物。写真は `input/okaeri-120s/` の 01〜12（16:9。無い本はテキストから）
- **風呂（専用 / つなぐ / つなぐ修）** … 第5話。夜の風呂。10秒×12本＝120秒。16:9。日常は支度と洗体。非日常は洗い場で根元まで。セリフは口元3本（先に洗って／湯だと余計勃ってる／上がったらご飯）。フェラは洗い場の寄り。口内は CUMOUF。ご飯〜食卓は食卓。写真は `input/bath-120s/` の 01〜12（16:9。無い本はテキストから）
- **食卓（専用 / つなぐ / つなぐ修）** … 第6話。風呂上がりから食卓。10秒×12本＝120秒。16:9。日常は配膳と食事。非日常はテーブルの下で根元まで。セリフは口元3本（食べなさい／ご飯中なのに／ちゃんと上も食べなさい）。フェラはテーブル下の寄り。口内は CUMOUF。夜の布団は布団。写真は `input/dinner-120s/` の 01〜12（16:9。無い本はテキストから）
- **布団（専用 / つなぐ / つなぐ修）** … 第7話。食卓から布団。10秒×12本＝120秒。16:9。日常は片付けと布団。非日常は横になったまま根元まで。セリフは口元2本（寝る前なのに／電気消したよ）。フェラは布団の寄り。口内は CUMOUF。仰向けの口にセックスやアナルは入れない。休日午前は休日。写真は `input/futon-120s/` の 01〜12（16:9。無い本はテキストから）
- **休日（専用 / つなぐ / つなぐ修）** … 第8話。休日午前。家から出ない。10秒×12本＝120秒。16:9。日常は二度寝・テレビ・洗濯。非日常はソファでもう入っている、抜いたあと根元まで。セリフは口元2本（休日なのに朝から勃ってる／昼ごはんまだよ）。セックスは AIO 横クローズ。フェラは床の寄り。口内は CUMOUF。アナルは入れない。午後の縁側は縁側。写真は `input/sunday-120s/` の 01〜12（16:9。無い本はテキストから）
- **縁側（専用 / つなぐ / つなぐ修）** … 第9話。休日午後。縁側と二回戦。竿役はマドカ。10秒×12本＝120秒。16:9。日常は昼残り・縁側・庭の風。非日常は縁側でもう入っている、抜いたあとアヤがマドカを根元まで。セリフは口元2本（午後も勃ってる／皿洗っとくから）。セックスは AIO 横クローズ。フェラは縁側の寄り。口内は CUMOUF。レイは入れない。アナルは入れない。写真は `input/engawa-120s/` の 01〜12（16:9。無い本はテキストから）
- **訪問販売（専用 / つなぐ / つなぐ修）** … 名前付きパック（専用ではない）。対面20秒。跪き済みでハヤク。おミズ＝放尿を飲み干してからジュボ15秒。8本＝85秒。9:16。玄関の対面。口はアヤ22ミニ・竿なし。販売員は5人目（25・短め黒髪・中乳・ふたなり20cm・金玉なし・根元にマンコ）。口内は粘る白液を残して見せる。セリフ: こんにちは。おミズをおトドケにきました／オソいわよ／ハヤクおミズちょうだい／あー、シミる／ありがとうございました。旧名「訪問販売60秒（つなぐ）」＝つなぐ修
- **定期検診（専用 / つなぐ / つなぐ修）** … 名前付きパック。対面30秒。セリフは10秒、ベロチューとジュボは無言15秒。9本＝100秒。9:16。診察室ではない。家の玄関。医師（32・結い髪・中乳・竿なし・聴診器）とレイ（20cm 立ち）。キスは両手で胸。カクニンは立ちの口パクのみ。口内は粘る白液を残して見せる。台詞: こんにちは。テイキケンシンにきました／あ…はい、ヨロシクオネガイします／では、シツレイします／クチとムネはモンダイないですね／では、つぎはおチンチンのカクニンをします／モンダイありますね。台詞本はシネマを外す。音声は「」の日本語だけ。プロンプトは読まない
- **終点40秒（つなぐ）** … 名前付きパック。10秒×4本。9:16。車掌（29・短髪・中乳・竿なし・ホイッスル）と座席で寝ているレイ（立たない）。「シュウテンです、オキテください」では起きない。ジュボで起きる。口内 CUMOUF（無言）。「オキましたか？オキャクサン、シュウテンだからオリテください」で車掌に戻る
- **アナル挿入（画質）** … 穴のアップ。挿入側はふたなり。男なし。Turbo なし・16step
- **アナルセックス（女体）** … ふたなり＋女。男なし。Turbo なし・12step。後ろから、穴が膣より上。手は腰。写真からが本線
- **アナル舐め・指** … 女同士。男なし。動きの本線はアナル指入れ
- **アナル指入れ** … 女1人。自分の右親指。男なし。後ろから、穴が膣より上。指入れ（膣）・アナルセックスとは別。写真からが本線
- **フェラ（女体）** … 女がふたなりにフェラ。男なし。`bl0w_j0b` と `PENISLORA` は自動
- **ふたなりフェラ** … ふたなりがフェラされる。男なし
- **セックス（女体）** … ふたなり＋女。男なし。空欄は全裸のごく普通の若い成人女性。描写は文章欄
- **騎乗位（女体）** … ふたなり＋女。男なし。総合えっちは積まない
- **後背位（女体）** … ふたなり＋女。男なし
- **正常位POV（女体）** … ふたなり＋女。男なし
- **後射精（女体）** … ふたなり。男なし。絶頂・顔射・中出しとは別
- **顔射（女体）** … ふたなり＋女。男なし。後射精・絶頂・口内とは別。写真からが本線
- **中出し（女体）** … ふたなり＋女。男なし。膣の中。後射精・顔射・口内とは別。写真からが本線
- **口内射精（女体）** … ふたなり＋女。男なし。口の中。顔射・フェラ本線とは別。写真からが本線（口が付いた途中の写真）
- **指入れ** … 女1人。男なし。膣。アナルはアナル指入れ
- **オナニー** … 女1人。男なし
- **足コキ** … ふたなり＋女。男なし
- **絶頂** … 女1人。男なし。射精ではない
- **汎用エロ（女体）** … ふたなり＋女。男なし。AIO + Larry 12step
- **試し打ち** … ふたなり＋女。男なし
- **秒数** … 4〜15 は1本。つなぐ 20〜120秒は同じカットを最後のコマで繋ぐ（10秒ずつ）。専用120秒は上の「やりたいシーン」で選ぶ（カット。ここは触らない）。1本で 16 秒以上は作らない
- **レズビアンクンニ** … 女同士。男なし
- **性器を広げる** … 女1人。男なし
- **レズ＋広げる** … 女同士。男なし
"""

CELL3 = r'''#@title ③ 動画を作る（ここだけ選ぶ）
#@markdown ### まずここ
#@markdown 専用11話と名前付きパック13本は3パターン: （専用）＝カット、（つなぐ）＝文そのまま最後のコマから I2V、（つなぐ修）＝最後のコマから I2V＋1本目を長回しに直す。パック（訪問販売〜花火）は専用ストーリーではないが再生は同じ。プロンプト・秒数・長さの作り方は不要。
やりたいシーン = "__DEFAULT_SCENE__"  #@param __SCENE_OPTIONS_3__
作り方 = "テキストから（写真なし）"  #@param ["テキストから（写真なし）", "写真から（1枚必要）"]
#@markdown 最後の本だけ選んだシーンに合わせて直す（普通のつなぐ・つなぐ修）。専用（カット）は写真からの本に「この本の静止画・独立カット」を足すだけ。「つなぐ」（文そのまま）では何もしない。最初の T2V→I2V のつなぎは触らない。
最終シーン合わせ = False  #@param {type:"boolean"}
#@markdown ### プロンプト（任意）
#@markdown 空ならシーンのおすすめ文。自分の文を貼ってよい。写真からで Picture 1 が無いときは自動で足します。テキストからに切り替えたとき、写真用の文が残っていても外します。
文章 = ""  #@param {type:"string"}
#@markdown 写真からのときだけ。`auto` か空なら input の一番新しい jpg。テキストからでは使いません。
写真ファイル = "auto"  #@param {type:"string"}
#@markdown 秒数。1本は 4〜15。同じカットを長くするなら下の「つなぐ」。専用120秒では無視。
秒数 = 10  #@param {type:"number"}
#@markdown 専用120秒（帰宅・登校など）は上の「やりたいシーン」で選ぶ。ここは**同じカットを繋ぐ**用。専用では触らなくてよい。20〜120秒は 10秒ずつ、最後のコマから I2V（解像度もステップも落とさない）。
長さの作り方 = "1本（最大15秒）"  #@param ["1本（最大15秒）", "つなぐ 20秒", "つなぐ 30秒", "つなぐ 40秒", "つなぐ 50秒", "つなぐ 60秒", "つなぐ 70秒", "つなぐ 80秒", "つなぐ 90秒", "つなぐ 100秒", "つなぐ 110秒", "つなぐ 120秒", "つなぐ 2分", "つなぐ（秒数欄・16〜120）"]
#@markdown ### つなぐときだけ（任意・専用では無視）
#@markdown 同じ場所・同じ人の続き。空欄は前の動きのまま。別の拍だけ書く。Picture 1 とカット割りは書かない。
つなぎ2 = ""  #@param {type:"string"}
つなぎ3 = ""  #@param {type:"string"}
つなぎ4 = ""  #@param {type:"string"}
つなぎ5 = ""  #@param {type:"string"}
つなぎ6 = ""  #@param {type:"string"}
つなぎ7 = ""  #@param {type:"string"}
つなぎ8 = ""  #@param {type:"string"}
つなぎ9 = ""  #@param {type:"string"}
つなぎ10 = ""  #@param {type:"string"}
つなぎ11 = ""  #@param {type:"string"}
つなぎ12 = ""  #@param {type:"string"}

#@markdown ---
#@markdown ### 触らなくていい（上級）
画面の向き = "おまかせ"  #@param ["おまかせ", "縦（スマホ）", "横", "やや正方形"]
リアル寄り = False  #@param {type:"boolean"}
胸を強調 = False  #@param {type:"boolean"}
動きの底上げ = False  #@param {type:"boolean"}
静止画用の写実 = False  #@param {type:"boolean"}
試し打ちだけ = False  #@param {type:"boolean"}

print("③ 設定を読みます…")

import json, os, sys, time, uuid, urllib.request, urllib.error
from pathlib import Path
from IPython.display import display, Video, HTML

sys.path.insert(0, "/content")
sys.path.insert(0, "/content/h3-lora-studio/scripts")
for name in ("select_loras", "h3_lora_studio", "h3_i2v_phone", "h3_t2v", "h3_r2v_core", "h3_motion_graphics"):
    sys.modules.pop(name, None)
from h3_r2v_core import REF2VA_NAME, assert_graph_identity_motion, build_r2v_graph, is_oom_error, frames, r2v_retry_plans
from h3_i2v_phone import DEFAULT_FIRST_IMAGE, collect_output_videos, newest_mp4, newest_image, stage_image_into_input, is_auto_image_name, ref_image_url
from h3_t2v import CANVAS_9_16, assert_t2v_graph, build_t2v_graph, canvas_for_aspect, resolve_t2v_prompt, t2v_retry_plans, validate_t2v_prompt
from h3_motion_graphics import CANVAS_8_9, assert_i2va_graph, build_i2va_graph, i2va_retry_plans, prefer_fl2v_lora, resolve_motion_prompt, validate_motion_ad_prompt, validate_studio_i2v_prompt
from h3_lora_studio import apply_user_prompt, explain_choice, format_job_fail, format_prompt_http_fail, friendly_lora, friendly_select_error, inject_lora_stack, is_blank_prompt, is_vanilla, is_story, is_chain_pack, is_anthology, load_story, prepare_story_clip, story_stills_dir, prepend_triggers, resolve_mode, resolve_situation, clamp_studio_duration, resolve_studio_length, apply_stack_fallbacks, missing_stack_files, comfy_missing_loras, download_jobs_for, fetch_weight, load_catalog, civitai_token, civitai_download_fallbacks, restart_studio_comfy, fetch_comfy_object_info, continue_chain_prompt, next_chain_prompt, rewrite_chain_opening_prompt, extract_last_frame, concat_studio_clips, has_i2v_lock, comfy_free, situation_ids, apply_drive_cache_env, stage_models_to_local, warmup_h3_engine, clear_warmup_stamp, resolve_story_play, apply_story_play, should_fit_scene_image_prompt, rewrite_final_scene_i2v_prompt, lock_spoken_japanese, STORY_PLAY_JA, STORY_PLAY_DEDICATED
from select_loras import forbidden_hits, load_forbidden, select_loras
import select_loras as _select_loras
import h3_lora_studio as _h3_studio
if not getattr(_select_loras, "MAX_HELPERS", None) or int(getattr(_h3_studio, "CHAIN_MAX_S", 0) or 0) < 120 or not getattr(_h3_studio, "fetch_comfy_object_info", None) or not getattr(_h3_studio, "has_i2v_lock", None) or not getattr(_h3_studio, "comfy_free", None) or not getattr(_h3_studio, "prepare_story_clip", None) or "fit_scene" not in getattr(_h3_studio.prepare_story_clip, "__code__").co_varnames or "cast_dir" not in getattr(_h3_studio.prepare_story_clip, "__code__").co_varnames or "prev_stack" not in getattr(_h3_studio.prepare_story_clip, "__code__").co_varnames or not getattr(_h3_studio, "validate_story_follow", None) or not getattr(_h3_studio, "lock_spoken_japanese", None) or getattr(_h3_studio, "AUDIO_LOCK_MARK", "") != "[AUDIO-LOCK]" or not getattr(_h3_studio, "drop_speech_face_killers", None) or not getattr(_h3_studio, "stage_models_to_local", None) or not getattr(_h3_studio, "warmup_h3_engine", None) or not getattr(_h3_studio, "rewrite_chain_opening_prompt", None) or not getattr(_h3_studio, "resolve_story_play", None) or not getattr(_h3_studio, "apply_story_play", None) or not getattr(_h3_studio, "should_fit_scene_image_prompt", None) or not getattr(_h3_studio, "rewrite_dedicated_scene_i2v_prompt", None) or not getattr(_h3_studio, "pick_cast_still", None) or not getattr(_h3_studio, "pick_cast_stills", None) or not getattr(_h3_studio, "lock_r2v_cast_prompt", None) or not getattr(_h3_studio, "STORY_PLAY_REF_CHAIN", None) or "engawa-120s" not in getattr(_h3_studio, "STORY_IDS", set()) or "last-stop-40s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set()) or "fireworks-50s" not in getattr(_h3_studio, "CHAIN_PACK_IDS", set()) or "shorts-immoral" not in getattr(_h3_studio, "ANTHOLOGY_ID_SET", set()) or not getattr(_h3_studio, "chain_pack_legacy_labels", None):
    raise SystemExit("部品の読み込みが古いです。ランタイムを再起動して①→②→③、または②をもう一度実行してから③。")

DURATION, CLIPS, CHAIN = resolve_studio_length(秒数, 長さの作り方)
CHAIN_EXTRAS = [つなぎ2, つなぎ3, つなぎ4, つなぎ5, つなぎ6, つなぎ7, つなぎ8, つなぎ9, つなぎ10, つなぎ11, つなぎ12]
STORY_PLAY = None
if is_anthology(やりたいシーン):
    print("短編集（参照）。15秒完結×複数。つなぎなし。長さの作り方・秒数・つなぎ欄は無視します。人物写真は Drive の input/cast/ を R2V 参照（最初のコマではない）。")
    CHAIN = False
if is_story(やりたいシーン) or is_chain_pack(やりたいシーン):
    STORY_PLAY = resolve_story_play(やりたいシーン)
    KIND_JA = "専用ストーリー" if is_story(やりたいシーン) else "名前付きパック（専用ストーリーではありません）"
    if STORY_PLAY == STORY_PLAY_DEDICATED:
        if CHAIN:
            print(KIND_JA + "を（専用）で選んでいるので「つなぐ」は使いません。長さの作り方・秒数・つなぎ欄は無視します（カット編集）。")
        CHAIN = False
    else:
        print(KIND_JA + "を最後のコマでつなぎます（" + STORY_PLAY_JA[STORY_PLAY] + "）。長さの作り方・秒数・つなぎ欄は無視します。JSON の本数と部品はそのまま。")
        CHAIN = True
else:
    if float(DURATION) != float(秒数):
        if CHAIN:
            print("秒数は", int(DURATION), "にします（つなぐは 16〜120 秒。20〜120秒のボタンは秒数欄を無視）。")
        else:
            print("秒数は", int(DURATION), "にします（1本は 4〜15 秒。16秒以上は「つなぐ」）。")
    if CHAIN:
        print("つなぐモード: 1本目はテキストまたは写真。2本目以降は最後のコマから I2V。同じ場所・同じ人・同じ服・同じカメラ。")
        print("つなぎ:", " + ".join(str(int(x)) + "秒" for x in CLIPS), "（最後のコマから続ける。画質は落とさない）")
        named = [str(i + 2) + "本目" for i, x in enumerate(CHAIN_EXTRAS) if not is_blank_prompt(x)]
        if named:
            print("別の文を使うクリップ:", "、".join(named), "。空の欄は前の続き。")
    elif any(not is_blank_prompt(x) for x in CHAIN_EXTRAS):
        print("つなぎ欄は「つなぐ」のときだけ使います。今は1本なので無視します。")

env = {}
with open("/content/h3_paths.env") as f:
    for line in f:
        k, v = line.strip().split("=", 1)
        env[k] = v
COMFY_DIR = Path(env["COMFY_DIR"])
DRIVE_ROOT = Path(env["DRIVE_ROOT"])
DRIVE_MODELS = Path(env.get("DRIVE_MODELS") or (DRIVE_ROOT / "models"))
OUT = COMFY_DIR / "output"
PORT = 8188
STUDIO = Path("/content/h3-lora-studio")
SEED = 42
apply_drive_cache_env(DRIVE_ROOT)

SITUATION = resolve_situation(やりたいシーン)
MODE = resolve_mode(作り方)
FORCE_T2V = MODE == "t2v"
VANILLA = is_vanilla(やりたいシーン)
STORY = None
STORY_STILLS = None
STORY_OVERRIDE = None
print()
print(explain_choice(やりたいシーン, 作り方))
print()
FORBIDDEN_FILE = DRIVE_ROOT / "forbidden.json"
fb = load_forbidden(FORBIDDEN_FILE)
print("禁止語ファイル:", FORBIDDEN_FILE)
print("extra:", ", ".join(fb["extra"]) or "（空）")
print("未成年・21歳未満・アフィURLはファイルから消せません。足す・消すのは extra。")
print()

STORY_SEAMLESS = False
STORY_REWRITE = False
CAST_DIR = DRIVE_ROOT / "input" / "cast"
CAST_DIR.mkdir(parents=True, exist_ok=True)
if is_anthology(やりたいシーン):
    STORY = load_story(SITUATION, studio_root=STUDIO)
    STORY["use_cast_ref"] = True
    STORY["seamless"] = False
    STORY["rewrite_chain_prompts"] = False
    STORY_SEAMLESS = False
    STORY_REWRITE = False
    DURATION = float(STORY.get("duration_s") or 180)
    CLIPS = [float(c.get("duration_s") or STORY.get("clip_s") or 15) for c in STORY["clips"]]
    CHAIN = False
    VANILLA = False
    STORY_STILLS = CAST_DIR
    print(str(STORY.get("title_ja") or STORY.get("id")), "短編集。", len(STORY["clips"]), "本 ×", int(STORY.get("clip_s") or 15), "秒。各本は独立。最後のコマではつなぎません。連結しません。")
    print("人物写真:", CAST_DIR, "（sayaka/rei/aya/madoka の bust と full）を R2V 参照。I2V の最初のコマにはしません。")
    print("③のテキストから／写真ファイルは使いません。")
elif is_story(やりたいシーン) or is_chain_pack(やりたいシーン):
    STORY = load_story(SITUATION, studio_root=STUDIO)
    if STORY_PLAY:
        STORY = apply_story_play(STORY, STORY_PLAY)
    STORY_SEAMLESS = bool(STORY.get("seamless"))
    STORY_REWRITE = bool(STORY.get("rewrite_chain_prompts", STORY_SEAMLESS))
    DURATION = float(STORY.get("duration_s") or 120)
    CLIPS = [float(c.get("duration_s") or STORY.get("clip_s") or 10) for c in STORY["clips"]]
    CHAIN = STORY_SEAMLESS
    VANILLA = False
    STORY_STILLS = story_stills_dir(DRIVE_ROOT / "input", STORY)
    STORY_STILLS.mkdir(parents=True, exist_ok=True)
    if not STORY_SEAMLESS:
        print(str(STORY.get("title_ja") or STORY.get("id")), "（専用＝カット）。つなぐではありません。文章欄・つなぎ欄・秒数は使いません。", len(STORY["clips"]), "本の JSON 文で部品を切り替えます。", int(DURATION), "秒。")
        print("カット編集です。各本は独立で、最後のコマからは続けません（再現優先）。")
        if 最終シーン合わせ:
            print("最終シーン合わせ: 専用は写真からの本だけ「この本の静止画・独立カット」を足します。部品は JSON のまま。")
    else:
        print(str(STORY.get("title_ja") or STORY.get("id")), "を最後のコマでつなぎます。", len(STORY["clips"]), "本。1本目はテキストまたは写真、2本目以降は前の本の最後のコマから I2V。文章欄・つなぎ欄・秒数は使いません。")
        if STORY_REWRITE:
            print("1本目は長回しに直します（途中の動きで終わる）。", "最終シーン合わせ: 最後の本だけ合わせます。" if 最終シーン合わせ else "")
        else:
            print("文は直しません（JSON のまま。Picture 1 のロックだけ足す）。", "最終シーン合わせはこの再生では使いません。" if 最終シーン合わせ else "")
    if STORY.get("use_cast_ref"):
        print("人物参照: Drive input/cast/ を1本目の R2V 参照に使います（最初のコマではない）。③のテキストから／写真ファイルは無視します。2本目以降は最後のコマから I2V。")
        FORCE_T2V = False
        STORY_OVERRIDE = None
    cv = STORY.get("canvas") or {}
    clip_secs = [int(x) for x in CLIPS]
    if len(set(clip_secs)) == 1:
        print("画面は", int(cv.get("width") or 576), "x", int(cv.get("height") or 1024), "（", str(cv.get("aspect") or "9:16"), "）固定。1本", clip_secs[0], "秒。")
    else:
        print("画面は", int(cv.get("width") or 576), "x", int(cv.get("height") or 1024), "（", str(cv.get("aspect") or "9:16"), "）固定。本ごとの秒:", ", ".join(str(x) for x in clip_secs))
    print("各本の写真（任意）:", STORY_STILLS)
    for c in STORY["clips"]:
        print(" ", c.get("still") or "（写真なし）", c.get("label") or "")
    if FORCE_T2V and not STORY.get("use_cast_ref"):
        print("作り方はテキストから。専用フォルダの写真は使いません。")
    elif STORY.get("use_cast_ref"):
        print("1本目は input/cast/ の人物写真を R2V 参照します。専用フォルダの試験jpgは使いません。")
    else:
        print("写真が無いクリップはテキストから（顔はクリップごとに変わります）。")
    if (not STORY.get("use_cast_ref")) and MODE == "i2v" and not is_auto_image_name(写真ファイル):
        src = Path(写真ファイル)
        if not src.is_file():
            src = DRIVE_ROOT / "input" / 写真ファイル
        if src.is_file():
            STORY_OVERRIDE = src
            print("1本目の写真として使います:", src.name)

CUSTOM_PROMPT = not is_blank_prompt(文章)
if STORY:
    CUSTOM_PROMPT = True
elif MODE == "t2v":
    print("写真欄はテキストからでは使いません。空でも auto でもエラーにしません。")
    if has_i2v_lock(文章):
        print("文章欄に写真用の文（Picture 1）が残っていたので外します。このシーンのおすすめ文でテキストから作ります。")
        CUSTOM_PROMPT = False

if STORY:
    FILENAME_PREFIX = "video/h3_" + str(STORY.get("id") or "story")
    # 専用+写真から+③: clip0 は rewrite_dedicated_scene_i2v_prompt だけ。rewrite_final_scene_i2v_prompt は走らせない。
    FIT_CLIP0 = bool(最終シーン合わせ and not STORY_SEAMLESS and not STORY.get("use_cast_ref"))
    try:
        planned0 = prepare_story_clip(STORY, 0, last_frame=None, stills_dir=STORY_STILLS, studio_root=STUDIO, catalog_path=STUDIO / "catalog" / "loras.json", forbidden_path=FORBIDDEN_FILE, clip0_override=None if FORCE_T2V else STORY_OVERRIDE, force_t2v=FORCE_T2V, fit_scene=FIT_CLIP0, cast_dir=CAST_DIR)
    except SystemExit as exc:
        hint = friendly_select_error(exc)
        raise SystemExit(hint or str(exc)) from None
    stack = planned0["stack"]
    prompt = planned0["prompt"]
    SAMPLER = planned0["sampler"]
    STEPS = int(SAMPLER.get("steps") or 12)
    cfg = planned0["cfg"]
    w, h = int(planned0["width"]), int(planned0["height"])
    MODE = planned0["mode"]
    print("1本目:", planned0["label"], MODE)
    print("入る部品:")
    for x in stack:
        print(" -", friendly_lora(x["id"]), "強さ", x.get("strength_model"), x.get("role") or "")
    if planned0.get("missing_still"):
        print("1本目の写真が無いのでテキストから作ります。")
elif VANILLA:
    stack = []
    STEPS = 4
    FILENAME_PREFIX = "video/h3_t2v_phone" if MODE == "t2v" else "video/h3_i2va_phone"
    if MODE == "t2v":
        w, h = CANVAS_9_16
        prompt, CUSTOM_PROMPT = apply_user_prompt(文章, mode="t2v", default_prompt=resolve_t2v_prompt("", landscape=False))
        errs = validate_t2v_prompt(prompt)
        if errs:
            raise SystemExit(errs)
    else:
        w, h = CANVAS_8_9
        default_i2v = resolve_motion_prompt("", duration_s=float(CLIPS[0]), with_last_frame=False)
        prompt, CUSTOM_PROMPT = apply_user_prompt(文章, mode="i2v", default_prompt=default_i2v)
        if CUSTOM_PROMPT:
            errs = validate_studio_i2v_prompt(prompt, forbidden_path=FORBIDDEN_FILE)
        else:
            errs = validate_motion_ad_prompt(prompt, with_last_frame=False)
        if errs:
            raise SystemExit(errs)
    print("入る部品: 速いモード（Turbo）だけ。えっち用は使いません。")
    print("文章:", "自分のプロンプト" if CUSTOM_PROMPT else "おすすめ文（空欄）")
    SAMPLER = {"sampler_name": "euler", "scheduler": "simple", "steps": 4}
    cfg = None
else:
    FILENAME_PREFIX = "video/h3_preview" if SITUATION in {"preview", "sfw_preview"} else "video/h3_lora_studio"
    prompt_arg, CUSTOM_PROMPT = apply_user_prompt(文章, mode=MODE, default_prompt="（シーン）")
    print("文章:", "自分のプロンプト" if CUSTOM_PROMPT else "シーンのおすすめ文（空欄）")
    if CUSTOM_PROMPT:
        print("文章欄（先頭）:", prompt_arg[:180].replace("\n", " "))
    try:
        cfg = select_loras(profile_name=SITUATION, mode=MODE, prompt_arg=prompt_arg, catalog_path=STUDIO / "catalog" / "loras.json", profiles_dir=STUDIO / "profiles", turbo_override=None, extra_forbidden=None, forbidden_path=FORBIDDEN_FILE)
    except TypeError:
        cfg = select_loras(profile_name=SITUATION, mode=MODE, prompt_arg=prompt_arg, catalog_path=STUDIO / "catalog" / "loras.json", profiles_dir=STUDIO / "profiles", turbo_override=None)
    except SystemExit as exc:
        hint = friendly_select_error(exc)
        raise SystemExit(hint or str(exc)) from None
    if 動きの底上げ or 胸を強調 or リアル寄り or 静止画用の写実:
        print("上級の追加部品は無視します。ふたなりの竿と穴はシーン側で既に併用しています。")
    stack = cfg["stack"]
    prompt = prepend_triggers(cfg["prompt"], stack)
    SAMPLER = cfg["sampler"]
    STEPS = int(SAMPLER["steps"])
    print("入る部品:")
    for x in stack:
        role = x.get("role") or ""
        print(" -", friendly_lora(x["id"]), "強さ", x.get("strength_model"), role)
    w, h = int(cfg["canvas"]["width"]), int(cfg["canvas"]["height"])
    if MODE == "i2v":
        errs = validate_studio_i2v_prompt(prompt, forbidden_path=FORBIDDEN_FILE)
        if errs:
            raise SystemExit(errs)

if CHAIN and not STORY:
    prompt = rewrite_chain_opening_prompt(prompt)

print()
print("使う文章（先頭）:")
print(prompt[:450])
print("…")
print()

if STORY:
    w, h = int(planned0["width"]), int(planned0["height"])
elif 画面の向き == "縦（スマホ）":
    w, h = canvas_for_aspect("9:16")
elif 画面の向き == "横":
    w, h = canvas_for_aspect("16:9")
elif 画面の向き == "やや正方形":
    w, h = CANVAS_8_9
print("画面サイズ:", w, "x", h, " / 秒数:", int(DURATION), " / ステップ:", STEPS, SAMPLER.get("sampler_name"), SAMPLER.get("scheduler"))
if STORY and not STORY_SEAMLESS:
    print("専用はカット編集。1本", int(CLIPS[0]), "秒 ×", len(CLIPS), "本。1本で 16秒以上は作りません。最後のコマからは続けません。")
elif STORY:
    print("最後のコマでつなぎます。1本", int(CLIPS[0]), "秒 ×", len(CLIPS), "本。部品は本ごとに JSON のまま。1本で 16秒以上は作りません。")
elif CHAIN:
    print("つなぐは最後のコマから続ける長回し。1本で 16秒以上は作りません。画質を保ったまま 10秒ずつ繋ぎます。")
if VANILLA and MODE == "t2v":
    prompt = resolve_t2v_prompt("" if has_i2v_lock(文章) else 文章, landscape=w > h)
    errs = validate_t2v_prompt(prompt)
    if errs:
        raise SystemExit(errs)
    if CHAIN:
        prompt = rewrite_chain_opening_prompt(prompt)
hits = forbidden_hits(prompt, path=FORBIDDEN_FILE)
if hits:
    hint = friendly_select_error(SystemExit(f"forbidden subject in prompt: {hits}"))
    raise SystemExit(hint or f"forbidden subject in prompt: {hits}")

obj = {}
need_r2v = bool(STORY) and (STORY.get("use_cast_ref") or str(STORY.get("kind") or "") == "anthology")
need_i2v = not (STORY and str(STORY.get("kind") or "") == "anthology")
if not 試し打ちだけ:
    print("エンジンの部品表を確認しています…")
    obj = fetch_comfy_object_info(PORT)
    if need_i2v and "MiniMaxH3ImageToVideo" not in obj:
        raise SystemExit("エンジンがまだです。②を先に実行してください。")
    if need_r2v and "MiniMaxH3ReferenceToVideo" not in obj:
        raise SystemExit("参照（R2V）ノードがありません。②をもう一度実行してください。")

fl2va_files = list((COMFY_DIR / "models/diffusion_models").glob("*fl2va*"))
ref2va_files = list((COMFY_DIR / "models/diffusion_models").glob("*ref2va*"))

def unet_for(mode):
    if mode == "r2v":
        if not ref2va_files and not 試し打ちだけ:
            raise SystemExit("参照用の土台（ref2va）がありません。②をもう一度実行してください。")
        return ref2va_files[0].name if ref2va_files else REF2VA_NAME
    if not fl2va_files and not 試し打ちだけ:
        raise SystemExit("土台がありません。②を先に実行してください。")
    return fl2va_files[0].name if fl2va_files else "minimax_h3_fl2va_pruned_int8_convrot.safetensors"

unet = unet_for(MODE)

if not VANILLA:
    lora_dir = COMFY_DIR / "models" / "loras"
    drive_lora = DRIVE_MODELS / "loras"
    catalog_now = load_catalog(STUDIO)
    id_list = [str(x.get("id") or "") for x in stack if x.get("id")]
    if STORY:
        id_list = situation_ids(SITUATION)
        if STORY.get("use_cast_ref") or str(STORY.get("kind") or "") == "anthology":
            for extra in ("minimax-h3-turbo-ref2v-4step", "aftermidnight-ref2va", "blowjob-h3", "cinema-dy"):
                if extra not in id_list:
                    id_list.append(extra)
        print(str(int(DURATION)) + "秒分の部品を確認します:", ", ".join(id_list))
    need = missing_stack_files(stack, lora_dir)
    if STORY:
        jobs_all = download_jobs_for(id_list, drive_lora, catalog=catalog_now)
        need = [str(dest.name) for url, dest, row in jobs_all if not dest.is_file() or dest.stat().st_size < 1000]
    if need:
        print("足りない部品を Drive に入れます:", ", ".join(need))
        token = civitai_token("")
        jobs = download_jobs_for(id_list, drive_lora, catalog=catalog_now)
        for url, dest, row in jobs:
            if dest.name not in need and dest.name not in [Path(n).name for n in need]:
                continue
            auth = "civitai" if str(row.get("source")) == "civitai" else ""
            fallbacks = civitai_download_fallbacks(row) if auth else None
            fetch_weight(url, dest, token=token, auth=auth, fallback_urls=fallbacks, strict=False)
        stage_models_to_local(DRIVE_MODELS, COMFY_DIR / "models")
    stack, replaced = apply_stack_fallbacks(stack, lora_dir, catalog_now)
    if replaced:
        print("アナル専用部品が無かったので総合えっちで代用します。Drive の models/loras に H3_anal_penetration_v1.safetensors を置けば専用になります。")
        print("入る部品:")
        for x in stack:
            print(" -", friendly_lora(x["id"]), "強さ", x.get("strength_model"), x.get("role") or "")
    still = missing_stack_files(stack, lora_dir)
    if still and not 試し打ちだけ:
        raise SystemExit("このシーンの部品がありません: " + ", ".join(still) + "。Drive の models/loras に置いて③をもう一度実行してください。②をもう一度回すだけでは取れないことがあります（Civitai 有料）。")
    unseen = comfy_missing_loras(stack, obj) if obj else []
    if unseen and not 試し打ちだけ:
        print("エンジンが新しい部品をまだ見ていないので、再読み込みします…")
        restart_studio_comfy(COMFY_DIR, port=PORT)
        obj = fetch_comfy_object_info(PORT)
        unseen = comfy_missing_loras(stack, obj)
        if unseen:
            print("まだ見えていないファイル:", ", ".join(unseen), "（このまま試します）")
        if str(MODE) != "r2v":
            warmup_h3_engine(COMFY_DIR, PORT, unet)

r2v_first = bool(STORY) and str(planned0.get("mode") or "") == "r2v"
if not 試し打ちだけ and unet and not r2v_first:
    warmup_h3_engine(COMFY_DIR, PORT, unet)
elif r2v_first:
    print("1本目は参照（R2V）。FL2VA の事前載せはしません。")
    comfy_free(PORT)
    clear_warmup_stamp(COMFY_DIR)

first_name = None
GRAPH_IMGS = []
inp = COMFY_DIR / "input"
inp.mkdir(parents=True, exist_ok=True)
if STORY:
    if str(planned0.get("mode") or "") == "r2v":
        still_paths0 = list(planned0.get("still_paths") or ([planned0["still_path"]] if planned0.get("still_path") else []))
        GRAPH_IMGS = [stage_image_into_input(p, inp) for p in still_paths0]
        first_name = GRAPH_IMGS[0] if GRAPH_IMGS else None
        print("使う参照写真:", ", ".join(GRAPH_IMGS))
    elif planned0.get("still_path"):
        first_name = stage_image_into_input(planned0["still_path"], inp)
        print("使う写真:", first_name)
elif MODE == "i2v":
    if is_auto_image_name(写真ファイル):
        hit = newest_image([DRIVE_ROOT / "input", inp])
        if hit is None and VANILLA:
            dest = inp / DEFAULT_FIRST_IMAGE
            print("参考画像を取得します")
            urllib.request.urlretrieve(ref_image_url(), dest)
            if dest.is_file() and dest.stat().st_size > 1000:
                hit = dest
        if hit is None:
            raise SystemExit("写真が見つかりません。スマホの Drive で「minimax-h3-comfyui/input」に jpg を置いてから、もう一度③を実行してください。")
        first_name = stage_image_into_input(hit, inp)
    else:
        src = Path(写真ファイル)
        if not src.is_file():
            src = DRIVE_ROOT / "input" / 写真ファイル
        if not src.is_file():
            raise SystemExit("その写真ファイルがありません: " + 写真ファイル)
        first_name = stage_image_into_input(src, inp)
    print("使う写真:", first_name)

lora_name = None
lora_strength = 0.0
if VANILLA:
    lora_paths = list((COMFY_DIR / "models" / "loras").glob("*.safetensors"))
    lora_name = prefer_fl2v_lora(lora_paths, True)
    lora_strength = 1.0
    if not lora_name:
        raise SystemExit("速いモード（Turbo）がありません。②を先に実行してください。")

vram_gb = 40.0
try:
    import torch
    if torch.cuda.is_available():
        vram_gb = float(torch.cuda.get_device_properties(0).total_memory) / (1024 ** 3)
except Exception:
    pass
if MODE == "r2v":
    plans = r2v_retry_plans(duration_s=float(CLIPS[0]), ref_image_size="max", width=w, height=h, n_images=max(1, len(GRAPH_IMGS)), has_video=False, vram_gb=vram_gb)
elif MODE == "t2v":
    plans = t2v_retry_plans(width=w, height=h)
else:
    plans = i2va_retry_plans(width=w, height=h)
CLIP_DURATION = float(CLIPS[0])
CLIP_INDEX = 0
GRAPH_MODE = MODE
GRAPH_FIRST = first_name
GRAPH_PROMPT = prompt
prev_prompt = prompt

def make_graph(plan):
    prompt_now = lock_spoken_japanese(GRAPH_PROMPT)
    steps = int(SAMPLER["steps"])
    clip_seed = int(SEED) + int(CLIP_INDEX)
    prefix = FILENAME_PREFIX + ("_p" + str(int(CLIP_INDEX)) if CHAIN else "")
    if GRAPH_MODE == "r2v":
        imgs = list(GRAPH_IMGS or ([] if not GRAPH_FIRST else [GRAPH_FIRST]))
        if not imgs:
            raise SystemExit("参照用の人物写真がありません。Drive の input/cast/ を確認してください。")
        g = build_r2v_graph(
            img_names=imgs, vid_names=[], prompt=prompt_now, unet=unet,
            lora_name=lora_name if VANILLA else None, lora_strength=lora_strength if VANILLA else 0.0,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=float(plan.get("duration_s") or CLIP_DURATION), seed=clip_seed, steps=steps,
            filename_prefix=prefix,
            ref_image_size=str(plan.get("ref_image_size") or "max"),
            use_videos=False, has_vhs=False,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or 試し打ちだけ,
            has_audio_decode=("VAEDecodeAudio" in obj) or 試し打ちだけ,
        )
        if not VANILLA:
            inject_lora_stack(g, stack, sampler=SAMPLER)
        errs = assert_graph_identity_motion(g, expect_images=len(imgs), expect_videos=0, prompt=prompt_now)
    elif GRAPH_MODE == "t2v":
        g = build_t2v_graph(
            prompt=prompt_now, unet=unet, lora_name=lora_name, lora_strength=lora_strength,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=CLIP_DURATION, seed=clip_seed, steps=steps,
            filename_prefix=prefix,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or 試し打ちだけ,
            has_audio_decode=("VAEDecodeAudio" in obj) or 試し打ちだけ,
        )
        if not VANILLA:
            inject_lora_stack(g, stack, sampler=SAMPLER)
        errs = assert_t2v_graph(g)
    else:
        g = build_i2va_graph(
            first_image=GRAPH_FIRST, last_image=None, prompt=prompt_now, unet=unet,
            lora_name=lora_name, lora_strength=lora_strength,
            width=int(plan["width"]), height=int(plan["height"]),
            duration_s=CLIP_DURATION, seed=clip_seed, steps=steps,
            filename_prefix=prefix,
            has_lora_loader=("LoraLoaderModelOnly" in obj) or 試し打ちだけ,
            has_audio_decode=("VAEDecodeAudio" in obj) or 試し打ちだけ,
        )
        if not VANILLA:
            inject_lora_stack(g, stack, sampler=SAMPLER)
        homage = bool(VANILLA and not CUSTOM_PROMPT and CLIP_INDEX == 0)
        errs = assert_i2va_graph(g, expect_last=False, homage=homage)
    if errs:
        raise SystemExit(errs)
    loaders = [n for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"]
    names = [str(n["inputs"].get("lora_name", "")) for n in loaders]
    blob = " ".join(names).lower()
    has_larry = "turbo_v4" in blob or "larry" in blob
    has_lx = "fl2v_turbo" in blob or "fl2v_lightx2v" in blob or "lightx2v" in blob or "ref2v_turbo" in blob
    if has_larry and has_lx:
        raise SystemExit("Larry と LightX2V は同時に積みません。")
    if VANILLA:
        if not names or all("turbo" not in n.lower() for n in names):
            raise SystemExit("普通（エロなし）なのに速いモードが入っていません。②からやり直してください。")
        if any("turbo" not in n.lower() for n in names):
            raise SystemExit("普通（エロなし）にえっち用の部品が混ざったので止めています。")
    elif cfg and cfg.get("turbo"):
        if not (has_larry or has_lx):
            raise SystemExit("このシーンは薄い Turbo が必要です。②からやり直してください。")
    elif has_larry or has_lx:
        raise SystemExit("アナル挿入の本線に Turbo は入れません。")
    return g

def post_prompt(g):
    body = {"prompt": g, "client_id": str(uuid.uuid4())}
    req = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/prompt",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, e.read().decode(errors="replace")[:2000]

def wait_prompt(pid, timeout=3600):
    t0 = time.time()
    while time.time() - t0 < timeout:
        with urllib.request.urlopen(f"http://127.0.0.1:{PORT}/history/{pid}", timeout=60) as r:
            hist = json.loads(r.read().decode())
        entry = hist.get(pid) or {}
        st = entry.get("status") or {}
        if st.get("completed") or entry.get("outputs"):
            if st.get("status_str") == "error":
                return False, entry
            return True, entry
        for m in st.get("messages") or []:
            if isinstance(m, list) and m and m[0] == "execution_error":
                return False, m
        time.sleep(2)
    return False, "timeout"

def generate_one():
    if GRAPH_MODE == "r2v":
        plans_now = r2v_retry_plans(duration_s=CLIP_DURATION, ref_image_size="max", width=w, height=h, n_images=max(1, len(GRAPH_IMGS or [])), has_video=False, vram_gb=vram_gb)
    elif GRAPH_MODE == "t2v":
        plans_now = t2v_retry_plans(width=w, height=h)
    else:
        plans_now = i2va_retry_plans(width=w, height=h)
    ok_entry = None
    before = newest_mp4(OUT)
    for plan in plans_now:
        label = plan.get("label") or plan
        for attempt in (1, 2):
            print("サイズを試しています:", label, "（同じサイズ再試行）" if attempt == 2 else "")
            g = make_graph(plan)
            res, err = post_prompt(g)
            oom = False
            if err:
                if is_oom_error(err):
                    oom = True
                else:
                    raise SystemExit(format_prompt_http_fail(err, stack))
            else:
                ok, payload = wait_prompt(res["prompt_id"])
                if ok:
                    ok_entry = payload
                    break
                if is_oom_error(str(payload)):
                    oom = True
                else:
                    raise SystemExit(format_job_fail(GRAPH_MODE, payload))
            print("メモリが足りません。VRAM を解放します。")
            comfy_free(PORT)
            if attempt == 1:
                continue
            print("小さい画面でやり直します。")
        if ok_entry is not None:
            break
    if ok_entry is None:
        raise SystemExit("メモリ不足で作れませんでした。秒数を短くするか、A100 のまま②からやり直してください。")
    videos = collect_output_videos(ok_entry, OUT)
    fresh = newest_mp4(OUT)
    if fresh and fresh not in videos and (before is None or fresh != before):
        videos.append(fresh)
    if not videos:
        raise SystemExit("ファイル名が取れませんでした。Drive の output フォルダを見てください: " + str(OUT))
    return videos[0]

if 試し打ちだけ:
    g = make_graph(plans[0])
    print("試し打ちOK。部品:", [n["inputs"]["lora_name"] for n in g.values() if n.get("class_type") == "LoraLoaderModelOnly"])
    if STORY:
        print(("つなぐ" if STORY_SEAMLESS else "専用（カット）") + str(len(STORY["clips"])) + "本:")
        for i, c in enumerate(STORY["clips"]):
            print(" ", i + 1, c.get("label"), c.get("situation"), c.get("start"))
    elif CHAIN:
        print("つなぎ予定:", " + ".join(str(int(x)) + "秒" for x in CLIPS))
        named = [str(i + 2) + "本目" for i, x in enumerate(CHAIN_EXTRAS) if not is_blank_prompt(x)]
        if named:
            print("別の文:", "、".join(named))
    print("実際の動画は「試し打ちだけ」をオフにして③をもう一度。")
else:
    print()
    print("作り始めています。数分〜十数分かかることがあります…")
    clip_paths = []
    inp = COMFY_DIR / "input"
    inp.mkdir(parents=True, exist_ok=True)
    prev_sit = None
    prev_stack = None
    for CLIP_INDEX, CLIP_DURATION in enumerate(CLIPS):
        if STORY:
            # 専用（カット）は last_frame なし。つなぐ / つなぐ修 / パックは 2本目以降を前の本の最後のコマから。
            last_now = first_name if (STORY.get("seamless") and CLIP_INDEX > 0) else None
            if STORY_SEAMLESS:
                # chain-raw（rewrite False）は ③チェックでも fit_now False。つなぐ修は最後の本だけ。
                fit_now = should_fit_scene_image_prompt(fit=最終シーン合わせ, mode="i2v", clip_index=CLIP_INDEX, clip_count=len(CLIPS), is_story=True, chain=True, seamless=True, rewrite_chain_prompts=STORY_REWRITE)
            else:
                # 専用: 写真からの本だけ rewrite_dedicated_scene_i2v_prompt（prepare_story_clip が静止画のときだけ掛ける）
                fit_now = bool(最終シーン合わせ)
            try:
                planned = prepare_story_clip(STORY, CLIP_INDEX, last_frame=last_now, stills_dir=STORY_STILLS, studio_root=STUDIO, catalog_path=STUDIO / "catalog" / "loras.json", forbidden_path=FORBIDDEN_FILE, clip0_override=(None if FORCE_T2V else STORY_OVERRIDE) if CLIP_INDEX == 0 else None, prev_situation=prev_sit, prev_stack=prev_stack, force_t2v=FORCE_T2V, fit_scene=fit_now, cast_dir=CAST_DIR)
            except SystemExit as exc:
                hint = friendly_select_error(exc)
                raise SystemExit(hint or str(exc)) from None
            prev_sit = planned["situation"]
            prev_stack = planned["stack"]
            stack = planned["stack"]
            SAMPLER = planned["sampler"]
            cfg = planned["cfg"]
            GRAPH_MODE = planned["mode"]
            GRAPH_PROMPT = planned["prompt"]
            if planned.get("missing_still"):
                print("写真が無いのでテキストから:", planned["label"], planned.get("missing_still"))
            if planned.get("first_kind") == "last_frame":
                if not last_now:
                    raise SystemExit("前の本の最後のコマがありません。③をもう一度。")
                first_name = last_now
                GRAPH_IMGS = []
                print("前の本の最後のコマから続けます:", planned["label"])
            elif planned.get("first_kind") == "cast":
                still_now = list(planned.get("still_paths") or ([planned["still_path"]] if planned.get("still_path") else []))
                GRAPH_IMGS = [stage_image_into_input(p, inp) for p in still_now]
                first_name = GRAPH_IMGS[0] if GRAPH_IMGS else None
                print("人物参照 (R2V):", planned["label"], [Path(str(p)).name for p in still_now])
            elif planned.get("still_path") is not None:
                first_name = stage_image_into_input(planned["still_path"], inp)
            elif GRAPH_MODE == "t2v":
                first_name = None
            if planned.get("fit_scene"):
                print("最終シーン合わせ:", "最後の本を合わせます" if planned.get("first_kind") == "last_frame" else "この本の静止画・独立カットとして送ります")
            w, h = int(planned["width"]), int(planned["height"])
            CLIP_DURATION = float(planned.get("duration_s") or CLIP_DURATION)
            print("クリップ", CLIP_INDEX + 1, "/", len(CLIPS), ":", planned["label"], int(CLIP_DURATION), "秒", GRAPH_MODE, [x.get("id") for x in stack], str(SAMPLER.get("steps")) + "step", "Turbo" if planned.get("turbo") else "フルステップ")
            next_unet = unet_for(GRAPH_MODE)
            unet_switched = next_unet != unet
            if unet_switched:
                print("土台を切り替えます:", unet, "→", next_unet)
                comfy_free(PORT)
                clear_warmup_stamp(COMFY_DIR)
                unet = next_unet
                if GRAPH_MODE != "r2v" and not 試し打ちだけ:
                    warmup_h3_engine(COMFY_DIR, PORT, unet, force=True)
            elif CLIP_INDEX > 0 and planned.get("stack_changed"):
                print("部品を切り替えます:", planned["label"], planned["situation"], "（土台は載せたまま。この本の LoRA だけ繋ぎます）")
        else:
            GRAPH_MODE = MODE if CLIP_INDEX == 0 else "i2v"
            GRAPH_PROMPT = next_chain_prompt(CLIP_INDEX, first_prompt=prompt, prev_prompt=prev_prompt, extras=CHAIN_EXTRAS)
            if CLIP_INDEX > 0:
                GRAPH_PROMPT = prepend_triggers(GRAPH_PROMPT, stack)
                extra_now = CHAIN_EXTRAS[CLIP_INDEX - 1] if CLIP_INDEX - 1 < len(CHAIN_EXTRAS) else ""
                if not is_blank_prompt(extra_now):
                    print("このクリップはつなぎ欄の文を使います")
            # ③合わせ: 最後の本だけ（最初の T2V→I2V つなぎ＝2本目は触らない）。1本の写真からも対象。
            if (not STORY) and (not VANILLA) and should_fit_scene_image_prompt(fit=最終シーン合わせ, mode=GRAPH_MODE, clip_index=CLIP_INDEX, clip_count=len(CLIPS), is_story=False, chain=CHAIN):
                try:
                    scene_cfg = select_loras(profile_name=SITUATION, mode="i2v", prompt_arg="（シーン）", catalog_path=STUDIO / "catalog" / "loras.json", profiles_dir=STUDIO / "profiles", turbo_override=None, extra_forbidden=None, forbidden_path=FORBIDDEN_FILE)
                    fitted = rewrite_final_scene_i2v_prompt(GRAPH_PROMPT, scene_prompt=str(scene_cfg.get("prompt") or ""))
                    fit_cfg = select_loras(profile_name=SITUATION, mode="i2v", prompt_arg=fitted, catalog_path=STUDIO / "catalog" / "loras.json", profiles_dir=STUDIO / "profiles", turbo_override=None, extra_forbidden=None, forbidden_path=FORBIDDEN_FILE)
                except SystemExit as exc:
                    hint = friendly_select_error(exc)
                    raise SystemExit(hint or str(exc)) from None
                fit_stack, _ = apply_stack_fallbacks(list(fit_cfg["stack"]), COMFY_DIR / "models" / "loras", load_catalog(STUDIO))
                if missing_stack_files(fit_stack, COMFY_DIR / "models" / "loras"):
                    print("最終シーン合わせの部品が足りないので、部品は今のまま文だけ合わせます。")
                else:
                    stack = fit_stack
                    SAMPLER = fit_cfg["sampler"]
                    cfg = fit_cfg
                GRAPH_PROMPT = prepend_triggers(str(fit_cfg.get("prompt") or fitted), stack)
                print("最終シーン合わせ: 最後の本を", やりたいシーン, "に合わせます。部品:", [x.get("id") for x in stack])
            if CLIP_INDEX > 0:
                hits = forbidden_hits(GRAPH_PROMPT, path=FORBIDDEN_FILE)
                if hits:
                    hint = friendly_select_error(SystemExit("forbidden subject in prompt: " + str(hits)))
                    raise SystemExit(hint or ("forbidden subject in prompt: " + str(hits)))
                if "Picture 1" not in GRAPH_PROMPT:
                    raise SystemExit("つなぎの2本目以降に最後のコマ（Picture 1）がありません。②のあと③をもう一度。")
            print("クリップ", CLIP_INDEX + 1, "/", len(CLIPS), ":", int(CLIP_DURATION), "秒", GRAPH_MODE)
        GRAPH_FIRST = first_name
        prev_prompt = GRAPH_PROMPT
        if GRAPH_MODE == "i2v" and not GRAPH_FIRST:
            raise SystemExit("写真または前のクリップの最後のコマがありません。")
        if GRAPH_MODE == "r2v" and not GRAPH_IMGS:
            raise SystemExit("参照用の人物写真がありません。Drive の input/cast/ を確認してください。")
        clip_path = generate_one()
        clip_paths.append(clip_path)
        print("保存:", clip_path)
        if CLIP_INDEX + 1 < len(CLIPS) and CHAIN:
            frame = inp / ("h3_chain_" + str(CLIP_INDEX) + ".png")
            extract_last_frame(clip_path, frame)
            first_name = stage_image_into_input(frame, inp)
    final = clip_paths[0]
    showed_all = False
    if STORY and str(STORY.get("kind") or "") == "anthology":
        print("短編集: 各クリップは独立した15秒です。つなぎません。連結しません。")
        for p in clip_paths:
            print(" 短編:", p)
            if p.is_file():
                display(HTML(f"<p style='font-size:16px'>短編: <code>{p}</code></p>"))
                display(Video(str(p), embed=True, width=360))
        final = clip_paths[-1]
        showed_all = True
    elif len(clip_paths) > 1:
        final = concat_studio_clips(clip_paths, OUT / (("h3_" + str(STORY.get("id")) + "_concat.mp4") if STORY else ("h3_chain_" + str(int(DURATION)) + "s.mp4")))
        print("つなぎ完了:", final)
        if STORY and not STORY_SEAMLESS:
            print("カット編集です。クリップの境はシームレスではありません。")
        else:
            print("最後のコマから繋げました。同じカットの続きです。")
    print()
    print("できました。下に再生、Drive にも保存しています。")
    print("保存:", final)
    if (not showed_all) and final.is_file():
        display(HTML(f"<p style='font-size:16px'>保存先: <code>{final}</code></p>"))
        display(Video(str(final), embed=True, width=360))
print()
print("③ 完了。キーは画面に出していません。")
'''


def to_source(text: str) -> list[str]:
    return [line + "\n" for line in text.strip("\n").split("\n")]


def fill_scene_options(text: str) -> str:
    return (
        text.replace("__DEFAULT_SCENE__", DEFAULT_SCENE)
        .replace("__SCENE_OPTIONS_2__", _options(SCENE_OPTIONS_2))
        .replace("__SCENE_OPTIONS_3__", _options(SCENE_OPTIONS_3))
        .replace("__STORY_ID_LIST__", _options(STORY_ID_LIST))
    )


CELL2 = fill_scene_options(CELL2)
CELL3 = fill_scene_options(CELL3)
assert 'やりたいシーン = "登校（専用）"' in CELL3
assert "__" + "SCENE_OPTIONS" not in CELL2 + CELL3

for _name, _src in (("CELL1", CELL1), ("CELL2", CELL2), ("CELL3", CELL3)):
    compile(_src, _name, "exec")


nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
        "accelerator": "GPU",
        "colab": {"provenance": [], "gpuType": "A100"},
    },
    "cells": [
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD0)},
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD1)},
        {"cell_type": "code", "metadata": {"id": "ls1_drive"}, "execution_count": None, "outputs": [], "source": to_source(CELL1)},
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD2)},
        {"cell_type": "code", "metadata": {"id": "ls2_setup"}, "execution_count": None, "outputs": [], "source": to_source(CELL2)},
        {"cell_type": "markdown", "metadata": {}, "source": to_source(MD3)},
        {"cell_type": "code", "metadata": {"id": "ls3_gen_v2"}, "execution_count": None, "outputs": [], "source": to_source(CELL3)},
    ],
}
blob = json.dumps(nb, ensure_ascii=False, indent=1)
for out in OUTS:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(blob, encoding="utf-8")
    print("wrote", out, "bytes", out.stat().st_size)
