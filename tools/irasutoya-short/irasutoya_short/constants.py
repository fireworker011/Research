"""画面サイズと、記事どおりの尺・点数の上限。"""

WIDTH = 1080
HEIGHT = 1920
FPS = 24
SAMPLE_RATE = 24000
MAX_ASSETS = 20
CHUNK_SECONDS = 6.0
MIN_DURATION = 25.0
MAX_DURATION = 40.0
MIN_SCENES = 12
MAX_SCENES = 14

FONT_CANDIDATES = (
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
)

# 青山龍星は個人事業・法人だと事前許可が要る。このパイプラインでは使わない。
BLOCKED_STYLE_IDS = frozenset({13, 81, 82, 83, 84, 85, 86})
