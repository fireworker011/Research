"""Rebuild colab/factory_extension.b64 from a factory tree, in the format the Colab cell reads.

Usage: python rebuild_bundle.py <extensions/sd-diff-set> [--zip out.zip]

The bundle is a base64 line of a zip whose entries are under ``extension/``. Tests, local output,
``config.json``, caches and the bundle itself are left out, which is what the shipped bundle did.
The Colab cell downloads the zip from Drive, so upload ``--zip`` over the Drive file as well.
"""

from __future__ import annotations

import argparse
import base64
import io
import sys
import zipfile
from pathlib import Path

SKIP_DIRS = frozenset({"tests", "out", "__pycache__", ".pytest_cache", ".git"})
SKIP_FILES = frozenset({"config.json", "factory_extension.b64"})
PREFIX = "extension/"


def collect(root: Path) -> list[Path]:
    found: list[Path] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in relative.parts[:-1]):
            continue
        if path.name in SKIP_FILES or path.suffix == ".pyc":
            continue
        found.append(path)
    return found


def build_zip(root: Path) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in collect(root):
            name = PREFIX + path.relative_to(root).as_posix()
            try:
                info = zipfile.ZipInfo.from_file(path, name)
            except ValueError:
                info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes())
    return buffer.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("extension", type=Path)
    parser.add_argument("--zip", type=Path, help="also write the plain zip (the file to put on Drive)")
    args = parser.parse_args()
    root = args.extension.resolve()
    if not (root / "sd_diff_set" / "ui.py").is_file():
        print(f"{root} does not look like the extension folder", file=sys.stderr)
        return 2
    data = build_zip(root)
    target = root / "colab" / "factory_extension.b64"
    target.write_text(base64.b64encode(data).decode("ascii"), encoding="ascii")
    if args.zip:
        args.zip.write_bytes(data)
    print(f"{len(collect(root))} files, {len(data)} bytes zipped, wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
