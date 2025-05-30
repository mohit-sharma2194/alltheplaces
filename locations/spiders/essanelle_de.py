from locations.storefinders.klier_hair_group import KlierHairGroupSpider


class EssanelleDESpider(KlierHairGroupSpider):
    name = "essanelle_de"
    start_urls = ["https://essanelle-friseur.de/salons/"]
    item_attributes = {"brand": "essanelle", "brand_wikidata": "Q121888190"}
