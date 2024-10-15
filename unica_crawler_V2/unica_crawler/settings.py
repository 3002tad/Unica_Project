# Scrapy settings for unica_crawler project

BOT_NAME = "unica_crawler"

SPIDER_MODULES = ["unica_crawler.spiders"]
NEWSPIDER_MODULE = "unica_crawler.spiders"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Configure maximum concurrent requests performed by Scrapy (default: 16)
CONCURRENT_REQUESTS = 16

# Configure a delay for requests for the same website (default: 0)
DOWNLOAD_DELAY = 0.5

# Disable cookies (enabled by default)
COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
TELNETCONSOLE_ENABLED = False

# Configure item pipelines
ITEM_PIPELINES = {
    "unica_crawler.pipelines.CSVUnicaPipeline": 300,      # Pipeline xuất ra CSV
}

# Configure AutoThrottle to optimize website load
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0

# Setup encoding for exported feeds
FEED_EXPORT_ENCODING = 'utf-8'

# Configure feed exports
FEEDS = {
    'data_crawl.csv': {
        'format': 'csv',
        'overwrite': False,
        'encoding': 'utf-8',
        'fields': [
            'course_link', 'course_name', 'instructor', 'old_price', 'new_price',
            'number_of_students', 'rating', 'sections', 'lectures', 'duration',
            'what_you_learn','tags'  
        ],
        'quote_fields': ['what_you_learn'],
    },
}

# Other settings
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"