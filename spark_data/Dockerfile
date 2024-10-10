# Use the latest Spark image
FROM apache/spark:latest

# Switch to root to set permissions and install packages
USER root

# Install pip for Python package installations
RUN apt-get update && apt-get install -y python3-pip

# Install necessary Python packages
RUN pip install pandas openpyxl

# Download MongoDB Spark Connector and MongoDB Java Driver into Spark JARs directory
RUN wget https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/3.0.1/mongo-spark-connector_2.12-3.0.1.jar -P /opt/spark/jars/ \
    && wget https://repo1.maven.org/maven2/org/mongodb/mongo-java-driver/3.12.10/mongo-java-driver-3.12.10.jar -P /opt/spark/jars/

# Download PostgreSQL JDBC Driver
RUN wget https://jdbc.postgresql.org/download/postgresql-42.2.18.jar -P /opt/spark/jars/

# Create the .ivy2 directory and give permissions to spark user
RUN mkdir -p /home/spark/.ivy2/cache && chown -R spark:spark /home/spark/.ivy2

# Ensure the spark user has write permissions on the necessary directories
RUN mkdir -p /spark_data && chown -R spark:spark /spark_data

# Switch back to spark user
USER spark

# Copy the Python script to the container
COPY data_cleaning.py /spark_data/data_cleaning.py

# Set the entrypoint to run the Python script with Spark
ENTRYPOINT ["/bin/bash", "-c", "/opt/spark/bin/spark-submit --packages org.mongodb.spark:mongo-spark-connector_2.12:3.0.1 /spark_data/data_cleaning.py"]