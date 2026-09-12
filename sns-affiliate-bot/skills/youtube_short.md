# スキル: YouTube Shorts 自動生成・アップロード

## 実行コマンド
```bash
python main.py post youtube career
```

## やること
1. career.json からニッチ設定を読み込む
2. ContentGenerator で台本を生成（タイトル + シーン構成 + CTA）
3. 台本の概要を表示して確認を求める
4. 確認後に動画生成:
   - Pexels API から背景画像を取得
   - VOICEVOX でナレーション音声を生成
   - FFmpeg で画像 + 音声 + テロップを合成
5. YouTube Shorts としてアップロード（最初は private 推奨）
6. 結果を `queue/youtube/career/` に保存

## 守るべきルール
- YouTube APIの1日アップロード上限: 6本
- スケジュール: 10:00 / 17:00
- 最初は `privacy="private"` でテスト、問題なければ `"public"` に変更
- 動画時間: 55秒以内（Shorts判定のため）
- タイトルに「#Shorts」を必ず含める
- VOICEVOX を先に起動しておく（localhost:50021）
