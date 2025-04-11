# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ImbdscraperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class MovieItem(scrapy.Item):
    title = scrapy.Field()
    year = scrapy.Field()
    imbd_rating = scrapy.Field()
    genres = scrapy.Field()
    directors = scrapy.Field()
    actors = scrapy.Field()
    runtime = scrapy.Field()
    watch_on = scrapy.Field()