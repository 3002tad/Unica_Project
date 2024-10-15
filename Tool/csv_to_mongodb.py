import pandas as pd
from pymongo import MongoClient

# Đọc file CSV
file_path = 'combined_courses.csv'  # Thay đổi đường dẫn tới file CSV của bạn
df = pd.read_csv(file_path)

# Kết nối tới MongoDB
client = MongoClient('mongodb://mymongodb:27017/')  # Thay đổi URL tới tên container MongoDB
db = client['unica_db']
collection = db['courses']  # Thay đổi tên collection nếu cần

# Chuyển đổi DataFrame thành danh sách các từ điển
data = df.to_dict(orient='records')

# Chèn dữ liệu vào MongoDB
collection.insert_many(data)

print(f"Đã chèn {len(data)} bản ghi vào MongoDB.")