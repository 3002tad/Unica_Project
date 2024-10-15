import pandas as pd

df = pd.read_csv('crawl_data.csv')

# Loại bỏ các dòng trùng lặp dựa trên các cột 'course_link', 'course_name', và 'instructor'
df_unique = df.drop_duplicates(subset=['course_link', 'course_name', 'instructor'])

df_unique.to_csv('filtered_data.csv', index=False, header=True)