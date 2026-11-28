"""公式LINEの友だち追加URLから、記事バナー用のQRを書く。"""

import segno

URL = "https://line.me/R/ti/p/@847jesif"
OUT = "html/qr-line.png"


def main() -> None:
    code = segno.make(URL, error="h")
    code.save(OUT, scale=10, border=2, dark="#1a1814", light="#fbfaf6")


if __name__ == "__main__":
    main()
