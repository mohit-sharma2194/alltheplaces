import re
from urllib.parse import unquote

from requests import Response
from scrapy.spiders import SitemapSpider

from locations.items import Feature
from locations.structured_data_spider import StructuredDataSpider


class ChipotleSpider(SitemapSpider, StructuredDataSpider):
    name = "chipotle"
    item_attributes = {"brand": "Chipotle", "brand_wikidata": "Q465751"}
    sitemap_urls = [
        "https://locations.chipotle.fr/sitemap.xml",
        "https://locations.chipotle.ca/sitemap.xml",
        "https://locations.chipotle.de/sitemap.xml",
        "https://locations.chipotle.com/sitemap.xml",
        "https://locations.chipotle.co.uk/sitemap.xml",
    ]
    sitemap_rules = [
        (r".*/[a-z-]+/[a-z-]+/[^/]+$", "parse_sd"),
    ]

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        item["lat"], item["lon"] = re.search(
            r"latitude\":(-?\d+\.\d+),\"longitude\":(-?\d+\.\d+)",
            unquote(response.xpath('//*[contains(text(),"latitude")]/text()').get()),
        ).groups()
        yield item
