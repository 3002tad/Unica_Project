import pandas as pd
import glob

# Đường dẫn chứa các file CSV
csv_files_path = r"D:\Source_Stable\Data_Crawl\*.csv"

# Danh sách các file CSV
csv_files = glob.glob(csv_files_path)

# Đọc và kết hợp tất cả các file CSV
combined_csv = pd.concat([pd.read_csv(f) for f in csv_files], ignore_index=True)

# Xóa các bản ghi trùng lặp dựa trên ba trường: course_link, course_name, instructor
unique_courses = combined_csv.drop_duplicates(subset=['course_link', 'course_name','instructor'])

# Lưu lại file CSV chỉ chứa các khóa học duy nhất
unique_courses.to_csv("unique_courses.csv", index=False)