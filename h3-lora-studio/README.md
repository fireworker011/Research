# h3-lora-studio

MiniMax H3 の LoRA を **シチュエーション × モード** で積む / 外す。Comfy の homage グラフ（ココナラ）とは別物。

成人向け profile は **21歳以上のみ**。Turbo はオフ。API キーは `.env` だけ。

## シチュエーション切替

`profiles/*.json` がシチュエーション。`--mode t2v|i2v` で同じ状況の T2V / I2V を出す。enabled 以外はアンロード。

| situation | T2V に積む | I2V に積む |
|---|---|---|
| `anal_penetration` | Realism + HMNSFW AIO | 同じ |
| `oral` | Realism + deepthroat | 同じ |
| `riding` | Realism + HMNSFW AIO（riding LoRA は I2V 専用） | Realism + riding pose |

```bash
cd h3-lora-studio
python scripts/select_loras.py --list
python scripts/select_loras.py --situation anal_penetration --mode t2v --prompt '（シーン）'
python scripts/select_loras.py --profile anal_penetration --mode i2v --prompt '（シーン）'
```

`--prompt '（シーン）'` は `scenes.<mode>` を使う。T2V に I2V の Picture 1 文面は使わない。

| モード | キャンバス | first_frame |
|---|---|---|
| T2V | 9:16 576×1024 | なし |
| I2V | 8:9 768×864 | 必須（`<Picture 1>`） |

出力 JSON:

- `stack` … そのシチュエーションの **enabled だけ**
- `unload` … 他シチュエーション / Turbo / FL2VA に使えない ref2va
- `turbo: false` … `res_multistep` / `beta` / **16 step**
- キー名も値も API キーを含まない

## 不変条件

1. Turbo / Acc LoRA を enabled にしない
2. T2V / I2V（FL2VA）に ref2va LoRA を積まない
3. T2V プロンプトに Picture 1 / first_frame を入れない
4. shota / loli / child / teen を catalog・prompt に入れない
5. `.env` を読まない・ログに出さない。実キーは Git 禁止
6. ココナラ homage の turbo 4-step 既定を変えない
7. Live2D の `syota` アセットを使わない

## キー

```bash
cp .env.example .env
# XAI_API_KEY= と HF_TOKEN= はローカルの .env だけ
```

`select_loras.py` は `.env` を開かない。
