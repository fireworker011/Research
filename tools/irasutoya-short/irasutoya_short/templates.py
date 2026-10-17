"""編集テンプレ。構成・テロップ・効果音・テンポをまとめて切り替える。"""

from __future__ import annotations

YELLOW = (255, 226, 40, 255)
WHITE = (255, 255, 255, 255)
BLUE = (186, 230, 255, 255)
ORANGE = (255, 148, 48, 255)
PINK = (255, 176, 206, 255)
GOLD = (255, 206, 64, 255)
GREEN = (176, 255, 176, 255)
MUTED = (214, 216, 226, 255)
BLACK_BAR = (0, 0, 0, 170)

TEMPLATE_NAMES = ("sukatto", "before_after", "aruaru", "ranking", "qa")


def _telop(
    bar: str,
    stroke: int,
    size: int,
    slide: float,
    y_ratio: float,
    colors: dict[str, tuple[int, int, int, int]],
    bar_fill: tuple[int, int, int, int] = BLACK_BAR,
    bar_fills: dict[str, tuple[int, int, int, int]] | None = None,
) -> dict:
    return {
        "bar": bar,
        "stroke": stroke,
        "size": size,
        "slide": slide,
        "y_ratio": y_ratio,
        "bar_fill": bar_fill,
        "bar_fills": bar_fills or {},
        "colors": colors,
    }


def _pace(
    speed: float,
    hook_speed: float,
    develop: float,
    punch: float,
    close: float,
    sfx_gain: float,
    tail: float,
    tails: dict[str, float],
) -> dict:
    return {
        "speed": speed,
        "hook_speed": hook_speed,
        "sfx_gain": sfx_gain,
        "tail": tail,
        "role_speed": {
            "hook": hook_speed,
            "develop": develop,
            "punch": punch,
            "close": close,
            "credit": speed,
        },
        "role_tail": tails,
    }


TEMPLATES: dict[str, dict] = {
    "sukatto": {
        "label": "フック→展開→オチ→締め",
        "pace": _pace(
            1.28, 1.48, 1.28, 1.28, 1.28, 0.22, 0.16,
            {"hook": 0.16, "develop": 0.16, "punch": 0.16, "close": 0.16, "credit": 0.0},
        ),
        "telop": _telop(
            "round", 5, 78, 0.16, 0.84,
            {"hook": YELLOW, "develop": WHITE, "punch": YELLOW, "close": YELLOW, "credit": WHITE},
        ),
    },
    "before_after": {
        "label": "ビフォーアフター",
        "pace": _pace(
            1.12, 1.42, 1.12, 1.45, 1.18, 0.2, 0.2,
            {"hook": 0.12, "develop": 0.24, "punch": 0.08, "close": 0.2, "credit": 0.0},
        ),
        "telop": _telop(
            "square", 6, 80, 0.2, 0.82,
            {
                "hook": ORANGE,
                "develop": BLUE,
                "before": BLUE,
                "turn": WHITE,
                "after": ORANGE,
                "punch": ORANGE,
                "close": YELLOW,
                "credit": WHITE,
            },
            bar_fills={
                "before": (16, 36, 72, 200),
                "after": (92, 36, 8, 200),
            },
        ),
    },
    "aruaru": {
        "label": "あるある列挙",
        "pace": _pace(
            1.5, 1.5, 1.5, 1.36, 1.22, 0.14, 0.08,
            {"hook": 0.08, "develop": 0.06, "punch": 0.1, "close": 0.18, "credit": 0.0},
        ),
        "telop": _telop(
            "pill", 4, 74, 0.08, 0.8,
            {
                "hook": PINK,
                "develop": WHITE,
                "item": WHITE,
                "punch": YELLOW,
                "close": PINK,
                "credit": WHITE,
            },
        ),
    },
    "ranking": {
        "label": "ランキング",
        "pace": _pace(
            1.3, 1.55, 1.3, 1.16, 1.2, 0.26, 0.14,
            {"hook": 0.1, "develop": 0.12, "punch": 0.28, "close": 0.16, "credit": 0.0},
        ),
        "telop": _telop(
            "square", 7, 86, 0.12, 0.78,
            {
                "hook": GOLD,
                "develop": WHITE,
                "rank": GOLD,
                "punch": GOLD,
                "close": WHITE,
                "credit": WHITE,
            },
            bar_fills={"rank": (48, 28, 8, 210), "punch": (48, 28, 8, 210)},
        ),
    },
    "qa": {
        "label": "問いかけ→答え",
        "pace": _pace(
            1.22, 1.08, 1.22, 1.4, 1.1, 0.18, 0.18,
            {"hook": 0.34, "develop": 0.14, "punch": 0.12, "close": 0.24, "credit": 0.0},
        ),
        "telop": _telop(
            "round", 5, 84, 0.24, 0.86,
            {
                "hook": YELLOW,
                "question": YELLOW,
                "develop": MUTED,
                "guess": MUTED,
                "answer": GREEN,
                "punch": GREEN,
                "close": YELLOW,
                "credit": WHITE,
            },
        ),
    },
}


def template_names() -> list[str]:
    return list(TEMPLATE_NAMES)


def require_template(name: str) -> dict:
    if name not in TEMPLATES:
        known = "、".join(TEMPLATE_NAMES)
        raise ValueError(f"未知のテンプレです: {name}。使えるのは {known} です。")
    return TEMPLATES[name]


def describe_templates() -> list[dict]:
    rows = []
    for name in TEMPLATE_NAMES:
        spec = TEMPLATES[name]
        pace = spec["pace"]
        telop = spec["telop"]
        rows.append(
            {
                "id": name,
                "label": spec["label"],
                "telop_bar": telop["bar"],
                "telop_y_ratio": telop["y_ratio"],
                "hook_speed": pace["hook_speed"],
                "develop_speed": pace["role_speed"]["develop"],
                "punch_speed": pace["role_speed"]["punch"],
                "sfx_gain": pace["sfx_gain"],
            }
        )
    return rows


def settings_for(name: str) -> dict:
    pace = require_template(name)["pace"]
    return {
        "speed": pace["speed"],
        "hook_speed": pace["hook_speed"],
        "telop_scale": 1.0,
        "sfx_gain": pace["sfx_gain"],
        "bgm_gain": 0.045,
        "mouth_gain": 1.0,
        "bgm": True,
        "tail": pace["tail"],
        "role_speed": dict(pace["role_speed"]),
        "role_tail": dict(pace["role_tail"]),
    }


def telop_style(name: str) -> dict:
    src = require_template(name)["telop"]
    return {
        "bar": src["bar"],
        "stroke": src["stroke"],
        "size": src["size"],
        "slide": src["slide"],
        "y_ratio": src["y_ratio"],
        "bar_fill": src["bar_fill"],
        "bar_fills": dict(src["bar_fills"]),
        "colors": dict(src["colors"]),
    }


def telop_color(style: dict, tone: str, role: str) -> tuple[int, int, int, int]:
    colors = style["colors"]
    if tone in colors:
        return colors[tone]
    if role in colors:
        return colors[role]
    return WHITE


def telop_bar_fill(style: dict, tone: str, role: str) -> tuple[int, int, int, int]:
    fills = style.get("bar_fills") or {}
    if tone in fills:
        return fills[tone]
    if role in fills:
        return fills[role]
    return style["bar_fill"]


def scene_speed(settings: dict, scene: dict) -> float:
    role_speed = settings.get("role_speed") or {}
    role = str(scene.get("role") or "")
    if role in role_speed:
        return float(role_speed[role])
    if role == "hook":
        return float(settings["hook_speed"])
    return float(settings["speed"])


def scene_tail(settings: dict, scene: dict) -> float:
    if not str(scene.get("text") or "").strip():
        return 0.0
    role_tail = settings.get("role_tail") or {}
    role = str(scene.get("role") or "")
    if role in role_tail:
        return float(role_tail[role])
    return float(settings.get("tail", 0.16))


def scale_speeds(settings: dict, body: float, hook: float) -> None:
    """body は展開・オチ・締め、hook はフック。1より大きいと速くなる。"""
    settings["speed"] = round(float(settings["speed"]) * body, 3)
    settings["hook_speed"] = round(float(settings["hook_speed"]) * hook, 3)
    role = settings.get("role_speed")
    if isinstance(role, dict):
        for key in list(role):
            factor = hook if key == "hook" else body
            role[key] = round(float(role[key]) * factor, 3)
