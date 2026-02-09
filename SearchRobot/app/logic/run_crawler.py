
import sys
from scrapy.crawler import CrawlerProcess
from logic.spiders.redis_sitemap_spider import RedisSitemapSpider
from logic.settings import scrapy_settings
from logic.db import get_mongo, get_redis
import yaml


def main():
    config_path = sys.argv[1]
    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    _, cfg["_mongo"] = get_mongo(
        mongo_uri=cfg["db"]["mongo_uri"],
        database=cfg["db"]["database"],
        collection=cfg["db"]["collection"],
    )
    cfg["_redis"] = get_redis(cfg["redis"]["redis_url"])
    
    process = CrawlerProcess(scrapy_settings(cfg))
    process.crawl(RedisSitemapSpider, config=cfg)
    process.start()


if __name__ == "__main__":
    main()