# トライアル01 v3「昨日のプール」（9.6秒）— v2の QA REJECT（runs/trial-01-v2/verdict.json）の修正と任意の指摘をすべて反映
登場人物はすべて大人。猫も大人の猫。縦9:16。生成する画には文字なし（テロップは編集で入れる）。

## サクラの参照
- i2vの参照画像：**/workspace/sakura-ig/refs/sakura-face-crop.jpg**（sakura-face.jpg から顔だけを切り出した。肩・襟・服は写っていない）
- 顔：大人の日本人女性（20代後半）、大人の顔立ち、茶色の目、やわらかい微笑み／髪：濃い茶色のロングストレート、シースルーバング、金の菊の髪飾り／服：紅色の着物（金と白の桜柄）、襟を閉じて正しく着る、金の帯
- 参照画像の服とプロンプトが合っているか：**一致**（参照は顔だけなので、服の指定はプロンプトだけで決まる）

## 固定語ブロックA（共通。全カットにそのままコピー）
`same adult brown mackerel tabby cat, white chest, foreground 40%; dreamcore liminal space, endless pale tiled indoor pool hall, flooded window, hazy pastel sky; vertical 9:16, smartphone footage, slight handheld shake, autofocus hunting, fluorescent light, sensor noise, compression artifacts, photorealistic, real concrete texture, weathered paint, no text, no logos`
## 固定語ブロックS（サクラ。サクラが映るC2・C4だけにそのままコピー）
`Sakura, adult Japanese woman in her late 20s, mature adult face and proportions, soft smile, brown eyes, long straight dark brown hair with see-through bangs, gold chrysanthemum hair ornament, crimson kimono with gold and white cherry blossom pattern, collar closed and properly worn, gold obi`
## ネガティブ
- 共通：`extra fingers, fused hands, extra legs, merged paws, deformed face, 3d render, CGI, plastic, smooth, text, watermark, logo`
- 口が動くカット（C2）に追加：`human-like mouth, extra teeth, deformed jaw`
- 手のアップ（C4）に追加：`extra knuckles, sleeve merging with hand, deformed wrist`

## 制御
- 全カット：カメラベクトルに手ブレ（1〜2px、不規則）。0.0〜0.5秒に、Depthの焦点面を手前→奥→手前で1往復（C4だけは猫→取っ手→猫）。
- C2：OpenPoseで猫の顎の開きに上限をつける（最大15°）。
- 元動画の秒数・OpenPose・Depth・カメラベクトルのデータ本体は**まだ作っていない**（カット段階で添付する）。

## 毒のセリフ（必須欄）
- セリフ：「また昨日のプール。あんたが『明日から本気出す』って言った日のやつ」
- テロップ：1.5–3.0秒「また昨日のプール。」→ 3.0–5.0秒「あんたが“明日から本気出す”って言った日の」

| カット | 秒 | 画（状態だけ） | OpenPoseのキーフレーム | 音（3層） | テロップ（中下段・白文字・黒フチ） |
|---|---|---|---|---|---|
| C1 | 0.0–1.5 | 人はいない。窓の外は一面水没。窓の外だけにレーンロープ、両端に固定点 | 猫：0.0秒 背中向き → 1.0秒 顔がカメラ向き | 0.0秒 猫の鼻息の溜息／プールの反響／声なし | なし |
| C2 | 1.5–5.0 | 手前に猫のアップ。奥は中距離でサクラと水没した窓、手はボケ | 猫の口（顎は最大15°）：1.6秒 開 → 3.0秒 閉 → 3.4秒 開 → 4.8秒 閉。サクラ：静止 | 猫の声（部屋鳴り）「また昨日のプール。あんたが『明日から本気出す』って言った日のやつ」／換気扇 | 1.5–3.0秒「また昨日のプール。」／3.0–5.0秒「あんたが“明日から本気出す”って言った日の」 |
| C3 | 5.0–8.0 | 人はいない。窓いっぱいに巨大な飛び込み台、雲の中、固定 | 猫：5.0秒 正面 → 6.5秒 前脚を口元へ → 8.0秒 戻す | 遠い笛の音／水滴 | なし |
| C4 | 8.0–9.6 | 手前40%に猫。中景に窓の取っ手と、横からのサクラの手（力が抜けた手、指は4本見える） | サクラの手：8.0秒 取っ手から10cm → 9.6秒 取っ手から1cm（**触れる直前でブツ切り**） | 笛が鳴りかけたところで無音 | なし |

## プロンプト（動詞なし、状態の語だけ）
- C1: [A], no person, flooded view outside window, suspended lane ropes with visible anchor points, static, consistent rope count, outside window only, pale cyan and beige / neg: [共通]
- C2: [A], [S], cat close-up, Sakura at mid distance, hands out of focus, flooded window behind, humid haze, muted pastel / neg: [共通], human-like mouth, extra teeth, deformed jaw
- C3: [A], no person, giant high-dive tower in clouds, window-sized, static, overcast cyan light, film grain / neg: [共通]
- C4: [A], [S], window handle at mid distance, Sakura's hand from side, relaxed hand, four fingers visible, crimson kimono sleeve, hand near handle, blue-white flooded light / neg: [共通], extra knuckles, sleeve merging with hand, deformed wrist

## 自己チェック
| # | 項目 | 結果 |
|---|---|---|
| ① | 全カットに同じ固定語ブロックがあるか | PASS（Aは全カット、Sはサクラが映るC2・C4だけ。C1・C3はQAの指摘どおり no person） |
| ② | -ing の動詞や動きの語がないか | PASS（例外は固定語の autofocus hunting だけ） |
| ③ | 全カットに handheld shake と autofocus hunting があるか | PASS |
| ④ | ネガティブに指・脚・CG対策があるか | PASS |
| ⑤ | 1.5〜5.0秒のセリフに「あんた」への棘があるか | PASS |
| ⑥ | テロップの欄があるか | PASS |
| ⑦ | 制御データが添付されているか | **FAIL**（データ本体はまだ作っていない） |
| 新⑧ | 毒のセリフ欄が、セリフとテロップの両方で埋まっているか | PASS |
| 新⑨ | 手のアップのネガティブと、口が動くカットのネガティブがあるか | PASS（C4・C2） |
| 新⑩ | 参照画像の服とプロンプトが合っているか | PASS（顔だけのクロップを使う） |
