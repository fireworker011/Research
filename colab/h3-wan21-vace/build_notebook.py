#!/usr/bin/env python3
"""Rebuild wan21_vace_14b_colab.ipynb from the cell sources."""

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook
from pathlib import Path

ROOT = Path(__file__).resolve().parent

MARKDOWN = """# Wan2.1 VACE 14B — H3 カット生成

既存の `wan22_i2v_lightx2v_colab.ipynb` と同じく、モデルは Google Drive に一度置いて再利用する。有料 API は使わない。

ランタイムは **A100 以上**。最初のコードセルで、それより小さい GPU は停止する。

上から順に実行する。起動手順とライセンスは同じフォルダの `README.md`。

1. GPU チェック
2. 制御 JSON の読み込みと、OpenPose / Depth / カメラ制御の作成
3. Drive をマウントし、ComfyUI を入れる
4. モデル取得（Drive にあればスキップ）
5. ComfyUI 起動
6. カットごとに 9:16 の mp4 と、使った制御 JSON を書く
7. 生成が終わったらランタイムを切断して削除する

入力は `マイドライブ/ComfyUI_vace_h3/input/face_ref.png` と `input/controls/*.json`。
出力は `マイドライブ/ComfyUI_vace_h3/output/<実行時刻>/`。

このノートを置いた時点では、A100 上の生成は未実施。
"""


def _read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def install_source():
    install = _read("cells/03_install.py")
    node = _read("h3_load_frames.py")
    needle = "from pathlib import Path\n"
    if needle not in install:
        raise RuntimeError("install cell is missing the pathlib import")
    assignment = "NODE_SOURCE = " + repr(node) + "\n"
    return install.replace(needle, needle + "\n" + assignment, 1)


def build():
    sources = [
        ("markdown", MARKDOWN),
        ("code", _read("cells/01_gpu.py")),
        ("code", _read("logic.py")),
        ("code", install_source()),
        ("code", _read("cells/04_download.py")),
        ("code", _read("cells/05_launch.py")),
        ("code", _read("cells/06_generate.py")),
        ("code", _read("cells/07_disconnect.py")),
    ]
    cells = []
    for kind, source in sources:
        if kind == "markdown":
            cells.append(new_markdown_cell(source))
        else:
            cells.append(new_code_cell(source))
    notebook = new_notebook(cells=cells)
    notebook.metadata["colab"] = {"provenance": [], "gpuType": "A100"}
    notebook.metadata["kernelspec"] = {"display_name": "Python 3", "name": "python3"}
    notebook.metadata["language_info"] = {"name": "python"}
    notebook.metadata["accelerator"] = "GPU"
    path = ROOT / "wan21_vace_14b_colab.ipynb"
    nbformat.write(notebook, path)
    return path


if __name__ == "__main__":
    print(build())
