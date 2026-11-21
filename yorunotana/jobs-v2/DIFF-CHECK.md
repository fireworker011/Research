# DIFF-CHECK: 14階 → 非常灯（オマージュ再執筆）

旧JSON（`jobs/`）は未変更。新JSONは `jobs-v2/`。

## タイトル候補（3）
1. **非常灯** ← JSONに採用
2. **給湯室**
3. **管理人日誌**

## 尺見積もり（VOICEVOX話者13、PC実測から校正: ≈5.6 mora/s）

| 話 | 推定尺 | mora | 字幕+ナレ文字数 | pause合計 | 目標 |
|---|---:|---:|---:|---:|---|
| day2 | **66.3s** | 321 | 372 | 8.9s | 60–70s（狙い65s） |
| day3 | **64.4s** | 312 | 360 | 8.7s | 60–70s（狙い65s） |

校正根拠: 旧day2 PC中身64.3s / mora295 → 5.40 mora/s、旧day3 PC中身59.8s / mora303 → 5.87 mora/s、平均≈5.6。

## 行オーバーラップ（最長共通部分文字列）

- **固定UI語（DAY / PR / Audible）を除いた最大共有ラン: 5 文字**（目標: 8文字超なし）
- 生の最大共有ラン（Audible製品名を含む）: 15 文字 ← `Audible（オーディブル）` 等の固定語
- クロス比較（new day2↔old day3 / new day3↔old day2）も同上基準で合格。

### day2 セグメント別 LCS

| # | scene | field | 新テキスト | 旧側で最長一致した文 | LCS(生) | 一致文字列 | LCS(固定語除く) |
|---:|---|---|---|---|---:|---|---:|
| 1 | door_handle | subtitle | 昨夜は、ドアに鍵をかけたまま眠った。 | ドアは開けなかった。 | 3 | `った。` | 3 |
| 2 | door_note | subtitle | 朝、隙間に紙が一枚。 | ドアは開けなかった。 | 1 | `。` | 1 |
| 2 | door_note | note_text | 705へ | ルール5。SNSを開くな。 | 1 | `5` | 1 |
| 3 | door_note | subtitle | 村上さんの字じゃない。 | 朝には、原田さんの声も | 3 | `さんの` | 3 |
| 3 | door_note | note_text | 705へ | ルール5。SNSを開くな。 | 1 | `5` | 1 |
| 4 | room_stickman | subtitle | 二晩目の闇が落ちる。 | 2日目の夜。 | 2 | `目の` | 2 |
| 5 | corridor_blink | subtitle | 廊下の非常灯が、また点滅を始めた。 | ドアは開けなかった。 | 2 | `た。` | 2 |
| 6 | corridor_blink | subtitle | 奥から、一灯ずつ手前へ。 | でも、光ってる窓から | 2 | `から` | 2 |
| 7 | corridor_blink | subtitle | 自分の扉の前まで来る。 | ところに来る。 | 3 | `来る。` | 3 |
| 8 | elevator_display | subtitle | エレベーター表示は、 | 朝には、原田さんの声も | 2 | `は、` | 2 |
| 9 | elevator_display | subtitle | ずっと「7」のまま動かない。 | 電気はまだ戻らない。 | 3 | `ない。` | 3 |
| 10 | breaker_panel | subtitle | 廊下の奥で配電箱が低く唸る。 | 廊下で足音がした。 | 2 | `廊下` | 2 |
| 11 | thin_wall | subtitle | 壁越しに、点滅と同じリズムの息がした。 | 廊下で足音がした。 | 4 | `がした。` | 4 |
| 12 | room_stickman | subtitle | 理解した。対象は、 | 廊下で足音がした。 | 3 | `した。` | 3 |
| 13 | corridor_blink | subtitle | 点滅を見つめた人の部屋へ寄る。 | SNSを開いた人の | 3 | `た人の` | 3 |
| 14 | room_stickman | subtitle | ルール3。非常灯を直視するな。 | ルール5。SNSを開くな。 | 3 | `ルール` | 3 |
| 14 | room_stickman | top_card | ルール3 / 非常灯を直視するな | ルール5。SNSを開くな。 | 3 | `ルール` | 3 |
| 15 | room_stickman | subtitle | カーテンを閉め、目を閉じた。 | すぐ閉じた。 | 4 | `閉じた。` | 4 |
| 16 | corridor_blink | subtitle | 点滅が、少し遠ざかった。 | ドアは開けなかった。 | 4 | `かった。` | 4 |
| 17 | door_note | subtitle | また紙が滑り込む。「次は705」 | 知らない番号からメッセージ。「見えてるよ」 | 2 | `。「` | 2 |
| 17 | door_note | note_text | 次は705 | ドアは開けなかった。 | 1 | `は` | 1 |
| 18 | door_handle | subtitle | 紙を置いた相手を怒鳴ってやろうと、 | でも、光ってる窓から | 2 | `って` | 2 |
| 19 | door_handle | subtitle | 意思と別に、ノブへ指が滑る。 | 順番に、 | 2 | `に、` | 2 |
| 20 | corridor_blink | subtitle | ノブに触れた瞬間、点滅が一気に寄った。 | 開いた瞬間、足音。さっきより近い。 | 4 | `た瞬間、` | 4 |
| 21 | door_handle | subtitle | 手を離すと、点滅が一息ついた。 | SNSを開いた。 | 3 | `いた。` | 3 |
| 22 | room_stickman | subtitle | ルール4。廊下に出るな。 | ルール5。SNSを開くな。 | 3 | `ルール` | 3 |
| 22 | room_stickman | top_card | ルール4 / 廊下に出るな | ルール5。SNSを開くな。 | 3 | `ルール` | 3 |
| 23 | elevator_display | subtitle | 表示板は「7」で凍ったまま。 | 閉じたまま | 3 | `たまま` | 3 |
| 24 | thin_wall | subtitle | 壁の向こうから、村上さんが呼ぶ。 | 朝には、原田さんの声も | 2 | `さん` | 2 |
| 25 | thin_wall | subtitle | 「一緒に、灯りを見よう」 | 順番に、 | 2 | `に、` | 2 |
| 0 | choice_card | question | 選ぶなら？ | あなたなら開く？閉じたまま？ | 2 | `なら` | 2 |
| 0 | choice_card | left | 壁を叩く | しなくなった。 | 1 | `く` | 1 |
| 0 | choice_card | right | 黙って耐える | でも、光ってる窓から | 2 | `って` | 2 |
| 0 | choice_card | narration | 壁を叩く？それとも沈黙？ | 開く？ | 2 | `く？` | 2 |
| 0 | choice_card | subtext | 答えはコメントへ ↓ | コメントで教えて ↓ | 4 | `コメント` | 4 |
| 0 | day_end_card | title | 非常灯 |  | 0 | `` | 0 |
| 0 | day_end_card | subtitle | DAY 2 | DAY 2 | 5 | `DAY 2` | 0 |
| 0 | day_end_card | status | 23時18分・室内待機 | 2日目の夜。 | 1 | `2` | 1 |
| 0 | day_end_card | button_text | フォローして3日目を待つ。 | フォローで3日目へ。 | 4 | `フォロー` | 4 |
| 0 | day_end_card | narration | フォローして、3日目を待つ。 | フォローで3日目へ。 | 4 | `フォロー` | 4 |

### day3 セグメント別 LCS

| # | scene | field | 新テキスト | 旧側で最長一致した文 | LCS(生) | 一致文字列 | LCS(固定語除く) |
|---:|---|---|---|---|---:|---|---:|
| 1 | corridor_blink | subtitle | 3日目、午前3時50分。 | 3日目の朝4時半。 | 3 | `3日目` | 3 |
| 2 | corridor_blink | subtitle | 点滅は、まだ扉の前にある。 | ドアの前にいる。 | 3 | `の前に` | 3 |
| 3 | room_stickman | subtitle | あれは、灯りを直視した部屋へ寄る。 | ドアの前にいる。 | 2 | `る。` | 2 |
| 4 | room_stickman | subtitle | だから、非常灯は見てはいけない。 | だから、SNSは開いちゃダメ。 | 4 | `だから、` | 4 |
| 4 | room_stickman | top_card | ルール3 / 非常灯を直視するな | ルール5 / SNSを開くな | 3 | `ルール` | 3 |
| 5 | breaker_panel | subtitle | でも、直したくなる。 | でも、開いちゃう。 | 3 | `でも、` | 3 |
| 6 | breaker_panel | subtitle | 共用のブレーカー箱が、頭から離れない。 | 分かってるのに、やめられない。 | 4 | `れない。` | 4 |
| 7 | door_handle | subtitle | 廊下へ出ようと、ノブに手がかかる。 | ドアの前にいる。 | 2 | `る。` | 2 |
| 8 | corridor_blink | subtitle | 触れた瞬間、点滅が暴れた。 | ガチャガチャ回り出した。 | 2 | `た。` | 2 |
| 9 | door_handle | subtitle | 離すと、静かになる。 | ドアの前にいる。 | 2 | `る。` | 2 |
| 10 | breaker_panel | subtitle | 分かっていても、確かめに行きたくなる。 | 分かってるのに、やめられない。 | 4 | `分かって` | 4 |
| 11 | room_stickman | subtitle | これが、確認衝動。 | これが、ドーパミン中毒。 | 4 | `これが、` | 4 |
| 11 | room_stickman | top_card | 正体 / 確認衝動 | 正体 / ドーパミン中毒 | 5 | `正体 / ` | 5 |
| 12 | room_stickman | subtitle | 第五則。配電箱へ触れるな。 | 3日目の朝4時半。 | 1 | `。` | 1 |
| 12 | room_stickman | top_card | 第五則 / 配電箱へ触れるな | ルール5 / SNSを開くな | 3 | ` / ` | 3 |
| 13 | room_stickman | subtitle | 無音の部屋だと、 | 無音の暗闇じゃ、 | 3 | `無音の` | 3 |
| 14 | room_stickman | subtitle | 点滅のリズムが頭の中で鳴る。 | ドアの前にいる。 | 2 | `る。` | 2 |
| 15 | app_demo_screen | subtitle | 対策はAudible。物語で耳を満たす。 | 深夜に画面を光らせないなら、Audible。 | 8 | `Audible。` | 3 |
| 16 | app_demo_screen | subtitle | 怖い朗読を選んで、 | 怖い話を再生して、 | 2 | `怖い` | 2 |
| 17 | app_demo_screen | subtitle | 端末は裏返しにして置く。 | 画面を真っ暗にして伏せる。 | 3 | `にして` | 3 |
| 18 | app_demo_screen | subtitle | 光量はゼロのまま、 | 光は一切漏れないまま、 | 3 | `まま、` | 3 |
| 19 | app_demo_screen | subtitle | 読み上げだけが点滅を追い出す。 | 耳だけに朗読が入ってくる。 | 2 | `だけ` | 2 |
| 20 | room_stickman | subtitle | 物語が続く限り、扉へは寄らない。 | 分かってるのに、やめられない。 | 3 | `ない。` | 3 |
| 21 | corridor_blink | subtitle | 点滅が、階の端まで退いた。 | 開いたら、ドアの鍵が | 2 | `いた` | 2 |
| 22 | morning_window | subtitle | 朝が来た。 | ガチャガチャ回り出した。 | 2 | `た。` | 2 |
| 23 | door_note | subtitle | 隙間に、また紙。 | 分かってるのに、やめられない。 | 2 | `に、` | 2 |
| 23 | door_note | note_text_white | その声が止んだら | あわてて閉じる。音が止まる。 | 2 | `が止` | 2 |
| 23 | door_note | note_text_red | 階の端で待つ | ドアの前で待ってるね。 | 2 | `で待` | 2 |
| 24 | door_note | subtitle | 「その声が止んだら、 | 「その朗読が終わるの、 | 3 | `「その` | 3 |
| 24 | door_note | note_text_white | その声が止んだら | あわてて閉じる。音が止まる。 | 2 | `が止` | 2 |
| 24 | door_note | note_text_red | 階の端で待つ | ドアの前で待ってるね。 | 2 | `で待` | 2 |
| 25 | door_note | subtitle | 階の端で待つ」 | ドアの前で待ってるね。 | 2 | `で待` | 2 |
| 25 | door_note | note_text_white | その声が止んだら | あわてて閉じる。音が止まる。 | 2 | `が止` | 2 |
| 25 | door_note | note_text_red | 階の端で待つ | ドアの前で待ってるね。 | 2 | `で待` | 2 |
| 0 | choice_card | question | 選ぶなら？ | あなたなら、次の話を再生する？それともイヤホンを外す？ | 2 | `なら` | 2 |
| 0 | choice_card | left | 続きを流す | あいつは、画面を光らせた人の | 1 | `を` | 1 |
| 0 | choice_card | right | 耳を開ける | ルール5 / SNSを開くな | 2 | `を開` | 2 |
| 0 | choice_card | narration | 続きを流す？耳を開ける？ | ルール5 / SNSを開くな | 2 | `を開` | 2 |
| 0 | choice_card | subtext | 答えはコメントへ ↓ | コメントで教えて ↓ | 4 | `コメント` | 4 |
| 0 | day_end_card | title | 非常灯 |  | 0 | `` | 0 |
| 0 | day_end_card | subtitle | DAY 3 | DAY 3 | 5 | `DAY 3` | 0 |
| 0 | day_end_card | status | 朝まで耐えた | 3日目の朝4時半。 | 1 | `朝` | 1 |
| 0 | day_end_card | button_text | フォローして4日目を待つ。 | フォローで4日目へ。 | 4 | `フォロー` | 4 |
| 0 | day_end_card | narration | フォローして、4日目を待つ。 | フォローで4日目へ。 | 4 | `フォロー` | 4 |
| 0 | promo_outro | headline | 未明に、 / 確認の手を止める。 | 暗闇で、 / スマホの画面を光らせない。 | 4 | `、 / ` | 4 |
| 0 | promo_outro | narration | 夜中の確認癖を断つなら Audible。 | 深夜に画面を光らせないなら、Audible。 | 8 | `Audible。` | 2 |
| 0 | promo_outro | sub_copy | 三日目の未明に流した怪談は | 3日目の夜に聴いていた怪談は | 4 | `た怪談は` | 4 |
| 0 | promo_outro | cta | プロフのURLからゼロ円で聴く | プロフィールのリンクから0円で再生 | 3 | `プロフ` | 3 |
| 0 | promo_outro | app_name | Audible（オーディブル） | Audible（オーディブル） | 15 | `Audible（オーディブル）` | 0 |
| 1 | promo_outro | step1 | 画面オフで、耳だけ物語を進める | 画面を消したまま、耳だけで物語を再生 | 4 | `、耳だけ` | 4 |
| 2 | promo_outro | step2 | はじめのひと月はゼロ円で聞き放題 | 初回30日間は0円で聴き放題 | 3 | `き放題` | 3 |

## 要素比較表

| 要素 | 旧（14階） | 新（非常灯） |
|---|---|---|
| シリーズ名 | 14階 | 非常灯 |
| 階 | 14階 | 7階 |
| 部屋 | （不明） | 705 |
| 隣人 | 原田さん | 村上さん（成人） |
| 脅威 | SNS画面の光に寄る存在／ドア下の足影 | 点滅する非常灯の列に乗って寄る存在 |
| 誘引条件 | SNSを開く・画面を光らせる | 非常灯を直視する／廊下に出る／配電箱に触る |
| 中核モチーフ | ドア足影、覗き穴2つ目、窓グリッド消灯、差出人不明SMS | 廊下非常灯の点滅進行、エレベーター表示「7」固着、扉下メモ、壁越しの息、配電箱 |
| 捨てた旧モチーフ | — | door_view足影 / peephole_stickman / window_grid / 差出人：不明 を不使用 |
| ルール（day2） | ルール5 SNSを開くな／ルール6 自分の指を信じるな | ルール3 非常灯を直視するな／ルール4 廊下に出るな |
| ルール（day3） | ルール5 SNSを開くな／正体 ドーパミン中毒 | ルール3 再掲／第五則 配電箱へ触れるな／正体 確認衝動 |
| メッセージ手段 | スマホ通知「差出人：不明」 | ドア下に滑り込む紙メモ |
| day2クライマックス | 覗き穴＋「もう1回、開いて」→開く？ | 壁越し「一緒に、灯りを見よう」→壁を叩く？沈黙？ |
| day3解決 | Audibleで耳を塞ぎ画面を消す | Audibleで点滅リズムを上書きし扉へ寄らない |
| day3選択 | 次の話を再生／イヤホンを外す | 続きを流す／耳を開ける |
| PR | day2 false / day3 true | 同（スキーマ維持） |
| HUD形式 | DAY + clock + 階ラベル | 同形式（文言は非常灯／7階） |
| 2択カード / 日終了 / Audibleアウトロ | あり | あり（文言は全面新規、製品事実のみ維持） |
| ナレーション声 | 低音シリアス男性 | 同指定（話者13想定） |
| 残虐描写 | なし | なし |
| 年齢 | 成人想定 | 成人のみ |

## シーン対比

### 旧シーン集合
- day2: door_view, peephole_stickman, phone_message, phone_tap, room_stickman, window_grid
- day3: app_demo_screen, door_view, morning_window, phone_message, phone_tap, room_stickman

### 新シーン集合
- day2: breaker_panel, corridor_blink, door_handle, door_note, elevator_display, room_stickman, thin_wall
- day3: app_demo_screen, breaker_panel, corridor_blink, door_handle, door_note, morning_window, room_stickman

### 新規シーン型（レンダラ要実装）: breaker_panel, corridor_blink, door_handle, door_note, elevator_display, thin_wall
### 流用可（既存型・params変更）: app_demo_screen, morning_window, room_stickman

## 新規シーン描画仕様

### 1. `corridor_blink`
- 構図: 暗い集合住宅廊下の一点透視。奥から手前へ非常灯が等間隔。
- 色: 壁ダークグレー、床リノリウム、非常灯は緑or赤の矩形カバー。
- params:
  - `mode`: `far_blink` / `advance` / `stare_risk` / `surge` / `retreat` / `steady_near`
  - `direction`: `toward_705`（手前の扉側へ進行）
  - `count_on`: 点灯中の灯数
  - `intensity`: `normal` / `high`（surge時は点滅速度↑・グロー強）
- アニメ: modeに応じ、奥→手前へ1灯ずつ点灯、または手前→奥へ退行。surgeは全灯高速点滅。
- 扉: 手前に「705」表札付き扉（足影なし）。

### 2. `breaker_panel`
- 構図: 壁付け配電箱のクローズアップ。グレー金属扉、内部にブレーカー列。
- params:
  - `door_ajar`: 箱扉の半開き
  - `hum`: trueで微振動±2px＋薄い音響同期想定
  - `hand_reaching`: 白い棒人間の腕が下から伸びる
  - `location`: `utility_closet` / `down_hall`（背景ラベル用）
  - `heard_only`: trueなら箱は遠景シルエット、主人公側は暗い室内
- 禁止: 火花の過剰、流血なし。

### 3. `door_note`
- 構図: 室内側から見た扉下部。隙間から折り紙メモが滑り込む。**足の影は描かない**。
- params:
  - `note_visible`, `under_gap`, `fresh`
  - `note_text` または `note_text_white` + `note_text_red`
- 文字: メモ中央に手書き風フォント。白／赤を分けて描画。
- 差出人欄は出さない（「差出人：不明」禁止）。

### 4. `elevator_display`
- 構図: 廊下壁のエレベーター階数LED。暗い壁、小さな縦長パネル。
- params: `floor`（表示文字列）, `flicker`, `stuck`, `ding`
- アニメ: flicker時は「7」が明滅。stuck時は他階へ遷移しない。

### 5. `thin_wall`
- 構図: 部屋の薄い壁断面 or 耳を壁に当てる棒人間＋壁向こう側の淡いシルエット。
- params: `ear_to_wall`, `silhouette`=`faint`/`closer`, `rhythm_marks`（点滅同期の縦線）, `whisper`
- 目や顔ディテールは最小。覗き穴の双眸構図は使わない。

### 6. `door_handle`
- 構図: 室内側ドアノブのクローズアップ。鍵穴あり。
- params: `hand_on_knob`, `shake`, `locked`, `backed_away`
- shake時±6px。足影・廊下側人物は映さない。

### 既存流用の描画差分
- `room_stickman`: 星空窓＋本棚の固定セットに依存しない。params追加 `lamp_dim`, `facing`, `eyes_closed`, `curtain_drawn`。本棚は任意。
- `morning_window`: `skyline: low_rise` で低層街並み（14階俯瞰感を出さない）。
- `app_demo_screen`: Audibleデモは構造維持、文言はJSON側で新規。

## day2 新あらすじ（要約）
7階705。昨夜は施錠して眠った。朝、扉下に「705へ」の紙。村上さんの字ではない。夜、廊下の非常灯が奥から一灯ずつ705へ寄る。エレベーター表示は「7」で固着。壁越しに点滅と同リズムの息。点滅を見つめた部屋へ寄ると悟り、ルール3。カーテンを閉め目を閉じると点滅が退く。再び紙「次は705」。怒鳴ろうとノブへ指が滑り、触れた瞬間に点滅が殺到→手を離すと止まる。ルール4。壁の向こうで村上が「一緒に灯りを見よう」。選択: 壁を叩く／黙って耐える。

## day3 新あらすじ（要約）
未明、点滅はまだ扉前。直視禁止を再確認するが、配電箱を直したくなる確認衝動が襲う。ノブに触れると点滅が暴れる。正体は確認衝動。第五則: 配電箱へ触れるな。無音だと点滅リズムが頭で鳴るためAudibleで耳を物語で満たし、画面は伏せる。朗読中は扉へ寄らない。点滅が階の端へ退く。朝、メモ「その声が止んだら／階の端で待つ」。選択: 続きを流す／耳を開ける。Audibleプロモ（新文言）。

## 変更していないもの（オマージュとして維持）
- ジャンル: マンション夜間ホラー＋ルールで生き延びる
- DAYカウンタ＋時計HUD、ルールカード（badge+title）、終盤2択、day終了カード
- day3のAudibleプロモ構造（steps①②＋CTA）と `pr_badge`
- JSONスキーマ／フィールド名（レンダラ互換）
- 低音シリアス男性ナレ想定、BGM `dark_ambient_drone.wav`

## ファイル
- `/workspace/yorunotana/jobs-v2/episode_day2.json`
- `/workspace/yorunotana/jobs-v2/episode_day3.json`
- `/workspace/yorunotana/jobs-v2/DIFF-CHECK.md`（本ファイル）

## 検証サマリ
- 推定尺: day2 66.3s / day3 64.4s
- 最大共有ラン（固定語DAY/PR/Audible除く）: 5
- 新規シーン型: breaker_panel, corridor_blink, door_handle, door_note, elevator_display, thin_wall
- 旧jobsファイル: 未変更
- 投稿・アップロード・外部送信: なし
