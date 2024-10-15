FROM python:3

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project to the working directory
COPY . .

# Set the default command to run Scrapy spider
CMD ["scrapy", "crawl", "unica_spider"]
