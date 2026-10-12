"""Genre templates for affiliate vertical shorts.

Reads an accounts snapshot and writes one template per genre.
Unknown values stay out of the denominator. Reference rows whose notes
start with 「ユーザー参考アカウント」 stay out of the counts.
This module does not generate video and does not post.
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

SCHEMA = "affi-genre-template/v1"
GROWING = "伸びてる"
STRUGGLING = "伸び悩み"
REF_PREFIX = "ユーザー参考アカウント"
UNKNOWN = frozenset({"", "不明", "その他/不明"})

GENRE_ORDER = ("美容スキンケア", "ドッグフード", "見守りカメラ", "婚活")
PLATFORM_ORDER = ("TikTok", "Instagram", "YouTube")
REFERENCE_HANDLES = {
    "美容スキンケア": "the.care.logic",
    "ドッグフード": "nuts0629",
    "見守りカメラ": "junjun_ranran",
    "婚活": "yako.shiawasekon",
}

# Structural homage only. Not in the 266-account count. No view or follower figures.
# Footage, the named cat, and the channel's titles are not for reuse.
SUZUMARU_HOMAGE = {
    "handle": "cat-yu-chan",
    "platform": "YouTube",
    "channel_title": "すず丸と暮らしてます",
    "url": "https://www.youtube.com/@cat-yu-chan/shorts",
    "in_count": False,
    "measured": False,
    "borrow": [
        "同じ子を最初から出す",
        "最初の一言は小さな不一致",
        "商品は後",
        "同じ子でシリーズにする",
    ],
    "do_not_copy": ["映像", "すず丸本人", "タイトルの文"],
}
HOMAGE_BY_GENRE = {
    "ドッグフード": {
        **SUZUMARU_HOMAGE,
        "fit": "集計の既定は商品名から入る・主役は手元。作るときは、その既定よりこの型を先に使う。",
        "first_3_seconds": "同じ子のふつうの食いしん坊。ごはん、袋、商品名は後ろ。",
    },
    "見守りカメラ": {
        **SUZUMARU_HOMAGE,
        "fit": "集計の「動物が主役」には合う。このチャンネルは飼い主が話に入るので、カメラ映像だけの型ではない。顔なしの既定は変えない。",
        "first_3_seconds": "同じ子のふつうの不一致。カメラ本体は後ろ。飼い主を話の中心にしない。",
    },
}

# Single-value fields. product_display is multi-valued and handled apart.
CATEGORICAL = (
    ("opening_type", "冒頭タイプ"),
    ("face_shown", "顔出し"),
    ("main_subject", "主役"),
    ("duration_band", "尺"),
    ("audio", "音"),
    ("hashtag_band", "ハッシュタグ数"),
    ("pr_label", "PR表記"),
    ("post_band", "投稿頻度"),
    ("template_fixed", "テンプレ固定"),
)
PRODUCT_LABEL = "商品の見せ方"


@dataclass(frozen=True)
class Thresholds:
    """Count gates. Change these when a new snapshot should be judged differently."""

    strong_min: int = 10
    compare_min: int = 3
    thin_below: int = 10
    min_gap_pt: int = 10
    example_n: int = 3


@dataclass
class CountShare:
    value: str
    m: int
    n: int

    @property
    def pct(self) -> int | None:
        return percent(self.m, self.n)

    def text(self) -> str:
        if self.n <= 0 or self.pct is None:
            return "判定可能0件"
        return f"{self.n}件中{self.m}件（{self.pct}%）"


@dataclass
class FieldChoice:
    key: str
    label: str
    choice: str | None
    reason: str
    confidence: str
    growing_n: int
    struggling_n: int
    growing: CountShare | None
    struggling: CountShare | None
    tie: bool = False
    tie_values: tuple[str, ...] = ()


@dataclass
class Gap:
    label: str
    value: str
    growing: CountShare
    struggling: CountShare
    gap_pt: int
    confidence: str

    @property
    def toward_growing(self) -> bool:
        return self.gap_pt > 0


@dataclass
class GenreTemplate:
    genre: str
    n_growing: int
    n_struggling: int
    account_confidence: str
    basis: str
    estimated_n: int
    checked_n: int
    choices: dict[str, FieldChoice]
    gaps: list[Gap]
    examples: list[dict[str, str]]
    platforms: list[dict[str, Any]]
    reference: dict[str, Any]
    medians: dict[str, Any]
    data_date: str

    def choice(self, key: str) -> FieldChoice:
        return self.choices[key]


@dataclass
class Built:
    data_date: str
    thresholds: Thresholds
    n_accounts: int
    n_reference: int
    n_videos: int | None
    genres: list[GenreTemplate] = field(default_factory=list)


def percent(m: int, n: int) -> int | None:
    if n <= 0:
        return None
    value = (Decimal(m) * Decimal(100) / Decimal(n)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(value)


def confidence(n_growing: int, n_struggling: int, thresholds: Thresholds) -> str:
    if n_growing < thresholds.compare_min or n_struggling < thresholds.compare_min:
        return "比較不能"
    if n_growing >= thresholds.strong_min and n_struggling >= thresholds.strong_min:
        return "強い"
    return "弱い"


def basis_for(n_struggling: int, thresholds: Thresholds) -> str:
    if n_struggling < thresholds.thin_below:
        return "伸びてる群の傾向"
    return "比較"


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def is_reference(row: Mapping[str, str]) -> bool:
    return str(row.get("notes") or "").startswith(REF_PREFIX)


def split_rows(rows: Sequence[Mapping[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Drop reference accounts from the counts. Keep only the two buckets."""
    analysis: list[dict[str, str]] = []
    references: list[dict[str, str]] = []
    for raw in rows:
        row = {key: str(value or "").strip() for key, value in raw.items()}
        if is_reference(row):
            references.append(row)
            continue
        if row.get("bucket") in {GROWING, STRUGGLING}:
            analysis.append(row)
    return analysis, references


def _number(value: str) -> float | None:
    text = (value or "").strip()
    if not text or text in UNKNOWN:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def duration_band(seconds: float) -> str:
    if seconds <= 15:
        return "15秒以下"
    if seconds <= 30:
        return "16〜30秒"
    if seconds <= 60:
        return "31〜60秒"
    return "61秒以上"


def hashtag_band(count: float) -> str:
    if count <= 3:
        return "0〜3個"
    return "4個以上"


def post_band(count: float) -> str:
    if count <= 3:
        return "30日3本以下（見えた範囲）"
    if count <= 9:
        return "30日4〜9本"
    return "30日10本以上"


def known_text(value: str) -> str | None:
    text = (value or "").strip()
    if text in UNKNOWN:
        return None
    if text == "あり（推定）":
        return "あり"
    return text


def product_tokens(value: str) -> list[str]:
    found: list[str] = []
    for part in (value or "").split(";"):
        token = part.strip()
        if token in UNKNOWN or token in found:
            continue
        found.append(token)
    return found


def prepared(row: Mapping[str, str]) -> dict[str, Any]:
    """One account, with bands filled and unknowns as None."""
    duration = _number(str(row.get("duration_sec") or ""))
    hashtags = _number(str(row.get("hashtag_count") or ""))
    posts = _number(str(row.get("posts_last30_seen") or ""))
    return {
        "platform": row.get("platform") or "",
        "genre": row.get("genre") or "",
        "bucket": row.get("bucket") or "",
        "handle": (row.get("handle") or "").lower(),
        "opening_type": known_text(str(row.get("opening_type") or "")),
        "face_shown": known_text(str(row.get("face_shown") or "")),
        "main_subject": known_text(str(row.get("main_subject") or "")),
        "template_fixed": known_text(str(row.get("template_fixed") or "")),
        "audio": known_text(str(row.get("audio") or "")),
        "pr_label": known_text(str(row.get("pr_label") or "")),
        "duration_band": duration_band(duration) if duration is not None else None,
        "duration_sec": duration,
        "hashtag_band": hashtag_band(hashtags) if hashtags is not None else None,
        "post_band": post_band(posts) if posts is not None else None,
        "product_tokens": product_tokens(str(row.get("product_display") or "")),
        "feature_source": row.get("feature_source") or "",
        "first_frame_text": (row.get("first_frame_text") or "").strip(),
        "opening_type_evidence": (row.get("opening_type_evidence") or "").strip(),
        "median_views": _number(str(row.get("median_views") or "")),
        "followers": _number(str(row.get("followers") or "")),
        "notes": row.get("notes") or "",
    }


def _bucket(rows: Sequence[Mapping[str, Any]], name: str) -> list[Mapping[str, Any]]:
    return [row for row in rows if row.get("bucket") == name]


def _tally(rows: Sequence[Mapping[str, Any]], key: str) -> tuple[dict[str, int], int]:
    counts: Counter[str] = Counter()
    for row in rows:
        value = row.get(key)
        if value:
            counts[str(value)] += 1
    return dict(counts), sum(counts.values())


def _product_tally(rows: Sequence[Mapping[str, Any]]) -> tuple[dict[str, int], int]:
    counts: Counter[str] = Counter()
    judged = 0
    for row in rows:
        tokens = list(row.get("product_tokens") or [])
        if not tokens:
            continue
        judged += 1
        for token in tokens:
            counts[token] += 1
    return dict(counts), judged


def _mode(counts: Mapping[str, int]) -> tuple[str | None, bool, tuple[str, ...]]:
    if not counts:
        return None, False, ()
    best = max(counts.values())
    winners = tuple(sorted(key for key, count in counts.items() if count == best))
    if len(winners) != 1:
        return None, True, winners
    return winners[0], False, ()


def _share(counts: Mapping[str, int], n: int, value: str) -> CountShare:
    return CountShare(value=value, m=int(counts.get(value, 0)), n=n)


def _choose_categorical(
    key: str,
    label: str,
    growing: Sequence[Mapping[str, Any]],
    struggling: Sequence[Mapping[str, Any]],
    thresholds: Thresholds,
) -> FieldChoice:
    grow_counts, grow_n = _tally(growing, key)
    struggle_counts, struggle_n = _tally(struggling, key)
    mode, tie, tie_values = _mode(grow_counts)
    level = confidence(grow_n, struggle_n, thresholds)
    growing_share = _share(grow_counts, grow_n, mode) if mode else None
    struggling_share = None
    if mode:
        struggling_share = _share(struggle_counts, struggle_n, mode)
    if grow_n == 0:
        reason = "データ不足"
        choice = None
    elif tie:
        reason = "伸びてる群で同数"
        choice = None
    else:
        reason = "伸びてる群の最頻値"
        choice = mode
    return FieldChoice(
        key=key,
        label=label,
        choice=choice,
        reason=reason,
        confidence=level,
        growing_n=grow_n,
        struggling_n=struggle_n,
        growing=growing_share,
        struggling=struggling_share,
        tie=tie,
        tie_values=tie_values,
    )


def _gaps_for(
    label: str,
    grow_counts: Mapping[str, int],
    grow_n: int,
    struggle_counts: Mapping[str, int],
    struggle_n: int,
    thresholds: Thresholds,
) -> list[Gap]:
    level = confidence(grow_n, struggle_n, thresholds)
    if level == "比較不能":
        return []
    found: list[Gap] = []
    values = set(grow_counts) | set(struggle_counts)
    for value in values:
        growing = _share(grow_counts, grow_n, value)
        struggling = _share(struggle_counts, struggle_n, value)
        if growing.pct is None or struggling.pct is None:
            continue
        gap_pt = growing.pct - struggling.pct
        if abs(gap_pt) < thresholds.min_gap_pt:
            continue
        found.append(
            Gap(
                label=label,
                value=value,
                growing=growing,
                struggling=struggling,
                gap_pt=gap_pt,
                confidence=level,
            )
        )
    return found


def collect_gaps(
    growing: Sequence[Mapping[str, Any]],
    struggling: Sequence[Mapping[str, Any]],
    thresholds: Thresholds,
) -> list[Gap]:
    found: list[Gap] = []
    for key, label in CATEGORICAL:
        grow_counts, grow_n = _tally(growing, key)
        struggle_counts, struggle_n = _tally(struggling, key)
        found.extend(_gaps_for(label, grow_counts, grow_n, struggle_counts, struggle_n, thresholds))
    grow_counts, grow_n = _product_tally(growing)
    struggle_counts, struggle_n = _product_tally(struggling)
    found.extend(_gaps_for(PRODUCT_LABEL, grow_counts, grow_n, struggle_counts, struggle_n, thresholds))
    found.sort(key=lambda item: (-abs(item.gap_pt), -item.gap_pt, item.label, item.value))
    return found


def _median(values: Iterable[float]) -> float | None:
    nums = list(values)
    if not nums:
        return None
    return float(statistics.median(nums))


def _examples(growing: Sequence[Mapping[str, Any]], limit: int) -> list[dict[str, str]]:
    ranked = sorted(
        growing,
        key=lambda row: (-(row.get("median_views") or -1), row.get("handle") or ""),
    )
    picked: list[dict[str, str]] = []
    for row in ranked:
        evidence = str(row.get("opening_type_evidence") or "")
        frame = str(row.get("first_frame_text") or "")
        if not evidence and not frame:
            continue
        views = row.get("median_views")
        picked.append(
            {
                "handle": str(row.get("handle") or ""),
                "opening_type": str(row.get("opening_type") or "不明"),
                "platform": str(row.get("platform") or ""),
                "median_views": "" if views is None else str(int(views) if views == int(views) else views),
                "evidence": evidence,
                "first_frame_text": frame,
            }
        )
        if len(picked) >= limit:
            break
    return picked


def _platforms(
    rows: Sequence[Mapping[str, Any]],
    genre_choices: Mapping[str, FieldChoice],
    thresholds: Thresholds,
) -> list[dict[str, Any]]:
    names = [name for name in PLATFORM_ORDER if any(row.get("platform") == name for row in rows)]
    extra = sorted({str(row.get("platform") or "") for row in rows if row.get("platform") not in PLATFORM_ORDER and row.get("platform")})
    diffs: list[dict[str, Any]] = []
    for platform in [*names, *extra]:
        subset = [row for row in rows if row.get("platform") == platform]
        growing = _bucket(subset, GROWING)
        struggling = _bucket(subset, STRUGGLING)
        changes: list[dict[str, str]] = []
        for key, label in CATEGORICAL:
            field_choice = _choose_categorical(key, label, growing, struggling, thresholds)
            genre_choice = genre_choices[key].choice
            if field_choice.growing_n < thresholds.compare_min:
                continue
            if choice_text(field_choice) != choice_text(genre_choices[key]):
                changes.append(
                    {
                        "field": label,
                        "genre": choice_text(genre_choices[key]),
                        "platform": choice_text(field_choice),
                        "growing": (
                            field_choice.growing.text()
                            if field_choice.growing
                            else f"伸びてる判定 {field_choice.growing_n}件"
                        ),
                        "confidence": field_choice.confidence,
                    }
                )
        diffs.append(
            {
                "platform": platform,
                "n_growing": len(growing),
                "n_struggling": len(struggling),
                "changes": changes,
            }
        )
    return diffs


def _reference_block(
    genre: str,
    references: Sequence[Mapping[str, Any]],
    choices: Mapping[str, FieldChoice],
    growing: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    handle = REFERENCE_HANDLES.get(genre, "")
    match = next((row for row in references if row.get("handle") == handle and row.get("genre") == genre), None)
    if match is None:
        return {"handle": handle, "present": False, "same": [], "different": []}
    same: list[dict[str, str]] = []
    different: list[dict[str, str]] = []
    for key, label in CATEGORICAL:
        actual = match.get(key)
        chosen = choices[key].choice
        grow_counts, grow_n = _tally(growing, key)
        share = _share(grow_counts, grow_n, str(actual)) if actual else None
        item = {
            "field": label,
            "reference": str(actual) if actual else "不明",
            "template": choice_text(choices[key]),
            "growing": share.text() if share else "判定可能0件",
        }
        if actual and chosen and actual == chosen:
            same.append(item)
        else:
            different.append(item)
    tokens = list(match.get("product_tokens") or [])
    return {
        "handle": handle,
        "present": True,
        "platform": match.get("platform") or "",
        "bucket": match.get("bucket") or "",
        "followers": match.get("followers"),
        "median_views": match.get("median_views"),
        "product_tokens": tokens,
        "feature_source": match.get("feature_source") or "",
        "same": same,
        "different": different,
    }


def build_genre(
    genre: str,
    rows: Sequence[Mapping[str, Any]],
    references: Sequence[Mapping[str, Any]],
    thresholds: Thresholds,
    data_date: str,
) -> GenreTemplate:
    growing = _bucket(rows, GROWING)
    struggling = _bucket(rows, STRUGGLING)
    choices = {
        key: _choose_categorical(key, label, growing, struggling, thresholds)
        for key, label in CATEGORICAL
    }
    return GenreTemplate(
        genre=genre,
        n_growing=len(growing),
        n_struggling=len(struggling),
        account_confidence=confidence(len(growing), len(struggling), thresholds),
        basis=basis_for(len(struggling), thresholds),
        estimated_n=sum(1 for row in rows if row.get("feature_source") == "推定（説明文）"),
        checked_n=sum(1 for row in rows if row.get("feature_source") == "確認済"),
        choices=choices,
        gaps=collect_gaps(growing, struggling, thresholds),
        examples=_examples(growing, thresholds.example_n),
        platforms=_platforms(rows, choices, thresholds),
        reference=_reference_block(genre, references, choices, growing),
        medians={
            "duration_sec": _median(row["duration_sec"] for row in growing if row.get("duration_sec") is not None),
            "duration_n": sum(1 for row in growing if row.get("duration_sec") is not None),
            "followers": _median(row["followers"] for row in growing if row.get("followers") is not None),
            "median_views": _median(row["median_views"] for row in growing if row.get("median_views") is not None),
        },
        data_date=data_date,
    )


def genre_names(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    found = {str(row.get("genre") or "") for row in rows if row.get("genre")}
    ordered = [name for name in GENRE_ORDER if name in found]
    ordered.extend(sorted(found - set(ordered)))
    return ordered


def build_from_rows(
    analysis: Sequence[Mapping[str, str]],
    references: Sequence[Mapping[str, str]],
    thresholds: Thresholds,
    data_date: str,
    n_videos: int | None = None,
) -> Built:
    prepared_rows = [prepared(row) for row in analysis]
    prepared_refs = [prepared(row) for row in references]
    genres = [
        build_genre(
            genre,
            [row for row in prepared_rows if row["genre"] == genre],
            prepared_refs,
            thresholds,
            data_date,
        )
        for genre in genre_names(prepared_rows)
    ]
    return Built(
        data_date=data_date,
        thresholds=thresholds,
        n_accounts=len(prepared_rows),
        n_reference=len(prepared_refs),
        n_videos=n_videos,
        genres=genres,
    )


def load_snapshot(data_dir: Path, thresholds: Thresholds | None = None) -> Built:
    data_dir = Path(data_dir)
    accounts = load_csv(data_dir / "accounts.csv")
    analysis, references = split_rows(accounts)
    video_path = data_dir / "videos.csv"
    n_videos = len(load_csv(video_path)) if video_path.is_file() else None
    return build_from_rows(
        analysis,
        references,
        thresholds or Thresholds(),
        data_date=data_dir.name,
        n_videos=n_videos,
    )


def choice_text(item: FieldChoice) -> str:
    if item.tie:
        return "同数（" + "・".join(item.tie_values) + "）"
    if item.choice:
        return item.choice
    return "データ不足"


def actionable_avoid(item: GenreTemplate) -> list[Gap]:
    """Drop a struggling-leaning value when it is still the growing majority."""
    by_label = {choice.label: choice for choice in item.choices.values()}
    kept: list[Gap] = []
    for gap in item.gaps:
        if gap.toward_growing:
            continue
        choice = by_label.get(gap.label)
        growing_pct = choice.growing.pct if choice and choice.growing else None
        majority = choice is not None and choice.choice == gap.value and growing_pct is not None and growing_pct >= 50
        if majority:
            continue
        kept.append(gap)
    return kept


def _choice_line(item: FieldChoice, avoid: Sequence[Gap]) -> str:
    warned = any(gap.label == item.label and gap.value == item.choice for gap in avoid)
    if item.choice is None and item.tie:
        return (
            f"{item.label}: 同数で決められない（{choice_text(item)}。"
            f"伸びてる判定 {item.growing_n}件、伸び悩み判定 {item.struggling_n}件）"
        )
    if item.choice is None:
        return f"{item.label}: データ不足（伸びてる判定 {item.growing_n}件、伸び悩み判定 {item.struggling_n}件）"
    bits = [f"{item.label}: {item.choice}"]
    if item.growing:
        bits.append(f"伸びてる {item.growing.text()}")
    if item.struggling and item.struggling.n:
        bits.append(f"伸び悩み {item.struggling.text()}")
    elif item.struggling_n == 0:
        bits.append("伸び悩みは判定可能0件")
    bits.append(f"信頼度 {item.confidence}")
    bits.append(item.reason)
    if warned:
        bits.append("ただし伸び悩み側の割合の方が高い。やらないことを見る")
    return "。".join(bits)


def _gap_line(item: Gap) -> str:
    side = "伸びてる側が高い" if item.toward_growing else "伸び悩み側が高い"
    sign = f"{item.gap_pt:+d}pt"
    return (
        f"{item.label}「{item.value}」: 伸びてる {item.growing.text()}、"
        f"伸び悩み {item.struggling.text()}（{sign}、{side}、信頼度 {item.confidence}）"
    )


def _clip(text: str, limit: int = 80) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[: limit - 1] + "…"


def homage_for(genre: str) -> dict[str, Any] | None:
    found = HOMAGE_BY_GENRE.get(genre)
    if found is None:
        return None
    return dict(found)


def _render_homage(genre: str) -> list[str]:
    homage = homage_for(genre)
    if homage is None:
        return []
    lines = [
        "## オマージュ（集計外）",
        "",
        (
            f"{homage['platform']} @{homage['handle']}「{homage['channel_title']}」。"
            "再生数とフォロワーは未計測。266件には入れない。"
        ),
        homage["fit"],
        f"作るときの最初の3秒: {homage['first_3_seconds']}",
        "借りるもの: " + "、".join(homage["borrow"]) + "。",
        "使わないもの: " + "、".join(homage["do_not_copy"]) + "。",
        "",
    ]
    return lines


def render_genre(item: GenreTemplate) -> str:
    if item.basis == "伸びてる群の傾向":
        lead = (
            f"伸び悩みは {item.n_struggling} 件で薄い。"
            "型は比較ではなく、伸びてる群の傾向。"
        )
    else:
        lead = "伸びてる群と伸び悩み群を比べて、既定値は伸びてる群の最頻値。"
    lines = [
        f"# {item.genre}",
        "",
        lead,
        (
            f"伸びてる {item.n_growing} 件 / 伸び悩み {item.n_struggling} 件。"
            f"アカウント数の信頼度は{item.account_confidence}。"
        ),
        (
            f"特徴の出どころ: 推定（説明文）{item.estimated_n} 件、確認済 {item.checked_n} 件。"
            "冒頭・顔出し・音・商品の見せ方の多くはキャプションと説明文からの推定で、動画は見ていない。"
        ),
        "",
    ]
    lines.extend(_render_homage(item.genre))
    lines.extend([
        "## このジャンルで作るとき",
        "",
    ])
    avoid = actionable_avoid(item)
    for key, _label in CATEGORICAL:
        lines.append(f"- {_choice_line(item.choice(key), avoid)}")
    duration = item.medians.get("duration_sec")
    duration_n = item.medians.get("duration_n") or 0
    if duration is None:
        lines.append(f"- 尺の中央値: データ不足（伸びてる群で尺が見えたのは {duration_n} 件）")
    else:
        shown = int(duration) if float(duration).is_integer() else duration
        lines.append(f"- 尺の中央値: {shown} 秒（伸びてる群 {duration_n} 件）")
    views = item.medians.get("median_views")
    followers = item.medians.get("followers")
    if views is not None and followers is not None:
        lines.append(
            f"- 規模（伸びてる群）: フォロワー中央値 {int(followers):,}、再生中央値の中央値 {int(views):,}"
        )
    favor = [gap for gap in item.gaps if gap.toward_growing]
    lines.extend(["", "## 伸びてる側に寄っている", ""])
    if favor:
        lines.extend(f"- {_gap_line(gap)}" for gap in favor)
    else:
        lines.append("- 差がしきい値以上で、伸びてる側だけが高い項目はない。")
    lines.extend(["", "## やらないこと", ""])
    if any(gap.label == "投稿頻度" for gap in item.gaps):
        lines.append("投稿頻度の差は、伸び悩みの定義が「直近30日に4本以上」である影響を受ける。")
    if avoid:
        lines.append("伸び悩み側の割合が高いもの。伸びてる群の過半（50%以上）の最頻値はここから外している。")
        lines.extend(f"- {_gap_line(gap)}" for gap in avoid)
    elif item.n_struggling < 3:
        lines.append("- 伸び悩みが3件未満なので、やらないことは比較できない。データ不足。")
    else:
        lines.append("- しきい値以上の差で、伸び悩み側だけが高い項目はない。")
    lines.extend(["", "## 最初の3秒の参考例", ""])
    lines.append("コピー用ではない。再生中央値が高い伸びてるアカウントの、説明文からの引用。")
    if not item.examples:
        lines.append("- 引用できる例がない。")
    for example in item.examples:
        lines.append(
            f"- {example['platform']} @{example['handle']}（再生中央値 {example['median_views'] or '不明'}、{example['opening_type']}）"
            f" 根拠: {_clip(example['evidence'] or example['first_frame_text'])}"
        )
    lines.extend(["", "## プラットフォームで違うところ", ""])
    any_change = False
    for platform in item.platforms:
        if not platform["changes"]:
            continue
        any_change = True
        lines.append(
            f"- {platform['platform']}（伸びてる {platform['n_growing']} / 伸び悩み {platform['n_struggling']}）"
        )
        for change in platform["changes"]:
            lines.append(
                f"  - {change['field']}: ジャンルは {change['genre']}、このプラットフォームの伸びてる群は {change['platform']}"
                f"（{change['growing']}、信頼度 {change['confidence']}）"
            )
    if not any_change:
        lines.append("- ジャンル全体の最頻値と違うプラットフォームはない（判定が3件未満の側は出していない）。")
    lines.extend(["", f"## 参考アカウント @{item.reference.get('handle') or '不明'}", ""])
    lines.append("集計には入れていない。")
    if not item.reference.get("present"):
        lines.append("- このCSVにいない。")
    else:
        lines.append("- 同じ: " + ("、".join(f"{row['field']}={row['reference']}" for row in item.reference["same"]) or "なし"))
        lines.append("- 違う: " + ("、".join(
            f"{row['field']}は {row['reference']}（テンプレは {row['template']}、伸びてる群では {row['growing']}）"
            for row in item.reference["different"]
        ) or "なし"))
    lines.append("")
    return "\n".join(lines)


def render_compare(built: Built) -> str:
    lines = [
        "# 4ジャンルの比較",
        "",
        f"データ {built.data_date}。アカウント {built.n_accounts} 件。参考 {built.n_reference} 件は表に入れていない。",
        "既定値は伸びてる群の最頻値。伸び悩みが薄いジャンルは「傾向」と書く。",
        "",
        "| ジャンル | 件数 | 信頼度 | 根拠 | 冒頭 | 主役 | 顔 | 尺 | 音 |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for item in built.genres:
        def cell(key: str) -> str:
            return choice_text(item.choice(key))

        lines.append(
            "| {genre} | {ng}/{ns} | {conf} | {basis} | {opening} | {subject} | {face} | {duration} | {audio} |".format(
                genre=item.genre,
                ng=item.n_growing,
                ns=item.n_struggling,
                conf=item.account_confidence,
                basis="傾向" if item.basis == "伸びてる群の傾向" else "比較",
                opening=cell("opening_type"),
                subject=cell("main_subject"),
                face=cell("face_shown"),
                duration=cell("duration_band"),
                audio=cell("audio"),
            )
        )
    lines.append("")
    return "\n".join(lines)


def _share_json(share: CountShare | None) -> dict[str, Any] | None:
    if share is None:
        return None
    return {"value": share.value, "m": share.m, "n": share.n, "pct": share.pct}


def genre_json(item: GenreTemplate, thresholds: Thresholds) -> dict[str, Any]:
    opening = item.choice("opening_type")
    subject = item.choice("main_subject")
    face = item.choice("face_shown")
    duration = item.choice("duration_band")
    audio = item.choice("audio")
    middle = [gap.value for gap in item.gaps if gap.label == PRODUCT_LABEL and gap.toward_growing]
    avoid_gaps = actionable_avoid(item)
    avoid = [
        {
            "field": gap.label,
            "value": gap.value,
            "gap_pt": gap.gap_pt,
            "confidence": gap.confidence,
            "growing": _share_json(gap.growing),
            "struggling": _share_json(gap.struggling),
        }
        for gap in avoid_gaps
    ]
    return {
        "schema": SCHEMA,
        "data_date": item.data_date,
        "genre": item.genre,
        "basis": item.basis,
        "account_confidence": item.account_confidence,
        "n_growing": item.n_growing,
        "n_struggling": item.n_struggling,
        "thresholds": {
            "strong_min": thresholds.strong_min,
            "compare_min": thresholds.compare_min,
            "thin_below": thresholds.thin_below,
            "min_gap_pt": thresholds.min_gap_pt,
        },
        "caution": "冒頭・顔出し・音・商品の見せ方の多くは説明文からの推定。動画は未視聴。不明は分母に入れていない。参考アカウントは集計に入れていない。",
        "feature_source": {"推定（説明文）": item.estimated_n, "確認済": item.checked_n},
        "script_brief": {
            "first_3_seconds": {
                "opening_type": choice_text(opening),
                "instruction": (
                    "最初の3秒は決められない。具体文は人間が書く。"
                    if opening.choice is None
                    else f"最初の3秒は「{opening.choice}」で入る。具体文は人間が書く。examples は参考で、コピーしない。"
                ),
                "confidence": opening.confidence,
                "growing": _share_json(opening.growing),
                "struggling": _share_json(opening.struggling),
                "examples": item.examples,
                "homage": homage_for(item.genre),
            },
            "middle_pattern": middle or ["データ不足"],
            "on_screen": {
                "main_subject": choice_text(subject),
                "face_shown": choice_text(face),
            },
            "duration_band": choice_text(duration),
            "duration_median_sec": item.medians.get("duration_sec"),
            "audio": choice_text(audio),
        },
        "production": {
            "hashtag_band": choice_text(item.choice("hashtag_band")),
            "pr_label": choice_text(item.choice("pr_label")),
            "post_frequency": choice_text(item.choice("post_band")),
            "template_fixed": choice_text(item.choice("template_fixed")),
        },
        "avoid": avoid,
        "favor": [
            {
                "field": gap.label,
                "value": gap.value,
                "gap_pt": gap.gap_pt,
                "confidence": gap.confidence,
                "growing": _share_json(gap.growing),
                "struggling": _share_json(gap.struggling),
            }
            for gap in item.gaps
            if gap.toward_growing
        ],
        "platforms": item.platforms,
        "reference": item.reference,
        "fields": {
            key: {
                "label": choice.label,
                "choice": choice.choice,
                "reason": choice.reason,
                "confidence": choice.confidence,
                "growing_n": choice.growing_n,
                "struggling_n": choice.struggling_n,
                "growing": _share_json(choice.growing),
                "struggling": _share_json(choice.struggling),
            }
            for key, choice in item.choices.items()
        },
    }


def write_outputs(built: Built, out_dir: Path) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    compare_path = out_dir / "compare.md"
    compare_path.write_text(render_compare(built), encoding="utf-8")
    written.append(compare_path)
    bundle = []
    for item in built.genres:
        markdown_path = out_dir / f"{item.genre}.md"
        json_path = out_dir / f"{item.genre}.json"
        markdown_path.write_text(render_genre(item), encoding="utf-8")
        payload = genre_json(item, built.thresholds)
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.extend([markdown_path, json_path])
        bundle.append(payload)
    index_path = out_dir / "all.json"
    index_path.write_text(
        json.dumps(
            {
                "schema": SCHEMA,
                "data_date": built.data_date,
                "n_accounts": built.n_accounts,
                "n_reference": built.n_reference,
                "n_videos": built.n_videos,
                "genres": bundle,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    written.append(index_path)
    return written


def run(data_dir: Path, out_dir: Path, thresholds: Thresholds | None = None) -> Built:
    built = load_snapshot(data_dir, thresholds)
    write_outputs(built, out_dir)
    return built


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="アフィ縦動画のジャンル別テンプレートを書く")
    parser.add_argument("--data", required=True, help="accounts.csv があるフォルダ")
    parser.add_argument("--out", required=True, help="Markdown と JSON の出力先")
    parser.add_argument("--strong-min", type=int, default=10)
    parser.add_argument("--compare-min", type=int, default=3)
    parser.add_argument("--thin-below", type=int, default=10)
    parser.add_argument("--min-gap-pt", type=int, default=10)
    args = parser.parse_args(argv)
    built = run(
        Path(args.data),
        Path(args.out),
        Thresholds(
            strong_min=args.strong_min,
            compare_min=args.compare_min,
            thin_below=args.thin_below,
            min_gap_pt=args.min_gap_pt,
        ),
    )
    print(f"accounts {built.n_accounts} reference {built.n_reference} videos {built.n_videos}")
    for item in built.genres:
        opening = item.choice("opening_type").choice or "データ不足"
        print(f"{item.genre}: {item.basis} / {item.account_confidence} / 冒頭 {opening}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
