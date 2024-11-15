import scrapy
from unica_crawler.items import UnicaCrawlerItem

class UnicaSpider(scrapy.Spider):
    name = 'unica_spider'

    # Các URL của category được chỉ định
    start_urls = [
        'https://unica.vn/course/tin-hoc-van-phong',
        'https://unica.vn/course/thiet-ke',
        'https://unica.vn/course/ngoai-ngu',
        'https://unica.vn/course/marketing',
        'https://unica.vn/course/tai-chinh-ke-toan',
        'https://unica.vn/course/lap-trinh-cntt',
        'https://unica.vn/course/suc-khoe-va-lam-dep',
        'https://unica.vn/course/hon-nhan-va-gia-dinh'
    ]
    
    page_limit = 16  # Giới hạn số trang cho mỗi category

    # Tạo từ điển ánh xạ URL với tên category mong muốn
    category_mapping = {
        'tin-hoc-van-phong': 'tin hoc van phong',
        'thiet-ke': 'thiet ke',
        'ngoai-ngu': 'ngoai ngu',
        'marketing': 'marketing',
        'tai-chinh-ke-toan': 'tai chinh ke toan',
        'lap-trinh-cntt': 'cong nghe thong tin',
        'suc-khoe-va-lam-dep': 'suc khoe va lam dep',
        'hon-nhan-va-gia-dinh': 'hon nhan va gia dinh'
    }

    def parse(self, response):
        # Lấy tên category từ URL và ánh xạ với category_mapping để có định dạng đúng
        category_key = response.url.split('/')[-1].split('?')[0].strip()  # Lấy phần không có query string
        category = self.category_mapping.get(category_key, category_key.capitalize())

        # Đảm bảo category là chuỗi và loại bỏ khoảng trắng thừa
        category = category.strip()

        # Lấy danh sách các khóa học trên trang
        courses = response.xpath('//a[contains(@class, "flex mb-6 lg:flex-row")]')

        for course in courses:
            course_name = course.xpath('.//span[@class="font-bold text-base leading-5"]/text()').get()
            instructor = course.xpath('.//div[@class="flex flex-col gap-2 text-sm font-light"]/span[1]/text()').get()
            new_price = course.xpath('.//div[@class="w-20"]/span[1]/text()').get()
            old_price = course.xpath('.//div[@class="w-20"]/span[2]/text()').get()
            course_link = response.urljoin(course.xpath('./@href').get())

            meta_data = {
                'course_name': course_name.strip() if course_name else '',
                'instructor': instructor.strip() if instructor else '',
                'new_price': new_price.strip() if new_price else '',
                'old_price': old_price.strip() if old_price else '',
                'course_link': course_link or '',
                'category': category,  # Sử dụng tên category đã được ánh xạ
            }

            # Gửi request tới từng trang chi tiết khóa học
            yield scrapy.Request(course_link, callback=self.parse_course_details, meta=meta_data)

        # Xử lý phân trang
        current_page = response.meta.get('page_count', 1)
        if current_page < self.page_limit:
            next_page = response.xpath('//li[@class="next"]/a/@href').get()
            if next_page:
                next_page_url = response.urljoin(next_page)
                yield scrapy.Request(
                    next_page_url, 
                    callback=self.parse,
                    meta={'category': category, 'page_count': current_page + 1}
                )

    def parse_course_details(self, response):
        item = UnicaCrawlerItem()
        
        # Lấy thông tin từ meta
        item['course_link'] = response.meta['course_link']
        item['course_name'] = response.meta['course_name']
        item['instructor'] = response.meta['instructor']
        item['old_price'] = response.meta['old_price']
        item['new_price'] = response.meta['new_price']
        item['category'] = response.meta['category']
        
        # Lấy số lượng học viên và đánh giá
        item['number_of_students'] = response.xpath('//div[contains(text(), "Học viên")]/text()').re_first(r'(\d+)') or ''
        item['rating'] = response.xpath('//div[contains(@class, "text-[#F77321]")]/text()').get() or ''
        
        # Lấy tags
        tags = response.xpath('//div[@class="flex gap-2 flex-wrap"]/a/text()').getall()
        item['tags'] = ', '.join([tag.strip() for tag in tags if tag.strip()]) or ''
        
        # Lấy các mục "Bạn sẽ học được"
        what_you_learn = response.xpath('//div[contains(@class, "grid md:grid-cols-2 gap-x-20 gap-y-5")]//p/text()').getall()
        item['what_you_learn'] = '. '.join([item.strip() for item in what_you_learn if item.strip()]) or ''
        
        # Lấy thông tin về số lượng phần, bài giảng và thời lượng
        course_details = response.xpath('//div[contains(@class, "text-sm font-light mb-4")]/text()').get()
        sections, lectures, duration = '', '', ''
        if course_details:
            details_parts = [part.strip() for part in course_details.split('-')]
            if len(details_parts) == 3:
                sections, lectures, duration = details_parts

        item['sections'] = sections or ''
        item['lectures'] = lectures or ''
        item['duration'] = duration or ''

        # Yield item để lưu thông tin ra ngoài
        yield item