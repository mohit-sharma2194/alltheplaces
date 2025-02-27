from typing import Iterable

from scrapy import Request
from scrapy.http import Response

from locations.categories import Categories
from locations.hours import CLOSED_IT, DAYS_IT, OpeningHours
from locations.items import Feature
from locations.storefinders.agile_store_locator import AgileStoreLocatorSpider


class SigmaITSpider(AgileStoreLocatorSpider):
    name = "sigma_it"
    item_attributes = {"brand": "Sigma", "brand_wikidata": "Q3977979", "extras": Categories.SHOP_SUPERMARKET.value}
    allowed_domains = ["www.supersigma.com"]

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Request]:
        item["website"] = "https://www.supersigma.com/pdv/" + feature["slug"] + "/"
        yield Request(url=item["website"], meta={"item": item}, callback=self.parse_hours)

    def parse_hours(self, response: Response) -> Iterable[Feature]:
        item = response.meta["item"]
        item["website"] = response.url  # Capture any redirected URL
        hours_string = " ".join(
            filter(
                None, map(str.strip, response.xpath('//span[contains(@class, "bkg_orari")]/span/span//text()').getall())
            )
        )
        if hours_string:
            item["opening_hours"] = OpeningHours()
            item["opening_hours"].add_ranges_from_string(hours_string, days=DAYS_IT, closed=CLOSED_IT)
        yield item
