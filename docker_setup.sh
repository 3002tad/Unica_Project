#!/bin/bash

# Xoá Docker Network cũ
echo "Delete old Docker Network..." && sudo docker network rm mynetwork && sleep 3

# Tạo Docker Network
echo "Create Docker Network..." && sudo docker network create mynetwork && sleep 3

# Chạy container Zookeeper cho Kafka
echo "Run container Zookeeper..." && sudo docker run -d --network mynetwork --name zookeeper -p 2181:2181 zookeeper:3.4 && sleep 3

# Chạy container Kafka trong network mynetwork
echo "Run container Kafka..." && sudo docker run -d --network mynetwork --name kafka -p 9092:9092 -e KAFKA_ZOOKEEPER_CONNECT=zookeeper:2181 -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://kafka:9092 -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 confluentinc/cp-kafka:latest && sleep 3

# Chạy container MongoDB trong network mynetwork
echo "Run container MongoDB..." && sudo docker run -d -p 27017:27017 --network mynetwork --name mymongodb mongo:4.4 && sleep 3

# Chạy container unica-full với biến môi trường Mongo_HOST
echo "Run container unica-full..." && sudo docker run -e Mongo_HOST=mymongodb --network mynetwork --name unica-full 3002tad/unica_data_testing && sleep 3

# Chạy container PostgreSQL với các thông số user, password, và database
echo "Run container PostgreSQL..." && sudo docker run --name mypostgres --network mynetwork -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=12345 -e POSTGRES_DB=unica_db -p 5432:5432 -d postgres && sleep 6

# Tạo bảng instructor trong database unica_db
echo "Create Table instructor..." && sudo docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE instructor (instructor_id SERIAL PRIMARY KEY, instructor_name VARCHAR(100) NOT NULL);" && sleep 9

# Tạo bảng category trong database unica_db
echo "Create Table category..." && sudo docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE category (category_id SERIAL PRIMARY KEY, category_name VARCHAR(50) NOT NULL);" && sleep 9

# Tạo bảng course trong database unica_db
echo "Create Table course..." && sudo docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE course (course_id SERIAL PRIMARY KEY, category_id INTEGER REFERENCES category(category_id), instructor_id INTEGER REFERENCES instructor(instructor_id), course_name VARCHAR(100) NOT NULL, old_price FLOAT, new_price FLOAT, number_of_students INTEGER, rating NUMERIC(2,1), total_duration_hours NUMERIC(3,1), sections INTEGER, lectures INTEGER, what_you_learn VARCHAR(3000));" && sleep 9

# Tạo bảng course_tag trong database unica_db
echo "Create Table course_tag..." && sudo docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE course_tag (tag_id SERIAL PRIMARY KEY, tag_name VARCHAR(50) NOT NULL);" && sleep 9

# Tạo bảng course_tag_assignments trong database unica_db
echo "Create Table course_tag_assignments..." && sudo docker exec -it mypostgres psql -U postgres -d unica_db -c "CREATE TABLE course_tag_assignments (course_id INTEGER REFERENCES course(course_id), tag_id INTEGER REFERENCES course_tag(tag_id), PRIMARY KEY (course_id, tag_id));" && sleep 9

# Chạy container Spark với cấu hình Kafka và MongoDB
echo "Run container Spark..." && sudo docker run -e Mongo_HOST=mymongodb -e KAFKA_BROKER=kafka:9092 --network mynetwork --name spark_container 3002tad/my_spark && sleep 3

# Hoàn thành
echo "Setup completed."
