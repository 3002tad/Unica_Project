from itemadapter import ItemAdapter
import pymongo
import csv
import os
from scrapy.exceptions import DropItem

class UnicaCrawlerPipeline:
    def process_item(self, item, spider):
        # Giữ lại pipeline cơ bản nếu cần xử lý gì khác
        return item

class MongoDBUnicaPipeline:
    def __init__(self):
        # Kết nối với MongoDB bằng Connection String từ biến môi trường
        econnect = str(os.environ.get('Mongo_HOST', 'localhost'))
        self.client = pymongo.MongoClient(f'mongodb://{econnect}:27017')
        self.db = self.client['unica_db']  # Tên database
        self.collection = self.db['courses']  # Tên collection

    def process_item(self, item, spider):
        # Kiểm tra xem item đã tồn tại trong MongoDB chưa dựa trên 'course_link'
        if self.collection.find_one({'course_link': item['course_link']}):
            raise DropItem(f"Duplicate item found: {item['course_link']}")
        else:
            # Nếu chưa tồn tại, thêm item vào collection
            self.collection.insert_one(dict(item))
            return item

    def close_spider(self, spider):
        # Đóng kết nối MongoDB khi spider kết thúc
        self.client.close()
        
class CSVUnicaPipeline:
    def __init__(self):
        self.file = None
        self.writer = None
        self.file_exists = os.path.isfile('data_crawl.csv')

    def open_spider(self, spider):
        # Mở file CSV để ghi
        self.file = open('data_crawl.csv', 'a', newline='', encoding='utf-8')
        self.writer = csv.writer(self.file, delimiter=',')
        
        # Ghi tiêu đề nếu file không tồn tại
        if not self.file_exists:
            self.writer.writerow([
                'course_link', 'course_name', 'instructor', 'old_price', 'new_price',
                'number_of_students', 'rating', 'sections', 'lectures', 'duration', 'what_you_learn','tags'
            ])

    def process_item(self, item, spider):
        # Ghi dữ liệu vào file CSV
        self.writer.writerow([
            item.get('course_link', ''),
            item.get('course_name', ''),
            item.get('instructor', ''),
            item.get('old_price', ''),
            item.get('new_price', ''),
            item.get('number_of_students', ''),
            item.get('rating', ''),
            item.get('sections', ''),
            item.get('lectures', ''),
            item.get('duration', ''),
            item.get('what_you_learn', ''),
            item.get('tags', '') 
        ])
        return item

    def close_spider(self, spider):
        # Đảm bảo file được đóng đúng cách
        if self.file:
            self.file.close()