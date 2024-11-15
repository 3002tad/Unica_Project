from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import udf, col, regexp_replace, split, trim, round, explode
from pyspark.sql.types import StringType, IntegerType, FloatType
from kafka import KafkaProducer, KafkaConsumer
import json
import time
import re

# Cấu hình Kafka
KAFKA_TOPIC = "unica_courses"
KAFKA_BROKER = "kafka:9092"

# Khởi tạo Spark session
spark = SparkSession.builder \
    .appName("Unica Data Cleaning with Kafka") \
    .getOrCreate()

# Khởi tạo Kafka Producer
producer = KafkaProducer(
    bootstrap_servers=KAFKA_BROKER,
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Đọc dữ liệu từ MongoDB collection
df = spark.read.format("com.mongodb.spark.sql.DefaultSource") \
    .option("uri", "mongodb://mymongodb:27017/unica_db.courses") \
    .load()

# Loại bỏ cột `_id`
df_no_id = df.drop("_id")

# Gửi dữ liệu từ MongoDB vào Kafka
for row in df_no_id.collect():
    producer.send(KAFKA_TOPIC, row.asDict())
producer.flush()

# Đợi một vài giây cho Kafka xử lý dữ liệu
time.sleep(6)

# Khởi tạo Kafka Consumer
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    group_id='unica_data_group',
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    consumer_timeout_ms=6000
)

print("Đã đẩy dữ liệu vào Kafka")

# Lấy dữ liệu từ Kafka và chuyển đổi thành DataFrame
kafka_data = [msg.value for msg in consumer]
if kafka_data:
    df_kafka = spark.createDataFrame(kafka_data)
else:
    print("Không nhận được dữ liệu từ Kafka.")
    df_kafka = spark.createDataFrame([], df_no_id.schema)

# Hàm chuẩn hóa tên giảng viên
def capitalize_special(text):
    if not text:
        return text
    
    # Sử dụng regex để tìm các từ sau các ký tự đặc biệt và viết hoa chữ cái đầu của mỗi từ
    def capitalize_word(word):
        # Viết thường toàn bộ từ trước khi viết hoa chữ cái đầu
        return word.lower().capitalize()

    # Tách thành các từ bởi dấu cách hoặc các ký tự đặc biệt (ngoại trừ dấu cách)
    words = re.split(r'(\W+)', text)
    
    # Áp dụng viết hoa chữ cái đầu cho mỗi từ và giữ lại các ký tự đặc biệt
    capitalized_words = [capitalize_word(word) if word.isalpha() else word for word in words]
    
    # Ghép lại thành chuỗi
    return ''.join(capitalized_words)

# Đăng ký UDF với Spark
capitalize_special_udf = udf(capitalize_special, StringType())

# Kiểm tra schema của DataFrame từ Kafka
df_kafka.printSchema()
print("Bắt đầu làm sạch dữ liệu")

# Bước 1: Làm sạch dữ liệu giảng viên và các cột khác
df_cleaned = df_kafka.withColumn("course_name", col("course_name").cast("string")) \
    .withColumn(
        "instructor",
        trim(col("instructor"))  # Xóa dấu cách thừa ở đầu và cuối
    ).withColumn(
        "instructor",
        regexp_replace(col("instructor"), "\\s+", " ")  # Thay thế nhiều khoảng trắng liên tiếp thành 1 khoảng trắng
    ).withColumn(
        "instructor",
        capitalize_special_udf(col("instructor"))  # Sử dụng UDF để viết hoa đúng cách
    ) \
    .withColumn("old_price", regexp_replace(col("old_price"), "\\.", "").cast(FloatType())) \
    .withColumn("new_price", regexp_replace(col("new_price"), "\\.", "").cast(FloatType())) \
    .withColumn("number_of_students", col("number_of_students").cast(IntegerType())) \
    .withColumn("rating", round(col("rating").cast(FloatType()), 1)) \
    .withColumn("sections", regexp_replace(col("sections"), " phần", "").cast(IntegerType())) \
    .withColumn("lectures", regexp_replace(col("lectures"), " bài giảng", "").cast(IntegerType())) \
    .withColumn("duration", regexp_replace(col("duration"), " giờ| phút", "")) \
    .withColumn("duration", regexp_replace(col("duration"), " ", ":"))

# Loại bỏ các dòng trùng lặp dựa trên course_name và instructor
df_cleaned = df_cleaned.dropDuplicates(["course_name", "instructor"])

# Bước 2: Chuyển đổi duration thành số giờ
df_cleaned = df_cleaned.withColumn("hours", split(col("duration"), ":").getItem(0).cast(FloatType())) \
    .withColumn("minutes", split(col("duration"), ":").getItem(1).cast(FloatType())) \
    .withColumn("total_duration_hours", col("hours") + col("minutes") / 60) \
    .drop("duration", "hours", "minutes")

# Làm tròn giá trị của `total_duration_hours` đến 1 chữ số thập phân
df_cleaned = df_cleaned.withColumn("total_duration_hours", round(col("total_duration_hours"), 1))

# Bước 3: Xử lý giá trị null và cột varchar
df_cleaned = df_cleaned.fillna({
    "number_of_students": 0,
    "rating": 0.0,
    "sections": 0,
    "lectures": 0,
    "what_you_learn": 'Updating Soon',
    "tags": 'Updating Soon'
})

df_cleaned = df_cleaned.withColumn("what_you_learn", col("what_you_learn").cast("string")) \
    .withColumn("tags", col("tags").cast("string"))

# Bước 4: Tách các tag thành từng giá trị riêng biệt (<=16 tags)
df_cleaned = df_cleaned.withColumn("tag_array", split(col("tags"), ",")) \
    .withColumn("limited_tag_array", F.expr("slice(tag_array, 1, 16)"))

# Bước 5: Tạo DataFrame và xử lý tag riêng biệt
tags_split_df = df_cleaned.withColumn("tag", explode(col("limited_tag_array"))) \
    .select(trim(col("tag")).alias("tag_name")).distinct()

# Ghi tags vào bảng course_tag
postgres_url = "jdbc:postgresql://mypostgres:5432/unica_db"
postgres_properties = {
    "user": "postgres",
    "password": "12345",
    "driver": "org.postgresql.Driver"
}

tags_split_df.write.jdbc(
    url=postgres_url,
    table="course_tag",
    mode="append",
    properties=postgres_properties
)

# Đọc lại bảng course_tag để lấy tag_id
tags_with_id_df = spark.read.jdbc(postgres_url, "course_tag", properties=postgres_properties)

# Bước 6: Ánh xạ tags từ tag_name sang tag_id
df_with_tag_ids = df_cleaned.select("course_name", "instructor", "new_price", "old_price", "number_of_students", "rating", "sections", "lectures", "total_duration_hours", "what_you_learn", "category", explode(col("limited_tag_array")).alias("cleaned_tag_name"))

df_tag_id_mapping = df_with_tag_ids.join(
    tags_with_id_df.select("tag_id", "tag_name"),
    trim(col("cleaned_tag_name")) == tags_with_id_df.tag_name,
    "left"
).groupBy("course_name", "instructor", "new_price", "old_price", "number_of_students", "rating", "sections", "lectures", "total_duration_hours", "what_you_learn", "category") \
    .agg(F.collect_list("tag_id").alias("tag_ids"))

# Bước 7: Thêm bảng category
categories_df = df_cleaned.select("category").distinct().withColumnRenamed("category", "category_name")
categories_df.write.jdbc(
    url=postgres_url,
    table="category",
    mode="append",
    properties=postgres_properties
)

# Đọc lại bảng category để lấy category_id
categories_with_id_df = spark.read.jdbc(postgres_url, "category", properties=postgres_properties)

# Bước 8: Ánh xạ category_id
df_with_category_id = df_tag_id_mapping.join(
    categories_with_id_df,
    df_tag_id_mapping["category"] == categories_with_id_df["category_name"],
    "left"
).drop("category_name")

# Thêm instructor table
instructors_df = df_cleaned.select("instructor").distinct().withColumnRenamed("instructor", "instructor_name")
instructors_df.write.jdbc(
    url=postgres_url,
    table="instructor",
    mode="append",
    properties=postgres_properties
)

# Đọc lại bảng instructor để lấy id
instructors_with_id_df = spark.read.jdbc(postgres_url, "instructor", properties=postgres_properties)

# Ánh xạ instructor_id
df_with_instructor_id = df_with_category_id.join(
    instructors_with_id_df,
    df_with_category_id.instructor == instructors_with_id_df.instructor_name,
    "left"
).drop("instructor_name")

# Bước kiểm tra cuối cùng: đảm bảo `rating` đã được làm tròn
df_with_instructor_id = df_with_instructor_id.withColumn("rating", round(col("rating"), 1))

# Bước 9: Tạo courses_df từ df_with_instructor_id
courses_df = df_with_instructor_id.select(
    "course_name", "new_price", "old_price",
    "number_of_students", "rating", "sections", "lectures",
    "total_duration_hours", "what_you_learn", "instructor_id", "category_id"
)

# Ghi các khóa học vào PostgreSQL
courses_df.write.jdbc(
    url=postgres_url,
    table="course",
    mode="append",
    properties=postgres_properties
)

# Đọc lại bảng course và đổi tên id thành course_id
courses_with_id_df = spark.read.jdbc(postgres_url, "course", properties=postgres_properties) \
                             .withColumnRenamed("id", "course_id")

# Bước 10: Tạo bảng ánh xạ course_tag_assignments với course_id
df_tag_assignments = df_with_instructor_id.join(
    courses_with_id_df,
    ["course_name"],
    "inner"
).select("course_id", explode("tag_ids").alias("tag_id")).dropDuplicates()

# Ghi course_tag_assignments vào PostgreSQL
df_tag_assignments.write.jdbc(
    url=postgres_url,
    table="course_tag_assignments",
    mode="append",
    properties=postgres_properties
)

print("Dữ liệu đã được ghi vào PostgreSQL.")