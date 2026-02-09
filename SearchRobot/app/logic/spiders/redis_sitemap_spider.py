from datetime import timedelta, datetime
import json
from urllib.parse import urlparse, urlunparse
from lxml import etree
from scrapy import Request
from scrapy_redis.spiders import RedisSpider
from scrapy.utils.request import fingerprint
from logic.items import PageItem
from logic.tasks import enqueue_url
from rq_scheduler import Scheduler


class RedisSitemapSpider(RedisSpider):
    name = "redis_sitemap_spider"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.sitemap_urls = kwargs["config"]["sitemaps"]
        self.mongo = kwargs["config"]["_mongo"]
        self.redis_key = "crawler:queue"
        self.reindex_after = timedelta(
            days=kwargs["config"]["logic"]["reindex_after_days"]
        )
        
        self.recheck_scheduler = None
        
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        spider.recheck_scheduler = Scheduler(connection=spider.server)
        return spider
    
    def _should_enqueue(self, url):
        doc = self.mongo.find_one({"url": url})
        if not doc:
            return True
        last = doc.get("last_crawled")
        if not last or (datetime.now() - last > self.reindex_after):
            return True
        return False
    
    def _enqueue(self, url, ignore_dupefilter=False):
        if not self._should_enqueue(url):
            return
        req = Request(url)
        fp = fingerprint(req)
        if ignore_dupefilter or self.server.sadd("crawler:dupefilter", fp):
            self.server.lpush(self.redis_key, json.dumps({"url": url}))
    
    def _parse_sitemap(self, response):
        tree = etree.fromstring(response.body)
        ns = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        for url in tree.xpath("//sm:loc/text()", namespaces=ns):
            self._enqueue(url, ignore_dupefilter=False)
     
    def start_requests(self):
        for sitemap_url in self.sitemap_urls:
            yield Request(
                sitemap_url,
                callback=self._parse_sitemap,
                dont_filter=True
            )
        yield from super().start_requests()
            
    def parse(self, response):
        url = response.url
        parsed = urlparse(url)
        normalized_url = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip('/'),
            '',
            '',
            '',
        ))
        domain = parsed.netloc.lower()
        html = response.text

        self.recheck_scheduler.enqueue_in(
            time_delta=self.reindex_after,
            func=enqueue_url,
            args=(url, self.reindex_after.days, True),
        )
        
        yield PageItem(
            url=url,
            normalized_url=normalized_url,
            domain=domain,
            html=html,
            last_crawled=datetime.now(),
        )
        