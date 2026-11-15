"""Apply the factory patches by content, not by line number or line ending.

Usage: python apply_patches.py <extensions/sd-diff-set> [--check] [--patch FILE ...]

`git apply` fails on a Windows checkout when the files have CRLF line endings or have drifted a few lines.
This tool reads the same patch files, finds each hunk's old text in the target file (ignoring line endings
and line numbers), and replaces it. It keeps each file's own line ending, skips a hunk that is already applied,
and writes nothing unless every patch matched. A record of what it applied is kept in .sd-diff-set-patches.json, so
a second run does not repeat a patch; --force ignores the record and relies on per-hunk detection. Run with --check first.

By default it applies 0001 through 0006 from this folder, in that order.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_PATCHES = (
    "0001-face-pass-mode.patch",
    "0002-limb-repairs-feed-the-diffs.patch",
    "0003-lora-check.patch",
    "0004-keep-base-lora-tags.patch",
    "0005-inpaint-keeps-lora.patch",
    "0006-http-inpaint.patch",
)
MARKER = ".sd-diff-set-patches.json"
HUNK = re.compile(r"^@@ -(\d+)(?:,\d+)? \+\d+(?:,\d+)? @@")


@dataclass
class Hunk:
    start: int
    old: list[str] = field(default_factory=list)
    new: list[str] = field(default_factory=list)
    seq: list[tuple[str, bool]] = field(default_factory=list)


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
            if tag == "+":
                hunk.new.append(body)
                hunk.seq.append((body, True))
            elif tag == " ":
                hunk.old.append(body)
                hunk.new.append(body)
                hunk.seq.append((body, False))
            elif tag == "-":
                hunk.old.append(body)
    return patches


def eol_of(data: bytes) -> str:
    return "\r\n" if data.count(b"\r\n") > data.count(b"\n") / 2 else "\n"


def find_block(text: str, lines: list[str], hint: int) -> list[int]:
    """Start offsets (as line indexes) where ``lines`` appear as whole consecutive lines."""
    body = text.split("\n")
    size = len(lines)
    hits = [i for i in range(len(body) - size + 1) if body[i : i + size] == lines]
    return sorted(hits, key=lambda i: abs(i + 1 - hint))


def contains_run(body: list[str], run: list[str]) -> bool:
    size = len(run)
    return any(body[i : i + size] == run for i in range(len(body) - size + 1))


def anchored_runs(hunk: Hunk) -> list[tuple[list[str], list[str], list[str]]]:
    """Each block of added lines with up to three lines of the new text before and after it."""
    found: list[tuple[list[str], list[str], list[str]]] = []
    seq = hunk.seq
    index = 0
    while index < len(seq):
        if not seq[index][1]:
            index += 1
            continue
        end = index
        while end < len(seq) and seq[end][1]:
            end += 1
        run = [line for line, _ in seq[index:end]]
        before = [line for line, _ in seq[max(0, index - 3) : index]]
        after = [line for line, _ in seq[end : end + 3]]
        found.append((before, run, after))
        index = end
    return [item for item in found if any(line.strip() for line in item[1])]


def run_applied(body: list[str], hunk: Hunk) -> bool:
    """A hunk that only adds lines: each added block is where the hunk puts it, or is a distinct multi-line block.

    When the hunk has context on both sides, both sides have to match. One side is not enough: the same
    added line can sit after the same three lines in a different function.
    """
    runs = anchored_runs(hunk)
    if not runs:
        return False
    for before, run, after in runs:
        if before and after:
            placed = contains_run(body, before + run) and contains_run(body, run + after)
        elif before:
            placed = contains_run(body, before + run)
        elif after:
            placed = contains_run(body, run + after)
        else:
            placed = False
        distinct = len(run) >= 2 and contains_run(body, run)
        if not (placed or distinct):
            return False
    return True


def replacement_applied(body: list[str], hunk: Hunk) -> bool:
    """A hunk that removes lines: its added blocks sit where it put them, or its added lines are all there and none of the removed ones are."""
    if run_applied(body, hunk):
        return True
    present = set(body)
    added = [line for line in hunk.new if line.strip() and line not in hunk.old]
    removed = [line for line in hunk.old if line.strip() and line not in hunk.new]
    return bool(added) and all(line in present for line in added) and not any(line in present for line in removed)


def apply_hunks(text: str, patch: FilePatch) -> tuple[str, list[str]]:
    notes: list[str] = []
    for number, hunk in enumerate(patch.hunks, start=1):
        old, new = list(hunk.old), list(hunk.new)
        if old == new:
            continue
        context = sum(1 for _, added in hunk.seq if not added)
        removes = len(old) != context
        body = text.split("\n")
        applied = replacement_applied(body, hunk) if removes else run_applied(body, hunk)
        hits = find_block(text, old, hunk.start) if old else []
        if applied and (not removes or not hits):
            notes.append(f"hunk {number}: already applied")
            continue
        if hits:
            if len(hits) > 1:
                notes.append(f"hunk {number}: {len(hits)} places match, took the one nearest line {hunk.start}")
            body[hits[0] : hits[0] + len(old)] = new
            text = "\n".join(body)
            continue
        raise ValueError(
            f"hunk {number} (near line {hunk.start}) does not match: first old line {old[0]!r}"
            if old
            else f"hunk {number} has nothing to anchor on"
        )
    return text, notes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("extension", type=Path, help="the sd-diff-set extension folder")
    parser.add_argument("--check", action="store_true", help="report only, write nothing")
    parser.add_argument("--force", action="store_true", help="ignore the record of patches this tool already applied")
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
    marker = root / MARKER
    recorded: dict[str, str] = {}
    if marker.is_file() and not args.force:
        recorded = json.loads(marker.read_text(encoding="utf-8"))
    applied_now: dict[str, str] = dict(recorded)
    sample_eol = eol_of((root / "sd_diff_set" / "planner.py").read_bytes())
    for patch_file in patch_files:
        digest = hashlib.sha256(patch_file.read_bytes()).hexdigest()
        if recorded.get(patch_file.name) == digest:
            print(f"== {patch_file.name}: recorded as applied by this tool (use --force to apply again)")
            continue
        print(f"== {patch_file.name}")
        before = failed
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
        if failed == before:
            applied_now[patch_file.name] = digest
    if not args.check and not failed:
        for target, text in texts.items():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(text.replace("\n", eols[target]).encode("utf-8"))
        marker.write_text(json.dumps(applied_now, indent=2), encoding="utf-8")
    elif not args.check:
        print("a patch failed, so nothing was written")
    print("nothing written (--check)" if args.check else ("done" if not failed else ""))
    print(f"{failed} problem(s)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
