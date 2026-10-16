# H3 adult monetize (parked)

判定の正本は `DECISION.md`。本線の 100万・Threads・ペット Shorts には混ぜない。デフォルトへマージするな。

モザイク補助（人が枠を書く。検出なし。法令・店舗の绿灯ではない）:

```bash
python3 mosaic_apply.py \
  --in /path/to/source.mp4 \
  --boxes boxes.example.json \
  --out /tmp/h3-mosaic/out.mp4 \
  --sheet /tmp/h3-mosaic/sheet.png
```

テスト:

```bash
cd h3-adult-monetize && python3 -m unittest test_mosaic_apply.py
```
