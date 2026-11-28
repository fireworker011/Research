"""Check, against a running WebUI, whether the <lora:...> tags of a job can work and do work.

Usage:
    python tools/diagnose_lora.py <api url> --jobs batch.json
    python tools/diagnose_lora.py <api url> --prompt "1girl, <lora:nieva_xl:0.8>"
    python tools/diagnose_lora.py <api url> --jobs batch.json --generate

Step 1 reads /sdapi/v1/loras and lists tag names the WebUI does not know. The WebUI drops such a tag without an
error, which looks exactly like "the LoRA has no effect".
Step 2 (--generate) asks the WebUI for two tiny pictures with the same seed, one with the tags and one without,
and reads the infotext it returns: a LoRA that was applied appears in "Lora hashes", and the two pictures differ.

The script only reads from the WebUI and generates two small test pictures. It uses the standard library only.
"""

from __future__ import annotations

import argparse
import base64
import difflib
import json
import re
import sys
import urllib.request
from pathlib import Path

TAG = re.compile(r"<(?:lora|lyco):([^:>]+)(?::[^>]*)?>", re.IGNORECASE)
HASHES = re.compile(r'Lora hashes:\s*"([^"]*)"')


def request(url: str, payload: dict[str, object] | None = None, timeout: float = 600) -> object:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {} if body is None else {"Content-Type": "application/json"}
    with urllib.request.urlopen(urllib.request.Request(url, data=body, headers=headers), timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def tag_names(prompt: str) -> list[str]:
    names: list[str] = []
    for match in TAG.finditer(prompt):
        name = match.group(1).strip()
        if name and name not in names:
            names.append(name)
    return names


def prompts_from(jobs_path: Path | None, prompt: str | None) -> list[tuple[str, str]]:
    if prompt:
        return [("--prompt", prompt)]
    if jobs_path is None:
        return []
    data = json.loads(jobs_path.read_text(encoding="utf-8"))
    rows = data.get("jobs") if isinstance(data, dict) else None
    if not isinstance(rows, list):
        raise SystemExit(f"{jobs_path} has no jobs list")
    return [(str(row.get("id") or index), str(row.get("prompt") or "")) for index, row in enumerate(rows, start=1)]


def known_names(api: str) -> set[str]:
    rows = request(api.rstrip("/") + "/sdapi/v1/loras", timeout=30)
    if not isinstance(rows, list):
        raise SystemExit("/sdapi/v1/loras did not return a list")
    names: set[str] = set()
    for row in rows:
        if isinstance(row, dict):
            for key in ("name", "alias"):
                if isinstance(row.get(key), str) and row[key].strip():
                    names.add(row[key].strip())
    return names


def applied_in(info: object) -> set[str] | None:
    """Names under "Lora hashes" in the first infotext of a txt2img answer. None when there is no infotext."""
    payload = info
    if isinstance(info, str):
        try:
            payload = json.loads(info)
        except json.JSONDecodeError:
            return None
    texts = payload.get("infotexts") if isinstance(payload, dict) else None
    if not isinstance(texts, list) or not texts or not isinstance(texts[0], str):
        return None
    match = HASHES.search(texts[0])
    if match is None:
        return set()
    return {part.split(":", 1)[0].strip() for part in match.group(1).split(",") if part.strip()}


def generate(api: str, prompt: str, seed: int) -> tuple[str, object]:
    payload = {
        "prompt": prompt,
        "negative_prompt": "lowres",
        "steps": 4,
        "width": 512,
        "height": 512,
        "seed": seed,
        "batch_size": 1,
        "n_iter": 1,
        "cfg_scale": 5,
    }
    answer = request(api.rstrip("/") + "/sdapi/v1/txt2img", payload)
    if not isinstance(answer, dict) or not answer.get("images"):
        raise SystemExit("txt2img returned no picture")
    return str(answer["images"][0]), answer.get("info")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("api")
    parser.add_argument("--jobs", type=Path)
    parser.add_argument("--prompt")
    parser.add_argument("--generate", action="store_true")
    args = parser.parse_args(argv)
    prompts = prompts_from(args.jobs, args.prompt)
    if not prompts:
        parser.error("give --jobs or --prompt")
    problems = 0
    available = known_names(args.api)
    print(f"the WebUI lists {len(available)} LoRA names")
    wanted: list[str] = []
    for label, text in prompts:
        for name in tag_names(text):
            if name not in wanted:
                wanted.append(name)
    for name in wanted:
        if name in available:
            print(f"  ok       {name}")
            continue
        problems += 1
        close = difflib.get_close_matches(name, sorted(available), n=3, cutoff=0.6)
        folded = [item for item in available if item.casefold() == name.casefold()]
        hint = f" (did you mean {', '.join(folded or close)}?)" if folded or close else ""
        print(f"  MISSING  {name}: the WebUI does not list it, so it will drop this tag{hint}")
    if not wanted:
        print("the prompts contain no <lora:...> tags")
    if args.generate:
        label, text = next((item for item in prompts if tag_names(item[1])), prompts[0])
        asked = tag_names(text)
        plain = TAG.sub("", text)
        picture_with, info = generate(args.api, text, 1234)
        picture_without, _ = generate(args.api, plain, 1234)
        applied = applied_in(info)
        print(f"test prompt from {label}, asked {asked}")
        if applied is None:
            print("  the WebUI returned no infotext, so applied LoRAs cannot be read")
        else:
            lost = [name for name in asked if name.casefold() not in {a.casefold() for a in applied}]
            print(f"  applied by the WebUI: {sorted(applied)}")
            if lost and asked:
                problems += 1
                print(f"  NOT APPLIED: {lost}")
        same = base64.b64decode(picture_with) == base64.b64decode(picture_without)
        print(f"  picture with the tags {'is IDENTICAL to' if same else 'differs from'} the one without them")
        if same and asked:
            problems += 1
            print("  the tags changed nothing at the same seed")
    print("PROBLEMS" if problems else "OK")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
