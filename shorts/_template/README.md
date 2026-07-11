# 完全自立型YouTube Shorts制作エージェント — 雛形

婚活ジャンル(`shorts/pc/06_婚活/`)で実績が出た「市場リサーチ→台本→Grokフル
Agent Mode完結プロンプト→投稿→数値分析」の自動化フローを、他ジャンルでも
使えるように汎用化したテンプレートです。

## 中身

```
_template/
├── AGENT_TEMPLATE.md          ← エージェント定義の雛形(【 】を埋めて使う)
└── pipeline/                  ← ジャンル非依存の実装(コピーするだけで動く)
    ├── run.py                 (合成・投稿オーケストレーター)
    ├── assemble.py             (FFmpeg合成・テロップ焼込)
    ├── tts.py                  (Edge TTSナレーション生成)
    ├── upload.py                (YouTube投稿)
    ├── make_prompts.py          (台本JSON→Grok用プロンプト自動生成)
    ├── requirements.txt
    ├── assets/fonts/            (テロップ用フォント)
    └── scripts_json/
        └── 001_example.json    (台本JSONのテンプレート。[ ]を埋めて使う)
```

## 新ジャンルを始める手順

1. `shorts/pc/0X_ジャンル名/` を作成
2. `_template/pipeline/` を丸ごと `shorts/pc/0X_ジャンル名/pipeline/` にコピー
   (Pythonコードはジャンル非依存なので変更不要)
3. `_template/AGENT_TEMPLATE.md` を `shorts/pc/0X_ジャンル名/AGENT.md` として
   コピーし、【 】の項目(ペルソナ・案件・アフィリンク・キャラ設定・切り口)を埋める
4. `pdca.md`(空のログ)を新規作成、または婚活の`pdca.md`をコピーして中身を空にする
5. Claudeに「`shorts/pc/0X_ジャンル名/AGENT.md` を読んで市場リサーチから始めて」
   と指示すれば、以降は毎回同じ起動コマンドで自動運用に入る

## 起動コマンド(コピー先で共通)

```
shorts/pc/0X_ジャンル名/AGENT.md を読んで次の動画を作って。
アナリティクス: [あれば数値を貼る]
```

これだけで、市場リサーチ→台本生成→GrokフルAgent Mode完結プロンプトの納品
までを毎回自動実行します。ユーザーの作業は「Grokに貼る→完成動画をアップ→
公開」の3ステップだけです。
