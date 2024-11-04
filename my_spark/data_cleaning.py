from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import regexp_replace, split, col, expr, explode, trim, round
from pyspark.sql.types import IntegerType, FloatType
from kafka import KafkaProducer, KafkaConsumer
import json
import time

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

# Gửi dữ liệu từ MongoDB vào Kafka
for row in df.collect():
    producer.send(KAFKA_TOPIC, row.asDict())
producer.flush()

# Đợi một vài giây cho Kafka xử lý dữ liệu
time.sleep(5)
print("Đã đẩy dữ liệu vào Kafka")

# Khởi tạo Kafka Consumer với timeout sau 10 giây nếu không có dữ liệu
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BROKER,
    auto_offset_reset='earliest',  # Lấy dữ liệu từ offset đầu tiên
    enable_auto_commit=True,  # Tự động xác nhận offset
    group_id='unica_data_group',  # Nhóm consumer
    value_deserializer=lambda x: json.loads(x.decode('utf-8')),
    consumer_timeout_ms=6000  # Timeout sau 6s nếu không có dữ liệu
)

# Lấy dữ liệu từ Kafka và chuyển đổi thành DataFrame
kafka_data = [msg.value for msg in consumer]
if kafka_data:
    df_kafka = spark.createDataFrame(kafka_data)
else:
    print("Không nhận được dữ liệu từ Kafka.")
    df_kafka = spark.createDataFrame([], df.schema)  # Tạo DataFrame trống với schema ban đầu

# Kiểm tra schema của DataFrame từ Kafka
df_kafka.printSchema()
print("Bắt đầu làm sạch dữ liệu")

# Bước 1: Làm sạch dữ liệu
df_cleaned = df_kafka.withColumn("course_name", col("course_name").cast("string")) \
    .withColumn("instructor", trim(col("instructor")).cast("string")) \
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
    .withColumn("limited_tag_array", expr("slice(tag_array, 1, 16)"))

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
df_with_tag_ids = df_cleaned.select("course_name", "instructor", "new_price", "old_price", "number_of_students", "rating", "sections", "lectures", "total_duration_hours", "what_you_learn", explode(col("limited_tag_array")).alias("cleaned_tag_name"))

df_tag_id_mapping = df_with_tag_ids.join(
    tags_with_id_df.select("tag_id", "tag_name"),
    trim(col("cleaned_tag_name")) == tags_with_id_df.tag_name,
    "left"
).groupBy("course_name", "instructor", "new_price", "old_price", "number_of_students", "rating", "sections", "lectures", "total_duration_hours", "what_you_learn") \
    .agg(F.collect_list("tag_id").alias("tag_ids"))

# Bước 7: Thêm instructor table
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
df_with_instructor_id = df_tag_id_mapping.join(
    instructors_with_id_df,
    df_tag_id_mapping.instructor == instructors_with_id_df.instructor_name,
    "left"
).drop("instructor_name")

# Bước kiểm tra cuối cùng: đảm bảo `rating` đã được làm tròn
df_with_instructor_id = df_with_instructor_id.withColumn("rating", round(col("rating"), 1))

# Bước 8: Tạo courses_df từ df_with_instructor_id
courses_df = df_with_instructor_id.select(
    "course_name", "new_price", "old_price",
    "number_of_students", "rating", "sections", "lectures",
    "total_duration_hours", "what_you_learn", "instructor_id"
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

# Bước 9: Tạo bảng ánh xạ course_tag_assignments với course_id
df_tag_assignments = df_tag_id_mapping.join(
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