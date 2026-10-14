# ショートのライン

脳は台本、体は Python と ffmpeg。Premiere は使わない。CapCut は人が手で直すときだけ。このコマンドは mp4 をレビューフォルダに置くところまでで、YouTube にも X にも投稿しない。CTA も URL も動画の中に入れない。

出す先は、今までのチャンネルとは別の新しいチャンネル。有力な案は防災の備えで、仮の名前は「30秒そなえ帳」。確定ではない。設定は `channels/sonae.yaml`。名前を空にした `channels/draft.yaml` も残してある。動画、UPLOAD、QA に、使わない古いチャンネル名は書かない。仮称は QA に仮称と出す。

画面は既存の静止画と同じ。1080x1920、20秒以上30秒以下、いらすとやの会社員、ゆっくりしたズームとパン、反応の行だけ小さく揺らす、字幕は大きく、声は VOICEVOX。口の重ね絵は無し。頭の上の名札は無し。字幕の後ろの帯は無し。背景の窓は一枚のガラスで、中の桟は描かない。

既存の声、口の位置、揺れ、効果音は `tools/irasutoya-short` を呼ぶ。ここは段のつなぎと、帯を付けない字幕と、落ちたら mp4 を出さない検査。

## 段

| 段 | 自動か | 入るもの | 出るもの |
| --- | --- | --- | --- |
| 1. 台本 | 自動。中身は手書きJSONか、テーマを型に埋めたもの | テーマ一文、または台本JSON | 検査済みの台本。声の番号と素材URLを足し、最後にクレジット行 |
| 2. 声 | 自動。VOICEVOX。話者の声はチャンネル設定 | 行の text、話者、感情 | 行ごとの wav と、効果音と小さなBGMを足した mix.wav |
| 3. 素材 | 自動。ローカルの索引から選ぶ | 行の character と emotion | キャッシュしたPNG。出典URLは credits に残す。画像そのものはリポジトリに置かない |
| 4. レイアウト | 自動 | 会社員1人、字幕、背景 | 1080x1920 のフレーム。字幕は動きのあとから載せる |
| 5. 組み立て | 自動。ffmpeg | フレームと mix.wav | 作業フォルダの out.mp4 と、行ごとの絵 |
| 6. 検査 | 自動。落ちたらレビューに mp4 を出さない | mp4 と、組む前の字幕・口の記録 | QA.md |
| 7. レビュー | 人 | レビューフォルダ | 出すか、CapCut で直すか、捨てるか。投稿ボタンは押さない |

台本の型は `script_from_theme`。オチの一文にテーマを入れるだけ。LLM に替えるときは、同じJSONを書かせる。試作は手書きJSON。

## 台本JSON

```json
{
  "id": "50-clearfile-coin",
  "channel": "draft",
  "title": "動画のタイトル",
  "theme": "テーマの短い名",
  "hook": "最初の行の text と同じ",
  "mouth_overlay": false,
  "lines": [
    {
      "speaker": "rival",
      "character": "rival_smug",
      "emotion": "smug",
      "text": "声に読む文",
      "caption": "画面の字幕。長いときは改行",
      "role": "hook",
      "effect": "zoom",
      "sfx": "none"
    }
  ]
}
```

| 欄 | 意味 |
| --- | --- |
| id | レビューフォルダの名前 |
| channel | `channels/<id>.yaml` の id。表示名ではない |
| title | 投稿用タイトル。batch1 から batch5 のタイトルとは重ねない |
| theme | 何の話か。金額は書かない |
| hook | 冒頭の一文。最初の行の text と揃える |
| mouth_overlay | 省略すると false。口の重ね絵を使わない |
| thumbnail | 省略すると、動画に出した絵をサムネイルにする。別の絵を指定したときだけ点数が増える |
| sources | `require_sources` のチャンネルでは必須。name、url、claim。url は首相官邸か内閣府 |
| facts_used | 出典の claim に、そのまま含まれる語句 |
| lines | 話す行。クレジット行はコマンドが後ろに足す |
| speaker | `narrator` / `hero` / `rival` / `boss` |
| character | 索引の id。省略したときは emotion と話者で一つに決まるときだけ進む |
| emotion | その絵の感情と揃える |
| text | VOICEVOX が読む文 |
| caption | 画面の字幕。帯は付けない |
| role | `hook` / `develop` / `punch`。無ければ先頭が hook、末尾が punch、あいだが develop |
| effect | `none` / `zoom` / `shake`。shake の行だけ小さく揺らす |
| sfx | `none` / `paper` / `whoosh` / `coin` / `shock` / `notify` / `tick` / `rise` |

ナレーションは画面の人物が違ってよい。それ以外は、話者と絵の役を揃える。名札（label, tag）と `#` と URL と金額は、検査の前に落とす。

## チャンネル設定

`channels/<id>.yaml`。

| 欄 | 意味 |
| --- | --- |
| name | チャンネル名。未定なら空。空のあいだは UPLOAD にチャンネル名の行を出さない |
| name_status | `working` なら仮称。`final` か空なら仮称とは書かない |
| genre | ジャンル。未定なら空 |
| require_sources | true のとき、台本に首相官邸か内閣府の出典が要る。動画で言う数量は、その記述にあるものだけ |
| tags | UPLOAD のタグ。動画の中には出さない |
| voices | 話者ごとの style_id とクレジット。hero は angry_style_id を別にできる |
| caption | 字幕の色、大きさ、位置、縁の太さ。bar は none。帯は付けない |
| credits | 画面に出すのは使った声の名前。note は credits.json に書く出典の説明 |
| upload_template | UPLOAD.md の型。`{title}` `{theme}` `{voices}` `{tags}` `{name}` `{genre}` `{channel_line}` `{genre_line}` `{credits_note}` `{sources}` `{name_note}` |

いまの声は draft と sonae で同じ。ナレーションは四国めたん、主人公は白上虎太郎、相手は玄野武宏、上司は剣崎雌雄。青山龍星は使わない。

試作は `scripts/51-water-stock.json`。テーマは備蓄の水の量。飲料水は3日分、1人1日3リットルが目安、大規模災害では1週間分の備蓄が望ましい、飲料水とは別に生活用水、という首相官邸の記述と、最低3日できれば一週間、一人1日3リットル、という内閣府の記述だけを使う。9リットルや21リットルのような、ページに無い合計は入れない。UPLOAD にページのURLと、使った記述を書く。

硬貨の見本 `scripts/50-clearfile-coin.json` は、名前が空の draft 用として残してある。

## 素材の索引

`assets/index.json`。会社員の絵だけ。運転手と駅員は入れていない。各項目は id、役、感情、出典URL。

選ぶときは character の id で取る。emotion が索引と違うときは止める。使った絵の出典URLは `review/<id>/credits.json` に残す。キャッシュは `~/.cache/irasutoya-short/pipeline-assets/`。

## 受け渡し

```
テーマ または script.json
        ↓ validate
resolved script.json（声、出典URL、クレジット行）
        ↓ VOICEVOX
audio/line_XX.wav → audio/mix.wav
        ↓ 索引
cache/<id>.png
        ↓ レイアウト（帯なし字幕、口の重ね絵なし）
フレームを ffmpeg へ流す
        ↓
work/out.mp4 と work/contact-sheet.jpg
        ↓ QA が pass
review/<id>/out.mp4
review/<id>/contact-sheet.jpg
review/<id>/UPLOAD.md
review/<id>/QA.md
review/<id>/credits.json
review/<id>/script.json
```

作業フォルダは `/tmp/shorts-pipeline/<id>`。レビューに出すのは pass のときだけ。

コンタクトシートは、各行の途中のフレームを2列に並べた1枚。人が通しで見る前の一覧。

## 検査

全部 pass のときだけ `out.mp4` をレビューにコピーする。一つでも落ちたら mp4 はレビューに置かない。QA.md は残す。

| 項目 | 通り |
| --- | --- |
| duration | ファイルの尺が 20秒以上 30秒以下 |
| resolution | 1080x1920 |
| audio | 音声トラックがあり、平均音量が無音ではない |
| caption_overflow | 字幕が画面の内側に収まっている |
| text_boxes | 字幕レイヤに塗りつぶしの帯が無い |
| name_tags | 名札も `#` も無い |
| mouth_overlay_absent | `mouth_overlay` が false のとき、重ね絵が1枚も無い |
| irasutoya_count | 動画とサムネイルを合わせた、別のいらすとやの絵が20点以下。同じ絵の再利用と、同じ絵の色違いは1点。表情が違う絵は別のURLなので別点。一覧は QA に残す。21点以上は mp4 をレビューに出さない |
| irasutoya_subject | 背景はコードで描いた部屋。イラストは縦80%、横90%、面積65%を超えない。字幕が1行以上ある |
| irasutoya_name | チャンネル名、ジャンル、タイトル、タグ、本文が、いらすとやとの協力を示す書き方になっていない。クレジットの注記に出典として名前を書くのは、ここには入れない |
| style_signature | 9軸の署名が、直前の動画と2軸まで、直近5本および公開済みとは3軸までしか重ならない。完全一致は不可。署名は `style-log.csv` に残す |
| style_thumb | サムネの構図・配色・文字位置は、直前のサムネと2つ以上違う |
| credit_line | 使った声の名前と「イラスト：いらすとや」がクレジット行にある |

見た目は動画ごとに `channels/<id>.yaml` の `style` から選ぶ。防災は `bousai`、硬貨の見本は `kane`。軸は構図、配色、文字位置、書体、冒頭、テンポ、BGM、長さ、素材の組み合わせ。同じ9軸の組は使わない。長さのメニューには15秒から60秒まであるが、今の尺の検査は20秒以上30秒以下のままなので、実際に選ぶのはその範囲に入る L1（20秒）と L2（21–30秒）だけ。字幕の位置が上や下でも、塗りつぶしの帯は付けない。BGMは軸ごとにその場で合成する。書体は `pipeline/fonts/` の別ファイル。公開済みの署名でルール表に書いてあったのは金メモ #14 の1本だけなので、それだけを style-log の先頭に置いてある。

YouTube に出すときの点数は、サムネイルを含めて1本20点まで、といういらすとやの案内に合わせている。収益化しない公開動画は案内上21点以上もできるが、このラインは20点で止める。イラストは内容の主体にしない。チャンネル名やタイトルに、いらすとやとの協力をにおわせる語は入れない。

`mouth_overlay` を true にしたときだけ、項目は mouth_position に替わる。目、鼻、口を人の顔の並びとして、重ね絵の中心がキャラの口（`mouth_anchor`。両目の下、鼻より下）に無いときは fail。目の位置、あごの外、口からずれた位置は止める。この判定が壊れていないことは、書き出す前に自己テストで見る。正しい口は通し、目の位置は落とす。

## 自動と手動

自動: 台本の形、声、素材の選択、レイアウト、ffmpeg、検査、レビューフォルダへのコピー。

手動: コンタクトシートと mp4 を見て、出すかどうかを決める。直すときは CapCut。投稿、固定コメント、プロフィールのURLは人がやる。このラインはそこを触らない。

## コマンド

```bash
python3 affiliate-shorts/pipeline/run.py \
  --script affiliate-shorts/pipeline/scripts/51-water-stock.json
```

テーマから型で埋めるとき:

```bash
python3 affiliate-shorts/pipeline/run.py \
  --channel draft \
  --theme "クリアファイルの奥の硬貨" \
  --id 50-clearfile-coin
```

口と帯の検査だけ:

```bash
python3 affiliate-shorts/pipeline/run.py --self-test
```

VOICEVOX の置き場所は `tools/irasutoya-short/docs/GROK_BUILD.md` と同じ。`IRASUTOYA_VOICEVOX` で変えられる。
