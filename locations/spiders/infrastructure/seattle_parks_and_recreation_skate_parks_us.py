from typing import Iterable

from scrapy.http import Response

from locations.categories import Categories, apply_category
from locations.items import Feature
from locations.storefinders.arcgis_feature_server import ArcGISFeatureServerSpider


class SeattleParksAndRecreationSkateParksUSSpider(ArcGISFeatureServerSpider):
    name = "seattle_parks_and_recreation_skate_parks_us"
    item_attributes = {"operator": "Seattle Parks and Recreation", "operator_wikidata": "Q7442147", "state": "WA"}
    host = "services.arcgis.com"
    context_path = "ZOyb2t4B0UYuYNYH/ArcGIS"
    service_id = "Skate_Parks"
    layer_id = "0"

    def post_process_item(self, item: Feature, response: Response, feature: dict) -> Iterable[Feature]:
        item["ref"] = feature.get("PMAID")
        item["name"] = feature["ALT_NAME"]
        apply_category(Categories.LEISURE_PITCH, item)
        apply_category({"sport": "skateboard"}, item)
        yield item
