# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class UnicaCrawlerItem(scrapy.Item):
    course_link = scrapy.Field()
    course_name = scrapy.Field()
    duration = scrapy.Field()
    instructor = scrapy.Field()
    lectures = scrapy.Field()
    new_price = scrapy.Field()
    old_price = scrapy.Field() 
    number_of_students = scrapy.Field()
    rating = scrapy.Field()
    sections = scrapy.Field()
    what_you_learn = scrapy.Field()
    tags= scrapy.Field()