# H3 LoRA Studio 引き継ぎ（アナル三択）

新規チャット用。Naomiichi（プロダクト）。質問せず、このファイルと `.cursor/skills/h3-lora-studio/SKILL.md` を読んでから作業する。

## 新規チャットに貼る文

```
MiniMax H3 LoRA Studio を続ける。会話が長くなったので新規チャット。Naomiichi。

まず読め:
- `h3-lora-studio/GROK_PROMPTS.md`（このエロ動画の GitHub プロンプト一覧）
- `h3-lora-studio/dump/G_h3_prompts.txt`（物語・ロック・③生成文の全文）
- `.cursor/skills/h3-lora-studio/SKILL.md`
- `h3-lora-studio/HANDOVER.md`
- `h3-lora-studio/README.md` の「アナルセックスの3パターン」

作業ブランチ: `cursor/h3-anal-stories-f112` だけ。新枝禁止。PR #138 は draft のままマージするな。
ベース: `cursor/h3-cabin-flow-f112`（anal-17 = `41867d0` を残す）
HEAD: `ffa3fb1`
Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-anal-stories-f112/minimax_h3_lora_studio.ipynb
clinic: https://github.com/fireworker011/Research/blob/cursor/h3-anal-stories-f112/h3-lora-studio/stories/clinic-75s.json
設定の版: `h3-20260914-anal-18`

Threads の schedule を戻すな。アナル本に cowgirl / riding / doggy / AIO / Final Thrust / ThumbInButt / CUMOUF / hmmotion を積むな。ipynb は手で直すな。anal-14 helper を被せるな。clinic を PLACEHOLDER にするな。checkup をアヤ受け＋医師竿に戻すな。

直近: clinic-75s は 9本＝90秒 16:9。アヤ受け＋医師竿。c1 椅子座りジュボ。c2 10秒ずっとジュボ（口を外すな・立つな・キスなし）。c3 口を外す・ありがとう！ゴホウビです→黄色い小便を顔へ。c4 おしっこ、あったかーい！ありがとー！→濃厚ベロチュー。c5-c9 黄色い小便まみれを落とさない。c5 lookback＋自分で尻を開く。c5-c8 は 30 degrees・SAME DIRECTION・行為中 NO KISS。語は `outer ring of the anus entrance`。JPGをリポジトリに入れるな。
```

## いまの枝

| 項目 | 値 |
|---|---|
| 作業 | `cursor/h3-anal-stories-f112` |
| ベース | `cursor/h3-cabin-flow-f112` |
| PR | https://github.com/fireworker011/Research/pull/138 draft |
| 版 | `STUDIO_REV` / `FETCH_REV` = `h3-20260914-anal-18` |
| HEAD | `ffa3fb1` clinic c2キスなし・ゴホウビ飲尿・c5-c9に yellow urine 残し |
| ノート | `minimax_h3_lora_studio.ipynb` を3箇所に同じものを書く（root / `minimaxh3/` / `h3-lora-studio/`） |

`colab/h3_lora_studio.py` と `minimaxh3/h3_lora_studio.py` は同期する。ノートは `python colab/_write_lora_studio_nb.py` で再生成。手で ipynb を直さない。

## ユーザーが求めたもの

アナルセックスを既存の物語パターンに入れる。3パターン。会話とタイムラインも直す。

1. **①口内で終わる** … 根元ジュボ → 口内射精。口移しあり
2. **②フェラのあとアナル** … 根元ジュボで**出さない** → 抜く → アナル挿入オンカメラ（まだ出さない） → パコパコ根本まで出し入れ → アナル中出し
3. **③会って即アナル** … 会話＋短いベロチュー → 0-10でアナル挿入オンカメラ（まだ出さない） → 10-20パコパコ → 20-30アナル中出し

体位は場面で変える（正常位・後背・立ち後背・騎乗・後輩騎乗・座位・後背座位）。結合部が見える後背／立ち後背を多めにするが無理はしない。

あとで「選択肢にアナルの三択ないよ？」→ 焼き込みだけではドロップダウンに出ない。③に3行を足した。

## 実装の分かれ方

**A. ③で選ぶ三択そのもの（汎用40秒）**

| ラベル | id | 流れ | 体位欄 |
|---|---|---|---|
| ①口内で終わる | `anal-p1-oral` | 会話 → oral → `oral_creampie` + 口移し | 無視 |
| ②フェラのあとアナル | `anal-p2-bj-anal` | 会話 → oral（出さない）→ `futa_anal` 中出し → 「アナルあつい」 | アナル本に効く |
| ③会って即アナル | `anal-p3-meet-anal` | 会話 → 短いベロチュー → 10-20 `futa_anal` 挿入（出さない）→ 20-30 中出し | アナル本に効く |

JSON ではない。`generate_anal_pattern()` が組む。キャストはアヤ受け＋レイ20cm。再生は **つなぐ**（`STORY_PLAY_CHAIN`）。ドロップダウンは ×5 専用/つなぐを付けない。並びは SFW 4行の直後、`生成し直し` の前。

コード: `ANAL_PATTERN_*` / `anal_pattern_labels()` / `is_anal_pattern()` / `generate_anal_pattern()` / `_ANAL_POSE_SPEC`。`load_story(..., pose=, scene=)`。文章欄は場所。体位は `resolve_pose(体位)` のあと英語キーで渡る（既定「立ち」→ `standing`）。

**B. 既存の帰宅〜縁側・名前付きパック**

各 JSON にどれか1つを焼き込み。1本の物語で2つ混ぜない。

- ①: 終点・カラオケ・赤信号・講義机・ガソスタ・トンネル電話・ハチコウ。終電の**車内口内**だけ①のまま
- ②: 帰宅・洗い物・登校・授業・おかえり・風呂・食卓・布団・山小屋・訪問・検診・ケンシン・終電ホーム・ニクカベ・肥溜め・カフェ・車内販売・背中流し。キャンプはクンニ→アナル
- ③: 屋上・休日・縁側・ヨガ・ランドリー・花火・ハイスイコウ・テトラ・ロッカー・ドウロ・展望台・川原・屋上クーラー・コウジョウ
- 例外: 休日・縁側は③アナル中出し（抜かない）のあとハードカットで①ジュボ→口内＋口移し（2回戦）
- 外: ザーメン風呂（挿入もジュボもない）

## アナル本の不変条件

- LoRA: Mystic 0.5 +（Drive に anal-any-h3 があれば行為 0.55＋竿ヘルパー、無ければ竿 0.45）+ 穴 0.4。Turbo なし・8step
- 積まない: cowgirl / riding-pose / doggy / AIO / Final Thrust / ThumbInButt / CUMOUF
- `hmmotion` は `futa_sex` だけ。アナル本に載せない
- 挿入クリップの先頭は `lock_anal_prep`（受け入れる姿勢・穴から手の幅・未挿入）。パコパコ本には足さない
- 精液は白。`lock_anal_creampie` と `lock_anal_hole` で **アナルからだけ**。マンコを開かない。使っていないマンコから漏らさない。抜いたら開いたアナルから漏れる。肛門は尾骨側。後背は上の穴、正常位・M字は下の穴
- ②③で終わった話は口移しなし（`SEMEN_SHARE_SKIP`。`anal-p2` / `anal-p3` 含む）。①だけ `[(2, "on_cumouf")]`
- 行為クリップは無言（`ACT_SITUATIONS`）
- 直前の本は受け入れる姿勢＋穴から手の幅・未挿入。次が `INSERTION ON CAMERA`
- `anus's anus` のような重複、`Clip N of M.` が HARD LOCK の先頭以外、洗い物の「床の口」ロックがアナル本を潰す、を再発させるな

## ノートの落とし穴（ユーザーが踏んだ）

ドロップダウンは `.ipynb` の `@param` に焼き付いている。**②は py だけ取り直す。選択肢は増えない。**

Drive 保存コピーと、設定の版が **xxx** のノートは古い。開き直すリンクは README 先頭とノート MD0 のバッジ。

③の初期値は今も **登校（専用）**。三択はリストを上までスクロールしないと見えない。下の `アナルセックス（女体）` は1本の行為で、三択ではない。②の「今使うシーン」にも同じ3行がある（専用×5は付けない）。

## 触るファイル

| 場所 | 役割 |
|---|---|
| `colab/h3_lora_studio.py` | 本体。三択生成・ロック・SITUATION_HELP |
| `minimaxh3/h3_lora_studio.py` | 写し。本体と同期 |
| `colab/_write_lora_studio_nb.py` | ノート生成。`SCENE_OPTIONS_3` に三択 |
| `h3-lora-studio/stories/*.json` | 既存話の焼き込み |
| `h3-lora-studio/GROK_PROMPTS.md` | Grok 用の GitHub プロンプト索引 |
| `h3-lora-studio/dump/G_h3_prompts.txt` | 物語・ロック・③生成文の全文。HQ dump ではない |
| `h3-lora-studio/scripts/dump_grok_prompts.py` | 上の2つを再生成 |
| `colab/test_h3_lora_studio.py` | `test_anal_pattern_three_choices` ほか |
| `.cursor/skills/h3-lora-studio/SKILL.md` | 将来セッション用 |
| `h3-lora-studio/README.md` | パターン表 |

## 検証

```bash
cd /workspace
python -c "import ast; ast.parse(open('colab/h3_lora_studio.py').read())"
python h3-lora-studio/scripts/dump_grok_prompts.py --check
python colab/_write_lora_studio_nb.py
python -m pytest colab/test_h3_lora_studio.py h3-lora-studio/tests/test_dump_grok_prompts.py -q
# 三択がノートの③にあること:
python -c "import json; nb=json.load(open('minimax_h3_lora_studio.ipynb')); c=''.join(nb['cells'][6]['source']); assert '①口内で終わる' in c"
```

ノートを直したら FETCH_REV / STUDIO_REV を上げて、py と3つの ipynb と写しを同じコミットに入れる。

## やってはいけない

- Threads / アフィ投稿の schedule を戻す（停止は故障ではない）
- 秘密を git に書く
- 体験談の捏造、#PR なしのリンク投稿
- 数字を発明する（動画判定は `video-judge.js`、insight.js を YouTube に使わない）
- ジャンル転換
- いいね／フォロー自動、人間を装う返信
- 物語チェーンの各本は10秒。ワンショット生成だけ最大15秒。チェーンを15秒にするな
- 男性キャラ・未成年。出演は 21+
- 作業ブランチ以外への勝手なマージ。YAML cron だけデフォルトブランチが必要（この PR では不要）

## 脱糞（コードに入っている注意）

コード側: `lock_scat_act` / `lock_scat_look`（ソーセージ状の固形。ゼリー／スライムではない。今出している。塗れではない）。脱糞は ThumbInButt を積む（積まないとマンコから出る。トリガーは書かない）。アナルセックスには積まない。医院・終電は `No feces.` のまま。既存話の飲尿はジュボのまま戻さない。

デフォルト以外の場所: ③「脱糞（どの構図）」＋体位＋文章欄。物語を選ぶな。山小屋／ニクカベ肥溜めは塗れパック。

## clinic-75s（正。スタブ禁止）

ファイル: `h3-lora-studio/stories/clinic-75s.json`。9 clips / duration_s 90 / canvas 1024x576 16:9。

キャスト: Doctor = 竿20cm。Aya = 口と穴・竿なし。Rei なし。騎乗なし。女医は仰向けにしない。download に cinema-dy なし。JPGをリポジトリに入れるな。

台詞（漢字はカナ。`validate_story_follow`）:
- c1 `こんにちは`
- c3 `ありがとう！ゴホウビです`
- c4 `おしっこ、あったかーい！ありがとー！`
- c9 `ゲンキになりましたか` / `はい、スッキリしました`
- c2 c5–c8 は無言

ビート:
- 0-10 c1 SEATED on pipe chair。しゃがみジュボ。PULLED BACK 16:9。ジュボ中も医師の顔がフレームに残る。lip-sync なので `Full bodies from head to feet` を書くな
- 10-20 c2 10秒ずっとジュボ。竿は涎でテカる。口の端から涎。医師メチャクチャ気持ちよさそう。口を外すな。立つな。キスするな。無言
- 20-30 c3 口を外す。医師笑顔 `ありがとう！ゴホウビです` → 先っぽから黄色い小便をアヤの顔へ。目を閉じ口を開け笑顔で顔と口で受ける。白禁止。精液禁止。カメラは医師の顔＋小便の線＋アヤの顔
- 30-40 c4 小便終わり。顔・髪・体が黄色い小便まみれ。`おしっこ、あったかーい！ありがとー！` → 濃厚ベロチュー
- 40-50 c5 向き転換→LOOKBACK→両手床→両膝→自分で尻を開く→医師が後ろに膝→先端が outer ring of the anus entrance に接触。未挿入。まみれを落とすな
- 50-60 c6 同じ姿勢のままその輪から根元まで挿入。まみれを落とすな
- 60-70 c7 パコパコ。行為中キスなし。まみれを落とすな
- 70-80 c8 アナル中出し（白）→抜いて垂れ。まみれを落とすな
- 80-90 c9 ゲンキ／スッキリ。まだまみれ

c5–c8: `30 degrees` + `SAME DIRECTION` + `NO KISS` + `PULLED BACK`。語 `rim` / `縁` はファイル全体でゼロ。使え: `the outer ring of the anus entrance`。

origin に PLACEHOLDER / `use local artifacts` が乗ったら pull するな。全文を残して force-with-lease。artifacts の anal-14 helper を origin にコピーするな。

## checkup-100s

キャストは変えるな。レイ竿20cm + 医師竿なし・玄関。canvas と CAMERA だけ 16:9。アヤ受けに戻すな。

## 秒数

物語チェーンの各本は10秒。ワンショット生成だけ最大15秒。チェーンを15秒にするな。helper の `FL2VA_MAX_CLIP_S` はワンショット経路だけ15。`STORY_CLIP_S` は10。

## 未着手・次に来そうなこと

- 既存の帰宅などを、③の三択で上書きする（今は焼き込み固定。三択は汎用40秒）
- Drive 上の古いノートがまだ開かれている（コードでは直せない。リンクから開き直す）
- 休日／縁側の2回戦を他の話にも足す、と頼まれたら例外が増えるので安易に広げない
- PR #138 は draft のまま。マージするな。ユーザーがレビューしてと言うまで ready にしない
- Grok dump（`GROK_PROMPTS.md` / `G_h3_prompts.txt`）は JSON を変えたら `python3 h3-lora-studio/scripts/dump_grok_prompts.py --write`

## このチャットの最後の返答（ユーザー向け）

clinic-75s は 9本90秒 16:9。c2 ずっとジュボ。c3 ゴホウビ小便を顔へ。c4 まみれベロチュー。c5-c9 まみれ残し。JPGをリポジトリに入れるな。版 `h3-20260914-anal-18`。枝 `cursor/h3-anal-stories-f112`。新枝禁止。PR138マージ禁止。
