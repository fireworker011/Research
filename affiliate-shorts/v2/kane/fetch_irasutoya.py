#!/usr/bin/env python3
"""いらすとやの公開ページから、動画に使う絵だけを取り直す。

元のPNGはリポジトリに置かない。よくある質問で、素材そのものの再配布は断られている。
取得先は irasutoya.com の記事に載っている画像だけで、他サイトのコピーは使わない。
"""

from __future__ import annotations

import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "remotion" / "public" / "ira"

# ページURLは出典。ファイルURLは、そのページの本文に出ていた元画像。
ASSETS = [
    (
        "payslip.png",
        "https://www.irasutoya.com/2015/09/blog-post_59.html",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjeUMgtaxgGuxqOwruBGsE_3sFhVpIVDGTDKwHshf9R5CwcxamHzlbPvZpGBip0n2u9AucDhmGRQ0ZEJh8DIQO8Xy3_hprMLobm8Ye4aFkI-Tm1JZ51JY_-UWian0fltSu54YJaIgMDBy0/s800/money_kyuuyo_kyuuryou_meisai.png",
    ),
    (
        "worker.png",
        "https://www.irasutoya.com/2017/07/blog-post_962.html",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEjk4shwXy1slsVGCZ6goHjeUTo19n6CYrgcu1zQ4zzIbX1QPtSlMeScN6z3dv7InCH2AsnEsBwqsWPxtk057JV8I49UfHVIZk1dVtjB65i3CHOKGEgGpiw48vm5uKux9W3MYkblf5wk1Pkz/s1600/kaisya_komaru_man.png",
    ),
    (
        "calc.png",
        "https://www.irasutoya.com/2013/03/blog-post_3975.html",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEiwCxAolQw2K7WcbduqGlI4-r4elMWZFoTAPLblrecuT_B0fFBLlI6Su_yE1wdMg-fHmpFzlS_5Cxk00YMf3XKvebhX-zmYc2bToYzdSrn6Kj0wE8V_pKd8axLAb5P7PHHS7KuHQ0QR5cv8/s1600/bunbougu_dentaku.png",
    ),
    (
        "nenkin.png",
        "https://www.irasutoya.com/2013/12/blog-post_5902.html",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhxkkkev89A6eh0usanS2llgHiYNscw78Jyh6CkTjlTqI1rvJJtV_UtlS_UIbndMPE9BnibvFg5TLRajhj8f7p-iql8nCx6gyVRtUcZSb5HErHsp2RBeINyz_mbSjKy4JXwieUTlPa91c4g/s1600/nenkin_techou_blue.png",
    ),
    (
        "office.png",
        "https://www.irasutoya.com/2016/04/blog-post_1.html",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEhoWd6_d86QKPrJ2sO6zo4FMneJzDzGaZlfQ4qDj0-BSRCjZ-fRp0hgG95sMO7UQlgvyVzMhihZliPu7aIH5i0qSlKAo7a29FXqLjtmlPwgTTwPJC31Z77Nql6NWIwzvUUBN_H2G-1liKba/s1600/building_nenkin_jimusyo.png",
    ),
    (
        "teiki.png",
        "https://www.irasutoya.com/2014/08/blog-post_103.html",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEidqyN9Jytyyw3bT4hjOpwBoynlbHobD4JgLKBow35WHjwRkIFvzZ-gAOXePUXwh0MAQgCs2VlY6z_i3xQIgvYGVHHnY8uRVVgxzEpGkjozpGPtee6NHsTw-Y6r1hBU3R9EdMZsdvNYpaMe/s1600/kippu_teiki.png",
    ),
    (
        "train.png",
        "https://www.irasutoya.com/2013/04/blog-post_3537.html",
        "https://blogger.googleusercontent.com/img/b/R29vZ2xl/AVvXsEgPfKSh8V0ePET5gr_llcj8aEcQ_K8Dac-LFDx81TQTHmfgu6nkukQihrzNHB8RKKwiOMxp1zQWlkvGLQUWKO8wRMCvLbSK1BiAl1Y6GGJgxls-lnxGiCVUQmfJ4gCFIp5jyK8wwgRsGA0/s1600/train_green.png",
    ),
]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for name, _page, url in ASSETS:
        dest = OUT / name
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        dest.write_bytes(urllib.request.urlopen(req, timeout=60).read())
        print(name, dest.stat().st_size)


if __name__ == "__main__":
    main()
