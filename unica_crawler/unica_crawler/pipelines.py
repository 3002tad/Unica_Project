import pymongo
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
        # Kiểm tra xem item đã tồn tại trong MongoDB chưa dựa trên 'course_name' và 'instructor'
        if self.collection.find_one({'course_name': item['course_name'], 'instructor': item['instructor']}):
            raise DropItem(f"Duplicate item found: {item['course_name']} by {item['instructor']}")
        else:
            # Xóa trường 'course_link' trước khi lưu vào MongoDB
            if 'course_link' in item:
                del item['course_link']
            
            # Nếu chưa tồn tại, thêm item vào collection
            self.collection.insert_one(dict(item))
            return item

    def close_spider(self, spider):
        # Đóng kết nối MongoDB khi spider kết thúc
        self.client.close()