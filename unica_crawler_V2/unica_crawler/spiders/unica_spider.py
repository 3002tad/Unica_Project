import scrapy
from unica_crawler.items import UnicaCrawlerItem

class UnicaSpider(scrapy.Spider):
    name = 'unica_spider'
    start_urls = ['https://unica.vn/']
    page_limit = 20
    category_limit = 7
    category_count = 0
    page_count = 1  

    def parse(self, response):
        categories = response.xpath('//div[contains(@class, "swiper-wrapper")]//a')
        
        for category in categories:
            if self.category_count >= self.category_limit:
                break

            category_url = response.urljoin(category.xpath('./@href').get())
            category_name = category.xpath('text()').get()

            self.category_count += 1
            yield scrapy.Request(
                category_url, 
                callback=self.parse_category_page, 
                meta={'category_name': category_name, 'page_count': 1}
            )

    def parse_category_page(self, response):
        courses = response.xpath('//a[contains(@class, "flex mb-6 lg:flex-row")]')

        for course in courses:
            course_name = course.xpath('.//span[@class="font-bold text-base leading-5"]/text()').get()
            instructor = course.xpath('.//div[@class="flex flex-col gap-2 text-sm font-light"]/span[1]/text()').get()
            new_price = course.xpath('.//div[@class="w-20"]/span[1]/text()').get()
            old_price = course.xpath('.//div[@class="w-20"]/span[2]/text()').get()
            course_link = response.urljoin(course.xpath('./@href').get())

            meta_data = {
                'course_name': course_name or '',
                'instructor': instructor or '',
                'new_price': new_price or '',
                'old_price': old_price or '',
                'course_link': course_link or '',
                'category_name': response.meta.get('category_name', ''),  # Đảm bảo 'category_name' có giá trị mặc định
            }
            yield scrapy.Request(course_link, callback=self.parse_course_details, meta=meta_data)

        if response.meta['page_count'] < self.page_limit:
            next_page = response.xpath('//li[@class="next"]/a/@href').get()
            if next_page:
                next_page_url = response.urljoin(next_page)
                yield scrapy.Request(
                    next_page_url, 
                    callback=self.parse_category_page,
                    meta={'category_name': response.meta.get('category_name', ''), 'page_count': response.meta['page_count'] + 1}
                )

    def parse_course_details(self, response):
        item = UnicaCrawlerItem()
        
        item['course_link'] = response.meta['course_link']
        item['course_name'] = response.meta['course_name']
        item['instructor'] = response.meta['instructor']
        item['old_price'] = response.meta['old_price']
        item['new_price'] = response.meta['new_price']
        item['category_name'] = response.meta['category_name']
        item['number_of_students'] = response.xpath('//div[contains(text(), "Học viên")]/text()').re_first(r'(\d+)') or ''
        item['rating'] = response.xpath('//div[contains(@class, "text-[#F77321]")]/text()').get() or ''
        
        tags = response.xpath('//div[@class="flex gap-2 flex-wrap"]/a/text()').getall()
        item['tags'] = ', '.join([tag.strip() for tag in tags if tag.strip()]) or ''
        
        what_you_learn = response.xpath('//div[contains(@class, "grid md:grid-cols-2 gap-x-20 gap-y-5")]//p/text()').getall()
        item['what_you_learn'] = '. '.join([item.strip() for item in what_you_learn if item.strip()]) or ''
        
        course_details = response.xpath('//div[contains(@class, "text-sm font-light mb-4")]/text()').get()
        sections, lectures, duration = '', '', ''
        if course_details:
            details_parts = [part.strip() for part in course_details.split('-')]
            if len(details_parts) == 3:
                sections, lectures, duration = details_parts

        item['sections'] = sections or ''
        item['lectures'] = lectures or ''
        item['duration'] = duration or ''

        yield item