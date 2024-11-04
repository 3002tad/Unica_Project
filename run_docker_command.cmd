@echo off
:: Xoá Docker Network cũ
echo Delete old Docker Network...
docker network rm mynetwork && timeout /t 3 /nobreak

:: Tạo Docker Network
echo Create Docker Network...
docker network create mynetwork && timeout /t 3 /nobreak

:: Chạy container Zookeeper cho Kafka
echo Run container Zookeeper...
docker run -d --network mynetwork --name zookeeper -p 2181:2181 zookeeper:3.4 && timeout /t 3 /nobreak

:: Chạy container Kafka trong network mynetwork
echo Run container Kafka...
docker run -d --network mynetwork --name kafka -p 9092:9092 -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092 -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 confluentinc/cp-kafka:latest && timeout /t 5 /nobreak

:: Chạy container MongoDB trong network mynetwork
echo Run container MongoDB...
docker run -d -p 27017:27017 --network mynetwork --name mymongodb mongo && timeout /t 3 /nobreak

:: Chạy container unica-full với biến môi trường Mongo_HOST
echo Run container unica-full...
docker run -e Mongo_HOST=mymongodb --network mynetwork --name unica-full unica_crawler
timeout /t 3 /nobreak

:: Chạy container PostgreSQL với các thông số user, password, và database
echo Run container PostgreSQL...
docker run --name mypostgres --network mynetwork -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=12345 -e POSTGRES_DB=unica_db -p 5432:5432 -d postgres && timeout /t 3 /nobreak

:: Tạo bảng instructor trong database unica_db
echo Create Table instructor...
docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE instructor (instructor_id SERIAL PRIMARY KEY, instructor_name VARCHAR(255) UNIQUE);" && timeout /t 3 /nobreak

:: Tạo bảng course trong database unica_db
echo Create Table course...
docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE course (course_id SERIAL PRIMARY KEY, course_name VARCHAR(255), new_price FLOAT, old_price FLOAT, number_of_students INTEGER, rating NUMERIC(3, 1), sections INTEGER, lectures INTEGER, total_duration_hours NUMERIC(3, 1), what_you_learn TEXT, instructor_id INTEGER REFERENCES instructor(instructor_id));" && timeout /t 3 /nobreak

:: Tạo bảng course_tag trong database unica_db
echo Create Table course_tag...
docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE course_tag (tag_id SERIAL PRIMARY KEY, tag_name VARCHAR(255) UNIQUE);" && timeout /t 3 /nobreak

:: Tạo bảng course_tag_assignments trong database unica_db
echo Create Table course_tag_assignments...
docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE course_tag_assignments (course_id INTEGER REFERENCES course(course_id), tag_id INTEGER REFERENCES course_tag(tag_id), PRIMARY KEY (course_id, tag_id));" && timeout /t 3 /nobreak

:: Chạy container Spark với cấu hình Kafka và MongoDB
echo Run container Spark...
docker run -e Mongo_HOST=mymongodb -e KAFKA_BROKER=kafka:9092 --network mynetwork --name spark_container my_spark

:: Giữ cửa sổ CMD mở
pause