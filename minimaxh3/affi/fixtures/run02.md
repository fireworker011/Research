# アフィShorts run02｜オルビスユー ドット｜型: 「買う前に知っておきたい点」（合わない人を先に出す）
作成: 2026-10-03（JST）／担当: 台本係（新しいBotは作っていない）／投稿・購入・外部連絡・ファイル削除: していない／動画ファイル: 作っていない
読んだもの: `/workspace/affi-rules-20261003.md`（最優先）、`/workspace/affi-run-20261003/run01.md`（形式）、`/workspace/factory-3prod-2026-10-02/report.md`と`work/`（orbis_pool / orbis_measured / dates.tsv / measure.log）、`/workspace/affi-stock-20260930/stock.md`（§1の工場ルール、美容のstock-01/06/07/10/11）
作業ファイル: `/workspace/affi-run-20261003/work02/`（s.sh・pool.jsonl＝10/3の検索結果、src/＝オルビス公式ページ3枚の保存）

---

## 0. 入力（伸び動画の根拠）
### 前提: 10/2の「オルビスユー」O1〜O3は、ユー ドットではない
- 10/2のレポートの O1〜O3 は「オルビスユー」（別シリーズ）。ユー ドットの動画は「EB1AY704CPk（ユードット＝別シリーズなので対象外）」として表から外されていた。今回の商品はユー ドットなので、`work/` の測定データからユー ドットの動画だけを拾い直した。

### 直近（1年以内）: **未確認**
- やったこと（2026-10-03 09:50〜09:55ごろ JST）: yt-dlpで検索。「オルビスユードット」「オルビスユー ドット」「ユードット 化粧水」「オルビスユードット 使い方」「ユードット モイスチャー」の5語 × 3通り（通常／今年／再生数順）＝446件（重複を除くと146本）。
- 「今年」フィルターで出たユー ドットの動画は、かずのすけ ruOZX4rufjs（156,252回）と 評判ナビ 4BB3YLkp8As（563回）だけ。10/2の測定で普段の 0.88倍・1.79倍。**3倍以上は0本**。
- ユー ドットのShorts（3分以下）は、主婦の暇つぶし h0lMeh159yY（61秒・1,096回・1.77倍）、kM1HXF2IfDo（46秒・0.38倍）、悪魔の口コミ oOXZ22ILiVQ（15秒・85回）、Kyna awate6RuTkw（35秒・82回）だけ。どれも3倍に届かない。
- transcriptapi: 検索は「クレジット不足（有料プランが必要）」で使えなかった（run01と同じ）。購入は禁止なので、そこで止めた。無料のRSS（get_channel_latest_videos）だけ使った。
- ボットチェック: 出なかった（1本ずつの取得はしていない）。

### 参考（1年以上前）: 3倍以上はすべて同じチャンネル・同じ型
| # | URL | タイトル | 再生数 | 普段（中央値・本数） | 倍率 | 投稿日 |
|---|---|---|---|---|---|---|
| U1 | https://www.youtube.com/watch?v=EB1AY704CPk | 【見たらショックかも…】オルビス ユードット ローションの悪評／購入する前に【悪魔の口コミランキング】 | 3,788（10/2）→3,790（10/3） | 345.5（前後12本） | 10.96倍 | 2022-06-11 |
| U2 | https://www.youtube.com/watch?v=BhB99mRrsLo | 【見たらショックかも…】オルビス ユードット モイスチャーの悪評／購入する前に【悪魔の口コミランキング】 | 1,861 | 345.5（前後12本） | 5.39倍 | 2022-06-08 |
| U3 | https://www.youtube.com/watch?v=LiXHJ4JFs54 | 【見たらショックかも…】オルビス ユードット ウォッシュの悪評／購入する前に【悪魔の口コミランキング】 | 1,085 | 345.5（前後12本） | 3.14倍 | 2022-05-28 |
- 数字は10/2の測定（`factory-3prod-2026-10-02/work/orbis_measured.json`・`dates.tsv`）。10/3にチャンネルRSS（最新15本）を取り直した: 最新15本の中央値は338回で、U1は今も約11倍。チャンネルは2023-08-06以降、投稿なし。
- 普段との差: 同じ「◯◯の悪評／購入する前に」の型（他の回は38〜2,374回）の中で、ユー ドットの3本がそろって上にいる。型は同じで、違うのは**扱った商品**。10/2のO1（オルビスユー ローション 6.9倍）も同じ型。
- ただし同じチャンネルの「ドレスリフトローション」1r3fTCkfxzk も6,156回あり、商品名だけで決まるわけではない。どれも尺は4〜5分（243〜303秒）の解説動画で、検索から何年もかけて積み上がった数字。**Shortsで伸びた証拠ではない。**
- 他に再生数が多かった「ユー と ユー ドットの違い」型（かずのすけ 0.88倍、日本すっぴん協会 BF3rWX2965U 2.65倍）は3倍に届かず不採用。

### 借りた型・借りないもの
- 借りた型: 「**買う前に知っておきたい点**」。良い点を並べる前に「合わない人」を先に出す（10/2のO1の「真似してよい型」と同じ）。
- 借りないもの: 「悪評」「ショック」「知らないと危険」で不安をあおる言葉。他人の口コミの引き写し。「効かない／肌荒れする」のような逆向きの断定。チャンネルの映像・スライド。
- 合わない人として出すのは、**公式ページで確認できる事実1つ**（無香料）だけ。口コミや体験は使わない。

---

## フック1行
**香りが好きな人ほど、買う前に見て。**
（0秒から、サクラ本人が語り手。顔は sakura-ref.jpg だけ。新しい顔は作らない。手元だけのカットは無い。2026-10-03の共通点に合わせて直した。尺は15秒のまま。）

---

## 15秒台本
ナレーションは Gemini TTS Achernar を後から乗せる。字数は句読点なし、各行6.5字/秒以下（stock.md §1と同じ基準）。商品名は台詞・字幕とも0回。

| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | 香りが好きな人ほど、買う前に見て。 | 15 | 5.00 | 香りが好きな人ほど / 買う前に見て |
| 3.0-6.0 | 具体 | このシリーズは、無香料。 | 10 | 3.33 | このシリーズは / 無香料 |
| 6.0-10.0 | 具体 | 香りで癒されたい人には、物足りないかも。 | 18 | 4.50 | 香りで癒されたい人には / 物足りないかも |
| 10.0-12.5 | 誘導 | 香りより、うるおい重視の人に。 | 13 | 5.20 | 香りより / うるおい重視の人に |
| 12.5-15.0 | 誘導 | 紹介してるのは、プロフィールに。 | 14 | 5.60 | 紹介してるのは / プロフィールへ ▲ |

- 具体1つ＝「シリーズ全体が無香料」。出典: オルビス公式オンラインショップ ユー ドットシリーズのページ（https://www.orbis.co.jp/mid/915/ ）と エッセンスローションのページ（https://www.orbis.co.jp/small/11010752/ ）の「よくある質問 Q1. 無香料・無着色・アルコールフリーですか？ → はい、無香料、無着色、アルコールフリー、パラベンフリーです。」。2026-10-03 09:53 JST 取得（`work02/src/`）。ローション単体の欄にも「●無油分、無香料、無着色」。
- シリーズのFAQで確認できるので、A8のリンク先がローション単品でもシリーズでも同じ台詞で使える。
- 「うるおい」は公式の表示（保湿成分・うるおい充満ローション）の範囲。「うるおう／うるおいが続く」とは言わず、「うるおい重視の人に」と**選ぶ人の話**にとどめた。
- 字幕: 上部・白ボックス＋黒太字・差し色1語（0-3秒は「香り」、3-6秒は「無香料」、10-12.5秒は「うるおい」）。右上に小さく「PR」を全尺。字幕と台詞の差は12.5-15.0秒だけ（行き先をはっきりさせる）。

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344・サクラの顔）**: 0.0-3.0 夕方の部屋。サクラ（オートミール色のニット）が胸から上でカメラを見て話す。火のついた小さなアロマキャンドルは後ろのテーブルで小さく、手は枠の外 → 3.0-6.0 同じ顔のまま。眉を少し下げて首をかしげる。手元アップには切らない。ボトルは後ろのテーブルに小さく立っている
- **9sパート（6.0-15.0秒・640x1152・サクラの顔）**: 6.0-10.0 同じ顔。申し訳なさそうに小さく首をかしげる。ボトルは持たない。手は枠の外 → 10.0-12.5 同じ顔のまま。奥に水の入ったグラスが小さく見える。手は出さない。肌のアップも塗る場面も出さない → 12.5-15.0 正面でサクラがほほえんで止まる。指さしはしない

---

## 縦動画プロンプト
共通: 9:16、FL2VA（最初のコマ＝静止画、I2VAの指示文）、画面の文字なし（字幕・PRは編集で入れる）、H3の声は捨ててAchernarを乗せる。LoRAは両パートとも FL2V Turbo 8step 1.0 だけ（大きな動きがないのでCombatは使わない＝BUNNYのクレジットは不要）。人の顔はサクラだけ。サクラが出るパートは両方とも、最初のコマを `assets/character/sakura-ref.jpg`（箱の実ファイル: `/workspace/ai-short-video/assets/character/sakura-ref.jpg`）から作る（顔と髪だけ残して服と場所を替える＝stock.md §1と同じ）。新しい顔は作らない。

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・335語）
最初のコマの静止画（`sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Medium close-up from the chest up, vertical 9:16, a cozy room at dusk with warm lamp light and a softly blurred beige wall. Sakura wears a plain oatmeal-colored crew-neck knit sweater and looks into the camera, eyes gently closed, a calm closed-lip smile. A small lit candle in a clear unlabeled glass jar sits small on the table behind her. Hands out of frame. No other people, no hands, no new face, no text, no letters, no logos, no labels.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, warm dusk-lit vertical 9:16 skincare short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears, and no hands appear. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, in a plain oatmeal knit sweater, looks into the camera from the chest up, eyes closed, hands out of frame. A small lit candle in a clear unlabeled jar flickers on the table behind her, small in the frame. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 香りが好きな人ほど、買う前に見て。</d> while her lips remain completely closed. [Shot 2] At 00:03.000, the shot stays on Sakura's face. She opens her eyes, looks into the camera, lowers her brows a little and tilts her head. A slim frosted-white glass bottle with a plain white cap, completely free of any logo, label, or lettering, stands small on the table behind her. No hand enters. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] このシリーズは、無香料。</d> while her lips remain completely closed.

overall_soundscape: Quiet indoor room tone at dusk with the faint crackle of a small candle flame behind Sakura.

non_diegetic_music: A gentle, slow felt-piano motif with soft warm pads, thinning to a single sustained note as the flame goes out at about 00:04.500.
```
#### 9sパート（FL2VA・9.00秒・640x1152・397語）
最初のコマの静止画（`sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Frontal medium close-up, vertical 9:16, the same cozy room at dusk with warm lamp light and a softly blurred beige wall. Sakura in a plain oatmeal-colored crew-neck knit sweater looks into the camera with slightly lowered brows and an apologetic closed-lip smile. Hands out of frame. A slim frosted-white unbranded bottle stands small on the table behind her. No other people, no hands, no new face, no text, no logos, no label on the bottle.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, warm dusk-lit vertical 9:16 skincare short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears, and no hands appear. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, in a plain oatmeal knit sweater, looks into the camera from the chest up, hands out of frame. Her brows lower a little and she tilts her head slightly, never touching her face. A slim frosted-white bottle with a plain white cap, free of any logo or lettering, stays small on the table behind her. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 香りで癒されたい人には、物足りないかも。</d> while her lips remain completely closed. [Shot 2] At 00:04.000, the shot stays on Sakura's face. A clear glass of water sits small and soft behind her. No hand enters. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 香りより、うるおい重視の人に。</d> while her lips remain completely closed. [Shot 3] At 00:06.500, Sakura looks directly into the camera with a gentle closed-lip smile and holds still until the final frame. She does not point. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるのは、プロフィールに。</d> while her lips remain completely closed.

overall_soundscape: Quiet indoor room tone at dusk. No object handling.

non_diegetic_music: The same slow felt-piano motif with soft warm pads at a steady tempo, ending on a gentle two-note tag in the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, real ORBIS bottle shape, celebrity, real person likeness, extra people, new human faces, face change between shots, distorted hands, extra fingers, lip-sync mouth movement, open mouth talking, horizontal video, black bars, slideshow, flicker, applying product to face, skin close-up, before and after comparison, pores, wrinkles, blemishes, spots, rash, redness, sniffing the bottle, perfume spray, flowers bouquet, fire hazard, large flames

### Imagine用（短い1本・9:16・10秒）
```text
Vertical 9:16, 10 seconds, photoreal. Reference: sakura-ref.jpg (keep only Sakura's exact face, long straight dark-brown hair and bangs; change clothes and place). In a cozy room at dusk with warm lamp light, Sakura in a plain oatmeal knit sweater looks into the camera from the chest up, eyes closed, then opens them with a soft closed-lip smile. A small unlabeled candle and a slim frosted-white unbranded bottle stay small on the table behind her. Hands stay out of frame. Slow push-in. No other people, no hands, no new face, no text, no logos, no labels.
```
（6sパートと9sパート頭の場面を1本にした差し替え用。セリフは入れない＝Achernarを後乗せ）

---

## タイトル
`香りが好きな人ほど、買う前に。オルビスユー ドット #Shorts #スキンケア #化粧水`
- 商品名はタイトルだけ（動画内0回）。run01の直す点3と同じ扱い（検索で最初に読まれるのはタイトル／U1〜U3もタイトルに商品名）。
- 「悪評」「ショック」は入れない。

## 概要欄
```text
アフィリエイト広告を含みます #PR
買う前に知っておきたいことを1つだけ。このシリーズは無香料です。香りで癒されたい人には物足りないかもしれません。
「無香料・無着色・アルコールフリー・パラベンフリー」はメーカー公式ショップのよくある質問で確認しました（2026年10月3日時点）。最新の表示は販売ページでご確認ください。
使った感想ではありません。肌に合うかどうかには個人差があります。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #スキンケア #化粧水 #無香料 #スキンケア選び

映像・ナレーションはAIで生成しています。映像の人物はAIのキャラクター、ボトルはAIで作ったイメージで、実際の商品やパッケージとは異なります。
```

### 注意点（法務・投稿前の確認）
- この商品は医薬部外品（公式表示）。台詞・字幕・概要欄で、美白・シミ・ハリ・エイジングケア・浸透・有効成分の話はしない（承認の範囲や注記の付け方を間違えやすいので、今回は使わない）。言うのは「無香料」という表示の事実と、「うるおい重視の人に」という選ぶ人の話だけ。
- 「治る」「必ず」「改善」「肌が変わる」は書いていない。逆向きの断定（「合わない」「荒れる」）も書かない。「物足りないかも」は香りの好みの話にとどめた。
- サクラは塗らない・においをかがない・肌のアップを出さない。手元だけのカットも指さしもしない。キャンドルは「香り」のイメージで、商品の香りではない。顔は sakura-ref.jpg だけ。新しい顔は作らない。
- ボトルはロゴなしのすりガラス。実物の容器や他社製品に似せない。
- ストックとのかぶり: stock-01（つっぱり・夜の洗面所）、06（選び方の街頭）、07（何から始める）、10（朝の時短）、11（あるある）とはテーマが別。サクラ＋すりガラスのボトル＋人差し指で上を指す締めは01/07と同じ絵なので、続けて投稿しないほうがいい。
- ジャンル: 美容だけ（ペット・婚活の要素なし）。美容とペットでアカウントを分ける場合は美容側。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。収入の数字・LINEなし。

---

## 採点
**判定: 使える**（投稿するかは人間が決める）
- 理由（短く）: 具体の「無香料」はシリーズ全体の公式表示で、A8のリンク先がローション単品でもシリーズでも崩れない。効能を一切言わないので、医薬部外品でもリスクが小さい。弱いのは、型の根拠がすべて2022年の長い動画（Shortsで伸びた証拠なし）なこと。

| 項目 | 点 | 理由 |
|---|---|---|
| 最初3秒 | 14 | 「買う前に見て」と対象の名指しで止める力はある。ただし「香りが好きな人」が刺さる層の広さは未確認。直近のShortsで同じ型が伸びた例は未確認 |
| テンポ | 15 | 切り替えは3.0／4.5（炎が消える）／6.0／10.0／12.5秒。3-6秒の台詞が3.33字/秒とゆっくりで、間延びしやすい（炎が消える動きで埋める） |
| 見やすさ | 15 | 字幕は2行・短い・上部固定、画面の文字なし、差し色1語。動画は未生成なので、サクラの顔の一致・手の崩れ・スナッファーの動きの見え方は不明 |
| プロフィール誘導 | 15 | 10-15秒で「うるおい重視の人に→紹介してるのはプロフィールに」とつながる。ただし「なぜ見に行くか」の理由はrun01（原材料を見に行く）より弱い |
| リスク | 17 | 効能ゼロ・体験の偽装なし・PR/AI明記・商品名0回。残るのは「物足りないかも」を否定的なレビューと受け取られる可能性と、医薬部外品の表示を投稿前に見直すこと |
| **合計** | **76** | |

- この採点は台本係の自己採点（動画は未生成）。run01と同じ物差しで付けた。動画ができたら採点係が付け直す。
- 数字は実測だけ（倍率・再生数は10/2の測定ファイルと10/3のyt-dlp検索・チャンネルRSS、無香料は10/3保存の公式ページ）。

### 残る「不明」
- 直近1年のユー ドットの伸び動画（普段の3倍以上）: **不明（未確認）**。transcriptapiはクレジット不足で使えず、yt-dlpの検索では0本。
- A8のリンク先が、ローション単品・シリーズ・お試しセットのどれか: **不明**（2026-10-03の実測は「オルビスユー ドット s00000008657021 提携中」だけで、リンク先URLの記録はない）。台詞はシリーズ全体の事実なので、どれでも使える想定。
- 動画にしたときの見え方（サクラの顔の一致・手）: **不明**（動画は作っていない）。

---

## 完了条件
**完了条件4つ（フック1行／15秒台本／縦動画プロンプト／採点）はすべて揃った（判定は「使える」。連続完了 2/3）。**
