import scrapy

class UnicaCrawlerItem(scrapy.Item):
    course_link = scrapy.Field()
    course_name = scrapy.Field()
    instructor = scrapy.Field()
    old_price = scrapy.Field()
    new_price = scrapy.Field()
    category_name = scrapy.Field() 
    number_of_students = scrapy.Field()
    rating = scrapy.Field()
    tags = scrapy.Field()
    what_you_learn = scrapy.Field()
    sections = scrapy.Field()
    lectures = scrapy.Field()
    duration = scrapy.Field()