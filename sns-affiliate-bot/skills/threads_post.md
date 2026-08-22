# スキル: Threads 自動投稿

## 実行コマンド
```bash
python main.py post threads career
```

## やること
1. career.json からニッチ設定を読み込む
2. ContentGenerator でコンテンツを生成（フック + 本文 + CTA + アフィリエイトリンク）
3. 投稿内容を画面に表示して確認を求める
4. 確認後に Threads API でテキスト投稿
5. 投稿結果を `queue/threads/career/` に保存

## 7日分まとめて生成してキューに保存する場合
```bash
python main.py generate threads career 7
```

## 守るべきルール
- 1日の投稿上限: 3件（Threads API レート制限: 250件/日）
- スケジュール: 08:00 / 12:00 / 19:00
- 投稿前に必ず内容を確認する（半自動モード）
- アフィリエイトリンクは必ず含める
- ハッシュタグは8個以内
