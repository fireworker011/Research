# アフィShorts run03｜Furbo 360°ビュー｜型: 「映ってない…？」→ 回して見つける（死角の話・結果を伏せる）
作成: 2026-10-03（JST）／担当: 台本係（新しいBotは作っていない）／投稿・購入・外部連絡・ファイル削除: していない／動画ファイル: 作っていない
読んだもの: `/workspace/affi-rules-20261003.md`（最優先）、`run01.md`・`run02.md`（形式）、`/workspace/factory-3prod-2026-10-02/report.md`と`work/furbo_measured.json`、`/workspace/affi-stock-20260930/stock.md`（§1の工場ルール、Furboのstock-03/04/09/12）
作業ファイル: `/workspace/affi-run-20261003/work03/`（s.sh・pool.jsonl・uniq.json＝10/3の検索結果、m.py・rss_check.json・rss/＝チャンネルRSS、ref/＝info.json 1本、src/＝Furbo公式ページの保存）

---

## 0. 入力（伸び動画の根拠）
### 直近（1年以内）: **未確認**（近い1本は参考扱い）
- やったこと（2026-10-03 09:55〜10:00ごろ JST）: yt-dlpで検索。「Furbo 360」「ファーボ 360」「ペットカメラ 360度」「ペットカメラ 首振り 犬」「見守りカメラ 犬 追いかける」「ペットカメラ 犬 shorts」「Furbo 犬」の7語 × 3通り（通常／今年／今年＋Shorts）＝580件（重複と再生数なしを除くと379本）。日本語でペットカメラが題材の10本について、チャンネルRSS（最新15本）で投稿日と普段の数字を取った。
- transcriptapi: クレジット不足なので使っていない（指示どおり）。
- ボットチェック: 1本ずつの取得2本のうち、tJ8Oafd1NVk で「Sign in to confirm you're not a bot」が出た（2026-10-03 09:58ごろ JST）。cookieでの回避はしていない。それ以降、1本ずつの取得はやめた。

| # | URL | タイトル | チャンネル | 再生数（10/3） | 普段（RSS中央値・本数） | 倍率 | 投稿日 |
|---|---|---|---|---|---|---|---|
| R1 | https://www.youtube.com/watch?v=saZniSjNeLM | 猫の留守番、ペットカメラ2台で死角ゼロに！共働き夫婦の見守り生活【Furboミニ 360°ビュー / Furboミニ】 | ととねこ（登録者307,000） | 20,672 | 2,678.5（14本・Shortsと長い動画が混ざる） | 7.72倍 | 2026-08-22 |
| R2 | https://www.youtube.com/watch?v=tJ8Oafd1NVk | Crusoe Dachshund Outsmarts Furbo Dog Camera (Almost) | Crusoe the Dachshund | 3,868,689 | 110,875（最新15本） | 34.9倍（同じ時期ではない） | 不明（RSSの最新15本＝2025-12-24以降には無い。ボットチェックで取れず） |

- **R1は「直近で3倍以上」にしなかった。** 理由: ①普段の数字にShorts（483〜2,380回）が混ざっている。長い動画だけ（6,368／7,114／11,856／12,240回、中央値9,485回）と比べると **約2.2倍** で3倍に届かない ②686秒・4Kの長い動画で、Shortsではない ③説明欄に「※本動画はFurbo様のプロモーションを含みます」（企業案件）。同じ日のFurbo案件のShorts 2PFMVp32_D4（おやつの回）は2,228回で、普段並み。
- R2は英語チャンネルの60秒動画。投稿日が取れず、普段の数字も同じ時期ではないので参考扱い（倍率は使わない）。
- ほかに測った8本（猫の黒ちゃんねる pX7j6DkngS8 1.01倍、ジョイの小部屋 NEO_SsILCgA 0.62倍、柴犬おにぎりくん 5o9FXiFheB4 74倍だが2022-11-14 など）は、1年以内で3倍以上が無いか、古い。
- 10/2の調査の F1（大型犬4頭のモニタリング・18.7倍・2021〜2022年）も参考のまま。

### 借りた型・借りないもの
- 借りた型（R1）: 「**カメラに映っていない子がどこにいるか分からない → 回して見つける**」という困りごと。R1の説明欄の言い方は『片方が映っても、もう片方がどこにいるか分からない』。Furbo公式の商品ページのお客様の声にも『部屋の中の見えないところにいることが多々あった』とある。
- 借りた型（F1）: 「…してみたら…」と**結果を伏せて**、最後に見せる。
- 借りないもの: R1・R2の猫や犬、部屋、映像。「死角ゼロ」という言い切り（公式の表示ではない）。R2の「カメラを出し抜く」演出（犬がカメラをいじる・倒す）。**おやつを投げる・飛び出す場面（stock-03/09/12と同じく外す）**。
- ストックとのかぶり: stock-03（首かしげ→ころん）、04（夜中におもちゃを並べる）、09（お風呂のあと耳だけぴくり）、12（お出かけあるある・カーディガン）と出来事が別。「回して死角を見る」は初めて。

---

## フック1行
**あれ、カメラに犬が映ってない。**
（0秒から、見守りカメラ映像風の誰もいないリビング。犬がいないことそのものを謎にして、答えを9sパートまで伏せる＝F1の「結果を伏せる」）

---

## 15秒台本
ナレーションは Gemini TTS Achernar を後から乗せる。字数は句読点なし、各行6.5字/秒以下（stock.md §1と同じ基準）。商品名は台詞・字幕とも0回。

| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | あれ、カメラに犬が映ってない。 | 13 | 4.33 | あれ？ / カメラに犬が映ってない |
| 3.0-6.0 | 具体 | このカメラは、ぐるっと一周見渡せる。 | 16 | 5.33 | このカメラは / 360°見渡せる |
| 6.0-10.0 | 具体 | 向きを変えたら、ソファの裏からこっち見てた。 | 20 | 5.00 | 向きを変えたら / ソファの裏から… |
| 10.0-12.5 | 誘導 | 向きを変えれば、そこも見える。 | 13 | 5.20 | 向きを変えれば / そこも見える |
| 12.5-15.0 | 誘導 | 紹介してるカメラは、プロフィールに。 | 16 | 6.40 | 紹介してるカメラは / プロフィールへ ▲ |

- 具体1つ＝「カメラが回って360°見渡せる」。出典: Furbo公式 商品ページ「Furboドッグカメラ 360°ビュー」（https://shopjp.furbo.com/products/furbo-dog-camera ＝ A8のリンク先 https://shopjp.furbo.com/ と同じドメイン）の『外出中も愛犬を360°見守り』と機能比較表の「カメラ単体：回転360°ビュー」。2026-10-03 09:56 JST 取得（`work03/src/`）。
- 「360度」はTTSで長く読まれるので、台詞は「ぐるっと一周」、字幕は「360°」にした。
- アプリで向きを変えるのか、自動追尾で向くのかは台詞で言わない（自動追尾は比較表で「ライブビュー中」、録画ありの追尾はFurboシッター（有料）の機能なので、条件の説明が要る言い方を避けた）。
- 字幕: 上部・白ボックス＋黒太字・差し色1語（0-3秒は「映ってない」、3-6秒は「360°」、6-10秒は「ソファの裏」）。右上に小さく「PR」を全尺。0-15秒の下に小さく『※AIで作ったイメージ映像です』（stock-04と同じ）。

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344・犬なし）**: 0.0-3.0 見守りカメラ映像風（カラー・少し魚眼・高い棚から・固定）。昼のリビング、ラグと丸い犬用ベッドは空っぽ、窓からの光だけ。画面の右端にソファの背もたれが半分だけ切れて映っている → 3.0-6.0 実景の寄り。棚の上のロゴなしの白い丸いペットカメラ（ドーム型の頭）が、静かに右へ回っていく。小さなランプがほのかに光る
- **9sパート（6.0-15.0秒・640x1152・犬あり）**: 6.0-10.0 見守りカメラ映像風・右を向いた画。ソファの横の、壁とソファのすき間。最初のコマから犬がソファの陰に伏せていて、顔だけ出してカメラを見上げている → デジタルズームでゆっくり寄る → 10.0-12.5 犬が立ち上がって、すき間からとことこ出てくる → 12.5-15.0 カメラの真下のラグまで来て、カメラを見上げたまま伏せて、しっぽをゆっくり2回振って止まる（**締めは犬のカメラ目線。サクラも、指で上を指す動きも出さない**）

---

## 縦動画プロンプト
共通: 9:16、FL2VA（最初のコマ＝静止画、I2VAの指示文）、画面の文字なし（字幕・PR・『AIで作ったイメージ映像です』は編集で入れる）、H3の声は捨ててAchernarを乗せる。LoRAは両パートとも FL2V Turbo 8step 1.0 だけ（大きな動きがないのでCombatは使わない＝BUNNYのクレジットは不要）。人は出さない（顔・手とも無し）。犬は stock.md §1 と同じ生成犬1匹で、犬が出る9sパートは最初のコマを必ず `dog-ref.jpg`（`/workspace/affi-stock-20260930/dog-ref.jpg`）から作る。6sパートは犬が出ないので参照なし。

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・311語）
最初のコマの静止画（参照なし・犬も人も出さない）:
```text
Photoreal still, vertical 9:16, home pet-camera footage look: slightly fisheye, slightly soft and muted colors, viewed from a high shelf looking down. A quiet, empty living room in daytime with window light: a beige rug, an empty round grey dog bed, a low wooden table. At the far right edge of the frame, the back of a grey fabric sofa is cut off by the frame. No animals, no people, no text, no timestamp, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal vertical 9:16 pet camera short; no on-screen text, subtitles, captions, timestamps, camera UI, logos, brand marks, or watermarks appear at any point, and no person or human face appears at any point. The shot begins in the composition of <Picture 1>, a home pet-camera view from a high shelf, slightly fisheye with soft, muted colors: a quiet, empty living room in daylight with a beige rug, an empty round grey dog bed and a low wooden table, the back of a grey sofa cut off at the far right edge. Nothing moves except a thin curtain swaying gently in the window light and faint dust drifting in the sunbeam. The camera holds a static shot. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] あれ、カメラに犬が映ってない。</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the shot cuts to a clean, natural-color close-up at eye level of a white wooden shelf: a small round white pet camera with a dome-shaped head, completely free of any logo, label, or lettering, with one tiny soft light glowing on its front, slowly and smoothly rotates its head to the right on its base, a quarter turn, then stops. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] このカメラは、ぐるっと一周見渡せる。</d> while no lips are visible on screen.

overall_soundscape: Quiet daytime living-room ambience with a faint ticking wall clock and distant birds outside, then a very soft, smooth mechanical whir as the small camera head turns.

non_diegetic_music: A light, curious pizzicato-string motif at a slow-moderate tempo with soft marimba, pausing on a questioning note at 00:02.800 and continuing as the camera turns.
```
#### 9sパート（FL2VA・9.00秒・640x1152・380語）
最初のコマの静止画（`dog-ref.jpg` を元に作る）:
```text
Photoreal edit using dog-ref.jpg: keep exactly the same dog (the same medium-sized adult Japanese-style dog with a short reddish-fawn coat and cream-white markings, upright triangular ears, curled tail, face and plain red collar) and change only its pose and the scene. Vertical 9:16, home pet-camera footage look: slightly fisheye, slightly soft and muted colors, viewed from a high shelf looking down. The narrow gap between the side of a grey fabric sofa and a white wall in a daytime living room; the same dog lies in the shadow of the sofa with only its head and front paws out, looking up at the camera, mouth closed. A beige rug in the foreground. No people, no text, no timestamp, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal vertical 9:16 pet camera short; no on-screen text, subtitles, captions, timestamps, camera UI, logos, brand marks, or watermarks appear at any point, and no person or human face appears at any point. The shot begins in the composition of <Picture 1>, a home pet-camera view from a high shelf, slightly fisheye with soft, muted colors: in the narrow gap between a grey sofa and a white wall, the same medium-sized adult Japanese-style dog from <Picture 1>, with a short reddish-fawn coat, cream-white muzzle and chest, upright triangular ears, a tail curled over its back and a plain red collar, lies in the sofa's shadow with only its head and front paws out, looking straight up at the camera and blinking slowly. The camera pushes in with small amplitude at slow speed, like a digital zoom. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 向きを変えたら、ソファの裏からこっち見てた。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the shot cuts back to a wider pet-camera view from the same high shelf: the dog stands up, steps out of the gap and trots calmly across the beige rug toward the bottom of the frame, ears up. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 向きを変えれば、そこも見える。</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the shot cuts to a closer high-angle pet-camera view straight down at the rug below the shelf: the dog lies down in the center, looks straight up into the lens and slowly wags its tail twice, then stays still, holding the pose until the final frame. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるカメラは、プロフィールに。</d> while no lips are visible on screen.

overall_soundscape: Quiet daytime living-room ambience, the soft pad of paws on the rug, a light jingle of the collar tag and the dog's calm breathing.

non_diegetic_music: The same light pizzicato-string motif with soft marimba resolving into a warm, cheerful phrase, ending on a gentle two-note tag in the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real Furbo device design, real product packaging, timestamp overlay, date stamp, camera UI text, recording icon, celebrity, real person likeness, people, human hands, visible faces, new human faces, distorted anatomy, extra legs, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, treats, snacks, food flying out of the device, treat dispenser, dog catching food in mid-air, dog eating, dog stuck or trapped, dog in distress, injured dog, barking dog, dog chewing furniture, dog knocking over the camera, cat, night vision, black-and-white footage

### Imagine用（短い1本・9:16・10秒）
```text
Vertical 9:16, 10 seconds, photoreal, home pet-camera footage look (slightly fisheye, soft muted colors, from a high shelf). Reference: dog-ref.jpg (keep the exact same dog). In a daytime living room, the same dog lies in the narrow gap between a grey sofa and a white wall with only its head out, looking up at the camera; slow digital-zoom push-in; the dog stands, trots out onto a beige rug below the camera, lies down, looks straight up into the lens and slowly wags its tail. No people, no treats, no text, no timestamp, no logos.
```
（9sパートの場面を1本にした差し替え用。セリフは入れない＝Achernarを後乗せ）

---

## タイトル
`カメラに犬が映ってない…と思ったら。Furbo 360°ビュー #Shorts #ペットカメラ #犬のいる暮らし`
- 商品名はタイトルだけ（動画内0回）。run01・02と同じ扱い。

## 概要欄
```text
アフィリエイト広告を含みます #PR
見守りカメラに映っていないとき、カメラの向きを変えて見られる、という紹介です（実際の留守番の記録ではありません）。
「回転360°ビュー」はメーカー公式ショップの商品ページで確認しました（2026年10月3日時点）。機能やプランの最新の内容は販売ページでご確認ください。
紹介しているものはプロフィールのリンクからどうぞ。

#PR #ペットカメラ #見守りカメラ #犬のいる暮らし #犬の留守番

映像・ナレーションはAIで生成しています。映像の犬・部屋・カメラはAIで作ったイメージで、実際の商品や映像とは異なります。
```

### 注意点（法務・投稿前の確認）
- 「死角ゼロ」「どこにいても見つかる」「安心」「防犯」「分離不安が治る」は書かない。言うのは公式の「回転360°ビュー」の範囲（向きを変えて見渡せる）だけ。
- 自動追尾・自動録画・通知は台詞に入れない（自動追尾はライブビュー中、録画つきの追尾と自動録画履歴は有料のFurboシッター。条件を省くと誤解になる）。
- おやつは使わない・映さない（ネガティブにも入れた）。
- 映像のカメラはロゴなしの白い丸い形だけのイメージで、実物のデザインに似せない。画面にタイムスタンプやアプリの表示を出さない（作り物の記録に見せない）。概要欄で「実際の留守番の記録ではありません」と書いた。
- A8のリンク先 https://shopjp.furbo.com/ のトップページは、2026-10-03 取得時点で「1080p フルHD・4倍ズーム・160°ワイドアングル」の古い説明文のままだった。360°ビューの説明があるのは同じドメインの商品ページ（/products/furbo-dog-camera）。プロフィールのリンクからトップに着いた人が「360°」の記載をすぐ見つけられない可能性がある → 投稿前に人間がリンク先を確認する。
- 締めの絵は「犬がカメラを見上げて伏せる」で、run02（サクラ＋指で上）とかぶらない。stock-04の締め（棚の上のカメラの実景）とも別。
- ジャンル: ペットだけ（美容・婚活の要素なし）。
- 共通: PR表記（動画右上＋概要欄先頭）、AI生成の明記、商品名は動画内0回、アフィURLは動画内に入れずプロフィール（A8）だけ。収入の数字・LINEなし。

---

## 採点
**判定: 使える**（投稿するかは人間が決める）
- 理由（短く）: 具体の「回転360°ビュー」はA8のリンク先と同じドメインの公式商品ページで確認でき、カメラ単体にある機能なので、条件を付けずに言える。フックは謎を出して9sパートで答える形でまとまっている。弱いのは、直近の伸びの根拠が無いこと（R1は長い動画・企業案件で、長い動画どうしで比べると約2.2倍）。

| 項目 | 点 | 理由 |
|---|---|---|
| 最初3秒 | 15 | 「映ってない」で答えを知りたくさせる。ただし0秒の画が「誰もいない部屋」で、ペットの顔が出ない（弱くなりうる）。直近で同じ型が伸びた例は未確認 |
| テンポ | 16 | 切り替えは3.0／6.0／10.0／12.5秒。謎→カメラが回る→見つかる→出てくる、と1本の流れで、間延びしにくい。12.5-15秒は6.40字/秒で上限に近い |
| 見やすさ | 15 | 字幕は2行・短い・上部固定、画面の文字なし。カメラ映像風の少しぼやけた画で、犬がソファの陰にいるのが小さい画面で分かるかは不明（動画は未生成） |
| プロフィール誘導 | 15 | 「向きを変えれば、そこも見える→紹介してるカメラはプロフィールに」とつながる。ただしリンク先トップに360°の説明が見当たらない点が誘導の弱み |
| リスク | 16 | 効果の断定なし・おやつなし・人なし・PR/AI明記・商品名0回・「記録ではない」と明記。残るのはリンク先トップの表示の古さと、イメージ映像を実録と受け取られる可能性 |
| **合計** | **77** | |

- この採点は台本係の自己採点（動画は未生成）。run01・02と同じ物差しで付けた。動画ができたら採点係が付け直す。
- 数字は実測だけ（再生数・倍率は10/3のyt-dlp検索・チャンネルRSS・info.json 1本、機能は10/3保存の公式ページ）。

### 残る「不明」
- 直近1年のFurbo／ペットカメラの伸び動画（普段の3倍以上）: **不明（未確認）**。R1は長い動画どうしで約2.2倍。Shortsでは0本。
- R2（Crusoe）の投稿日: **不明**（ボットチェックで取れなかった。cookieでの回避はしていない）。
- A8のリンク先トップに360°ビューの説明が無い件で、着地ページが実際にどこへ飛ぶか（トップのままか、商品ページへ転送されるか）: **不明**。
- 動画にしたときの見え方（犬の一致・ソファの陰の犬が小さい画面で見えるか・カメラの頭の回り方）: **不明**（動画は作っていない）。

---

## 完了条件
**完了条件4つ（フック1行／15秒台本／縦動画プロンプト／採点）はすべて揃った（判定は「使える」。連続完了 3/3）。**
- ルールの「3回続けて完了条件を満たすまで、台本以降（量産）に進まない」の条件は、これで数の上では満たした。量産に進むか、投稿するかは人間が決める（この作業では進めていない）。
