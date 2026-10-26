# pet-06〜08 作業報告（未投稿）

指示書 `cursor-inputs/20261026/03-pet-06-08.md` に沿って、10秒型の台本3本を書いた。投稿・ログイン・外部への送信はしていない。A8への広告掲載URLの提出もしていない。

## 書いたファイル
- `affiliate-shorts/lines/20261026/pet-06.md` … 木の床・黒猫・無地の紙袋
- `affiliate-shorts/lines/20261026/pet-07.md` … 出窓・サビ猫・緑の葉
- `affiliate-shorts/lines/20261026/pet-08.md` … 玄関・ハチワレ・空のスリッパ1足

型は `affiliate-engine/docs/grok-bots/research/kata/pet.md`（ブランチ `cursor/grok-bot-research-2026-08-26`）の型1。秒割りは 0.0–2.0 レンズを見る、2.0–6.0 で1歩、6.0–10.0 で鼻を1回寄せて止まる。カメラ固定。出典の映像とせりふは写していない。

既存と場面を重ねていない。pet-03 は皿、pet-04 はソファで丸くなる、pet-05 はソファで2匹、水を飲む場所の台本は蛇口・コップ・お風呂のふち・水の皿。この3本はどれも猫1匹で、それらの物は映さない。

音声は元音ミュート＋BGMだけ（声なし）。画面文字は、1秒目のテキストフック、0.0–2.0 の右上の小さい「PR」、10.0–12.0 のPR画面だけ。本編の字幕は置いていない。声のセリフは0本なので、セリフ間1.5秒の対象は無い。テキストフックの終わり（1.0秒）からエンドカード（10.0秒）までは9.0秒空く。本編字幕なしの指定なので、この間は字幕で埋めていない。

## 自己採点
- pet-06: 82（最初の3秒18、テンポ16、見やすさ18、プロフィールへの誘導14、壊れ16）
- pet-07: 82（同配点。理由は各ファイルの表）
- pet-08: 82（同配点。理由は各ファイルの表）

80未満は無い。直しは0周。直した点は各ファイルとも「なし。」時間の上限では止めていない。HANDOFF は作っていない。

## リンクの grep（pet-03 と完全一致）

コマンド:

```
rg -n "px\.a8\.net" affiliate-shorts/lines/20261026/pet-06.md affiliate-shorts/lines/20261026/pet-07.md affiliate-shorts/lines/20261026/pet-08.md cursor-inputs/20261026/pet/pet-03.md
```

結果:

```
cursor-inputs/20261026/pet/pet-03.md:94:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
cursor-inputs/20261026/pet/pet-03.md:97:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
affiliate-shorts/lines/20261026/pet-08.md:79:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
affiliate-shorts/lines/20261026/pet-08.md:82:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
affiliate-shorts/lines/20261026/pet-07.md:79:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
affiliate-shorts/lines/20261026/pet-07.md:82:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
affiliate-shorts/lines/20261026/pet-06.md:79:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok
affiliate-shorts/lines/20261026/pet-06.md:82:https://px.a8.net/svt/ejp?a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube
```

TikTok用は4本とも `a8mat=4BEAX1+9IZ8A+3J9O+1NJRXE&a8sns=tiktok`。YouTube用は4本とも `a8mat=4BEAX1+9J002+3J9O+1NJRXE&a8sns=youtube`。programId は pet-03 と同じ `s00000016494010`。

## 禁止語の grep

コマンド:

```
rg -n "効く|治る|予防|健康になる" affiliate-shorts/lines/20261026/pet-06.md affiliate-shorts/lines/20261026/pet-07.md affiliate-shorts/lines/20261026/pet-08.md
```

結果: 一致なし（出力なし）。

「健康」も3ファイルに無い。案件欄の「効果効能は言い切らない」は pet-03 と同じ遵守の一文で、効能の断定ではない。
