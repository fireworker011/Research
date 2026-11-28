import subprocess

A100_OR_BETTER = ("A100", "H100", "H200", "B100", "B200", "GH200")
MIN_VRAM_MIB = 38000


def gpu_is_a100_or_better(name, vram_mib):
    upper = str(name).upper()
    named = any(token in upper for token in A100_OR_BETTER)
    return named and int(vram_mib) >= MIN_VRAM_MIB


def gpu_stop_message(name, vram_mib):
    return (
        "このノートは A100 以上の GPU が必要です。小さい GPU ではここで止めます。生成は開始しません。\n"
        f"検出した GPU: {name} / {vram_mib} MiB\n"
        "ランタイム → ランタイムのタイプを変更 → A100 を選び、ランタイムを接続し直してから、最初のセルを再実行してください。\n"
        "T4 / L4 / V100 / A10 では動きません。"
    )


def parse_nvidia_smi(text):
    rows = []
    for line in str(text).splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) < 2 or not parts[0]:
            continue
        mem = parts[1].lower().replace("mib", "").strip()
        try:
            vram = int(float(mem))
        except ValueError:
            continue
        rows.append((parts[0], vram))
    return rows


def evaluate_gpus(rows):
    if not rows:
        return False, "(なし)", 0, gpu_stop_message("(なし)", 0)
    good = [row for row in rows if gpu_is_a100_or_better(row[0], row[1])]
    if good:
        name, vram = max(good, key=lambda row: row[1])
        return True, name, vram, ""
    name, vram = max(rows, key=lambda row: row[1])
    return False, name, vram, gpu_stop_message(name, vram)


def assert_a100_or_stop():
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        message = gpu_stop_message("(nvidia-smi 失敗)", 0)
        print(message)
        if result.stderr.strip():
            print(result.stderr.strip())
        raise RuntimeError(message)
    ok, name, vram, message = evaluate_gpus(parse_nvidia_smi(result.stdout))
    if not ok:
        print(message)
        raise RuntimeError(message)
    print(f"GPU OK: {name} / {vram} MiB（A100 以上）")
    return name, vram


_GPU_NAME, _GPU_VRAM = assert_a100_or_stop()
GPU_OK = True
