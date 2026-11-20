#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p previews

pairs=(
  "MoneyStamp:money-stamp"
  "MoneyReceipt:money-receipt"
  "MoneyTicker:money-ticker"
  "PetPulse:pet-pulse"
  "PetLamp:pet-lamp"
  "PetBounce:pet-bounce"
  "MatchFlip:match-flip"
  "MatchRibbon:match-ribbon"
  "MatchSpot:match-spot"
  "BeautySheen:beauty-sheen"
  "BeautyRipple:beauty-ripple"
  "BeautyFrame:beauty-frame"
  "SleepMoon:sleep-moon"
  "SleepBreath:sleep-breath"
  "SleepCurtain:sleep-curtain"
)

for pair in "${pairs[@]}"; do
  id="${pair%%:*}"
  name="${pair##*:}"
  npx remotion render src/index.ts "$id" "previews/${name}.mp4" --concurrency=2
done
