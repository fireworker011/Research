# H3 LoRA Studio 引き継ぎ（アナル三択）

新規チャット用。Naomiichi（プロダクト）。質問せず、このファイルと `.cursor/skills/h3-lora-studio/SKILL.md` を読んでから作業する。

## 新規チャットに貼る文

```
MiniMax H3 LoRA Studio を続ける。会話が長くなったので新規チャット。Naomiichi。

まず読め:
- `.cursor/skills/h3-lora-studio/SKILL.md`
- `h3-lora-studio/HANDOVER.md`
- `h3-lora-studio/README.md` の「アナルセックスの3パターン」

作業ブランチ: `cursor/h3-anal-stories-f112`
ベース: `cursor/h3-cabin-flow-f112`
PR: https://github.com/fireworker011/Research/pull/138 （draft）
Colab: https://colab.research.google.com/github/fireworker011/Research/blob/cursor/h3-anal-stories-f112/minimax_h3_lora_studio.ipynb
設定の版: `h3-20260913-anal-5`

Threads の schedule を戻すな。アナル本に cowgirl / riding / doggy / AIO / Final Thrust / ThumbInButt / CUMOUF / hmmotion を積むな。

直近: 脱糞は ThumbInButt を積む（積まないとマンコから出る）。訪問販売の「キャップ」は蓋ではなく頭の帽子（ハット）。GitHub から開き直す。
```

## いまの枝

| 項目 | 値 |
|---|---|
| 作業 | `cursor/h3-anal-stories-f112` |
| ベース | `cursor/h3-cabin-flow-f112` |
| PR | https://github.com/fireworker011/Research/pull/138 draft |
| 版 | `STUDIO_REV` / `FETCH_REV` = `h3-20260913-anal-5` |
| ノート | `minimax_h3_lora_studio.ipynb` を3箇所に同じものを書く（root / `minimaxh3/` / `h3-lora-studio/`） |

`colab/h3_lora_studio.py` と `minimaxh3/h3_lora_studio.py` は同期する。ノートは `python colab/_write_lora_studio_nb.py` で再生成。手で ipynb を直さない。

## ユーザーが求めたもの

アナルセックスを既存の物語パターンに入れる。3パターン。会話とタイムラインも直す。

1. **①口内で終わる** … 根元ジュボ → 口内射精。口移しあり
2. **②フェラのあとアナル** … 根元ジュボで**出さない** → 抜く → アナル挿入オンカメラ → アナル中出し
3. **③会って即アナル** … 濃厚ベロチュー＋胸揉み＋竿／マンコこすり（挿入でもジュボでもない）→ アナル挿入 → アナル中出し

体位は場面で変える（正常位・後背・立ち後背・騎乗・後輩騎乗・座位・後背座位）。結合部が見える後背／立ち後背を多めにするが無理はしない。

あとで「選択肢にアナルの三択ないよ？」→ 焼き込みだけではドロップダウンに出ない。③に3行を足した。

## 実装の分かれ方

**A. ③で選ぶ三択そのもの（汎用40秒）**

| ラベル | id | 流れ | 体位欄 |
|---|---|---|---|
| ①口内で終わる | `anal-p1-oral` | 会話 → oral → `oral_creampie` + 口移し | 無視 |
| ②フェラのあとアナル | `anal-p2-bj-anal` | 会話 → oral（出さない）→ `futa_anal` 中出し → 「アナルあつい」 | アナル本に効く |
| ③会って即アナル | `anal-p3-meet-anal` | 会話 → ベロチュー（`NOT oral. NOT insertion`）→ `futa_anal` 中出し | アナル本に効く |

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

- LoRA: Mystic 0.5 + 竿 0.45 + 穴 0.4 だけ。Turbo なし・8step
- 積まない: cowgirl / riding-pose / doggy / AIO / Final Thrust / ThumbInButt / CUMOUF
- `hmmotion` は `futa_sex` だけ。アナル本に載せない
- 精液は白。`lock_anal_creampie` で **アナルからだけ**。使っていないマンコから漏らさない
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
| `colab/test_h3_lora_studio.py` | `test_anal_pattern_three_choices` ほか |
| `.cursor/skills/h3-lora-studio/SKILL.md` | 将来セッション用 |
| `h3-lora-studio/README.md` | パターン表 |

## 検証

```bash
cd /workspace
python -c "import ast; ast.parse(open('colab/h3_lora_studio.py').read())"
python colab/_write_lora_studio_nb.py
python -m pytest colab/test_h3_lora_studio.py -q
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
- 15秒クリップ（VRAM で画面が小さくなる）
- 男性キャラ・未成年。出演は 21+
- 作業ブランチ以外への勝手なマージ。YAML cron だけデフォルトブランチが必要（この PR では不要）

## 脱糞（コードに入っている注意）

コード側: `lock_scat_act` / `lock_scat_look`（ソーセージ状の固形。ゼリー／スライムではない。今出している。塗れではない）。脱糞は ThumbInButt を積む（積まないとマンコから出る。トリガーは書かない）。アナルセックスには積まない。医院・終電は `No feces.` のまま。既存話の飲尿はジュボのまま戻さない。

デフォルト以外の場所: ③「脱糞（どの構図）」＋体位＋文章欄。物語を選ぶな。山小屋／ニクカベ肥溜めは塗れパック。

## 未着手・次に来そうなこと

- 既存の帰宅などを、③の三択で上書きする（今は焼き込み固定。三択は汎用40秒）
- Drive 上の古いノートがまだ開かれている（コードでは直せない。リンクから開き直す）
- 休日／縁側の2回戦を他の話にも足す、と頼まれたら例外が増えるので安易に広げない
- PR は draft のまま。ユーザーがレビューしてと言うまで ready にしない

## このチャットの最後の返答（ユーザー向け）

脱糞は ThumbInButt を積む（積まないとマンコから出る）。訪問販売は蓋のキャップではなく頭のハット。GitHub の Colab から開き直す。版 `h3-20260913-anal-5`。
