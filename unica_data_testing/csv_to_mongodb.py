import pandas as pd
from pymongo import MongoClient

# Đọc file CSV
file_path = 'data_crawl.csv' 
df = pd.read_csv(file_path)

# Loại bỏ các dòng trùng lặp dựa trên course_name và instructor
df = df.drop_duplicates(subset=['course_name', 'instructor'])

# Kết nối tới MongoDB
client = MongoClient('mongodb://mymongodb:27017/') 
db = client['unica_db']
collection = db['courses'] 

# Chuyển đổi DataFrame thành danh sách các từ điển
data = df.to_dict(orient='records')

# Chèn dữ liệu vào MongoDB
collection.insert_many(data)

print(f"Đã chèn {len(data)} bản ghi vào MongoDB.")