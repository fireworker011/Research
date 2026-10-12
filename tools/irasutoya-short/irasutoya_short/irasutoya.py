"""いらすとやを検索してダウンロードし、目視チェックを通ったものだけ残す。"""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from PIL import Image

from irasutoya_short.catalog import ASSET_CATALOG
from irasutoya_short.constants import MAX_ASSETS
from irasutoya_short.qa import inspect_image, title_rejection

FEED = "https://www.irasutoya.com/feeds/posts/default"
USER_AGENT = "irasutoya-short/1.0"


def default_cache_root() -> Path:
    return Path(os.environ.get("IRASUTOYA_CACHE", Path.home() / ".cache/irasutoya-short/images"))


def cache_file(url: str, root: Path | None = None) -> Path:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:24]
    return (root or default_cache_root()) / f"{digest}.png"


def normalize_entries(entry: object) -> list:
    """Blogger の entry は、1件のとき辞書、0件のとき欠ける。"""
    if entry is None:
        return []
    if isinstance(entry, dict):
        return [entry]
    if isinstance(entry, list):
        return entry
    return []


def _get(url: str) -> bytes:
    last: Exception | None = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=40) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (404, 410):
                raise
            last = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
            last = exc
        time.sleep(0.4 * (attempt + 1))
    if last is None:
        raise RuntimeError(f"取得に失敗しました: {url}")
    raise last


def _attr(tag: str, name: str) -> str:
    m = re.search(rf'{name}\s*=\s*"([^"]*)"', tag, re.I)
    if m:
        return html.unescape(m.group(1))
    m = re.search(rf"{name}\s*=\s*'([^']*)'", tag, re.I)
    return html.unescape(m.group(1)) if m else ""


def parse_images(content_html: str) -> list[dict]:
    items: list[dict] = []
    seen: set[str] = set()
    for match in re.finditer(r"<img\b([^>]*)>", content_html, re.I):
        src = _attr(match.group(1), "src")
        alt = _attr(match.group(1), "alt")
        if not src or not re.search(r"\.(png|jpe?g)", src, re.I):
            continue
        if "thumbnail_" in src or "/s1600/twitter" in src:
            continue
        window = content_html[max(0, match.start() - 500) : match.start()]
        hrefs = re.findall(r'href="([^"]+\.(?:png|jpe?g)[^"]*)"', window, re.I)
        url = html.unescape(hrefs[-1] if hrefs else src)
        url = re.sub(r"/s\d+/", "/s800/", url)
        if url in seen:
            continue
        seen.add(url)
        items.append({"url": url, "alt": alt})
    return items


def search_posts(query: str, max_results: int = 8) -> list[dict]:
    params = urllib.parse.urlencode({"q": query, "alt": "json", "max-results": str(max_results)})
    raw = _get(f"{FEED}?{params}")
    data = json.loads(raw.decode("utf-8"))
    posts = []
    for entry in normalize_entries(data.get("feed", {}).get("entry")):
        title = entry.get("title", {}).get("$t", "")
        content = entry.get("content", {}).get("$t", "")
        link = ""
        for item in entry.get("link", []):
            if item.get("rel") == "alternate":
                link = item.get("href", "")
        images = parse_images(content)
        if images:
            posts.append({"title": title, "link": link, "images": images})
    return posts


def match_score(title: str, alt: str, needles: list[str], gender: str) -> int:
    """0 は針が一つも刺さっていない。負はタイトル不採用。針が刺さると正。"""
    if title_rejection(title, alt, gender):
        return -1
    blob = f"{title} {alt}"
    score = 0
    hit = False
    for needle in needles:
        if needle and needle in blob:
            score += 2
            hit = True
    if not hit:
        return 0
    if gender and gender in alt:
        score += 3
    if gender and gender in title:
        score += 1
    return score


def _download(url: str, dest: Path, cache_root: Path | None = None) -> None:
    cached = cache_file(url, cache_root)
    if cached.is_file() and cached.stat().st_size > 0:
        try:
            dest.write_bytes(cached.read_bytes())
            with Image.open(dest) as im:
                im.verify()
            return
        except (OSError, SyntaxError, ValueError):
            cached.unlink(missing_ok=True)
    data = _get(url)
    dest.write_bytes(data)
    with Image.open(dest) as im:
        im.verify()
    cached.parent.mkdir(parents=True, exist_ok=True)
    cached.write_bytes(data)


def collect_assets(asset_ids: list[str], dest_dir: Path, pinned: dict | None = None) -> dict:
    """検索→DL→目視。採用は20点まで。戻り値はレポート。"""
    if len(asset_ids) > MAX_ASSETS:
        raise ValueError(f"素材{len(asset_ids)}点は上限{MAX_ASSETS}を超えています。")
    dest_dir.mkdir(parents=True, exist_ok=True)
    rejected_dir = dest_dir / "rejected"
    rejected_dir.mkdir(exist_ok=True)
    pinned = pinned or {}
    used_urls: set[str] = set()
    accepted: list[dict] = []
    rejected: list[dict] = []

    for asset_id in asset_ids:
        spec = ASSET_CATALOG[asset_id]
        winner = _pick_one(asset_id, spec, dest_dir, rejected_dir, used_urls, pinned.get(asset_id), rejected)
        if winner is None:
            raise RuntimeError(f"「{asset_id}」の適切ないらすとやが見つかりませんでした。")
        used_urls.add(winner["url"])
        accepted.append(winner)
        if winner.pop("network", False):
            time.sleep(0.25)

    report = {
        "count": len(accepted),
        "limit": MAX_ASSETS,
        "within_limit": len(accepted) <= MAX_ASSETS,
        "accepted": accepted,
        "rejected": rejected,
    }
    (dest_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _contact_sheet(accepted, dest_dir / "sheet.png")
    return report


def _pick_one(asset_id, spec, dest_dir, rejected_dir, used_urls, pin, rejected) -> dict | None:
    seen: set[str] = set()
    tried = 0
    networked = False
    if pin:
        seen.add(pin)
        had_cache = cache_file(pin).is_file()
        winner = _try_candidate(
            asset_id, spec, dest_dir, rejected_dir, rejected,
            {"url": pin, "alt": asset_id, "title": "pinned", "link": pin, "score": 99},
            1,
        )
        tried = 1
        if winner is not None:
            winner["network"] = not had_cache
            return winner
    for query in spec["queries"]:
        if tried >= 6:
            break
        try:
            posts = search_posts(query)
        except Exception as exc:  # noqa: BLE001 - 検索失敗は次の語へ
            rejected.append({"id": asset_id, "reason": f"検索失敗: {exc}", "query": query})
            continue
        batch: list[dict] = []
        for post in posts:
            for image in post["images"]:
                score = match_score(post["title"], image["alt"], spec["needles"], spec.get("gender") or "")
                if score < 0:
                    rejected.append({
                        "id": asset_id,
                        "reason": title_rejection(post["title"], image["alt"], spec.get("gender") or ""),
                        "title": post["title"],
                        "alt": image["alt"],
                        "url": image["url"],
                    })
                    continue
                if score == 0 or image["url"] in used_urls or image["url"] in seen:
                    continue
                batch.append({
                    "url": image["url"],
                    "alt": image["alt"],
                    "title": post["title"],
                    "link": post["link"],
                    "score": score,
                })
        batch.sort(key=lambda c: c["score"], reverse=True)
        for cand in batch:
            if tried >= 6:
                break
            seen.add(cand["url"])
            tried += 1
            winner = _try_candidate(asset_id, spec, dest_dir, rejected_dir, rejected, cand, tried)
            if winner is not None:
                winner["network"] = True
                return winner
        time.sleep(0.2)
    return None


def _try_candidate(asset_id, spec, dest_dir, rejected_dir, rejected, cand: dict, rank: int) -> dict | None:
    path = dest_dir / f"{asset_id}.png"
    tmp = dest_dir / f"_{asset_id}_try.png"
    try:
        _download(cand["url"], tmp)
    except Exception as exc:  # noqa: BLE001
        rejected.append({"id": asset_id, "reason": f"DL失敗: {exc}", "url": cand["url"]})
        return None
    reason = inspect_image(str(tmp), cand["title"], cand["alt"], spec.get("gender") or "", spec["kind"])
    if reason:
        reject_path = rejected_dir / f"{asset_id}_{rank}.png"
        tmp.replace(reject_path)
        rejected.append({
            "id": asset_id,
            "reason": reason,
            "title": cand["title"],
            "alt": cand["alt"],
            "url": cand["url"],
            "path": str(reject_path),
        })
        return None
    tmp.replace(path)
    return {
        "id": asset_id,
        "kind": spec["kind"],
        "path": str(path),
        "url": cand["url"],
        "title": cand["title"],
        "alt": cand["alt"],
        "link": cand["link"],
        "page": cand["link"],
    }


def _contact_sheet(accepted: list[dict], dest: Path) -> None:
    thumbs = []
    for item in accepted:
        with Image.open(item["path"]) as im:
            im = im.convert("RGBA")
            im.thumbnail((240, 240))
            thumbs.append((item["id"], im))
    if not thumbs:
        return
    cols = 3
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 260, rows * 280), (255, 255, 255))
    for i, (name, im) in enumerate(thumbs):
        x = (i % cols) * 260 + 10
        y = (i // cols) * 280 + 10
        plate = Image.new("RGB", im.size, (255, 255, 255))
        plate.paste(im, mask=im.split()[-1])
        sheet.paste(plate, (x, y))
    sheet.save(dest)
