# エピソード一発（MiniMax H3 → 完成動画）

`episode.json` 1つとスチール数枚を置くと、Colab の Run all 一発で
**全ビート生成 → HUD 合成 → タイトル／免責エンドカード → 音声クロスフェード連結** まで終わり、
Drive `minimax-h3-comfyui/episodes/<slug>/final/<slug>-<日時>.mp4`（と `latest.mp4`）が出る。

ネタを変えるときは `_template/` を複製して `episode.json` とスチールを差し替えるだけ。コードは触らない。

| 場所 | 中身 |
|---|---|
| `minimaxh3/episodes/<slug>/episode.json` | 唯一の入力（世界観・キャスト・小道具ロック・ビート・台詞・HUD 状態・免責） |
| `minimaxh3/episodes/<slug>/stills/*.jpg` | クリーンな先頭フレーム。HUD を焼き込まない。1280×720 でよい（1024×576 に自動で正規化） |
| `minimaxh3/h3_episode.py` | スキーマ検査・プロンプト生成と検査・ステージング・レンダ・HUD・連結・CLI |
| `minimaxh3/h3_hud.py` | HUD／カード描画と ffmpeg（compose / card / stitch / last-frame） |
| `minimaxh3/h3_episode_colab_main.py` | Colab のヘッドレス入口（env で slug・preset・fresh） |
| `minimax_h3_episode_bot.ipynb` | ワンクリック用ノート。コードセル1本。`colab/_write_episode_nb.py` で再生成 |
| `minimaxh3/grokbot/run_episode.py` | colab CLI からの一発（Automation ではない） |
| `colab/test_h3_episode.py` | スキーマ／プロンプト／LoRA チェーン／OOM／HUD／連結／隔離の回帰テスト |

## 一発の実行

**スマホ／ブラウザ**: [minimax_h3_episode_bot.ipynb](../../minimax_h3_episode_bot.ipynb) を Colab で開き、`EPISODE` に slug、`PRESET` を選んで Run all。
GPU は A100（High-RAM）。終わるとランタイムを自分で手放す。

**PC（colab CLI）**:

```bash
python minimaxh3/grokbot/run_episode.py --episode bandai-district            # 全部
python minimaxh3/grokbot/run_episode.py --episode bandai-district --fresh    # raw を捨てて作り直し
python minimaxh3/grokbot/run_episode.py --episode bandai-district --dry-run  # コマンド確認だけ
```

**GPU なしで確認**（この順で使う）:

```bash
cd minimaxh3
python h3_episode.py check   episodes/bandai-district                 # スキーマ＋プロンプト検査＋フォント＋ffmpeg
python h3_episode.py prompts episodes/bandai-district                 # logs/<beat>.prompt.txt を書く
python h3_episode.py stills  episodes/bandai-district --out /tmp/ep   # スチール保持の予告（HUD・カード・連結は本番と同じ）
python h3_episode.py dry-run episodes/bandai-district --out /tmp/ep   # 合成クリップで全パイプライン
python h3_episode.py finish  /path/to/episode_root                    # raw/*.mp4 があるとき HUD＋連結だけやり直す
```

`--out` を付けるとリポジトリのフォルダを汚さない。付けないと `episodes/<slug>/` 直下に raw/hud/final ができる（git に入れない）。

## 途中で止まったら

`raw/<beat>.mp4` が残っているビートは飛ばして続きから描く。壊れた本だけ消して再実行、または `FRESH`（`--fresh`）で全部作り直し。
進行は `status.json`、各本のプロンプトは `logs/<beat>.prompt.txt`。

## episode.json の決まり

- 英語で書く。日本語は台詞の中身だけ（`speech[].line`、かな限定、`「」` は自動で付く）。HUD の文言（`hud.mission` など）は日本語でよい（画面に後載せするだけで H3 には渡さない）
- 1ビート = 1場所 1動作 10秒。`clip_seconds` は 4〜10。15秒は使わない（OOM でキャンバスが縮む）
- `source`: `still`（クリーンな先頭フレーム）／`chain`（前の本の最後のコマから続ける。先頭の本では使えない）／`t2v`（先頭フレームなし）
- 台詞は `face_visible: true` の本だけ、1本2行まで
- `cast[].age` は成人（20以上）。子供は画面にも文にも入れない（自動で「Adults only in frame」を付け、未成年語は検査で落ちる）
- `violence: "game"` ＋ ビートの `physics: true` で「大人がラグドールで飛ぶ・血なし・怪我なし」の文を自動で足す。流血・ゴア語は正の文で書くと落ちる
- `homage.never` に、参照元の固有要素（物・人名・小道具）を並べる。プロンプトに出たら落ちる。ブランド／IP 名（格ゲー・オープンワールドの実名、Pollo、Seedance）と「HUD・ミニマップ・字幕・透かし」を H3 に描かせる語も落ちる。`lip-synced` などの英語メタも落ちる（H3 が読み上げる）
- `cards.disclaimer` は必須。エンドカードに「架空のゲームのコンセプト映像」を出す
- `canvas`: `16:9`（1024×576）か `9:16`（576×1024）。出力は `stitch.output_height` 720 か 1080

## レンダの決まり

- LoRA プリセット: `daily` = Larry v4 1.0 + シネマ DY 0.65 / 8step（トリガー `DY` を先頭に付ける）、`preview` = LightX2V 4step + シネマ 0.5、`fast` = LightX2V 4step のみ。Larry と LightX2V は同時に積まない。ファイルが無ければ `fallback_preset` に落ちる（`status.json` に記録）
- OOM のときはキャンバスを維持して秒数だけ 10→8→6 に落とす。先頭フレームは外さない
- 音は H3 のまま。連結は xfade + acrossfade 0.35秒 + loudnorm。`transition: "cut"` で直結

## 本番を壊さないための境界

- Drive は `episodes/<slug>/` の下だけに書く。`inbox/queued/running/done/failed/input/output` は触らない。`models/` は読むだけ
- 本番 I2V の `drop_job.py` / `run_i2v.py` / 15分 Automations にエピソードを入れない（裸 jpg はココナラ I2V に拾われ、Imagine 既定文でキャラが消える）
- Imagine 2.0 は呼ばない。`XAI_API_KEY` は不要
- helper は GitHub のブランチから `/content` へ取り、Drive は `episodes/_lib/` にだけキャッシュ。本番ルート直下の同名ファイルは上書きしない
- LoRA スタジオ（`h3_lora_studio.py`、③、STORY）には足さない
- 投稿しない。アフィ URL・収入主張はプロンプトに入れない（検査で落ちる）

## 番台ディストリクト（完成例）

9ビート × 10秒 ＋ タイトル 2.6秒 ＋ エンド 3.2秒 ≈ 92秒。暖簾 → 自転車 → 理容室 → 会話 → 軽トラ → 吹き飛び走行 → 蒸気アッパー → 釜爆発 → 着地。
借りたのは三人称カメラとミッション字幕の文法、日常クエストが裏返る構成、爆発で締める着地だけ。舞台・人物・物語はオリジナル。参照元の要素は `homage.never` で禁止。
