from requests import Response
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from locations.google_url import extract_google_position
from locations.items import Feature


class ApcoaSpider(CrawlSpider):
    name = "apcoa"
    item_attributes = {"operator": "APCOA Parking", "operator_wikidata": "Q296108"}
    allowed_domains = [
        "www.apcoa.at",
        "www.apcoa.dk",
        "www.apcoa.de",
        "www.apcoa.ie",
        "www.apcoa.it",
        "www.apcoa.nl",
        "www.apcoa.no",
        "www.apcoa.se",
        "www.apcoa.co.uk",
        "www.apcoa.pl",
        "www.apcoa.ch",
    ]
    start_urls = [
        "https://www.apcoa.at/standorte/staedte/alle-staedte/",  # Austria
        "https://www.apcoa.dk/alle-lokationer/",  # Denmark
        "https://www.apcoa.de/standorte/alle-standorte/",  # Germany
        "https://www.apcoa.ie/locations/all-locations/",  # Ireland
        "https://www.apcoa.it/parcheggi/",  # Italy
        "https://www.apcoa.nl/alle-locaties/",  # Netherlands
        "https://www.apcoa.no/finn-parkering/finn-en-parkeringsplass/byer-a-aa",  # Norway
        "https://www.apcoa.se/alla-staeder/",  # Sweden
        "https://www.apcoa.co.uk/parking-locations/all-locations/",  # UK
        "https://www.apcoa.pl/en/parking-locations/all-locations/",  # Poland
        "https://www.apcoa.ch/en/parking-locations/cities/all-cities/",  # Switzerland
    ]
    rules = [
        Rule(
            LinkExtractor(
                allow=[
                    "/kurzparken/standorte/[^/]+$",  # Austria, Germany
                    ".*/parkings-per-stad/",  # Belgium
                    "/find-en-p-plads/lokationer/[^/]+$",  # Denmark
                    "/location-overview/location/[^/]+$",  # Ireland
                    "/sosta-breve/sedi/[^/]+",  # Italy
                    "/kort-parkeren/locaties/[^/]+",  # Netherlands
                    "/finn-parkering/lokasjoner/[^/]+$",  # Norway
                    "/hitta-parkering/parkering/[^/]+$",  # Sweden
                    "/find-parking/locations/[^/]+",  # UK
                    "/parking-in/[^/]+",
                    "/short-stay-parking/locations/[^/]+",
                ]
            )
        ),
        Rule(
            LinkExtractor(
                allow=[
                    "/kurzparken/standorte/[^/]+/[^/]+$",  # Austria, Germany
                    "/find-en-p-plads/lokationer/[^/]+/[^/]+$",  # Denmark
                    "/location-overview/location/[^/]+/[^/]+$",  # Ireland
                    "/sosta-breve/sedi/[^/]+/[^/]+",  # Italy
                    "/kort-parkeren/locaties/[^/]+/[^/]+$",  # Netherlands
                    "/finn-parkering/lokasjoner/[^/]+/[^/]+$",  # Norway
                    "/hitta-parkering/parkering/[^/]+/[^/]+$",  # Sweden
                    "/find-parking/locations/[^/]+/[^/]+$",  # UK
                    "/parking-in/[^/]+/[^/]+$",
                    "/short-stay-parking/locations/[^/]+/[^/]+$",
                ]
            ),
            callback="parse",
        ),
    ]

    def parse(self, response: Response, **kwargs):
        item = Feature()
        item["branch"] = response.xpath('//*[@class="text-h3 inline"]//text()').get()
        item["addr_full"] = response.xpath('//*[@class="main"]//span[2]/text()').get()
        extract_google_position(item, response)
        item["ref"] = item["website"] = response.url
        yield item
