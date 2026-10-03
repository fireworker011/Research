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
**この子、ソファの陰からこっち見てた。**
（0秒から、同じ犬が主役。カメラ本体は後半に小さく出す。商品の機能は6秒以降。手元は出さない。2026-10-03の共通点に合わせて直した。尺は15秒のまま。）

---

## 15秒台本
ナレーションは Gemini TTS Achernar を後から乗せる。字数は句読点なし、各行6.5字/秒以下（stock.md §1と同じ基準）。商品名は台詞・字幕とも0回。

| 秒 | 役割 | 台詞 | 字数 | 字/秒 | 字幕（2行・/ で改行） |
|---|---|---|---|---|---|
| 0.0-3.0 | フック | この子、ソファの陰からこっち見てた。 | 16 | 5.33 | この子 / ソファの陰からこっち見てた |
| 3.0-6.0 | 具体 | 顔だけ出して、止まってる。 | 11 | 3.67 | 顔だけ出して / 止まってる |
| 6.0-10.0 | 具体 | 奥に小さなカメラが、ゆっくり向く。 | 15 | 3.75 | 奥に小さなカメラが / ゆっくり向く |
| 10.0-12.5 | 誘導 | ぐるっと一周、見渡せる。 | 10 | 4.00 | ぐるっと一周 / 見渡せる |
| 12.5-15.0 | 誘導 | 紹介してるのは、プロフィールに。 | 14 | 5.60 | 紹介してるのは / プロフィールへ ▲ |

- 具体1つ＝「カメラが回って360°見渡せる」。出典: Furbo公式 商品ページ「Furboドッグカメラ 360°ビュー」（https://shopjp.furbo.com/products/furbo-dog-camera ＝ A8のリンク先 https://shopjp.furbo.com/ と同じドメイン）の『外出中も愛犬を360°見守り』と機能比較表の「カメラ単体：回転360°ビュー」。2026-10-03 09:56 JST 取得（`work03/src/`）。
- 「360度」はTTSで長く読まれるので、10秒以降の台詞は「ぐるっと一周」、字幕も「ぐるっと一周」。冒頭ではカメラを名前にしない。
- アプリで向きを変えるのか、自動追尾で向くのかは台詞で言わない（自動追尾は比較表で「ライブビュー中」、録画ありの追尾はFurboシッター（有料）の機能なので、条件の説明が要る言い方を避けた）。
- 字幕: 上部・白ボックス＋黒太字・差し色1語（0-3秒は「映ってない」、3-6秒は「360°」、6-10秒は「ソファの裏」）。右上に小さく「PR」を全尺。0-15秒の下に小さく『※AIで作ったイメージ映像です』（stock-04と同じ）。

### 時間ごとの絵
- **6sパート（0.0-6.0秒・768x1344・同じ犬）**: 0.0-3.0 同じ犬がソファと壁のすき間から顔を出して、こちらを見ている。カメラ本体は映さない。人の手も出さない → 3.0-6.0 同じ犬の顔の寄り。口を閉じて止まっている
- **9sパート（6.0-15.0秒・640x1152・同じ犬）**: 6.0-10.0 同じ犬が手前の主役のまま、すき間から出てくる。奥の高い棚に、ロゴなしの白い丸いカメラが小さく映り、ゆっくり右を向く → 10.0-12.5 犬がラグに出て、カメラ本体は小さく奥のまま → 12.5-15.0 犬がカメラ目線で伏せて、しっぽをゆっくり2回振って止まる（**締めは犬。サクラも、指で上を指す動きも、手元も出さない**）

---

## 縦動画プロンプト
共通: 9:16、FL2VA（最初のコマ＝静止画、I2VAの指示文）、画面の文字なし（字幕・PR・『AIで作ったイメージ映像です』は編集で入れる）、H3の声は捨ててAchernarを乗せる。LoRAは両パートとも FL2V Turbo 8step 1.0 だけ（大きな動きがないのでCombatは使わない＝BUNNYのクレジットは不要）。人は出さない（顔・手とも無し）。犬は stock.md §1 と同じ1匹。6sも9sも最初のコマを `dog-ref.jpg` から作る。新しい犬は作らない。

### H3用プロンプト
#### 6sパート（FL2VA・6.00秒・768x1344・同じ犬）
最初のコマの静止画（`dog-ref.jpg` を元に作る）:
```text
Photoreal edit using dog-ref.jpg: keep exactly the same dog (the same medium-sized adult Japanese-style dog with a short reddish-fawn coat and cream-white markings, upright triangular ears, curled tail, face and plain red collar) and change only its pose and the scene. Vertical 9:16, daytime living room, soft window light. The same dog lies in the narrow gap between a grey sofa and a white wall, head and chest large in frame, looking into the camera, mouth closed. No pet-camera device, no people, no hands, no text, no timestamp, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal vertical 9:16 pet short; no on-screen text, subtitles, captions, timestamps, logos, brand marks, or watermarks appear at any point, and no person, no human face, and no hands appear at any point. The shot begins in the composition of <Picture 1>: the same medium-sized adult Japanese-style dog from <Picture 1>, with a short reddish-fawn coat, cream-white muzzle and chest, upright triangular ears, a tail curled over its back and a plain red collar, lies in the gap between a grey sofa and a white wall, head large in frame, looking straight into the camera, mouth closed. No camera device is visible. The camera pushes in with small amplitude at slow speed. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] この子、ソファの陰からこっち見てた。</d> while no lips are visible on screen. [Shot 2] At 00:03.000, the same dog's face fills more of the frame, ears up, mouth closed, holding still. Still no camera device. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 顔だけ出して、止まってる。</d> while no lips are visible on screen.

overall_soundscape: Quiet daytime living-room ambience and the dog's calm breathing.

non_diegetic_music: A light, curious pizzicato-string motif at a slow-moderate tempo with soft marimba, holding a gentle note at 00:03.000.
```
#### 9sパート（FL2VA・9.00秒・640x1152・380語）
最初のコマの静止画（`dog-ref.jpg` を元に作る）:
```text
Photoreal edit using dog-ref.jpg: keep exactly the same dog (the same medium-sized adult Japanese-style dog with a short reddish-fawn coat and cream-white markings, upright triangular ears, curled tail, face and plain red collar) and change only its pose and the scene. Vertical 9:16, daytime living room. The same dog stands large on a beige rug, just out of the gap beside a grey sofa, looking toward the lens. Far behind, small on a high white shelf, a plain round white dome camera with no logo. No people, no hands, no text, no timestamp, no logos.
```
H3プロンプト（`<Picture 1>` = 上の静止画。秒はパート内の秒）:
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] Photoreal vertical 9:16 pet short; no on-screen text, subtitles, captions, timestamps, camera UI, logos, brand marks, or watermarks appear at any point, and no person, no human face, and no hands appear at any point. The shot begins in the composition of <Picture 1>: the same dog stands and steps out of the sofa gap onto a beige rug, still the largest subject. Far behind, small on a high white shelf, a round white pet camera with a dome-shaped head, free of any logo, label, or lettering, and one tiny soft light, slowly turns its head a little to the right. The filming camera stays on the dog. A calm, composed adult Japanese woman with a soft, low-mid-pitched voice and an unhurried pace (S1) says in an off-screen voiceover: <d>[Japanese] 奥に小さなカメラが、ゆっくり向く。</d> while no lips are visible on screen. [Shot 2] At 00:04.000, the dog trots a few steps across the rug and pauses, ears up. The round white camera stays small in the background and stops turning. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] ぐるっと一周、見渡せる。</d> while no lips are visible on screen. [Shot 3] At 00:06.500, the dog lies down in the center of the rug, looks straight up into the lens and slowly wags its tail twice, then stays still. The device on the shelf remains small. The camera holds a static shot. The same calm voice (S1) continues in an off-screen voiceover: <d>[Japanese] 紹介してるのは、プロフィールに。</d> while no lips are visible on screen.

overall_soundscape: Quiet daytime living-room ambience, the soft pad of paws on the rug, a light jingle of the collar tag and the dog's calm breathing.

non_diegetic_music: The same light pizzicato-string motif with soft marimba resolving into a warm, cheerful phrase, ending on a gentle two-note tag in the final second.
```
**ネガティブ（メモ用）**: text, subtitles, captions, letters, numbers, logo, brand name, watermark, product label, real Furbo device design, real product packaging, timestamp overlay, date stamp, camera UI text, recording icon, celebrity, real person likeness, people, human hands, visible faces, new human faces, distorted anatomy, extra legs, lip-sync mouth movement, horizontal video, black bars, slideshow, flicker, dog changing breed or color between shots, extra dogs, dog with human expression, treats, snacks, food flying out of the device, treat dispenser, dog catching food in mid-air, dog eating, dog stuck or trapped, dog in distress, injured dog, barking dog, dog chewing furniture, dog knocking over the camera, cat, night vision, black-and-white footage

### Imagine用（短い1本・9:16・10秒）
```text
Vertical 9:16, 10 seconds, photoreal. Reference: dog-ref.jpg (keep the exact same dog). The same dog is large in frame, lying in the gap between a grey sofa and a white wall and looking into the lens, then steps onto a beige rug and wags its tail. Only late, and small on a high shelf behind the dog, a plain white round camera turns a little. No people, no hands, no treats, no text, no timestamp, no logos.
```
（9sパートの場面を1本にした差し替え用。セリフは入れない＝Achernarを後乗せ）

---

## タイトル
`この子、ソファの陰からこっち見てた #Shorts #犬のいる暮らし`
- 商品名はタイトルにも動画内にも入れない。カメラの機能は6秒以降。概要欄の事実は残す。

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
| 最初3秒 | 15 | 0秒から同じ犬。カメラ本体は後半に小さく出す。直近で同じ型が伸びた例は未確認 |
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
