# h3-lora-studio

MiniMax H3 の LoRA を **profile 単位で積む / 外す** ための設定器。Comfy の homage グラフ（ココナラ I2V）とは別物。

成人向け profile は **21歳以上のみ**。Turbo はオフ。API キーは `.env` だけ。

## このリクエストの出し方

```bash
cd h3-lora-studio
python scripts/select_loras.py --profile anal_penetration --mode i2v --prompt '（シーン）'
```

`--prompt '（シーン）'` は `profiles/anal_penetration.json` の `scene` を使う。

出力 JSON:

- `stack` … **enabled だけ** を積む順（Realism → HMNSFW AIO）
- `unload` … disabled / Turbo / I2V に使えない ref2va。Comfy に載せない
- `turbo: false` … sampler は `res_multistep` / `beta` / **16 step**。euler 4-step にしない
- `prompt` … I2V シーン。`<Picture 1>` が first frame
- キー名も値も API キーを含まない

## 不変条件

1. Turbo / Acc LoRA を enabled にしない
2. I2V（FL2VA）に ref2va LoRA（AfterMidnight など）を積まない
3. shota / loli / child / teen を catalog・prompt に入れない
4. `.env` を読まない・ログに出さない。実キーは Git 禁止
5. ココナラ homage の turbo 4-step 既定を変えない
6. Live2D の `syota` アセットを使わない

## キー

```bash
cp .env.example .env
# XAI_API_KEY= と HF_TOKEN= はローカルの .env だけ
```

`select_loras.py` は `.env` を開かない。
