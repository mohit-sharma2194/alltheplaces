import scrapy

from locations.categories import Categories, Extras, apply_category, apply_yes_no
from locations.hours import OpeningHours
from locations.items import Feature
from locations.spiders.geldmaat_nl import GeldmaatNLSpider
from locations.user_agents import BROWSER_DEFAULT


class AbnAmroNLSpider(scrapy.Spider):
    name = "abn_amro_nl"
    item_attributes = {"brand": "ABN AMRO", "brand_wikidata": "Q287471"}
    start_urls = ["https://www.abnamro.nl/servicelocations/v3/"]
    custom_settings = {"ROBOTSTXT_OBEY": False, "USER_AGENT": BROWSER_DEFAULT}

    def parse(self, response, **kwargs):
        for stores in response.json().get("serviceLocations"):
            store = stores.get("serviceLocation")
            oh = OpeningHours()
            for services in store.get("services"):
                for day, hours in services.get("officeHours", {}).items():
                    if "-" not in hours[0]:
                        continue
                    starting, closing = hours[0].split("-")
                    oh.add_range(day, starting, closing)
            item = Feature(
                {
                    "ref": store.get("propRef"),
                    "street_address": store.get("address"),
                    "postcode": store.get("zipCode"),
                    "city": store.get("city"),
                    "lat": store.get("lat"),
                    "lon": store.get("lng"),
                    "opening_hours": oh,
                }
            )

            services = [s["functionality"] for s in store["services"]]
            # SFG, Notes out
            # MRA, Coins out
            # MFG, Notes in
            # MSA, Coins in
            # SBA, Sealbags in
            apply_yes_no(Extras.CASH_OUT, item, "SFG" in services or "MRA" in services)
            apply_yes_no(Extras.CASH_IN, item, "MFG" in services or "MSA" in services)

            location_type = store.get("locationType")
            if location_type == "CASHPOINT":
                item.update(GeldmaatNLSpider.item_attributes)
                apply_category(Categories.ATM, item)
            elif location_type == "OFFICE":
                apply_category(Categories.BANK, item)

            yield item
