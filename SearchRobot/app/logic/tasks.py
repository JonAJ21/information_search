from datetime import datetime, timedelta
import json

from scrapy import Request
from scrapy.utils.request import fingerprint
from logic.db import mongo_collection
from logic.db import redis

def should_enqueue(url: str, reindex_after_days: int) -> bool:
    doc = mongo_collection.find_one({"url": url})
    if not doc:
        return True
    last = doc.get("last_crawled")
    if not last or (datetime.now() - last > timedelta(days=reindex_after_days)):
        return True
    return False

def enqueue_url(url: str, reindex_after_days: int, signpore_dupefilter: bool = False):
    if not should_enqueue(url, reindex_after_days):
        return
    req = Request(url)
    fp = fingerprint(req)
    if signpore_dupefilter or redis.sadd("crawler:dupefilter", fp):
        redis.lpush("crawler:queue", json.dumps({"url": url}))