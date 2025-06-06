from scrapy import Spider
from scrapy.http import JsonRequest

from locations.categories import Categories, apply_category
from locations.dict_parser import DictParser
from locations.hours import OpeningHours


class Mitre10NZSpider(Spider):
    name = "mitre_10_nz"
    item_attributes = {"brand": "Mitre 10", "brand_wikidata": "Q6882394"}
    allowed_domains = ["ccapi.mitre10.co.nz"]
    start_urls = [
        "https://ccapi.mitre10.co.nz/occ/v2/mitre10/geolocation/store-locator?fields=FULL&page=0&pageSize=1000&storeCode=28&lang=en&curr=NZD"
    ]
    requires_proxy = "NZ"

    def start_requests(self):
        for url in self.start_urls:
            yield JsonRequest(url=url)

    def parse(self, response):
        for location in response.json()["stores"]:
            item = DictParser.parse(location)
            item["ref"] = location["name"]
            name = location.get("displayName", "")
            if name.startswith("Mitre 10 MEGA "):
                item["name"] = "Mitre 10 MEGA"
                item["branch"] = name.removeprefix("Mitre 10 MEGA ")
            else:
                item["name"] = "Mitre 10"
                item["branch"] = name.removeprefix("Mitre 10 ")
            item["city"] = location["address"].get(
                "suburb", location["address"].get("town", location["address"].get("city"))
            )
            item["addr_full"] = location["address"]["formattedAddress"]
            item["phone"] = location["address"].get("phone")
            item["email"] = location["address"].get("email")
            item["website"] = "https://www.mitre10.co.nz/store-locator?storeCode=" + location["name"]
            if location.get("openingHours"):
                item["opening_hours"] = OpeningHours()
                for day_hours in location["openingHours"]["weekDayOpeningList"]:
                    if day_hours["closed"]:
                        item["opening_hours"].set_closed(day_hours["weekDay"])
                        continue
                    if "openingTime" not in day_hours.keys():
                        continue
                    if "closingTime" not in day_hours.keys():
                        continue
                    item["opening_hours"].add_range(
                        day_hours["weekDay"],
                        day_hours["openingTime"]["formattedHour"].upper(),
                        day_hours["closingTime"]["formattedHour"].upper(),
                        "%I:%M %p",
                    )

            apply_category(Categories.SHOP_DOITYOURSELF, item)

            yield item
