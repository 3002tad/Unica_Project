# Use the Apache Spark base image
FROM apache/spark:latest

# Switch to root user to install additional packages
USER root

# Update package list and install Python3-pip for package management
RUN apt-get update && apt-get install -y python3-pip

# Install Python packages for Spark, Kafka, and MongoDB
RUN pip install pandas openpyxl kafka-python pymongo

# Download MongoDB Spark connector and the MongoDB Java Driver
RUN wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/3.0.1/mongo-spark-connector_2.12-3.0.1.jar -P /opt/spark/jars/ \
    && wget https://repo1.maven.org/maven2/org/mongodb/mongo-java-driver/3.12.10/mongo-java-driver-3.12.10.jar -P /opt/spark/jars/

# Download the PostgreSQL JDBC Driver
RUN wget https://jdbc.postgresql.org/download/postgresql-42.2.18.jar -P /opt/spark/jars/

# Ensure Spark user has write permissions in necessary directories
RUN mkdir -p /spark_data && chown -R spark:spark /spark_data

# Switch back to Spark user
USER spark

# Copy the Python script into the container
COPY data_cleaning.py /spark_data/data_cleaning.py

# Set the entrypoint to run the Spark job with the necessary JARs for MongoDB and PostgreSQL
ENTRYPOINT ["/bin/bash", "-c", "/opt/spark/bin/spark-submit --jars /opt/spark/jars/mongo-spark-connector_2.12-3.0.1.jar,/opt/spark/jars/postgresql-42.2.18.jar /spark_data/data_cleaning.py"]