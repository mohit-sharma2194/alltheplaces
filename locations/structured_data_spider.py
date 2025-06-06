import re
from typing import Iterable
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

from scrapy import Selector, Spider
from scrapy.http import Response

from locations.categories import PaymentMethods, map_payment
from locations.items import Feature
from locations.linked_data_parser import LinkedDataParser
from locations.microdata_parser import MicrodataParser


def extract_email(item, sel: Selector):
    for link in sel.xpath(".//a[contains(@href, 'mailto')]/@href").getall():
        link = link.strip()
        if link.startswith("mailto:") and "@" in link:
            item["email"] = urlparse(link).path
            return


def extract_phone(item, sel: Selector):
    for link in sel.xpath(".//a[contains(@href, 'tel')]/@href").getall():
        link = link.strip()
        if link.startswith("tel:"):
            item["phone"] = urlparse(link).path
            return


def clean_twitter(url: str) -> str:
    if not url:
        return None
    return (
        url.strip()
        .replace("http:", "")
        .replace("https:", "")
        .replace("www.", "")
        .replace("twitter.com", "")
        .replace("twitter.co.uk", "")
        .strip("@/")
        .split("?", 1)[0]
    )


def extract_twitter(item: Feature, sel: Selector):
    if twitter := sel.xpath('//meta[@name="twitter:site"]/@content').get():
        if twitter := clean_twitter(twitter):
            item["twitter"] = twitter
            return
    for url in sel.xpath('.//a[contains(@href, "twitter.com")]/@href').getall():
        if twitter := clean_twitter(url):
            item["twitter"] = twitter
            return


def clean_facebook(url: str) -> str:
    if not url:
        return None
    clean_url = urlparse(url)
    if "facebook.com" not in clean_url.netloc:
        return None
    if clean_url.path in [None, "/", ""]:
        return None
    elif clean_url.path in ["/profile.php", "/group.php"]:
        # Just copy id/gid param eg https://www.facebook.com/profile.php?id=100057371322568
        query = parse_qs(clean_url.query)
        clean_query = {}
        for k, v in query.items():
            if k in ["id", "gid"]:
                clean_query[k] = v[0]
        clean_url = clean_url._replace(
            scheme="https", netloc="www.facebook.com", query=urlencode(clean_query), fragment=""
        )
    else:
        # Just copy the path eg https://www.facebook.com/Ernstingsfamily/
        clean_url = clean_url._replace(scheme="https", netloc="www.facebook.com", query="", fragment="")
        return clean_url.geturl()


def extract_facebook(item: Feature, sel: Selector):
    for fb in sel.xpath(
        './/a[contains(@href, "facebook.com")]'
        '[not(contains(@href, " "))]'
        '[not(contains(@href, "events"))]'
        '[not(contains(@href, "posts"))]'
        '[not(contains(@href, "sharer.php"))]'
        '[not(contains(@href, "share.php"))]/@href'
    ).getall():
        if url := clean_facebook(fb):
            item["facebook"] = url
            return

    if fb := sel.xpath('.//div[@class="fb-customerchat"][@page_id]/@page_id').get():
        item["facebook"] = f"https://www.facebook.com/profile.php?id={fb}"
        return


def clean_instagram(url: str) -> str:
    if not url:
        return None
    clean_url = urlparse(url)
    if "instagram.com" not in clean_url.netloc:
        return None
    if clean_url.path in [None, "/", ""]:
        return None
    clean_url = clean_url._replace(scheme="https", netloc="www.instagram.com", query="", fragment="")
    return clean_url.geturl()


def extract_instagram(item: Feature, response: Selector):
    for instagram in response.xpath('.//a[contains(@href, "instagram.com")]/@href').getall():
        if url := clean_instagram(instagram):
            item["extras"]["contact:instagram"] = url
            return


def extract_image(item, response):
    if image := response.xpath('//meta[@name="twitter:image"]/@content').get():
        item["image"] = image.strip()
        return
    if image := response.xpath('//meta[@name="og:image"]/@content').get():
        item["image"] = image.strip()


def get_url(response) -> str:
    if canonical := response.xpath('//link[@rel="canonical"]/@href').get():
        return canonical
    return response.url


class StructuredDataSpider(Spider):
    """
    From a scrapy Response, attempt to extract all JSON LD information.

    Use in conjunction with a `CrawlSpider` or directly call `parse_sd`.

    To search for or omit specific data, set any of the spider attributes for:
    - search_for_email
    - search_for_phone
    - search_for_twitter
    - search_for_facebook
    - search_for_instagram
    - search_for_image
    - search_for_amenity_features
    - search_for_payment_accepted

    By default the spider only looks for certain `wanted_types`.
    You can change this behaviour by specifying this as a list of your desired types.
    Use either https://validator.schema.org/ or uv run scrapy sd <url> to examine potential structured data available.

    `time_format` can be specified if a non standard pattern is used.

    Use either `pre_process_data` or `post_process_item` to add to the core behaviour of this spider.

    If the response contains malformed JSON; an alternative `json_parser` can be specified - ie json5 or chompjs.
    """

    dataset_attributes = {"source": "structured_data"}

    wanted_types = [
        "LocalBusiness",
        "ConvenienceStore",
        "Store",
        "Restaurant",
        "BankOrCreditUnion",
        "GroceryStore",
        "FastFoodRestaurant",
        "Hotel",
        "ClothingStore",
        "DepartmentStore",
        "HardwareStore",
        "AutomotiveBusiness",
        "BarOrPub",
        "SportingGoodsStore",
        "Dentist",
        "AutoRental",
        "AutoPartsStore",
        "GasStation",
        "LiquorStore",
        "BikeStore",
        "Optician",
        "Bakery",
        "InsuranceAgency",
        "ElectronicsStore",
        "Accommodation",
        "AccountingService",
        "AutoDealer",
        "AutoGlass",
        "AutomatedTeller",
        "AutoRepair",
        "AutoWash",
        "BagsStore",
        "BeautySalon",
        "CafeOrCoffeeShop",
        "Campground",
        "ChildCare",
        "EmergencyService",
        "ExerciseGym",
        "FinancialService",
        "FoodEstablishment",
        "FurnitureStore",
        "HairSalon",
        "HealthAndBeautyBusiness",
        "HealthClub",
        "HobbyShop",
        "HomeAndConstructionBusiness",
        "HomeGoodsStore",
        "Hospital",
        "IceCreamShop",
        "JewelryStore",
        "LegalService",
        "LodgingBusiness",
        "MedicalBusiness",
        "MedicalClinic",
        "MobilePhoneStore",
        "MovieTheater",
        "OutletStore",
        "PetStore",
        "Pharmacy",
        "Physician",
        "RealEstateAgent",
        "SelfStorage",
        "ShoeStore",
        "ShoppingCenter",
        "SportsActivityLocation",
        "StadiumOrArena",
        "TrainStation",
        "TravelAgency",
        "VeterinaryCare",
    ]
    convert_microdata = True
    search_for_email = True
    search_for_phone = True
    search_for_twitter = True
    search_for_facebook = True
    search_for_instagram = False
    search_for_amenity_features = True
    search_for_payment_accepted = True
    search_for_image = True
    json_parser = "json"
    time_format = "%H:%M"

    def __init__(self):
        for i, wanted in enumerate(self.wanted_types):
            if isinstance(wanted, list):
                self.wanted_types[i] = [LinkedDataParser.clean_type(t) for t in wanted]
            else:
                self.wanted_types[i] = LinkedDataParser.clean_type(wanted)

    def parse(self, response: Response, **kwargs):
        yield from self.parse_sd(response)

    def parse_sd(self, response: Response):  # noqa: C901
        if self.convert_microdata:
            MicrodataParser.convert_to_json_ld(response)
        for ld_item in self.iter_linked_data(response):
            self.pre_process_data(ld_item)

            item = LinkedDataParser.parse_ld(ld_item, time_format=self.time_format)
            url = get_url(response)

            if item["ref"] is None:
                item["ref"] = self.get_ref(url, response)

            if isinstance(item["website"], list):
                if len(item["website"]) > 0:
                    item["website"] = item["website"][0]

            if not item["website"]:
                item["website"] = url
            elif item["website"].startswith("www"):
                item["website"] = "https://" + item["website"]
            elif item["website"].startswith("/"):
                item["website"] = urljoin(response.url, item["website"])

            if self.search_for_email and item["email"] is None:
                extract_email(item, response)

            if self.search_for_phone and item["phone"] is None:
                extract_phone(item, response)

            if self.search_for_twitter and item.get("twitter") is None:
                extract_twitter(item, response)

            if self.search_for_facebook and item.get("facebook") is None:
                extract_facebook(item, response)

            if self.search_for_image and item.get("image") is None:
                extract_image(item, response)

            if self.search_for_amenity_features:
                self.extract_amenity_features(item, response, ld_item)

            if self.search_for_payment_accepted:
                self.extract_payment_accepted(item, response, ld_item)

            if self.search_for_instagram and not item["extras"].get("instagram"):
                extract_instagram(item, response)

            if item.get("image") and item["image"].startswith("/"):
                item["image"] = urljoin(response.url, item["image"])

            yield from self.post_process_item(item, response, ld_item) or []

    def iter_linked_data(self, response: Response) -> Iterable[dict]:
        for ld_obj in LinkedDataParser.iter_linked_data(response, self.json_parser):
            if not ld_obj.get("@type"):
                continue

            types = ld_obj["@type"]

            if not isinstance(types, list):
                types = [types]

            types = [LinkedDataParser.clean_type(t) for t in types]

            for wanted_types in self.wanted_types:
                if isinstance(wanted_types, list):
                    if all(wanted in types for wanted in wanted_types):
                        yield ld_obj
                elif wanted_types in types:
                    yield ld_obj

    def extract_amenity_features(self, item, response: Response, ld_item):
        if "amenityFeature" in ld_item and len(ld_item["amenityFeature"]) > 0:
            self.logger.info(
                "Found amenityFeature data, implement `extract_amenity_features` or set `search_for_amenity_features` to suppress this message"
            )
            self.logger.debug(ld_item["amenityFeature"])
            self.crawler.stats.inc_value("atp/structured_data/unmapped/amenity_features")

    def extract_payment_accepted(self, item, response: Response, ld_item):
        """
        https://schema.org/paymentAccepted
        """
        if "paymentAccepted" not in ld_item:
            return
        if isinstance(ld_item["paymentAccepted"], str) and "," in ld_item["paymentAccepted"]:
            ld_item["paymentAccepted"] = ld_item["paymentAccepted"].split(",")
        if (
            isinstance(ld_item["paymentAccepted"], list)
            and len(ld_item["paymentAccepted"]) == 1
            and "," in ld_item["paymentAccepted"][0]
        ):
            ld_item["paymentAccepted"] = ld_item["paymentAccepted"][0].split(",")
        if isinstance(ld_item["paymentAccepted"], str):
            ld_item["paymentAccepted"] = [ld_item["paymentAccepted"]]
        for payment in ld_item["paymentAccepted"]:
            if payment:
                payment = payment.strip()
            if not payment:
                continue
            if not map_payment(item, payment, PaymentMethods):
                self.logger.info(
                    "Found paymentAccepted data that could not be mapped, implement `extract_payment_accepted` or set `search_for_payment_accepted` to suppress this message"
                )
                self.logger.debug(payment)
                self.crawler.stats.inc_value("atp/structured_data/unmapped/payment_accepted/{}".format(payment))

    def get_ref(self, url: str, response: Response) -> str:
        if hasattr(self, "rules"):  # Attempt to pull a match from CrawlSpider.rules
            for rule in getattr(self, "rules"):
                for allow in rule.link_extractor.allow_res:
                    if match := re.search(allow, url):
                        if len(match.groups()) > 0:
                            return match.group(1)
        elif hasattr(self, "sitemap_rules"):
            # Attempt to pull a match from SitemapSpider.sitemap_rules
            for rule in getattr(self, "sitemap_rules"):
                if match := re.search(rule[0], url):
                    if len(match.groups()) > 0:
                        return match.group(1)
        return url

    def pre_process_data(self, ld_data: dict, **kwargs):
        """Override with any pre-processing on the item."""

    def post_process_item(self, item: Feature, response: Response, ld_data: dict, **kwargs):
        """Override with any post-processing on the item."""
        yield item
