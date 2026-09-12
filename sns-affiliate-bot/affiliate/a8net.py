import os
from typing import Optional


class A8NetManager:
    """
    A8.net アフィリエイトリンクの管理。
    A8.net 管理画面でアフィリエイトリンクを生成して .env に貼り付けます。
    """

    def __init__(self):
        self.affiliate_id = os.getenv("A8_AFFILIATE_ID", "")

    def build_link(self, base_url: str) -> str:
        """A8.net リンクに affiliate_id を埋め込む。"""
        if not self.affiliate_id:
            return base_url
        return base_url.replace("{A8_ID}", self.affiliate_id)

    def get_product_url(self, niche_config: dict, product_id: str) -> Optional[str]:
        """ニッチ設定から商品URLを取得する。"""
        products = niche_config.get("affiliate", {}).get("products", [])
        for product in products:
            if product.get("id") == product_id:
                url = product.get("url_template", "")
                return self.build_link(url)
        return None

    def get_cta_text(self, niche_config: dict, product_id: str) -> str:
        """商品のCTAテキストを取得する。"""
        products = niche_config.get("affiliate", {}).get("products", [])
        for product in products:
            if product.get("id") == product_id:
                return product.get("cta", "詳細はプロフのリンクから")
        return "詳細はプロフのリンクから"
