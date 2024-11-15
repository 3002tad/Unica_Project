import pymongo
import os
import csv
from scrapy.exceptions import DropItem

class UnicaCrawlerPipeline:
    def process_item(self, item, spider):
        # Giữ lại pipeline cơ bản nếu cần xử lý gì khác
        return item

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
                'course_name', 'instructor', 'old_price', 'new_price', 'number_of_students', 
                'rating', 'sections', 'lectures', 'duration', 'category', 'tags', 'what_you_learn'
            ])

    def process_item(self, item, spider):
        # Ghi dữ liệu vào file CSV
        self.writer.writerow([
            item.get('course_name', ''),
            item.get('instructor', ''),
            item.get('old_price', ''),
            item.get('new_price', ''),
            item.get('number_of_students', ''),
            item.get('rating', ''),
            item.get('sections', ''),
            item.get('lectures', ''),
            item.get('duration', ''),
            item.get('category', ''),
            item.get('tags', ''),
            item.get('what_you_learn', '')
        ])
        return item

    def close_spider(self, spider):
        # Đảm bảo file được đóng đúng cách
        if self.file:
            self.file.close()