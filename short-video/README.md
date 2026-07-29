# ショート動画制作パイプライン（縦1080x1920 / 30fps / 顔出しなし）

台本 JSON から、ナレーション・背景・テロップ・BGM を組み立てて mp4 を書き出す。
API キーが 1 つも無くても最後まで通る（音声はモック無音、背景はコード生成）。
キーを足して同じコマンドを流し直すと、本番音声・実写素材に差し替わる。

## 使い方

```bash
cd short-video
npm install
npm run prepare:all      # フォント → 台本検証 → 音声 → 素材 → BGM → タイムライン
npm run render           # out/short.mp4 を書き出し
npm run check            # 投稿前チェック
```

プレビューしながら調整したいときは `npm run studio`（ブラウザで開く）。

## API キー（任意）

| 環境変数 | 用途 | 無いとき |
|---|---|---|
| `GOOGLE_TTS_API_KEY` または `GOOGLE_APPLICATION_CREDENTIALS` | Google TTS Chirp3-HD `ja-JP-Chirp3-HD-Orus` | モック無音（尺だけ本番相当） |
| `DASHSCOPE_API_KEY` | Qwen3-TTS（Google の代替） | 同上 |
| `PEXELS_API_KEY` | portrait 向きストック動画 | コード生成のグラデーション背景 |

```bash
export GOOGLE_TTS_API_KEY=xxx
export PEXELS_API_KEY=yyy
npm run prepare:all && npm run render && npm run check
```

音声のモックは**尺だけ本番相当**に作ってある（モーラ数から推定）。
先にモックで構成・テロップを固めて、最後にキーを入れて本番音声で回す、という進め方ができる。

## ファイルの役割

| 場所 | 役割 |
|---|---|
| `script.json` | 台本（確定稿）。ここだけが編集対象 |
| `pronunciation.json` | TTS に渡す直前の読み替え。`script.json` は書き換えない |
| `scripts/validate-script.mjs` | STEP2 構造検証 + 表現検品（収益の断定・誇大表現） |
| `scripts/gen-voice.mjs` | STEP3 ナレーション生成（Google / Qwen / モック） |
| `scripts/fetch-media.mjs` | STEP4 背景素材（Pexels / グラデーション生成） |
| `scripts/make-bgm.mjs` | STEP6 BGM を合成（権利処理不要） |
| `scripts/build-timeline.mjs` | 音声実測値からシーン尺を決めて `public/timeline.json` を生成 |
| `scripts/preflight.mjs` | STEP8 投稿前チェック（解像度 / fps / 尺 / CTA / 音量） |
| `src/Short.tsx` | STEP5 本体。背景 + テロップ + 音声 + BGM の組み立て |
| `src/theme.ts` | テロップのサイズ・色。見た目の調整はまずここ |

## 設計のきまり

1. **`script.json` は確定稿として扱う。** 読みの修正は `pronunciation.json` の置換で行う。
   台本そのものを直したい箇所は `pronunciation.json` の `review_required` に書き出して人が判断する。
2. **尺は音声の実測値から決める。** ハードコードしない。TTS エンジンを変えても
   `npm run timeline` を流せばシーン尺・BGM のダッキング位置が全部追従する。
3. **60 秒に収める。** 収まらない場合はシーン間の余白を自動で詰め、それでも超えるなら警告を出す
   （台本を削るのは人の判断）。
4. **モックでも本番でもマニフェストの形は同じ。** 生成手段が変わっても `src/` は無改造。
5. **収益の断定・誇大表現は検証で落とす。** `validate-script.mjs` の `BANNED` に列挙。
   景品表示法（優良誤認・有利誤認）と各プラットフォーム規約への配慮。

## 素材のライセンス

- **BGM**: `make-bgm.mjs` が合成している。権利処理不要。差し替えるなら `public/bgm/bgm.wav` を上書き。
- **背景（キーなし）**: コード生成。権利処理不要。
- **背景（Pexels）**: Pexels License。商用利用可・クレジット任意。素材単体の再配布/販売は不可。
  出典は `public/media/media-manifest.json` に記録される。
- **フォント**: IPAゴシック（IPAフォントライセンス）。`npm run font` が環境から探してコピーする。
  リポジトリには含めない。

## よくある調整

```bash
# 話速を変える（尺が 60 秒に収まらないとき）
TTS_SPEAKING_RATE=1.2 npm run voice && npm run timeline

# 別のボイスを試す
TTS_VOICE=ja-JP-Chirp3-HD-Aoede npm run voice && npm run timeline

# キーがあってもモックで確認したい
FORCE_MOCK_TTS=1 npm run voice && npm run timeline
```

テロップのサイズ・色は `src/theme.ts`、表示位置は `src/components/Telop.tsx` の `TELOP_TOP`。
BGM 音量とダッキング量は `scripts/make-bgm.mjs` の manifest 出力部分。
