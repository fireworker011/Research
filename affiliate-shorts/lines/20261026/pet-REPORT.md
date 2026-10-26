# pet-06〜08 作業報告（未投稿）

指示書 `cursor-inputs/20261026/03-pet-06-08.md` に沿って、10秒型の台本3本を書いた。投稿・ログイン・外部への送信はしていない。A8への広告掲載URLの提出もしていない。

点検のあと、直し1周。マージはしていない。

## 書いたファイル
- `affiliate-shorts/lines/20261026/pet-06.md` … 木の床・黒猫・水の入った白い皿。1秒目の文字は「この水、飲んでない？」
- `affiliate-shorts/lines/20261026/pet-07.md` … 出窓・サビ猫・薄いベージュの毛糸玉。1秒目の文字は「毛糸玉、目の前」
- `affiliate-shorts/lines/20261026/pet-08.md` … 玄関・ハチワレ・空のスリッパ1足。中身は変えていない

型は `affiliate-engine/docs/grok-bots/research/kata/pet.md`（ブランチ `cursor/grok-bot-research-2026-08-26`）の型1。秒割りは 0.0–2.0 レンズを見る、2.0–6.0 で1歩、6.0–10.0 で鼻を1回寄せて止まる。カメラ固定。出典の映像とせりふは写していない。

場面の重なりは、点検の直しで pet-06 だけ変えた。pet-03 は皿に顔を入れる。pet-04 はソファで丸くなる。pet-05 はソファで2匹。水を飲む場所の台本は蛇口・コップ・お風呂のふち・水の皿を巡る。pet-06 はリビングの木の床で、水の入った皿の前に止まり、飲まずに鼻を手前で止める。蛇口・コップ・お風呂のふちは映さない。顔は皿に入れない。pet-07 は毛糸玉。pet-08 は空のスリッパ。この3本はどれも猫1匹。ソファは映さない。

音声は元音ミュート＋BGMだけ（声なし）。画面文字は、1秒目のテキストフック、0.0–2.0 の右上の小さい「PR」、10.0–12.0 のPR画面だけ。本編の字幕は置いていない。声のセリフは0本なので、セリフ間1.5秒の対象は無い。テキストフックの終わり（1.0秒）からエンドカード（10.0秒）までは9.0秒空く。本編字幕なしの指定なので、この間は字幕で埋めていない。

## 自己採点
- pet-06: 82（最初の3秒18、テンポ16、見やすさ18、プロフィールへの誘導14、壊れ16）
- pet-07: 82（同配点。理由は各ファイルの表）
- pet-08: 82（同配点。理由は各ファイルの表）

80未満は無い。点検のあと直し1周。pet-06 と pet-07 の「直した点」に書いた。pet-08 は中身を変えていない。動画の必須5項目の確認欄は3本とも付けた。時間の上限では止めていない。HANDOFF は作っていない。

## 点検の直し（1周目）
- pet-07: 猫が鼻を寄せる対象が葉だと、猫に危ない観葉植物を連想させる。置き物を薄いベージュの毛糸玉に差し替え、1秒目の文字を「毛糸玉、目の前」にした。口は閉じ、触れる前で止まる。糸の端は出ていない。
- pet-06: フック「その袋、見るだけ？」は腎活サプリとのつながりが弱い。1秒目の画を水の入った白い皿、文字を「この水、飲んでない？」にした。飲み水が気になる気持ちで、効能は断定していない。固定カメラなので、2秒以降の1歩と鼻の停止も同じ皿に揃えた。
- PRの位置（右上 0.0–2.0、最後2秒のPR画面）は変えていない。本編字幕・CTA・商品名は本編に置いていない。

## リンクの grep（pet-03 と完全一致）

コマンド:

```
rg -n "px\.a8\.net" affiliate-shorts/lines/20261026/pet-06.md affiliate-shorts/lines/20261026/pet-07.md affiliate-shorts/lines/20261026/pet-08.md cursor-inputs/20261026/pet/pet-03.md
```

結果:

直しのあと再実行:

```
affiliate-shorts/lines/20261026/pet-06.md:79:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
affiliate-shorts/lines/20261026/pet-06.md:82:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
cursor-inputs/20261026/pet/pet-03.md:94:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
cursor-inputs/20261026/pet/pet-03.md:97:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
affiliate-shorts/lines/20261026/pet-08.md:79:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
affiliate-shorts/lines/20261026/pet-08.md:82:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
affiliate-shorts/lines/20261026/pet-07.md:79:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
affiliate-shorts/lines/20261026/pet-07.md:82:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
```

TikTok用は4本とも `a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok`。YouTube用は4本とも `a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube`。programId は pet-03 と同じ `s00000016494010`。

## 禁止語の grep

コマンド:

```
rg -n "効く|治る|予防|健康になる" affiliate-shorts/lines/20261026/pet-06.md affiliate-shorts/lines/20261026/pet-07.md affiliate-shorts/lines/20261026/pet-08.md
```

結果: 一致なし（出力なし）。直しのあとも再実行して、一致なし。

「健康」も3ファイルに無い。案件欄の「効果効能は言い切らない」は pet-03 と同じ遵守の一文で、効能の断定ではない。

## pet-07 の「植物」「葉」

コマンド:

```
rg -n "植物|葉" affiliate-shorts/lines/20261026/pet-07.md
```

結果: 一致なし（出力なし）。0件。
