"""Apply the factory patches by content, not by line number or line ending.

Usage: python apply_patches.py <extensions/sd-diff-set> [--check] [--patch FILE ...]

`git apply` fails on a Windows checkout when the files have CRLF line endings or have drifted a few lines.
This tool reads the same patch files, finds each hunk's old text in the target file (ignoring line endings
and line numbers), and replaces it. It keeps each file's own line ending, skips a hunk that is already applied,
and writes nothing for a file unless every hunk of that file matched. Run with --check first.

By default it applies 0001-face-pass-mode.patch and then 0002-limb-repairs-feed-the-diffs.patch from this folder.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PATCHES = ("0001-face-pass-mode.patch", "0002-limb-repairs-feed-the-diffs.patch")
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")


@dataclass
class Hunk:
    start: int
    old: list[str] = field(default_factory=list)
    new: list[str] = field(default_factory=list)


@dataclass
class FilePatch:
    path: str
    is_new: bool = False
    hunks: list[Hunk] = field(default_factory=list)


def parse(text: str) -> list[FilePatch]:
    patches: list[FilePatch] = []
    current: FilePatch | None = None
    hunk: Hunk | None = None
    for raw in text.replace("\r\n", "\n").split("\n"):
        if raw.startswith("diff --git "):
            match = re.match(r"diff --git a/(.+) b/(.+)$", raw)
            current = FilePatch(path=match.group(2) if match else raw)
            patches.append(current)
            hunk = None
        elif current is None:
            continue
        elif raw.startswith("new file mode"):
            current.is_new = True
        elif raw.startswith(("--- ", "+++ ", "index ", "deleted file", "similarity", "rename ")):
            if raw.startswith("--- /dev/null"):
                current.is_new = True
            hunk = None if not raw.startswith(("--- ", "+++ ")) else hunk
        elif HUNK.match(raw):
            hunk = Hunk(start=int(HUNK.match(raw).group(1)))  # type: ignore[union-attr]
            current.hunks.append(hunk)
        elif hunk is not None:
            if raw.startswith("\\"):
                continue
            tag, body = raw[:1], raw[1:]
            if tag == " ":
                hunk.old.append(body)
                hunk.new.append(body)
            elif tag == "-":
                hunk.old.append(body)
            elif tag == "+":
                hunk.new.append(body)
    return patches


def eol_of(data: bytes) -> str:
    return "\r\n" if data.count(b"\r\n") > data.count(b"\n") / 2 else "\n"


def find_block(text: str, lines: list[str], hint: int) -> list[int]:
    """Start offsets (as line indexes) where ``lines`` appear as whole consecutive lines."""
    body = text.split("\n")
    size = len(lines)
    hits = [i for i in range(len(body) - size + 1) if body[i : i + size] == lines]
    return sorted(hits, key=lambda i: abs(i + 1 - hint))


def loosely_applied(text: str, old: list[str], new: list[str]) -> bool:
    """Every added line is present and no removed line is: the hunk was applied and then touched nearby."""
    present = set(text.split("\n"))
    added = [line for line in new if line.strip() and line not in old]
    removed = [line for line in old if line.strip() and line not in new]
    return bool(added) and all(line in present for line in added) and not any(line in present for line in removed)


def apply_hunks(text: str, patch: FilePatch) -> tuple[str, list[str]]:
    notes: list[str] = []
    for number, hunk in enumerate(patch.hunks, start=1):
        old, new = list(hunk.old), list(hunk.new)
        if old == new:
            continue
        hits = find_block(text, old, hunk.start) if old else []
        if hits:
            if len(hits) > 1:
                notes.append(f"hunk {number}: {len(hits)} places match, took the one nearest line {hunk.start}")
            body = text.split("\n")
            index = hits[0]
            body[index : index + len(old)] = new
            text = "\n".join(body)
            continue
        if new and find_block(text, new, hunk.start):
            notes.append(f"hunk {number}: already applied")
            continue
        if loosely_applied(text, old, new):
            notes.append(f"hunk {number}: already applied (a later edit changed its surroundings)")
            continue
        raise ValueError(f"hunk {number} (near line {hunk.start}) does not match: first old line {old[0]!r}" if old else f"hunk {number} has nothing to anchor on")
    return text, notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("extension", type=Path, help="the sd-diff-set extension folder")
    parser.add_argument("--check", action="store_true", help="report only, write nothing")
    parser.add_argument("--patch", action="append", type=Path, help="patch file (default: 0001 then 0002)")
    args = parser.parse_args()
    root = args.extension.resolve()
    if not (root / "sd_diff_set" / "planner.py").is_file():
        print(f"{root} does not look like the extension folder", file=sys.stderr)
        return 2
    patch_files = args.patch or [HERE / name for name in DEFAULT_PATCHES]
    failed = 0
    texts: dict[Path, str] = {}
    eols: dict[Path, str] = {}
    sample_eol = eol_of((root / "sd_diff_set" / "planner.py").read_bytes())
    for patch_file in patch_files:
        print(f"== {patch_file.name}")
        for patch in parse(patch_file.read_text(encoding="utf-8")):
            relative = patch.path.split("/", 1)[1] if patch.path.startswith("sd-diff-set/") else patch.path
            target = root / relative
            if patch.is_new:
                body = "\n".join(line for hunk in patch.hunks for line in hunk.new) + "\n"
                if target.exists() or target in texts:
                    current = texts.get(target)
                    if current is None:
                        current = target.read_bytes().replace(b"\r\n", b"\n").decode("utf-8")
                    print(f"  {'same' if current == body else 'EXISTS, left alone'}: {relative}")
                    failed += 0 if current == body else 1
                    continue
                print(f"  new file: {relative} ({'CRLF' if sample_eol == chr(13) + chr(10) else 'LF'})")
                texts[target] = body
                eols[target] = sample_eol
                continue
            if target not in texts:
                if not target.is_file():
                    print(f"  MISSING: {relative}")
                    failed += 1
                    continue
                data = target.read_bytes()
                eols[target] = eol_of(data)
                texts[target] = data.decode("utf-8").replace("\r\n", "\n")
            try:
                updated, notes = apply_hunks(texts[target], patch)
            except ValueError as exc:
                print(f"  FAILED {relative}: {exc}")
                failed += 1
                continue
            texts[target] = updated
            label = "CRLF" if eols[target] == "\r\n" else "LF"
            print(f"  ok {relative} ({label}, {len(patch.hunks)} hunks){' ' + '; '.join(notes) if notes else ''}")
    if not args.check and not failed:
        for target, text in texts.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.replace("\n", eols[target]).encode("utf-8"))
    elif not args.check:
        print("a patch failed, so nothing was written")
    print("nothing written (--check)" if args.check else ("done" if not failed else ""))
    print(f"{failed} problem(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
