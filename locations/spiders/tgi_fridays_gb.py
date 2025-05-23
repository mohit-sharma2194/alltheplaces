import json
import re
from typing import Iterable
from urllib.parse import urljoin

from scrapy.http import FormRequest, Request
from scrapy.spiders import Spider

from locations.dict_parser import DictParser
from locations.hours import OpeningHours, day_range


class TgiFridaysGBSpider(Spider):
    name = "tgi_fridays_gb"
    item_attributes = {
        "brand": "TGI Fridays",
        "brand_wikidata": "Q1524184",
        "country": "GB",
    }
    allowed_domains = ["tgifridays.co.uk"]

    def make_request(self, page: int) -> FormRequest:
        return FormRequest(
            url="https://www.tgifridays.co.uk/locations?ajax_form=1&_wrapper_format=drupal_ajax",
            formdata={
                "search_current_page": str(page),
                "form_uuid": "form--10a1a57d-ecb7-4a97-8eee-7c6560247fb0",
                "search_geolocation": "",
                "restaurant_search": "",
                "form_build_id": "form-MqLH2mZqPxSJNhOlqm--0hu5jwm8L8YxnBqtuZfwZs0",
                "form_id": "fridays_restaurants_restaurant_selector",
                "_triggering_element_name": "search_geolocation",
                "_drupal_ajax": "1",
                "ajax_page_state[theme]": "fridays",
                "ajax_page_state[theme_token]": "",
                "ajax_page_state[libraries]": "eJyNj-tugzAMRl-olEeKTPJBPUJMbacdbz-mqaTqVG2_4hzfjqMoei4OLZTPH9cK3c6j6HIalRNt1lOMoomlNJJuKN5FyiiJ9OCDyMxlCndOE_wNDvj8WfYuzyVzwZGNpMn2XSrV0JoSdivyZ62RrnZ8piwD5c5826dNDe9vZ5kTmvYFKq-sSGoKiqlm0tcaQ6yKblW-Udwado7z1i2Snm60O6_4NcFRZnY0a5f4iIPCnKpS8W-DRxwym4chS5z_qjSQxkuguk-VZc1w_LPF6rCwn2wzx9IPZPgC6gHZuQ",
            },
            method="POST",
            meta={"page": page},
        )

    def start_requests(self) -> Iterable[Request]:
        yield self.make_request(0)

    def parse(self, response):
        data = response.xpath("//textarea/text()").get()
        jsondata = json.loads(data)[1]["args"][1]

        for location in jsondata["results"]:
            item = DictParser.parse(location)
            item["branch"] = item.pop("name").removeprefix("TGI Fridays ")
            item["lat"], item["lon"] = location["geolocation"].split(",")
            slug = re.sub("(TGI Fridays |'| $)", "", location["title"])
            slug = re.sub(" +", "-", slug)
            slug = "restaurant/" + slug.lower()
            item["website"] = urljoin("https://www.tgifridays.co.uk/", slug)
            item["ref"] = location["nid"]
            yield Request(item["website"], callback=self.parse_opening_hours, cb_kwargs={"item": item})

        if jsondata["totalCount"] > jsondata["offset"] + jsondata["limit"]:
            yield self.make_request(int(jsondata["offset"] / jsondata["limit"]) + 1)

    def parse_opening_hours(self, response, item):
        opening_hours = OpeningHours()
        hours = response.xpath('//div[contains(@class, "field--type-opening-timetable")]//div[@class="mb-5 last:mb-0"]')
        for hour in hours:
            days = hour.xpath('p[contains(@class, "subtitle-s")]/text()').get()
            if "-" in days:
                days = day_range(*days.split(" - "))
            else:
                days = [days]
            hour_range = hour.xpath('p//span[@class="font-bold"]/text()').get()
            opening_hours.add_days_range(days, *hour_range.replace(".", ":").split(" - "))
        item["opening_hours"] = opening_hours
        item["phone"] = response.xpath('//a[contains(@href, "tel:")]/text()').get()

        yield item
