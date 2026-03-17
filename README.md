# Unica Project

This repository contains a Docker-based ETL pipeline for Unica course data.

## Project Structure

- `unica_crawler/`: Scrapy crawler and CSV export pipeline (`data_crawl.csv`).
- `unica_data_testing/`: Loads crawled CSV data into MongoDB.
- `my_spark/`: Spark job that reads from MongoDB, cleans/transforms data, and writes to PostgreSQL.
- `postgresql_to_sqlserver/`: Script to migrate PostgreSQL data to SQL Server.
- `data/`: Sample source data files.
- `report/`: Project report and design assets.
- `docker_setup.sh` / `run_docker_command.cmd`: End-to-end environment bootstrap scripts.

## Prerequisites

- Docker
- Docker images referenced in scripts (`zookeeper`, `confluentinc/cp-kafka`, `mongo`, `postgres`, `3002tad/unica_data_testing`, `3002tad/my_spark`)

## Run the pipeline

### Linux/macOS

```bash
bash docker_setup.sh
```

### Windows (Command Prompt)

```cmd
run_docker_command.cmd
```

These scripts create the Docker network and required services (Zookeeper, Kafka, MongoDB, PostgreSQL), create PostgreSQL tables, then run the data-loading and Spark processing containers.
