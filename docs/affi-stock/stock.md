# アフィShorts 台本ストック 10本（MiniMax H3 一括生成用）
作成: 2026-09-30（JST） / 保存先: `/workspace/affi-stock-20260930/`（この `stock.md` と `h3_batch.json`。生成元 `stock_data.py`→`build.py`）

> **H3の生成・投稿はしていない。** `orbis01_h3_prompts.md` の注記どおり、H3は人間のOKが出てから回す。

## 0. 前提（読んだもの）
- `affi-h3-research-20260929/orbis01_h3_prompts.md`（1本目の正本）、`report.md`（型の分解 V1〜V9・作り直し案 R1〜R9）、`channels_report.md`（成功/失敗の共通点・やること/やらないこと）、`caption_narration_report.md`（字幕の差）、`post/`（タイトル・概要欄・Achernar の実測）。
- GitHub `fireworker011/Research`: ブランチ `cursor/h3-fast-fl2va-lora-6dc5` の `h3-runner/README.md`（FL2VA 6秒+9秒・Turbo・Combat/Repair LoRA）、`.cursor/skills/h3-prompt-writing/`（`references/base-en.txt`）、`.cursor/skills/h3-lora-studio/SKILL.md`。
- 「research フォルダ」: main にも FL2VA ブランチにも `research/` は無かった。全111ブランチを調べて `research/` があったのは `cursor/tomo-shorts-edit-memo-66cf` だけで、中身は tomo（CW案件）の編集手順1本（アフィの勝ち型ではない）。勝ち型は箱の `affi-h3-research-20260929/report.md`・`channels_report.md` を使った。

## 1. 工場ルールの当てはめ方（全10本共通）
- 15秒 = **6秒パート（0.0-6.0）＋9秒パート（6.0-15.0）**。0-3秒フック / 3-10秒具体1つ / 10-15秒プロフィール誘導。
- H3 は **FL2VA**（最初のコマ＝静止画）。最後のコマは渡さない運用なので、プロンプト1行目は `base-en.txt` の I2VA の指示文（最初のコマだけ固定）にした。
- **サクラの顔が出るパートは、最初のコマにサクラの顔を入れる**（最初のコマ以外では顔を固定できない。途中から顔が出るとサクラと別人になりうる）。顔が要らないパートは手元・物・犬だけの静止画から始める。
- 最初のコマの静止画: サクラ入りは `sakura-ref.jpg`（着物・夜景）から**顔と髪だけ残して服と場所を替える**（orbis01 と同じ扱い）。新しい人の顔は作らない。街頭は肩から下・後ろ姿・手元・スマホ画面だけ。
- 犬は3商品共通の**同じ生成犬**（クリーム色のふわふわ・赤い首輪。report.md §3 の指定）。犬の参照画像はまだ無い → 最初の1枚を作ったら、以後の犬入り静止画はそれを元に作る（ずれ対策）。
- 画面の文字は H3 に描かせない（プロンプトに no text）。字幕・PR表記・『街頭インタビュー風の演出です』は編集で入れる。字幕は上部・白ボックス＋黒太字・差し色1語（caption_narration_report.md の差があった3点）。右上に小さく「PR」を全尺。
- ナレーション: **Gemini TTS Achernar**（落ち着いた大人の女性）を後乗せ。H3 の声は捨てる。速さは Achernar 実測 6.40字/秒（wav全長）・6.65字/秒（発話区間、atempo 1.1）なので、**各行 6.5字/秒以下**にした（build.py で検査済み）。BGM と環境音は全尺で鳴らし、無音区間を作らない。
- 商品名は**動画内0回**（台詞・字幕とも。build.py で検査）。商品はロゴなしの形だけ（ボトル・魚シルエットのパウチ・白い見守りカメラ）。収入・LINE・転職ネタなし。
- 体験のでっち上げを避けるため、誘導は「使ってるもの」ではなく **「紹介してるもの」**。失敗談は「よくある失敗」、街頭の答えは「心配ごと」だけ（商品の感想は言わせない）。
- LoRA: 全パート **FL2V Turbo 8step 1.0**。動きが大きいパートだけ **Combat BASE V2 0.7 ＋ Motion Continuity Repair V2 0.6**（README の比較テスト C/D 構成。質はまだ未確認）。使ったら概要欄に BUNNY（FourBunny）のクレジット。
- ネガティブ: h3-lora-studio の SKILL.md に「negative は文書用（CFG なし。除外は正の文に書く）」とあるので、除外したいもの（文字・ロゴ・他の顔）はプロンプト本文にも書いた。ネガティブ欄は ComfyUI 等で使う場合のメモ。
- 概要欄: 先頭「アフィリエイト広告を含みます #PR」、末尾「映像・ナレーションはAIで生成しています。」。

## 2. 一覧（型の網羅）
| ID | 投稿順 | 商品 | 型 | ルート | フック（0-3秒） | 台詞の字数 | Combat LoRA |
|---|---|---|---|---|---|---|---|
| stock-01 | Day 1 | オルビスユー（化粧水） | 悩み→解決 | キャラ喋り（サクラ） | お風呂上がり、顔がつっぱる？ | 65字 | — |
| stock-02 | Day 2 | ドッグフードおさかな | あるある共感 | キャラ喋り（サクラ・声のみ／手元） | 寝てたのに、袋の音で起きる子。 | 64字 | 6s |
| stock-03 | Day 3 | Furbo（ペット見守りカメラ） | 留守番カメラの一瞬1カット（意外な反応にツッコむ） | キャラ喋り（サクラ・声のみ）＋見守りカメラ映像風 | 見守りカメラに、まさかの一瞬が。 | 65字 | 9s |
| stock-04 | Day 4 | オルビスユー（化粧水） | ビフォーアフター風（朝の支度の変化・効果断定なし） | キャラ喋り（サクラ） | 朝のスキンケア、並べすぎてない？ | 62字 | — |
| stock-05 | Day 5 | ドッグフードおさかな | 比較（選び方） | キャラ喋り（サクラ・声のみ／手元） | お肉とお魚、どっちにする？ | 70字 | — |
| stock-06 | Day 6 | Furbo（ペット見守りカメラ） | 街頭インタビュー風 | 街頭インタビュー風（顔なし・手元と後ろ姿） | 犬の留守番、何が心配ですか？ | 69字 | — |
| stock-07 | Day 7 | オルビスユー（化粧水） | 悩み→解決（別の切り口・お悩みカード返信型） | キャラ喋り（サクラ） | スキンケア、何から始めればいい？ | 76字 | — |
| stock-08 | Day 8 | ドッグフードおさかな | 失敗談→気づき（よくある失敗として） | キャラ喋り（サクラ・声のみ／手元） | ごはんの切り替え、一気にやってない？ | 72字 | — |
| stock-09 | Day 9 | Furbo（ペット見守りカメラ） | 静かなケア日常観察 | キャラ喋り（サクラ）＋見守りカメラ映像風 | お風呂のあと、大人しく拭かせてくれる子。 | 74字 | — |
| stock-10 | Day 10 | オルビスユー（化粧水） | 時短比較（朝の工程を1本にまとめる・分割画面） | キャラ喋り（サクラ） | いつもの朝と、1本の朝。工程を比べる。 | 75字 | — |

配分: オルビスユー4本（01/04/07/10）、ドッグフードおさかな3本（02/05/08）、Furbo 3本（03/06/09）。
2026-09-30 の実測監査（`/workspace/buzz-research-affi-stock-audit-20260930.md`）を受けて、stock-03（ストーリー：2本・倍率中央値0.3）と stock-09（Q&A：4本・0.9、2025-26年の動画なし）を入れ替えた。新しい型は『留守番カメラの一瞬1カット』（参考 Swt-8_hj_pc 44.0倍）と『静かなケア日常観察』（参考 biBzOuRiAGY 83.6倍）。ふつうの留守番の様子は34本で中央値0.2倍なので、stock-03 は一瞬の出来事1つに絞った。どちらも強い1本が引っぱっている型で、同じ型のほかの動画は伸びていない（監査の注意どおり、型を変えれば伸びるとは言い切れない）。
同じ監査で、開封・使ってみたレビューは中央値0.8倍、3選は強いのが2021年の1本だけだったので、stock-07（開封）と stock-10（3選）も入れ替えた。stock-07 は『悩み→解決』の別の切り口（お悩みカード返信型。参考 Ir0VlXFSjyk 22.5倍・2026-08。stock-01 とは場面も悩みも別）、stock-10 は『朝の工程を1本にまとめる時短比較』（参考 iVCAQLUhCdo 300.2倍）。**iVCAQLUhCdo は2023年の動画なので、この形式が今も伸びる証拠はない。** stock-10 で変わるのは工程の数と時間（手数）だけで、肌の比較・効能・実測していない時間の数字は出さない。
投稿順は美容→ペット→ペットの順に回す。`channels_report.md` の『やること7』は美容とペットでアカウントを分けるのが望ましいとしている。分ける場合、美容は Day1・4・7・10、ペットは残りの日の順で使う。

---
## stock-01｜オルビスユー（化粧水）｜型: 悩み→解決
- 想定投稿順: **Day 1** / ルート: キャラ喋り（サクラ） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | お風呂上がり、顔がつっぱる？ | 12 | 4.00 | お風呂上がり / つっぱる？ |
| 3.0-6.0 | 具体 | 急いで、何本も重ねてない？ | 11 | 3.67 | 急いで / 何本も重ねてない？ |
| 6.0-10.0 | 具体 | 化粧水を手のひらで温めて、そっと押さえるだけ。 | 21 | 5.25 | 手のひらで温めて / そっと押さえる |
| 10.0-12.5 | 誘導 | 夜は、この1本から。 | 8 | 3.20 | 夜は / この1本から |
| 12.5-15.0 | 誘導 | 紹介してるのは、プロフィールに。 | 13 | 5.20 | 紹介してるのは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 夜の洗面所。鏡の前のサクラ（グレーの部屋着）が頬に触れ、少し眉を寄せる → 3.0-6.0 手元のアップ。洗面台に並んだロゴなしボトル5〜6本を手でよけ、すりガラスのボトル1本だけ残す（顔は映らない）
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 暖かい灯りの洗面所。サクラが胸の高さでボトルを傾け、手のひらに透明な化粧水 → 両手で頬をそっと包む（目を閉じる） → 10.0-12.5 手を下ろして肩の力が抜ける → 12.5-15.0 カメラ目線でほほえみ、人差し指で画面の上を指す

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・312語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Medium close-up, vertical 9:16. She stands at a white bathroom sink at night in front of a mirror, wearing a plain soft light-grey long-sleeve lounge top with a closed round neck, fingertips lightly touching her left cheek, slight worried frown. Warm dim vanity light, a little steam in the air, shallow depth of field. No text, no logos, no accessories.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, soft warm-lit vertical 9:16 skincare short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, stands at a white bathroom sink at night in a plain light-grey lounge top, fingertips on her left cheek. She presses the cheek lightly twice and her brows draw together slightly as faint steam drifts past the mirror. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] お風呂上がり、顔がつっぱる？</d> while her lips remain completely closed. [Shot 2] At 00:03.000, the shot cuts to a high-angle close-up of the sink counter, her face out of frame: five or six unbranded bottles and jars of different shapes stand crowded together. Her hand in a light-grey sleeve slides them aside one by one until only a slim frosted-white glass bottle with a plain white cap, completely free of any logo, label, or lettering remains in the center. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 急いで、何本も重ねてない？</d> while no lips are visible on screen.

overall_soundscape: Quiet bathroom room tone with a faint ventilation hum continues throughout. Soft skin taps on the cheek, then light glass clinks and slides as the bottles are pushed aside on the counter.

non_diegetic_music: A light, sparse piano motif at a slow-moderate tempo with soft high synth pads, lifting slightly in volume at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・379語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Medium shot, vertical 9:16, warm-lit white bathroom at night. Sakura in a plain light-grey long-sleeve lounge top with a closed round neck holds a slim frosted-white unbranded glass bottle with a white cap at chest height above her cupped right palm, calm expression, looking down at her hands. No text, no logos, no label on the bottle.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, soft warm-lit vertical 9:16 skincare short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, stands in a warm-lit bathroom in a light-grey lounge top holding a slim frosted-white glass bottle with a plain white cap, completely free of any logo, label, or lettering at chest height. She tilts the bottle so a thin stream of clear liquid pools in her right palm, sets the bottle down, rubs her palms together once, closes her eyes and gently presses both palms against her cheeks, holding them there. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 化粧水を手のひらで温めて、そっと押さえるだけ。</d> while her lips remain completely closed. [Shot 2] At 00:04.000, the shot cuts to a medium close-up from a slight side angle: she slowly lowers her hands, her shoulders drop and she exhales, eyes still half closed. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 夜は、この1本から。</d> while her lips remain completely closed. [Shot 3] At 00:06.500, the shot cuts to a frontal medium shot: she opens her eyes, looks directly into the camera with a gentle closed-lip smile and raises her right index finger toward the top of the frame, holding the pose until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるのは、プロフィールに。</d> while her lips remain completely closed.

overall_soundscape: Quiet bathroom room tone continues throughout. A thin liquid trickle into the palm, a soft glass tap as the bottle is set down, a light rub of palms and the rustle of the lounge top's sleeves.

non_diegetic_music: The same sparse piano motif with soft synth pads at a steady volume, fading out gently over the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, skin redness, acne close-up, before-after skin comparison, medical setting, syringe, pills

### タイトル
`お風呂上がり、顔がつっぱる夜に #Shorts #スキンケア #化粧水`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
お風呂上がりに顔がつっぱる夜の、シンプルなスキンケア。
化粧水は手のひらで温めて、そっと押さえるだけ。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #スキンケア #化粧水 #夜のスキンケア #保湿

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- 「つっぱりが治る／改善」「浸透」「肌が変わる」等は言わない（薬機法・化粧品の効能範囲外）。台詞は手順（温めて押さえる）と気持ちだけ。
- 並べたボトルは全部ロゴなし。他社製品を思わせる形・色にしない（比較広告に見せない）。
- 商品名は動画内で0回。映像のボトルは形だけのイメージで、実物パッケージとは異なる旨を必要なら概要欄に足す。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-02｜ドッグフードおさかな｜型: あるある共感
- 想定投稿順: **Day 2** / ルート: キャラ喋り（サクラ・声のみ／手元） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 + Combat BASE V2 0.7 + Motion Continuity Repair V2 0.6 / 9s: FL2V Turbo 8step 1.0
- **Combat LoRA 向き**（6sパート: 動きが大きい）。

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | 寝てたのに、袋の音で起きる子。 | 13 | 4.33 | 寝てたのに / 袋の音で起きる |
| 3.0-6.0 | 具体 | うちだけじゃない、よね？ | 10 | 3.33 | うちだけ / じゃないよね？ |
| 6.0-10.0 | 具体 | お魚のごはん、器に入れる前から、もう座ってる。 | 20 | 5.00 | 入れる前から / もう座ってる |
| 10.0-12.5 | 誘導 | この顔、ずるい。 | 6 | 2.40 | この顔 / ずるい |
| 12.5-15.0 | 誘導 | 紹介してるごはんは、プロフィールに。 | 15 | 6.00 | 紹介してるごはんは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 昼のソファ。クッションで丸くなって寝ている犬 → カサッという音で耳が動き、頭を上げる → 3.0-6.0 犬が廊下をキッチンへ全力で走る（低いアングルで追う）
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 キッチン。立った人の目線から見下ろす構図。犬がお座りして見上げる。人の手（クリーム色ニットの袖）がロゴなしの魚柄パウチから白い器へカリカリを注ぐ。犬は震えながら待つ → 10.0-12.5 犬の顔アップ、首をかしげる → 12.5-15.0 器が床に置かれ、犬がカメラを見て舌なめずり

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・276語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, afternoon living room. A small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sleeps curled up on a beige sofa cushion, eyes closed, soft window light from the left, shallow depth of field. No people, no text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright natural-light vertical 9:16 pet short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>: the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sleeps curled on a beige sofa cushion in afternoon light. A crinkling paper sound comes from off-screen; one ear twitches, then the other, and the dog lifts its head abruptly, eyes wide open and fixed toward the right edge of the frame. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 寝てたのに、袋の音で起きる子。</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the shot cuts to a low-angle tracking shot at floor level in a wooden hallway: the same dog sprints toward a bright kitchen doorway, ears flapping and paws scrabbling on the floorboards. The camera tracks the dog at fast speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] うちだけじゃない、よね？</d> while no lips are visible on screen.

overall_soundscape: Quiet living-room ambience with soft paper crinkling off-screen, the rustle of the sofa cushion as the dog lifts its head, then quick paw clicks and skids on the wooden hallway floor.

non_diegetic_music: A playful pizzicato string motif at a moderate tempo with light hand percussion, picking up in rhythm at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・382語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, bright kitchen with light wooden floor, high angle from a standing adult's eye level. A small cream-colored fluffy mixed-breed dog with round dark eyes and a plain red collar sits upright on the floor looking up; at the top of the frame a woman's hands in cream knit sleeves hold a plain kraft-paper pouch with only a simple blue fish silhouette above an empty white ceramic bowl. Face of the person out of frame. No text, no letters, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright natural-light vertical 9:16 pet short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>, a high angle from a standing adult's eye level in a bright kitchen: the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sits upright on the wooden floor and looks up. A woman's hands in cream knit sleeves, her face out of frame, tilt a plain matte kraft-paper stand-up pouch printed only with a simple blue fish silhouette, with no letters, numbers, or logos so small round golden-brown kibble pours into a white ceramic bowl. The dog stays seated, trembling slightly with excitement, tail sweeping the floor. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] お魚のごはん、器に入れる前から、もう座ってる。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the shot cuts to a close-up at the dog's eye level: the dog's round dark eyes stare up, it tilts its head slowly to one side and its nose twitches. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] この顔、ずるい。</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the shot cuts to a high angle: the hands place the filled bowl on the floor in front of the dog, withdraw out of frame, and the dog looks straight up into the camera and licks its lips, holding still until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるごはんは、プロフィールに。</d> while no lips are visible on screen.

overall_soundscape: Bright kitchen ambience. Kibble rattles into the ceramic bowl, the dog's tail thumps softly on the wooden floor, a small sniff, and the bowl clicks down on the floor.

non_diegetic_music: The same pizzicato string motif with light percussion at a steady moderate tempo, ending on a soft pluck in the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, vomiting, sick animal, vet clinic

### タイトル
`袋の音だけは聞き逃さない犬 #Shorts #犬のいる暮らし #ドッグフード`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
寝ていても、ごはんの袋の音だけは聞き逃さない。犬のいる家のあるある。
お魚のドッグフードを紹介しています。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #犬のいる暮らし #ドッグフード #犬のごはん #あるある

映像・ナレーションはAIで生成しています。
（Combat LoRA を使って生成した場合のみ）映像の一部に BUNNY（FourBunny）氏の LoRA「Combat BASE V2」「Motion Continuity Repair V2」を使用しています。
```

### 注意点（法務）
- 「よく食べる」「食いつきが良い」「健康になる」等の嗜好性・効果は言わない（根拠なし・ペットは効果断定しない）。映像も「待っている」までで、食べっぷりの誇張をしない。
- パウチはロゴなしの魚シルエットのみ。実物パッケージと違う旨は必要なら概要欄に書く。
- 犬は生成キャラ。6秒と9秒で見た目がずれやすい（最初のコマの犬を毎回同じ静止画にする）。
- 6秒パートは Combat LoRA を試す場合、概要欄に BUNNY（FourBunny）のクレジットを入れる。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-03｜Furbo（ペット見守りカメラ）｜型: 留守番カメラの一瞬1カット（意外な反応にツッコむ）
- 想定投稿順: **Day 3** / ルート: キャラ喋り（サクラ・声のみ）＋見守りカメラ映像風 / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0 + Combat BASE V2 0.7 + Motion Continuity Repair V2 0.6
- **Combat LoRA 向き**（9sパート: 動きが大きい）。

### 参考動画（型だけ借りる・映像は新規）
- https://www.youtube.com/shorts/Swt-8_hj_pc 「猫、ペットカメラに衝撃の映像(笑) #猫」（ミーちゃん　箱入り娘です。）: 再生 559,072 / 登録者 12,700 / 44.0倍 / 投稿 2026-08-25 / 15秒。数字は yt-dlp で取得（2026-09-30）。
- 最初の3秒の見せ方（確認方法は「3. 出典」）: 0〜4.5秒: いちばん意外な瞬間（猫が白い器に前足を入れる）を見守りカメラ映像のアップで先に見せる（ティーザー）。画面上の黒帯に赤文字＋白縁の大きい2行「ペットカメラに、／衝撃の映像が(笑)」。右下にカメラの透かし。→ 5秒で固定の広角カメラ映像（部屋全体）に切り替え、字幕「ここに乗るたびに…」→ 寄り（デジタルズーム）で「見てはいけないものを見てしまった…笑」。15秒・縦・音あり（平均 -14.8dB）。
- 借りたもの: ①最初の3秒は『意外な一瞬』のアップを先に見せる ②上に大きい2行のツッコミ気味の字幕 ③固定の広角カメラ映像→寄りで種明かし。出来事は1つだけ。映像・動物・出来事は新規（猫・器・椅子は使わない）。

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | 見守りカメラに、まさかの一瞬が。 | 14 | 4.67 | 見守りカメラに / まさかの一瞬が(笑) |
| 3.0-6.0 | 具体 | 留守番中、カメラから名前を呼んだら… | 16 | 5.33 | カメラから / 名前を呼んだら… |
| 6.0-10.0 | 具体 | 首をかしげて、かしげて、そのまま、ころん。 | 17 | 4.25 | かしげて かしげて / ころん |
| 10.0-12.5 | 誘導 | かしげすぎ。 | 5 | 2.00 | かしげすぎ(笑) |
| 12.5-15.0 | 誘導 | 見守りカメラは、プロフィールに。 | 13 | 5.20 | 見守りカメラは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 【ティーザー】見守りカメラ映像風のアップ（少し魚眼・少し色あせ・高い位置から）。犬が首を思いきりかしげたまま、横にころんと倒れかける一瞬 → 3.0-6.0 固定の広角カメラ映像（棚の上から見下ろすリビング全体）。犬がラグの真ん中でお座りしてカメラを見上げ、カメラのスピーカーからの小さな声に耳を立てる
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 固定の広角カメラ映像。お座りした犬が声に首をかしげる → もっとかしげる → さらにかしげて、そのまま横にころん（ここが一瞬の出来事・1回だけ） → 10.0-12.5 デジタルズームで寄る。横に倒れたままの犬が、きょとんとカメラを見上げてまばたき → 12.5-15.0 起き上がってお座りし直し、カメラを見上げてしっぽを振る

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・309語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still in the look of a home pet-camera feed, vertical 9:16: slightly fisheye wide-angle lens, high angle from a shelf, mildly desaturated colors with soft video compression, no timestamp or any overlay text. Close view of a small cream-colored fluffy mixed-breed dog with round dark eyes and a plain red collar on a beige living-room rug, its head tilted extremely far to one side, body starting to lean over. No people, no text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal footage in the look of a home pet-camera feed, vertical 9:16, slightly fisheye wide-angle lens from a high shelf angle, mildly desaturated colors and soft video compression; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point, and no timestamp or overlay graphics appear. The shot begins in the composition of <Picture 1>: the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sits on a beige rug with its head tilted extremely far to one side; it keeps tilting until it loses balance and slowly tips over onto its side, legs briefly in the air. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 見守りカメラに、まさかの一瞬が。</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the shot cuts to a wider static pet-camera view of the whole living room from the same high shelf: the same dog sits upright in the middle of the rug looking up toward the lens; a soft, muffled voice comes from the camera's speaker and the dog's ears prick up. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 留守番中、カメラから名前を呼んだら…</d> while no lips are visible on screen.

overall_soundscape: Quiet living-room room tone with a faint electronic hiss of a camera feed; a soft thump of the dog tipping onto the rug, then a soft, unintelligible voice from the camera speaker.

non_diegetic_music: A light comedic pizzicato and glockenspiel motif at a moderate tempo, stopping for a beat at 00:03.000 and restarting quietly.
```
#### 9sパート（FL2VA・9.00秒・640x1152・400語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still in the look of a home pet-camera feed, vertical 9:16: slightly fisheye wide-angle lens, high angle from a shelf looking down at a whole cozy living room, mildly desaturated colors with soft video compression, no timestamp or overlay text. A small cream-colored fluffy mixed-breed dog with round dark eyes and a plain red collar sits upright in the middle of a beige rug, looking up at the lens with its head slightly tilted. No people, no text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal footage in the look of a home pet-camera feed, vertical 9:16, slightly fisheye wide-angle lens from a high shelf angle, mildly desaturated colors and soft video compression; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point, and no timestamp or overlay graphics appear. The shot begins in the composition of <Picture 1>: the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sits upright on a beige rug in the middle of the living room, looking up at the lens. As a soft voice comes from the camera speaker, it tilts its head to the left, then further, then even further, until it loses balance and flops onto its side on the rug in one sudden moment. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 首をかしげて、かしげて、そのまま、ころん。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the view switches to a digital zoom-in of the same feed, slightly softer and grainier: the dog lies on its side on the rug and blinks up at the lens with a puzzled look, not moving. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] かしげすぎ。</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the view switches back to the wide pet-camera framing: the dog rolls back up, sits upright again, looks at the lens and wags its tail, holding the pose until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 見守りカメラは、プロフィールに。</d> while no lips are visible on screen.

overall_soundscape: Quiet living-room room tone with a faint electronic hiss of a camera feed; a soft, unintelligible voice from the camera speaker, a soft thump as the dog flops onto the rug, fur rustling as it gets up, and the swish of its tail.

non_diegetic_music: The comedic pizzicato and glockenspiel motif builds with each head tilt, lands on a single cartoonish pluck at the flop, and resumes lightly until a soft end at the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, vomiting, sick animal, vet clinic, treats, snacks, food flying out of the device, treat dispenser, dog catching food in mid-air, timestamp overlay, camera UI text, cat, bowl, chair, injured dog, dog in pain

### タイトル
`見守りカメラに、まさかの一瞬(笑) #Shorts #犬の留守番 #見守りカメラ`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
留守番中、見守りカメラから名前を呼んだら…首をかしげすぎて、ころん。
※AIで生成したイメージ映像です（実際の見守りカメラの録画ではありません）。
見守りカメラなら、外からスマホで様子を見たり、話しかけたりできます。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #犬の留守番 #見守りカメラ #ペットカメラ #犬のいる暮らし

映像・ナレーションはAIで生成しています。
（Combat LoRA を使って生成した場合のみ）映像の一部に BUNNY（FourBunny）氏の LoRA「Combat BASE V2」「Motion Continuity Repair V2」を使用しています。
```

### 注意点（法務）
- 映像は見守りカメラの録画『風』のAI生成。実際の録画に見せないよう、概要欄に「AIで生成したイメージ映像」を明記（画面に実機の画質・画角だと誤認させる表示＝タイムスタンプやアプリUIは入れない）。
- 機能は全機種の公式仕様にある範囲だけ（スマホでライブ映像・リアルタイム双方向会話）。おやつは使わない。犬が声に反応する・倒れるのは演出で、反応を保証しない。
- 倒れる動きは痛そう・けがに見せない（柔らかいラグの上でゆっくり・すぐ起き上がる）。
- 参考動画（Swt-8_hj_pc）から借りたのは構成（意外な一瞬を先に見せる→固定カメラ→寄り）だけ。映像・動物・出来事・字幕の文言は新規。
- 9秒パートで Combat LoRA を使った場合は概要欄に BUNNY（FourBunny）のクレジットを入れる。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-04｜オルビスユー（化粧水）｜型: ビフォーアフター風（朝の支度の変化・効果断定なし）
- 想定投稿順: **Day 4** / ルート: キャラ喋り（サクラ） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | 朝のスキンケア、並べすぎてない？ | 14 | 4.67 | 朝のスキンケア / 並べすぎてない？ |
| 3.0-6.0 | 具体 | ビフォー、ボトルがずらり。 | 10 | 3.33 | BEFORE / ボトルがずらり |
| 6.0-10.0 | 具体 | アフター、まずは化粧水1本から始める朝。 | 17 | 4.25 | AFTER / まずは1本から |
| 10.0-12.5 | 誘導 | 支度が、シンプルに。 | 8 | 3.20 | 支度が / シンプルに |
| 12.5-15.0 | 誘導 | 紹介してるのは、プロフィールに。 | 13 | 5.20 | 紹介してるのは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 朝の窓辺のドレッサー。サクラ（クリーム色ニット）の前にロゴなしのボトルがずらり。困った顔で見比べる → 3.0-6.0 真上から、ボトルで埋まった台と迷う手（顔なし）
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 同じドレッサーが片付き、すりガラスのボトル1本だけ。サクラがそれを手に取り、手のひらに出して頬を包む → 10.0-12.5 窓の光の中で肩の力が抜ける → 12.5-15.0 カメラ目線でほほえみ、上を指す。※肌のアップ比較はしない

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・291語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Medium close-up, vertical 9:16, bright morning light from a window. Sakura in a plain cream high-neck knit sweater sits at a white vanity table crowded with about eight unbranded skincare bottles and jars of different shapes, looking at them with a slightly puzzled expression. No text, no logos, no labels on any bottle.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright morning-lit vertical 9:16 lifestyle short with a clean white and cream palette; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, in a cream high-neck knit sweater, sits at a white vanity crowded with about eight unbranded bottles and jars. Her eyes move from one bottle to the next and she tilts her head slightly with a puzzled look. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 朝のスキンケア、並べすぎてない？</d> while her lips remain completely closed. [Shot 2] At 00:03.000, the shot cuts to a top-down static shot of the vanity surface completely covered with unbranded bottles, jars and cotton pads; her hand in a cream knit sleeve hovers over them, picks one up, puts it back and hovers again, her face out of frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] ビフォー、ボトルがずらり。</d> while no lips are visible on screen.

overall_soundscape: Quiet morning room tone with faint birdsong outside the window; light glass clinks and the soft tap of a bottle being set back down.

non_diegetic_music: A light, sparse piano motif at a moderate tempo with soft synth pads, holding a hesitant repeated note through 00:06.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・375語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Medium shot, vertical 9:16, the same white vanity by a bright morning window, now tidy with only one slim frosted-white unbranded glass bottle with a white cap. Sakura in a plain cream high-neck knit sweater holds the bottle in one hand, relaxed soft smile. No text, no logos, no label.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright morning-lit vertical 9:16 lifestyle short with a clean white and cream palette; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, in a cream high-neck knit sweater, sits at the same white vanity, now tidy with only a slim frosted-white glass bottle with a plain white cap, completely free of any logo, label, or lettering. She pours a little clear liquid into her palm, sets the bottle down in the empty space, and gently presses both palms against her cheeks with her eyes closed. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] アフター、まずは化粧水1本から始める朝。</d> while her lips remain completely closed. [Shot 2] At 00:04.000, the shot cuts to a medium side angle against the bright window: she lowers her hands, stretches her shoulders lightly and glances out of the window with a relaxed expression. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 支度が、シンプルに。</d> while her lips remain completely closed. [Shot 3] At 00:06.500, the shot cuts to a frontal medium shot: she turns to look directly into the camera with a gentle closed-lip smile and raises her right index finger toward the top of the frame, holding the pose until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるのは、プロフィールに。</d> while her lips remain completely closed.

overall_soundscape: Quiet morning room tone with faint birdsong; a thin liquid trickle, a single soft glass tap on the vanity, and the rustle of knit sleeves as she stretches.

non_diegetic_music: The piano motif resolves into a brighter, flowing phrase at a moderate tempo with soft pads, fading out gently over the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, skin redness, acne close-up, before-after skin comparison, medical setting, syringe, pills

### タイトル
`朝のスキンケア、並べすぎてない？ #Shorts #スキンケア #朝のルーティン`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
ボトルを何本も並べていた朝から、まずは化粧水1本から始める朝へ。
変わったのは支度の流れです（肌の変化を示すものではありません）。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #スキンケア #朝のルーティン #化粧水 #シンプルスキンケア

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- ビフォーアフターは「支度（並べる本数）」の変化だけ。肌の見た目の比較・「肌が変わった」は入れない（化粧品のビフォーアフター表現は薬機法・景表法で誤認を招きやすい）。
- 「1本で十分」「他はいらない」と言い切らない（「まずは1本から」にとどめる）。
- ボトルはすべてロゴなし。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-05｜ドッグフードおさかな｜型: 比較（選び方）
- 想定投稿順: **Day 5** / ルート: キャラ喋り（サクラ・声のみ／手元） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | お肉とお魚、どっちにする？ | 11 | 3.67 | お肉とお魚 / どっちにする？ |
| 3.0-6.0 | 具体 | 迷ったら、原材料の先頭を見る。 | 13 | 4.33 | 迷ったら / 原材料の先頭 |
| 6.0-10.0 | 具体 | 多い順の表示が多いから、先頭がお魚ならお魚が主役。 | 23 | 5.75 | 先頭がお魚なら / お魚が主役 |
| 10.0-12.5 | 誘導 | あとは、その子の好みで。 | 10 | 4.00 | あとは / その子の好みで |
| 12.5-15.0 | 誘導 | お魚のごはんは、プロフィールに。 | 13 | 5.20 | お魚のごはんは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 真上から。木の床に白い器2つ（左: 小さな焼いた鶏肉の横に濃い茶色の粒／右: 小さな焼き魚の横に明るい粒）。間から犬の鼻が入り、左右をくんくん → 3.0-6.0 手元アップ。ロゴなしパウチの裏面を指でなぞる（文字は読めないぼかし）
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 マクロ。明るい粒が白い器に注がれる、奥に小さな焼き魚（ぼけ） → 10.0-12.5 指先で1粒つまんで犬の鼻の前へ。犬がくんくん → 12.5-15.0 器の横でお座りした犬がカメラを見上げ、しっぽを振る

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・316語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, top-down view of a light wooden floor. Two identical white ceramic bowls side by side: the left bowl holds dark-brown kibble with a small piece of cooked chicken beside it, the right bowl holds lighter golden kibble with a small grilled fish beside it. The black nose and cream fluffy muzzle of a small dog enter from the bottom edge between the bowls. No people, no text, no letters, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, soft natural-light vertical 9:16 pet short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>, a top-down view of a light wooden floor with two white ceramic bowls: dark-brown kibble with a small piece of cooked chicken on the left, lighter golden kibble with a small grilled fish on the right. The black nose and cream muzzle of the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar enters between them, sniffs toward the left bowl, then swings to the right bowl, hesitating in the middle. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] お肉とお魚、どっちにする？</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the shot cuts to a close-up of a woman's hands in cream knit sleeves turning a plain matte kraft-paper stand-up pouch printed only with a simple blue fish silhouette, with no letters, numbers, or logos to its back panel, which shows only soft blurred, unreadable grey lines; her index finger slides to the very first line at the top. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 迷ったら、原材料の先頭を見る。</d> while no lips are visible on screen.

overall_soundscape: Quiet room ambience; soft sniffing from the dog, a faint scrape of a bowl on the wood, and the crinkle of the paper pouch being turned over.

non_diegetic_music: A light marimba motif at a moderate tempo with soft claps, pausing briefly on an open note at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・339語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, macro close-up of small round golden kibble pouring from the top of the frame into a white ceramic bowl on a light wooden floor, a small grilled fish softly out of focus in the background, soft window light. No people's faces, no text, no letters, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, soft natural-light vertical 9:16 pet short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>, a macro of small round golden kibble pouring into a white ceramic bowl with a grilled fish softly out of focus behind it. The kibble piles up and a few pieces bounce and settle while the light glints on their surfaces. The camera pulls out with small amplitude at slow speed to reveal the full bowl. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 多い順の表示が多いから、先頭がお魚ならお魚が主役。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the shot cuts to a close-up at floor level: a woman's fingertips, her face out of frame, hold a single piece of kibble in front of the black nose of the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar; the dog sniffs it carefully, whiskers moving. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] あとは、その子の好みで。</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the shot cuts to a slightly high angle: the dog sits beside the bowl, looks up into the camera and wags its tail, holding the pose until the final frame. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] お魚のごはんは、プロフィールに。</d> while no lips are visible on screen.

overall_soundscape: Kibble rattles into the ceramic bowl, a few pieces tick against the rim, soft sniffing, and the light swish of the tail on the wooden floor.

non_diegetic_music: The marimba motif continues at a moderate tempo with soft claps, ending on a bright two-note tag.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, vomiting, sick animal, vet clinic

### タイトル
`お肉とお魚、ドッグフードの選び方 #Shorts #ドッグフード #犬のごはん`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
お肉とお魚で迷ったら、原材料の先頭をチェック。
ペットフードの表示に関する公正競争規約では、添加物以外の原材料は多い順に書くことになっています（会員事業者の自主ルール。すべての商品に当てはまるとは限りません）。
紹介しているお魚のドッグフードはプロフィールのリンクからどうぞ。

#PR #ドッグフード #犬のごはん #フードの選び方 #犬のいる暮らし

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- 「多い順」は公正競争規約（ペットフード公正取引協議会）の自主ルールで、ペットフード安全法は順序を定めていない（出典: pffta.org/label/required_fair_competition/ ・ petfood.or.jp/column/column-1051/）。だから台詞は「多い順の表示が多いから」と言い切らない形にした。
- 肉より魚が良い、という優劣は言わない（比較広告にしない）。「その子の好みで」で締める。
- アフィ先商品の原材料の先頭が本当に魚かを、公式の原材料表示で確認してから使う（違ったらこの本は使わない）。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-06｜Furbo（ペット見守りカメラ）｜型: 街頭インタビュー風
- 想定投稿順: **Day 6** / ルート: 街頭インタビュー風（顔なし・手元と後ろ姿） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | 犬の留守番、何が心配ですか？ | 12 | 4.00 | Q. 犬の留守番 / 何が心配？ |
| 3.0-6.0 | 具体 | 何してるか分からないのが、一番。 | 14 | 4.67 | A. 何してるか / 分からないのが一番 |
| 6.0-10.0 | 具体 | 見守りカメラなら、外から様子を見て、話しかけも。 | 21 | 5.25 | 外から様子を見て / 話しかけも |
| 10.0-12.5 | 誘導 | 留守番が気になる人は、 | 10 | 4.00 | 留守番が / 気になる人は |
| 12.5-15.0 | 誘導 | プロフィールを、のぞいてみて。 | 12 | 4.80 | プロフィールを / のぞいてみて ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 夕方の商店街（背景ぼけ）。手元だけ映るマイク（ロゴなし）が、リードを持つ人の肩から下（後ろ姿寄り）へ向く。足元に犬 → 3.0-6.0 答える人の手がリードを握り直すアップ、犬が見上げる。顔は一切映さない。画面に『街頭インタビュー風の演出です』を編集で入れる
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 両手で持ったスマホの画面（文字なしのUI）に、広角のリビング映像。寝ていた犬が起きて画面の方へ → 10.0-12.5 実際のリビング。ロゴなしの白い見守りカメラのスピーカーから小さな声、犬が耳を立ててカメラの前でお座り → 12.5-15.0 商店街に戻り、リードを持った人と犬が歩き去る後ろ姿

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・294語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, early-evening Japanese shopping street with warm shop lights heavily blurred in the background. From behind and slightly to the side, a person seen only from the shoulders down in a navy coat holds a red leash; a hand holding a plain black handheld microphone with no logo reaches in from the left edge toward them. A small cream-colored fluffy mixed-breed dog with a plain red collar sits at their feet looking up. No faces visible at all, no text, no letters, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, handheld street-interview style vertical 9:16 short with warm evening light; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point, and every person is seen only from the shoulders down or from behind. The shot begins in the composition of <Picture 1>: on an early-evening shopping street with blurred warm shop lights, a hand holding a plain black handheld microphone with no logo reaches toward a person in a navy coat seen from the shoulders down, who holds a red leash; the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sits at their feet. The microphone moves a little closer. The camera shakes slightly with small amplitude, handheld. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 犬の留守番、何が心配ですか？</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the shot cuts to a close-up of the person's hands tightening their grip on the red leash, the microphone at the edge of the frame; below, the dog looks up at its owner's hands. The camera holds a static shot with a slight handheld sway. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 何してるか分からないのが、一番。</d> while no lips are visible on screen.

overall_soundscape: Street ambience with distant footsteps, soft chatter that stays unintelligible, a bicycle bell far away, and the jingle of the dog's collar tag.

non_diegetic_music: A soft lo-fi beat at a moderate tempo with muted electric piano chords, kept low under the voice.
```
#### 9sパート（FL2VA・9.00秒・640x1152・412語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, close-up of two hands holding a smartphone in the evening street light; the phone screen shows a wide-angle pet-camera view of a sunny living room with a small cream-colored fluffy dog with a red collar asleep in a round grey bed. The screen has no text, no icons with letters, no timestamps. No faces, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, street-interview style vertical 9:16 short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point, and every person is seen only from the shoulders down or from behind. The shot begins in the composition of <Picture 1>: two hands hold a smartphone whose screen shows a wide-angle live view of a sunny living room without any text or icons, where the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sleeps in a round grey bed. On the screen, the dog lifts its head, stands up and walks toward the camera until its face fills the screen. The camera pushes in with small amplitude at slow speed toward the phone. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 見守りカメラなら、外から様子を見て、話しかけも。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the shot cuts to the real living room at the dog's height: a plain white rounded tabletop pet camera with one dark round lens and a small speaker grille on its front, completely free of any logo, label, or lettering stands on a low white shelf; a soft, muffled voice comes from its small speaker, and the same dog pricks up its ears, walks to the shelf and sits facing the lens, tail wagging slowly. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 留守番が気になる人は、</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the shot cuts back to the evening shopping street: seen from behind, the person in the navy coat walks away with the dog on the red leash, the lowered microphone at the bottom edge, shop lights blurred ahead. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] プロフィールを、のぞいてみて。</d> while no lips are visible on screen.

overall_soundscape: Muted street ambience around the phone, then a quiet living room with a soft, unintelligible voice from the device speaker and light paw steps, then street footsteps and the collar tag jingling as they walk away.

non_diegetic_music: The lo-fi beat with muted electric piano continues at a moderate tempo and fades out over the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, vomiting, sick animal, vet clinic, treats, snacks, food flying out of the device, treat dispenser, dog catching food in mid-air, visible faces, face of interviewer, face of passerby, crowd faces

### タイトル
`犬の留守番、何が心配？（街頭インタビュー風） #Shorts #犬の留守番 #ペットカメラ`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
犬の留守番、何が心配？という街頭インタビュー風の演出です（登場する人物・声はAIで生成したもので、実在の人物・実際の取材ではありません）。
見守りカメラなら、外からスマホで様子を見たり、話しかけたりできます。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #犬の留守番 #ペットカメラ #見守りカメラ #犬のいる暮らし

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- 実在の取材に見せない: 動画内に「※街頭インタビュー風の演出です（AI生成）」を0〜3秒に小さく表示＋概要欄にも明記。答えは『心配ごと』だけで、商品の感想・口コミを言わせない（架空の口コミ＝景表法・ステマのリスク）。
- 顔は一切映さない（肩から下・後ろ姿・手元・スマホ画面のみ）。群衆の顔もぼかし／映さない。
- 機能は全機種の公式仕様にある範囲だけ（ライブ映像・リアルタイム双方向会話）。おやつは機種によって無いので出さない。スマホ画面は文字なしの架空UI（実際のアプリ画面に見せない）。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-07｜オルビスユー（化粧水）｜型: 悩み→解決（別の切り口・お悩みカード返信型）
- 想定投稿順: **Day 7** / ルート: キャラ喋り（サクラ） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 参考動画（型だけ借りる・映像は新規）
- https://www.youtube.com/shorts/Ir0VlXFSjyk 「30代の肌、何から手をつけたらいいか...」（のべちゃん）: 再生 3,303,912 / 登録者 147,000 / 22.5倍 / 投稿 2026-08-24 / 59秒。数字は yt-dlp で取得（2026-09-30）。
- 最初の3秒の見せ方（確認方法は「3. 出典」）: 0秒から顔の寄り（正面・カメラ目線で話す）。画面の真ん中に白いコメントカード「30代、お肌のあれこれ気になって何から手をつけていいか分かりません…」を重ね、その質問を本人が読み上げる。左上に小さく「プロモーション」。約5秒で「分かります」と受け、気になること（乾燥・ハリ・毛穴…）のチェックリスト → 商品へ。
- 借りたもの: ①0秒から顔の寄り＋画面中央の白い質問カード ②カードの質問をそのまま読む ③すぐ『分かる』と受けて共感 ④PR表示を最初から。カードは視聴者コメントを装わず『よくあるお悩み』と明記（架空のコメントを作らない）。口は閉じたまま表情とうなずきで受ける。映像・人物は新規（サクラ参照のみ）。

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | スキンケア、何から始めればいい？ | 14 | 4.67 | スキンケア / 何から始めればいい？ |
| 3.0-6.0 | 具体 | 分かる。気になることが多すぎるよね。 | 16 | 5.33 | 分かる / 気になることが多すぎる |
| 6.0-10.0 | 具体 | 一度に全部はいらない。毎日使う化粧水から見直す。 | 22 | 5.50 | 一度に全部はいらない / 毎日の化粧水から |
| 10.0-12.5 | 誘導 | 続けられるのが、いちばん。 | 11 | 4.40 | 続けられるのが / いちばん |
| 12.5-15.0 | 誘導 | 紹介してるのは、プロフィールに。 | 13 | 5.20 | 紹介してるのは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 昼の明るい部屋（白い壁）。サクラ（淡い水色のニット）の顔の寄り、正面。胸元のスマホに目を落としてから、少し困った顔でカメラを見る。画面中央に白い角丸カード『よくあるお悩み｜スキンケア、何から始めればいい？』、右上に PR（編集で合成） → 3.0-6.0 同じ寄り。表情がゆるみ、胸に手を当ててゆっくり2回うなずく。編集でチェックリスト『洗顔？ 美容液？ パック？ 化粧水？』を重ねる（効能の言葉は入れない）
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 同じ明るい部屋。サクラが頬の横にすりガラスのロゴなしボトルを持ち、手のひらに出して両手で頬をそっと包む（目を閉じる） → 10.0-12.5 窓際の小さな棚、観葉植物の横の定位置にボトルを置く（毎日の場所） → 12.5-15.0 正面でほほえみ、人差し指で画面の上を指す。※肌のアップ・比較はしない

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・279語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Frontal close-up from the chest up, vertical 9:16, bright daytime room with a plain white wall and soft window light from the side. Sakura wears a plain pale-blue crew-neck knit sweater, holds a smartphone low at chest height and looks straight into the camera with a slightly puzzled, thoughtful expression, lips closed. Leave the center of the frame uncluttered. No text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright daylight vertical 9:16 talking-to-camera style skincare short with a clean white palette; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, in a pale-blue crew-neck knit, faces the camera in a frontal close-up against a plain white wall, a smartphone held low at chest height. She glances down at the phone, then lifts her eyes back to the camera with a slightly puzzled look and tilts her head a little. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] スキンケア、何から始めればいい？</d> while her lips remain completely closed. [Shot 2] At 00:03.000, the shot cuts to a slightly tighter frontal close-up: her expression softens into a sympathetic closed-lip smile, she lays her free hand on her chest and nods slowly twice. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 分かる。気になることが多すぎるよね。</d> while her lips remain completely closed.

overall_soundscape: Quiet daytime room tone with faint birdsong outside the window, the soft rustle of the knit sweater and a light tap on the phone.

non_diegetic_music: A gentle, warm acoustic guitar pattern at a moderate tempo, softening slightly at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・373語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs. Frontal medium close-up, vertical 9:16, the same bright daytime room with a plain white wall and soft side window light. Sakura in a plain pale-blue crew-neck knit sweater holds a slim frosted-white unbranded glass bottle with a white cap up beside her right cheek, a calm closed-lip smile. No text, no logos, no label on the bottle.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright daylight vertical 9:16 skincare short with a clean white palette; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, in a pale-blue knit, holds a slim frosted-white glass bottle with a plain white cap, completely free of any logo, label, or lettering beside her right cheek in a bright room. She lowers the bottle, pours a little clear liquid into her left palm, rubs her palms together once, closes her eyes and presses both palms gently against her cheeks, holding them still. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 一度に全部はいらない。毎日使う化粧水から見直す。</d> while her lips remain completely closed. [Shot 2] At 00:04.000, the shot cuts to a side medium shot by the window: she sets the bottle on a small white shelf next to a little green potted plant, as if in its everyday spot, and gives it a light tap. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 続けられるのが、いちばん。</d> while her lips remain completely closed. [Shot 3] At 00:06.500, the shot cuts to a frontal close-up against the white wall: she looks directly into the camera with a gentle closed-lip smile and raises her right index finger toward the top of the frame, holding the pose until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるのは、プロフィールに。</d> while her lips remain completely closed.

overall_soundscape: Quiet daytime room tone with faint birdsong; a thin liquid trickle, a light rub of palms, a soft tap of glass on the shelf.

non_diegetic_music: The warm acoustic guitar pattern continues at a moderate tempo and ends on a soft open chord.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, skin redness, acne close-up, before-after skin comparison, medical setting, syringe, pills, comment section UI, social media interface, username, speech bubble with text

### タイトル
`スキンケア、何から始めればいい？ #Shorts #スキンケア #化粧水`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
スキンケア、何から始めればいい？というよくあるお悩みに。
一度に全部そろえなくても大丈夫。まずは毎日使う化粧水から見直してみて。
※映像のボトルはAIによるイメージで、実際の商品とは異なります。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #スキンケア #化粧水 #スキンケア初心者 #保湿

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- 冒頭のカードは『よくあるお悩み』と明記した一般的な問いで、視聴者コメント・DMに見せない（架空のコメントを作らない＝でっち上げ・ステマ防止）。SNSのコメント欄UIやユーザー名も付けない。
- チェックリストは『何から始めるか』の選択肢（洗顔？美容液？パック？化粧水？）だけ。乾燥・毛穴・ハリなど悩みの名前を並べて『化粧水で解決』に見せない（薬機法・効能の暗示を避ける）。
- stock-01（夜の洗面所・お風呂上がりのつっぱり）とは場面（昼の明るい部屋）も悩み（何から始めるか分からない）も別。stock-04（朝のドレッサー・並べすぎ）とも別で、台詞に『並べる／1本から』を使わない。
- 参考動画（Ir0VlXFSjyk）から借りたのは冒頭3秒の見せ方（顔の寄り＋中央の質問カード＋読み上げ→共感）だけ。人物は新規の顔を作らずサクラのみ。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-08｜ドッグフードおさかな｜型: 失敗談→気づき（よくある失敗として）
- 想定投稿順: **Day 8** / ルート: キャラ喋り（サクラ・声のみ／手元） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | ごはんの切り替え、一気にやってない？ | 16 | 5.33 | ごはんの切り替え / 一気にやってない？ |
| 3.0-6.0 | 具体 | 急に替えると、戸惑う子もいる。 | 13 | 4.33 | 急に替えると / 戸惑う子も |
| 6.0-10.0 | 具体 | いつものごはんに、少しずつ混ぜていく。 | 17 | 4.25 | いつものに / 少しずつ混ぜる |
| 10.0-12.5 | 誘導 | 量や日数は、袋の説明を見てね。 | 13 | 5.20 | 量や日数は / 袋の説明を見てね |
| 12.5-15.0 | 誘導 | お魚のごはんは、プロフィールに。 | 13 | 5.20 | お魚のごはんは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 見下ろし。山盛りの見慣れない粒の器の前で、犬が匂いをかいで顔をそむける → 3.0-6.0 犬がカメラを見上げて首をかしげる（困り顔・病気っぽくしない）
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 マクロ。いつもの茶色い粒の上に、手（クリーム色ニット）が明るい魚の粒を少しだけ足し、スプーンで混ぜる → 10.0-12.5 ロゴなしパウチの裏面（文字は読めないぼかし）を指さす → 12.5-15.0 真上から、犬が落ち着いて器から食べる、しっぽを振る

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・264語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, high angle from a standing adult's eye level in a bright kitchen with a light wooden floor. A small cream-colored fluffy mixed-breed dog with round dark eyes and a plain red collar stands in front of a white ceramic bowl heaped with unfamiliar light kibble, nose close to the bowl, looking hesitant. No people, no text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, soft natural-light vertical 9:16 pet short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>, a high angle in a bright kitchen: the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar stands before a white ceramic bowl heaped with unfamiliar light kibble. The dog sniffs the kibble, pauses, then slowly turns its head away and takes one step back, looking healthy and alert but unsure. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] ごはんの切り替え、一気にやってない？</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the shot cuts to a close-up at the dog's eye level: the dog sits down, looks up into the camera and tilts its head to one side with a puzzled expression, ears slightly raised. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 急に替えると、戸惑う子もいる。</d> while no lips are visible on screen.

overall_soundscape: Quiet kitchen ambience; soft sniffing, a faint click of claws stepping back on the wooden floor, and a small curious huff from the dog.

non_diegetic_music: A light ukulele pattern at a moderate tempo, pausing on a questioning chord at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・351語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still, vertical 9:16, macro close-up of a white ceramic bowl filled with dark-brown kibble on a light wooden counter; a woman's hand in a cream knit sleeve, face out of frame, holds a small handful of lighter golden kibble just above it. Soft daylight. No text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, soft natural-light vertical 9:16 pet short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point. The shot begins in the composition of <Picture 1>, a macro of a white bowl of dark-brown kibble with a woman's hand in a cream knit sleeve above it, her face out of frame. She sprinkles a small handful of lighter golden kibble on top, then stirs gently with a small steel spoon until the two are loosely mixed. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] いつものごはんに、少しずつ混ぜていく。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the shot cuts to a close-up of her hands holding a plain matte kraft-paper stand-up pouch printed only with a simple blue fish silhouette, with no letters, numbers, or logos turned to its back panel, which shows only soft blurred, unreadable grey lines; her index finger taps the panel twice. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 量や日数は、袋の説明を見てね。</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the shot cuts to a top-down static shot on the kitchen floor: the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar eats calmly from the bowl, tail wagging slowly, until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] お魚のごはんは、プロフィールに。</d> while no lips are visible on screen.

overall_soundscape: Kibble patters into the bowl, a light metallic scrape of the spoon against ceramic, the crinkle of the paper pouch, then soft crunching and the swish of the tail.

non_diegetic_music: The ukulele pattern resolves into a warm major phrase at a moderate tempo, fading out over the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, vomiting, sick animal, vet clinic

### タイトル
`ごはんの切り替え、一気にやってない？ #Shorts #ドッグフード #犬のごはん`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
ごはんの切り替えでやりがちなのが、一気に替えること。
いつものごはんに少しずつ混ぜて。量や日数は、フードの袋に書かれた給与方法を確認してください。気になる様子があるときは獣医師に相談を。
紹介しているお魚のドッグフードはプロフィールのリンクからどうぞ。

#PR #ドッグフード #犬のごはん #フードの切り替え #犬のいる暮らし

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- 失敗談は作り話の体験にせず「よくある失敗」として一般論で言う（でっち上げ防止）。
- 「お腹を壊す」「下痢」など健康症状は言わない・映さない。具体的な日数も言わない（袋の給与方法と獣医師に誘導）。
- 最後の『落ち着いて食べる』絵は効果の証明に見せない（台詞は食べっぷりに触れない）。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-09｜Furbo（ペット見守りカメラ）｜型: 静かなケア日常観察
- 想定投稿順: **Day 9** / ルート: キャラ喋り（サクラ）＋見守りカメラ映像風 / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 参考動画（型だけ借りる・映像は新規）
- https://www.youtube.com/shorts/biBzOuRiAGY 「大人しくシャワーさせてくれる柴犬　A gentle Shiba Inu」（はるあき）: 再生 1,471,252 / 登録者 17,600 / 83.6倍 / 投稿 2026-07-22 / 89秒。数字は yt-dlp で取得（2026-09-30）。
- 最初の3秒の見せ方（確認方法は「3. 出典」）: 0秒から説明なしでケアの最中に入る。固定カメラ1台・正面・引きの構図で、飼い主のひざに柴犬が抱かれ、シャワーを当てられても大人しくカメラの方を向いている。最初の3秒に字幕なし・カットなし。音はシャワーの水音中心で静か（平均 -25.8dB）。89秒の長回し。
- 借りたもの: ①0秒からケアの最中（前置きなし） ②固定カメラ・正面・引き ③動物が大人しく身を任せている表情がフック ④静かな音。人の顔は新規にしない（サクラ参照のみ）。シャワーはタオルで拭く場面に替え、映像は新規。工場ルールに合わせ、字幕は0秒から上に入れる。

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | お風呂のあと、大人しく拭かせてくれる子。 | 18 | 6.00 | お風呂のあと / 大人しく拭かせてくれる子 |
| 3.0-6.0 | 具体 | 目を細めて、されるがまま。 | 11 | 3.67 | 目を細めて / されるがまま |
| 6.0-10.0 | 具体 | 留守番中も、見守りカメラで、この顔を見られる。 | 20 | 5.00 | 留守番中も / この顔が見られる |
| 10.0-12.5 | 誘導 | 話しかけると、耳だけぴくり。 | 12 | 4.80 | 話しかけると / 耳だけぴくり |
| 12.5-15.0 | 誘導 | 見守りカメラは、プロフィールに。 | 13 | 5.20 | 見守りカメラは / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-3.0 明るい脱衣所の床。固定カメラ・正面・引き。バスマットに座ったサクラ（袖をまくったグレーの部屋着）のひざで、白いタオルにくるまれた犬が大人しくカメラの方を向き、タオルで頭をやさしく拭かれている（前置きなしでケアの最中から） → 3.0-6.0 犬の顔の寄り。目を細めて、されるがまま
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 見守りカメラ映像風（少し魚眼・高い位置から・少し色あせ）。留守番中のリビング、ソファの同じ白いタオルの上で犬が丸くなって静かに寝ている、日差しがゆっくり動く → 10.0-12.5 カメラのスピーカーから小さな声、犬は目を閉じたまま耳だけぴくり → 12.5-15.0 棚の上のロゴなしの白い見守りカメラと、その下で眠る犬（実景）

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・319語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair (loosely tied back) and bangs. Vertical 9:16, static frontal wide-ish shot like a phone on a tripod, bright white bathroom changing area. Sakura sits on a bath mat on the floor in a plain soft light-grey long-sleeve lounge top with sleeves pushed up, holding on her lap a small cream-colored fluffy mixed-breed dog with round dark eyes wrapped in a white towel, the dog calmly facing the camera, her hands gently rubbing the towel over its head. No text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright soft-lit vertical 9:16 pet-care short filmed as one static frontal shot like a phone on a tripod; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>, already in the middle of the care routine: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, in a light-grey lounge top with sleeves pushed up, sits on a bath mat with the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar wrapped in a white towel on her lap. She slowly rubs the towel over the dog's head and ears while the dog stays completely still, facing the camera calmly. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] お風呂のあと、大人しく拭かせてくれる子。</d> while her lips remain completely closed. [Shot 2] At 00:03.000, the shot cuts to a static close-up of the dog's face framed by the white towel: its damp fur is slightly fluffed, its eyes narrow slowly into a relaxed squint as her hands pat the towel gently around its cheeks, her face out of frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 目を細めて、されるがまま。</d> while no lips are visible on screen.

overall_soundscape: Quiet bathroom ambience with a few water drips from the tub, the soft rub and pat of a cotton towel, and the dog's slow, calm breathing.

non_diegetic_music: A very soft, slow music-box motif at a low volume, steady throughout.
```
#### 9sパート（FL2VA・9.00秒・640x1152・392語）
最初のコマの静止画（参照画像なし（人の顔を入れない））:
```text
Photoreal still in the look of a home pet-camera feed, vertical 9:16: slightly fisheye wide-angle lens from a high shelf, mildly desaturated colors with soft video compression, no timestamp or overlay text. A quiet sunlit living room; a small cream-colored fluffy mixed-breed dog with a plain red collar sleeps curled up on a white towel on a light-grey sofa. No people, no text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal footage in the look of a home pet-camera feed, vertical 9:16, slightly fisheye wide-angle lens from a high shelf angle, mildly desaturated colors and soft video compression; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face appears at any point, and no timestamp or overlay graphics appear. The shot begins in the composition of <Picture 1>: the same small cream-colored fluffy mixed-breed dog with round dark eyes, a short muzzle and a plain red collar sleeps curled up on a white towel on a light-grey sofa in a quiet sunlit living room. Its side rises and falls slowly as a patch of sunlight creeps across the cushion. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 留守番中も、見守りカメラで、この顔を見られる。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the view switches to a digital zoom-in of the same feed on the sleeping dog: a soft, muffled voice comes from the camera speaker; with its eyes still closed, only one ear twitches and turns toward the sound, then relaxes. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 話しかけると、耳だけぴくり。</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the shot cuts to a real, full-color low-angle shot of the room: a plain white rounded tabletop pet camera with one dark round lens and a small speaker grille on its front, completely free of any logo, label, or lettering stands on a low white shelf in soft window light, and below it on the sofa the dog keeps sleeping peacefully until the final frame. The camera pushes in with small amplitude at slow speed. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 見守りカメラは、プロフィールに。</d> while no lips are visible on screen.

overall_soundscape: A very quiet living room with the faint electronic hiss of a camera feed, slow soft breathing, a soft unintelligible voice from the camera speaker, and a distant bird outside the window.

non_diegetic_music: The same soft, slow music-box motif at a low volume, fading out over the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, vomiting, sick animal, vet clinic, treats, snacks, food flying out of the device, treat dispenser, dog catching food in mid-air, timestamp overlay, camera UI text, shower spray on camera, wet clothes, struggling dog, dog in distress

### タイトル
`大人しく拭かせてくれる犬 #Shorts #犬のいる暮らし #見守りカメラ`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
お風呂のあと、大人しく拭かせてくれる子。留守番中も、見守りカメラでこの顔を見られます。
見守りカメラなら、外からスマホで様子を見たり、話しかけたりできます。
※映像はAIで生成したイメージです。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #犬のいる暮らし #見守りカメラ #ペットカメラ #犬の留守番

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- 機能は全機種の公式仕様にある範囲だけ（スマホでライブ映像・リアルタイム双方向会話）。おやつは使わない。『耳だけぴくり』は演出で、反応を保証しない。「安心して眠れる」「ストレスが減る」等は言わない。
- 見守りカメラ映像風の場面はAI生成（実際の録画・アプリ画面に見せない）。概要欄に明記。
- お風呂の後のケアは犬が嫌がらない描写だけ（無理に押さえる・暴れる絵にしない）。
- 参考動画（biBzOuRiAGY）から借りたのは構成（0秒からケアの最中・固定正面・大人しい表情）だけ。人物は新規の顔を作らずサクラのみ、シャワーは使わずタオル。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## stock-10｜オルビスユー（化粧水）｜型: 時短比較（朝の工程を1本にまとめる・分割画面）
- 想定投稿順: **Day 10** / ルート: キャラ喋り（サクラ） / 推奨LoRA: 6s: FL2V Turbo 8step 1.0 / 9s: FL2V Turbo 8step 1.0

### 参考動画（型だけ借りる・映像は新規）
- https://www.youtube.com/watch?v=iVCAQLUhCdo 「サボリーノ時短比較」（BCLカンパニー）: 再生 354,214 / 登録者 1,180 / 300.2倍 / 投稿 2023-07-19 / 15秒。数字は yt-dlp で取得（2026-09-30）。
- 最初の3秒の見せ方（確認方法は「3. 出典」）: 0〜1秒は左右2分割。左『いつもの朝』（眠そうな顔）／右『商品の朝』（のびをして余裕）。続いて『いつもの朝』が始まり、枕元の時計の横にストップウォッチ（00:00から動く）を重ねる。その後は工程名（洗顔／スキンケア／保湿下地）が積み上がり、合計時間を大きく表示 → 商品の朝も同じくストップウォッチ → 最後にもう一度2分割で比べてパックショット。※横長16:9・15秒。動画本体は YouTube の bot 確認で取得できず、ストーリーボード（ref/ivc_sb_1.jpg, ivc_sb_2.jpg）で確認。
- 借りたもの: ①0〜1秒の2分割『いつもの朝／1本の朝』 ②すぐ『いつもの朝』を始めて工程を1つずつ積み上げる ③同じ構図で『1本の朝』 ④最後に工程の数を並べて比べる。縦9:16に合わせて左右→上下の分割に変更。時間の数字は実測していないので出さない（ストップウォッチは数字なしのアイコンだけ）。肌の比較・効能は入れず、変わるのは工程の数と時間（手数）だけ。※2023年の動画なので、この形式が今も伸びる証拠はない。

### 台詞（Achernar・音読用）と字幕
| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | いつもの朝と、1本の朝。工程を比べる。 | 16 | 5.33 | いつもの朝 / 1本の朝 |
| 3.0-6.0 | 具体 | 導入液、化粧水、ミスト。重ねて、待って。 | 15 | 5.00 | 工程 ①導入液 ②化粧水 ③ミスト / 重ねて、待って |
| 6.0-10.0 | 具体 | 1本の朝は、化粧水をこの1本にまとめるだけ。 | 20 | 5.00 | 1本の朝 / 化粧水の工程はこの1本 |
| 10.0-12.5 | 誘導 | 変わるのは、工程の数と時間。 | 12 | 4.80 | 変わるのは / 工程の数と時間 |
| 12.5-15.0 | 誘導 | 紹介の1本は、プロフィールに。 | 12 | 4.80 | 紹介の1本は / プロフィールへ ▲ |

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344）**: 0.0-1.0 上下2分割（編集で合成）：上＝6sパート最初のコマの静止画『いつもの朝』（眠そう）、下＝9sパート最初のコマの静止画『1本の朝』（すっきり）。 1.0-3.0 『いつもの朝』開始。朝の洗面所の鏡の前、サクラ（淡いセージ色のパジャマ・白いヘアバンド）が目をこすり、スポイトのボトルを手に取る。壁に数字なしの丸い時計。左上に数字なしのストップウォッチのアイコン（編集） → 3.0-6.0 早回し風のカット：スポイトの液を手のひら→頬、化粧水をパッティング、ミストを吹きかけ、手であおいで待つ。工程ラベル①②③が積み上がる（編集）
- **9sパート（6.0-15.0秒・640x1152）**: 6.0-10.0 『1本の朝』。同じ洗面所・同じパジャマとヘアバンド、明るい朝の光。台の上はすりガラスのロゴなしボトル1本だけ。手のひらに出して両手で頬を包み、ボトルを置く。工程ラベルは①化粧水の1つだけ（編集） → 10.0-12.5 ヘアバンドを外して髪をほどき、窓辺へ歩いてのびをする。画面に『工程 3→1』（編集。時間の数字は出さない） → 12.5-15.0 窓辺で正面、ほほえんで人差し指で上を指す。※肌のアップ・肌の比較はしない

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・344語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs, the hair pulled back with a plain white fabric headband. Medium close-up, vertical 9:16, a white bathroom in cool early-morning daylight from a small window, in front of a mirror. Sakura wears a plain pale sage-green long-sleeve pajama top with a closed round neck and looks a little sleepy, lips closed. On the counter in front of her stand three unbranded items: a small glass dropper bottle, a slim frosted bottle and a small spray-mist bottle, all without labels. A plain round wall clock with no numerals hangs behind her. No text, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, cool early-morning daylight vertical 9:16 routine-comparison short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, with her hair pulled back by a plain white headband and wearing a pale sage-green pajama top, stands sleepily at a white bathroom mirror with three unlabeled items on the counter: a glass dropper bottle, a slim frosted bottle and a small spray-mist bottle. She rubs one eye with the back of her hand, then picks up the dropper bottle; behind her the hand of a plain round wall clock without numerals ticks forward. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] いつもの朝と、1本の朝。工程を比べる。</d> while her lips remain completely closed. [Shot 2] At 00:03.000, the shot cuts to a brisk sequence of quick close-ups at the same mirror: drops from the dropper fall into her palm and she presses it to her cheek; at 00:04.000 she pats liquid from the frosted bottle onto her face; at 00:05.000 she sprays mist over her face with eyes closed and fans her cheeks with one hand, waiting. The camera holds a static shot in each close-up. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 導入液、化粧水、ミスト。重ねて、待って。</d> while her lips remain completely closed.

overall_soundscape: Quiet morning bathroom room tone, a steady clock tick, small glass clicks as bottles are picked up and put down, soft pats on the skin, a short hiss of the mist spray and the flutter of a fanning hand.

non_diegetic_music: A light, ticking pizzicato-strings pattern at a brisk moderate tempo, slightly speeding up at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・385語）
最初のコマの静止画（`assets/character/sakura-ref.jpg` を元に作る）:
```text
Photoreal edit of sakura-ref.jpg: keep only Sakura's face, long straight dark-brown hair and bangs, the hair pulled back with a plain white fabric headband. Medium close-up, vertical 9:16, the same white bathroom in front of the mirror but in bright warm morning sunlight. Sakura in the same plain pale sage-green long-sleeve pajama top with a closed round neck holds a slim frosted-white unbranded glass bottle with a white cap at chest height, looking fresh and relaxed with a soft closed-lip smile. The counter is clear except for that one bottle. No text, no logos, no label on the bottle.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal, bright warm morning-sunlight vertical 9:16 routine-comparison short; no on-screen text, subtitles, captions, logos, brand marks, or watermarks appear at any point, and no human face other than Sakura's appears. The shot begins in the composition of <Picture 1>: the young Japanese woman shown in <Picture 1>, Sakura, with long straight dark-brown hair, soft wispy bangs, warm brown eyes, fair skin and a gentle closed-lip smile, with a white headband and the pale sage-green pajama top, stands at the same bathroom mirror in bright sunlight holding a slim frosted-white glass bottle with a plain white cap, completely free of any logo, label, or lettering, the counter otherwise empty. She pours a little clear liquid into her palm, presses both palms gently against her cheeks for a moment, then sets the bottle back on the counter. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 1本の朝は、化粧水をこの1本にまとめるだけ。</d> while her lips remain completely closed. [Shot 2] At 00:04.000, the shot cuts to a wider side angle: she slides off the headband, shakes her hair loose, walks a few steps to a sunlit window and stretches both arms up over her head. The camera pans with small amplitude at slow speed to follow her. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 変わるのは、工程の数と時間。</d> while her lips remain completely closed. [Shot 3] At 00:06.500, the shot cuts to a frontal medium shot by the bright window: she looks directly into the camera with a gentle closed-lip smile and raises her right index finger toward the top of the frame, holding the pose until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介の1本は、プロフィールに。</d> while her lips remain completely closed.

overall_soundscape: Quiet bright morning room tone with distant birdsong; a thin liquid trickle, a single soft glass tap on the counter, the snap of the headband, light footsteps and a relaxed breath during the stretch.

non_diegetic_music: The pizzicato-strings pattern relaxes into a warm, airy melody at a moderate tempo and fades out over the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real product packaging, celebrity, real person likeness, extra people, new human faces, distorted hands, extra fingers, melting face, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, skin redness, acne close-up, before-after skin comparison, medical setting, syringe, pills, split screen generated in video, clock numerals, stopwatch digits, timer numbers, skin close-up comparison, glowing skin effect

### タイトル
`いつもの朝と、1本の朝。工程を比べる #Shorts #朝のスキンケア #時短`

### 概要欄（全文）
```text
アフィリエイト広告を含みます #PR
いつもの朝と、1本の朝。化粧水まわりの工程の数を比べました（導入液・化粧水・ミストを重ねる朝 → 化粧水をこの1本にまとめる朝）。
変わるのは工程の数と手間だけで、肌の状態を比べたものではありません。化粧水のあとのお手入れは、お使いのアイテムの使い方に沿ってください。
※映像はAIで生成したイメージで、実際の商品とは異なります。
紹介している化粧水はプロフィールのリンクからどうぞ。

#PR #朝のスキンケア #時短 #化粧水 #スキンケア

映像・ナレーションはAIで生成しています。
```

### 注意点（法務）
- 比べるのは工程の数（3→1）だけ。肌のアップ・肌の比較・効能（うるおう、ハリが出る等）は入れない（薬機法・ビフォーアフターの効能暗示を避ける）。
- 時間は実測していないので分・秒の数字を出さない（ストップウォッチは数字なしのアイコン、時計も数字なし）。数字を入れるなら実際に測った値だけ。
- 『これ1本で完結』とは言わない。公式ではオルビスユーはウォッシュ→ローション→モイスチャーの3ステップ設計で、比べているのは化粧水まわりの工程（導入液・化粧水・ミスト→化粧水1本）だけ。概要欄で化粧水のあとのお手入れは各アイテムの使い方に沿うと明記。アフィ先がローション単品かシリーズかを確認してから使う。
- 導入液・ミストのボトルはロゴなしで他社製品を思わせない（比較広告に見せない）。stock-04（朝のドレッサーの『並べすぎ→1本から』）とは形式が別：こちらは2分割＋工程カウントの比較。
- 参考動画（iVCAQLUhCdo）は2023年の投稿で、この形式が今も伸びる証拠はない（今年の実測データなし）。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。

---
## 3. 出典（数字・事実）
- Achernar の速さ 6.40 / 6.65字/秒: `/workspace/affi-h3-research-20260929/post/narration_gemini_Achernar.txt`（実測）。
- 解像度・秒数・steps・LoRA の強さ: `fireworker011/Research` `cursor/h3-fast-fl2va-lora-6dc5` `h3-runner/README.md`（コミット 20dd89a）。
- Furbo の全機種共通の機能（ライブ映像・リアルタイム双方向会話。おやつは機種により無し）: https://furbo.com/jp/pages/comparison ・ https://help.furbo.com/hc/ja/articles/6152557612569 （ミニ仕様） / Wi-Fi 2.4GHz のみ: https://help.furbo.com/hc/ja/articles/17499371681177 （2026-09-30 確認）。
- ペットフードの原材料は多い順（公正競争規約。ペットフード安全法は順序の定めなし）: https://pffta.org/label/required_fair_competition/ ・ https://petfood.or.jp/column/column-1051/ （2026-09-30 確認）。
- 参考動画 Swt-8_hj_pc / biBzOuRiAGY: yt-dlp で info.json と動画を取得し、0.5秒ごとのコマを確認（`/workspace/affi-stock-20260930/ref/`。分析だけに使い、再配布しない）。型ごとの倍率は `/workspace/buzz-research-affi-stock-audit-20260930.md`。
- 参考動画 Ir0VlXFSjyk: 動画ファイル（`ref/Ir0VlXFSjyk.mp4`）と info.json から最初の6秒のコマを確認（`ref/ir0_first6.jpg`, `ref/ir0_sheet.jpg`）。iVCAQLUhCdo: 動画本体は YouTube の bot 確認で取得できず、info.json とストーリーボード画像（`ref/ivc_sb_1.jpg`, `ref/ivc_sb_2.jpg`）で確認。どちらも分析だけに使い、再配布しない。
- オルビスユーは ウォッシュ→ローション→モイスチャー の3ステップ設計（公式）: https://www.orbis.co.jp/special/orbis_u/4_simplestep/ ・ https://www.orbis.co.jp/mid/910/ （2026-09-30 確認）。stock-10 は『1本で完結』とは言わず、化粧水まわりの工程だけを比べる。
- 字幕の見た目（白ボックス・白一色でない・太字）: `affi-h3-research-20260929/caption_narration_report.md`。

## 4. 人間が確認すること（生成前）
1. H3 を回すOK（`workflow.md`: H3は人間OKまで使用禁止）。
2. アフィ先の商品情報: おさかなの原材料の先頭が魚か（stock-05）。Furbo はおやつ機能を使わない台本にしたので機種確認は不要（ライブ映像と話しかけは全機種の公式仕様）。
3. 犬の最初の1枚を決める（以後の犬入り静止画の元にする）。
4. Combat / Repair LoRA は README の比較テスト（B→C→D）の結果を見てから使う。ダメなら Turbo だけで回す（JSON の loras から外すだけ）。
