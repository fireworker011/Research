#!/usr/bin/env python3
"""Stamp sha256 of an order body. Same rules as the PowerShell runner.

Body hash = SHA256 of the UTF-8 bytes after the closing front-matter line.
Newlines are normalized to LF first. A leading UTF-8 BOM is ignored.
"""
import hashlib
import re
import sys

SPLIT = re.compile(r"\A---\n(.*?)\n---(?:\n(.*))?\Z", re.S)
SHA_LINE = re.compile(r"(?m)^sha256:\s*([0-9a-fA-F]+)\s*$")


def load_text(path):
    raw = open(path, "rb").read()
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        raise SystemExit("UTF-16 orders are not supported; save as UTF-8")
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    return raw.decode("utf-8")


def split_order(text):
    norm = text.replace("\r\n", "\n").replace("\r", "\n")
    match = SPLIT.match(norm)
    if not match:
        raise SystemExit("front matter must start with --- and close with ---")
    body = match.group(2) or ""
    return norm, match.group(1), body


def body_sha256(body):
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def stamp_text(text):
    norm, front, body = split_order(text)
    digest = body_sha256(body)
    found = list(SHA_LINE.finditer(front))
    if len(found) > 1:
        raise SystemExit("duplicate sha256")
    if len(found) == 1:
        if found[0].group(1).lower() != digest:
            raise SystemExit("sha256 mismatch")
        return norm
    front_out = front.rstrip("\n")
    return "---\n%s\nsha256: %s\n---\n%s" % (front_out, digest, body)


def main(argv):
    if len(argv) < 3 or argv[1] not in ("stamp", "hash"):
        raise SystemExit("usage: order_stamp.py stamp|hash <file>")
    text = load_text(argv[2])
    if argv[1] == "hash":
        _norm, _front, body = split_order(text)
        sys.stdout.write(body_sha256(body))
        return 0
    sys.stdout.write(stamp_text(text))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
