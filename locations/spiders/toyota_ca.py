import datetime
from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.dict_parser import DictParser
from locations.hours import OpeningHours
from locations.items import Feature
from locations.json_blob_spider import JSONBlobSpider
from locations.spiders.toyota_au import TOYOTA_SHARED_ATTRIBUTES

current_day = (datetime.datetime.now()).strftime("%A")


class ToyotaCASpider(JSONBlobSpider):
    name = "toyota_ca"
    item_attributes = TOYOTA_SHARED_ATTRIBUTES
    start_urls = [
        "https://www.toyota.ca/bin/find_a_dealer/dealersList?brand=toyota&language=en&userInput=vancover&latitude=49.2827291&longitude=-123.1207375&scenario=proximity&dayOfWeek={}".format(
            current_day
        )
    ]

    def parse(self, response: Response) -> Iterable[Feature]:
        for location in response.json()["dealers"]:
            item = DictParser.parse(location)
            item["ref"] = location["dealerCode"]
            item["street_address"] = item.pop("addr_full")
            apply_category(Categories.SHOP_CAR, item)
            yield item
