---
format: 1920x1080
duration: 30s
message: "夜の都市を、光の文字と一緒に飛び抜ける"
arc: "降下 → ネオン → 軌跡 → 夜航"
audience: "CursorでHyperFramesのモーショングラフィックスを再現したい人"
mode: autonomous
---

## Frame 1 — 降下

- scene: 高い位置から街の谷へ降り、左上に「降下」が叩きつけられる
- duration: 6.8s
- poster: 2.2
- transition_in: cut
- status: animated
- src: index.html
- blueprint: kinetic-beat-slam
- rules: chromatic-glitch, ambient-glow-bloom

カメラは高い進入から谷へ。言葉は左上。マゼンタの光が言葉の後ろで咲く。

## Frame 2 — ネオン

- scene: 通りの高さで右へ「ネオン」が着地する
- duration: 6.8s
- poster: 9.2
- transition_in: cut
- status: animated
- src: index.html
- blueprint: kinetic-beat-slam
- rules: chromatic-glitch, ambient-glow-bloom

街の窓がマゼンタとシアンに灯る。言葉は右。光の帯が車道に沿って流れる。

## Frame 3 — 軌跡

- scene: 左下の「軌跡」と、前方でほどけるワイヤフレーム
- duration: 6.8s
- poster: 16.6
- transition_in: cut
- status: animated
- src: index.html
- blueprint: kinetic-beat-slam
- rules: chromatic-glitch, ambient-glow-bloom

抽象の立体が前方で姿を現す。軌跡のリボンは時間だけの関数。

## Frame 4 — 夜航

- scene: 上昇しながら左下に「夜航」と「光の中を抜ける」が残る
- duration: 8.2s
- poster: 26.5
- transition_in: cut
- status: animated
- src: index.html
- blueprint: kinetic-beat-slam
- rules: ambient-glow-bloom

言葉は退出せず保持する。カメラは立体を見上げて上がる。
