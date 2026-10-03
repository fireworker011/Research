# アフィShorts run01｜ドッグフード「おさかな」｜型: 商品名をタイトルに入れた「紹介」（D1の直し）
作成: 2026-10-03（JST）／担当: 台本係（新しいBotは作っていない）／投稿・購入・外部連絡・ファイル削除: していない
読んだもの: `/workspace/affi-rules-20261003.md`（最優先）、`/workspace/factory-3prod-2026-10-02/report.md`と`work/`、`/workspace/affi-stock-20260930/stock.md`（§1の工場ルールの当てはめ方、stock-02/05の書式）、`src/kanetora_202.html`・`src/kanetora_lp.html`（9/30に保存した金虎ショップの公開ページ）
作業ファイル: `/workspace/affi-run-20261003/work/`（s.py・s2.py・r.py、pool.json・pool2.json・cands2.json・rss_check.json、rss/）

---

## 0. 直す点3つの結果
### 直す点1：根拠が2022年で、直近の伸びが未確認 → **直近は未確認。D1は参考扱い**
- やったこと（2026-10-03 09:45〜10:05ごろ JST）
  - yt-dlpで検索：「おさかな ドッグフード」「犬 魚 ごはん」「ドッグフード 魚」「犬 お魚 ごはん」「金虎 おさかな」「犬 魚 フード」。Shortsフィルター付きの検索は、ほぼ0件（6語で計16件、ほとんどが関係ない子ども向け動画）。フィルターなしの検索（5語×60件＝251件）で取り直した。
  - そこから「3分以下・日本語・犬が題材」の46本にしぼり、公式・販売店・メーカー（POCHI公式、ドットわん、Bowls Fresh公式、ドッグダイナー、機械メーカーなど）は外した。
  - 投稿日と普段の数字は、チャンネルのRSS（最新15本）で確認。RSSに入っていない動画は、そのチャンネルの最新15本より古い。
  - 倍率が高く見えた Office Guri の4本（RXjs170Q9KY 9,080回・JoLlaB3q-ok・85KTpaK4MpA・yMy1Un6jMn8）は1本ずつ投稿日を取った → 2015〜2021年で対象外。
- 結果
  - 直近1年の可能性がある動画で、普段（RSSの他の動画の中央値）の3倍以上は **0本**。いちばん近かったのは「ニュース」1qCby7W2xGY『ドッグフードおさかな』（11回／中央値4回＝2.75倍。5秒で中身が薄い）と、帝塚山ハウンドカム CKdwkoVwS9k（473回／233回＝2.03倍。手作りごはんの動画で商品と関係なし）。ほかは0.05〜0.68倍。
  - 10/2の調査の TsX2u94TWYg（2.7倍）も3倍に届いていないまま。
  - → **直近は未確認。D1（Xl7McNrgODg・23.8倍・2022-05-14）は参考扱い**にした。D1は検索で何年もかけて積み上がった数字で、Shortsで伸びた証拠ではない。
- ボットチェック: 出なかった（1本ずつの取得は4本だけ）。
- transcriptapi: 「クレジット不足（有料プランが必要）」で使えなかった。購入は禁止なので、そこで止めた。
- 限界: 普段の数字は、RSSの最新15本（長い動画とShortsが混ざる）の中央値で見た簡易版。この日は「今年」フィルターがうまく効かず、直近のShortsを探しきれたとは言えない。

### 直す点2：AIの犬に「食べた」と見せると体験の偽装になる → **「紹介」の形にした**
- 台詞・字幕・映像のどれでも、犬が食べる・においをかぐ・舌なめずりする・食いつく様子は出さない。犬は器の後ろに座って、カメラを見るだけ。
- 「うちの子が食べた」「よく食べる」「大好き」は言わない。言うのは、メーカーの公開ページで確認できた事実1つ（鰹節メーカーが作っている／原材料の先頭が魚介類）だけ。
- 誘導は「紹介してるごはん」（stock.md §1と同じ）。概要欄にも「食べた感想ではありません」と書いた。

### 直す点3：商品名は動画内で0回 → **タイトルに入れた**（概要欄には入れない）
- 理由1: D1と他の伸びた例（D2・D3）で、普段と違ったのは「タイトルに『おさかな』が入っていること」だけ。検索とおすすめ欄で最初に読まれるのはタイトル。
- 理由2: 動画内0回（台詞・字幕・パッケージに文字なし）の工場ルールは、そのまま守れる。
- 理由3: 1か所にしておくと、商品名の表記をあとで直すときに1か所で済む。概要欄は「鰹節屋さんが作ったドッグフード」と原材料の事実だけにした。

---

## フック1行
**鰹節屋さんが、犬のごはんを作ったら。**
（0秒から、鰹節を削る手元のアップ。「誰が作ったか」を一言で出す型＝D3の「メーカー名を一言添える」を、名前を出さずに使った）

---

## 15秒台本
ナレーションは Gemini TTS Achernar を後から乗せる。字数は句読点なし、各行6.5字/秒以下（stock.md §1と同じ基準）。商品名は台詞・字幕とも0回。

| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | 鰹節屋さんが、犬のごはんを作ったら。 | 16 | 5.33 | 鰹節屋さんが / 犬のごはんを作ったら |
| 3.0-6.0 | 具体 | 原材料の先頭は、お魚。 | 9 | 3.00 | 原材料の先頭は / お魚 |
| 6.0-10.0 | 具体 | お魚は、まぐろ、かつお、かつお節など。 | 15 | 3.75 | まぐろ・かつお / かつお節など |
| 10.0-12.5 | 誘導 | 紹介してるごはんの原材料は、 | 13 | 5.20 | 紹介してるごはんの / 原材料は |
| 12.5-15.0 | 誘導 | プロフィールから、どうぞ。 | 11 | 4.40 | 紹介ページは / プロフィールへ ▲ |

- 具体1つ＝「原材料の先頭が魚介類（まぐろ、かつお、かつお節…）」。出典: 金虎ショップ（メーカー公式通販）の商品ページとLP、2026-09-30 11:03 JST 取得（`/workspace/affi-stock-20260930/src/`）。原材料欄は『魚介類（まぐろ、かつお、かつお節、かつおエキス）、でん粉類…』。「鰹節屋さん」は同ページの『大正二年創業の老舗鰹節メーカー』から。
- 「など」を付けたのは、魚介類の中に「かつおエキス」もあり、全部は言っていないため。
- 字幕: 上部・白ボックス＋黒太字・差し色1語（0-3秒は「鰹節屋さん」、3-6秒は「お魚」）。右上に小さく「PR」を全尺。字幕と台詞の差は12.5-15.0秒だけ（字幕で行き先をはっきりさせる）。

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344・犬なし）**: 0.0-3.0 マクロ。白い作業着の袖の手が、木の削り箱で鰹節を削る。薄い削り節がくるっと丸まって落ちる（顔は映らない） → 3.0-6.0 真上からの手元アップ。クリーム色ニットの袖の手が、ロゴなしのクラフト紙パウチ（青い魚のシルエットだけ）を裏返し、ぼかした読めない表示の「いちばん上の行」を人差し指で指す
- **9sパート（6.0-15.0秒・640x1152・犬あり）**: 6.0-10.0 少し上から。木の床に白いトレー、小皿3つ（加熱したまぐろの角切り／加熱したかつおの切り身／削り節）と、金色の粒が入った白い器。後ろに同じ犬が落ち着いて座っている。カメラは小皿の上を左から右へゆっくり動く → 10.0-12.5 手がパウチを器の横に置き、引っ込む。犬は座ったまま → 12.5-15.0 犬がカメラを見上げて首をかしげ、そのまま止まる。ごはんには最後まで口をつけない

---

## 縦動画プロンプト
共通: 9:16、FL2VA（最初のコマ＝静止画、I2VAの指示文）、画面の文字なし（字幕・PRは編集で入れる）、H3の声は捨ててAchernarを乗せる。LoRAは両パートとも FL2V Turbo 8step 1.0 だけ（大きな動きがないのでCombatは使わない＝BUNNYのクレジットは不要）。犬は stock.md §1 と同じ生成犬1匹で、犬が出る9sパートは最初のコマを必ず `dog-ref.jpg` から作る。6sパートは犬が出ないので参照なし（stock-06/11と同じZ-Image-Turbo扱い）。

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・307語）
最初のコマの静止画（参照なし・犬も人の顔も出さない）:
```text
Photoreal still, vertical 9:16, macro close-up on a wooden workbench in a small traditional workshop. Two hands in plain white work-coat sleeves, face out of frame, push a dark, hard dried bonito block (katsuobushi) across the blade of a traditional wooden shaving box; thin translucent pale-pink flakes curl up from the blade. Warm side light, fine dust in the air, shallow depth of field. No people's faces, no text, no letters, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, warm natural-light vertical 9:16 pet food short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>, a macro close-up on a wooden workbench: two hands in plain white work-coat sleeves push a dark, hard dried bonito block across the blade of a traditional wooden shaving box in two slow, steady strokes, and thin translucent pale-pink flakes curl up and tumble onto the wood. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 鰹節屋さんが、犬のごはんを作ったら。</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the shot cuts to a high-angle close-up on a light wooden kitchen table, the person's face out of frame: a woman's hands in cream knit sleeves turn a plain matte kraft-paper stand-up pouch printed only with a simple blue fish silhouette, with no letters, numbers, or logos over to its back panel, which shows only soft blurred, unreadable grey lines; her index finger comes to rest on the very first line at the top. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 原材料の先頭は、お魚。</d> while no lips are visible on screen.

overall_soundscape: Quiet workshop room tone with the dry, rhythmic rasp of the shaving blade and flakes rustling onto the wood, then a soft kitchen ambience and the crinkle of the paper pouch being turned over.

non_diegetic_music: A light koto-like plucked motif at a slow-moderate tempo with soft hand percussion, opening into a brighter chord at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・420語）
最初のコマの静止画（`dog-ref.jpg` を元に作る）:
```text
Photoreal edit using dog-ref.jpg: keep exactly the same dog (the same medium-sized adult Japanese-style dog with a short reddish-fawn coat and cream-white markings, upright triangular ears, curled tail, face and plain red collar) and change only its pose and the scene. Photoreal still, vertical 9:16, slightly high angle over a light wooden floor, soft window light. In the foreground a white rectangular tray holds three small white dishes in a row: a cube of cooked tuna, a slice of cooked bonito, and a small mound of pale bonito flakes; beside the tray a white ceramic bowl of small round golden kibble. The same dog sits calmly behind them, looking at the camera, mouth closed. No people, no text, no letters, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, soft natural-light vertical 9:16 pet food short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>, a slightly high angle over a light wooden floor: a white tray with three small white dishes in a row, a cube of cooked tuna, a slice of cooked bonito and a small mound of pale bonito flakes, beside a white ceramic bowl of small round golden kibble. The same medium-sized adult Japanese-style dog from <Picture 1>, with a short reddish-fawn coat, cream-white muzzle and chest, upright triangular ears, a tail curled over its back and a plain red collar sits calmly behind them with its mouth closed and does not move toward the food. The camera glides slowly from left to right along the three dishes. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] お魚は、まぐろ、かつお、かつお節など。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the shot cuts to a closer high angle on the bowl: a woman's hand in a cream knit sleeve, her face out of frame, sets a plain matte kraft-paper stand-up pouch printed only with a simple blue fish silhouette, with no letters, numbers, or logos upright beside the bowl and withdraws out of frame; the dog stays seated in the soft background. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるごはんの原材料は、</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the shot cuts to a slightly high angle on the dog: it looks straight up into the camera and slowly tilts its head to one side, the bowl and dishes untouched in front of it, holding the pose until the final frame. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] プロフィールから、どうぞ。</d> while no lips are visible on screen.

overall_soundscape: Quiet room ambience with soft daylight, a faint tap as the pouch is set down on the wooden floor, a light rustle of the knit sleeve and the dog's calm breathing.

non_diegetic_music: The same koto-like plucked motif with soft hand percussion at a steady tempo, ending on a gentle two-note tag in the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog eating, dog sniffing food, dog licking lips, drooling, dog changing breed or color between shots, extra dogs, dog with human expression, raw fish gore, vomiting, sick animal, vet clinic

### Imagine用（短い1本・9:16・10秒）
```text
Vertical 9:16, 10 seconds, photoreal. Reference: dog-ref.jpg (keep the exact same dog). The dog sits calmly on a light wooden floor behind a white tray with three small dishes — a cooked tuna cube, a cooked bonito slice, pale bonito flakes — and a white bowl of golden kibble. The dog does not eat or sniff; it looks up at the camera and slowly tilts its head. Slow push-in, soft window light. No people, no text, no logos.
```
（9sパートの絵と同じ場面。H3が使えないときの差し替え用。セリフは入れない＝Achernarを後乗せ）

---

## タイトル
`鰹節屋さんのドッグフード「おさかな」 #Shorts #ドッグフード #犬のごはん`
- 商品名はここだけ（動画内0回・概要欄にも入れない）。理由は「0. 直す点3」のとおり。

## 概要欄
```text
アフィリエイト広告を含みます #PR
鰹節屋さんが作ったドッグフードの紹介です（食べた感想ではありません）。
原材料の先頭は魚介類（まぐろ、かつお、かつお節、かつおエキス）。メーカー公式ショップの表示で確認しました（2026年9月30日時点）。最新の表示は販売ページでご確認ください。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #ドッグフード #犬のごはん #犬のいる暮らし

映像・ナレーションはAIで生成しています。映像の犬・食材・パッケージはAIで作ったイメージで、実際の商品やパッケージとは異なります。
```

### 注意点（法務・投稿前の確認）
- **A8の提携先が金虎の「おさかな」かどうか: 不明。** /workspace 内にA8のおさかなのリンク記録が見つからなかった（stock.md 9/30時点と同じ）。台本の具体（鰹節屋さん・原材料）は金虎の公式ページの事実なので、提携先が別の商品なら3-10秒とタイトルは使えない。投稿前に人間が照合する。
- 健康効果・アレルギー・食いつき・好き嫌いは言わない（「アレルギーに配慮」「食物アレルギー対策」「よく食べる」は書かない。公式ページにある「小麦・卵・乳・肉を入れないライン」の話も、アレルギーの訴求に読めるので使わない）。
- 映像の小皿（まぐろ・かつお・削り節）は「原材料の魚」を見せるイメージで、商品の中身そのものではない → 概要欄にAIのイメージと明記した。犬は食べない・においをかがない（ネガティブにも入れた）。
- 鰹節を削る手元は「鰹節屋さん」のイメージ。メーカーの工場や職人の映像ではない（実在の工場・人に似せない）。
- stock-05（比較・選び方の一般論「先頭がお魚ならお魚が主役」）と、テーマの「原材料の先頭」が近い。続けて投稿しないほうがいい（間を空けるか、どちらか一方にする）。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---

## 採点
**判定: 直す**
- 理由（短く）: 前回の直す点3つは片づいた（直近の根拠を探し直した→未確認で参考扱いにした／「紹介」に変えた／商品名はタイトル）。残りは1つで、**A8の提携先が金虎「おさかな」かどうかが不明**。具体の台詞とタイトルがその商品の事実に乗っているので、照合できれば「使える」、別の商品なら3-10秒を書き直す。直近の伸びの根拠が無い（D1は参考）ことも点を下げている。

| 項目 | 点 | 理由 |
|---|---|---|
| 最初3秒 | 15 | 「鰹節屋さんが犬のごはんを？」で意外性はある。ただし0秒に犬の顔が無い（ペットのShortsでは弱くなりうる）。直近で伸びた同じ型の例は未確認 |
| テンポ | 15 | 切り替えは3.0／6.0／10.0／12.5秒。3-10秒の台詞が3.0〜3.75字/秒とゆっくりで、間延びしやすい |
| 見やすさ | 15 | 字幕は2行・短い名詞・上部固定。画面の文字なし。動画は未生成なので、実際の見え方（犬の一致・手の崩れ）は不明 |
| プロフィール誘導 | 16 | 10-15秒で「紹介してるごはんの原材料は→プロフィールから」と行き先と理由がつながっている。字幕に▲ |
| 規約 | 15 | PR表記・AI明記・商品名0回・体験の偽装なし・効果の断定なし。ただしA8の提携商品と未照合（投稿前に必須） |
| **合計** | **76** | |

- この採点は台本係の自己採点（動画は未生成）。採点係の5項目と同じ物差しで付けた。動画ができたら採点係が付け直す。
- 数字は実測だけ（倍率・再生数はyt-dlpとRSSで2026-10-03に取得、原材料は9/30保存の公式ページ）。

---

## 完了条件
**完了条件4つ（フック1行／15秒台本／縦動画プロンプト／採点）はすべて揃った（判定は「直す」。連続完了 1/3）。**

## A8提携確認（2026-10-03 09:49 JST 実測）
- 株式会社金虎 ドッグフードおさかな s00000022193001 提携中 https://www.kanetora-shop.jp/lp?u=osakana_2_a8_blg_ad11_1
- オルビス オルビスユー ドット s00000008657021 提携中
- Tomofun Furbo 360°ビュー s00000017737001 提携中
→ 不明だった1点は解消。判定：使える（連続完了 1/3）
