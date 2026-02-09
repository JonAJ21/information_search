import re
import requests
from pymongo import MongoClient
from bs4 import BeautifulSoup
from hashlib import sha256
from scrapy.exceptions import DropItem
from cpp.text_processor_cpp import process_document

class ExtractContentPipeline:
    def _extract_title(self, soup):
        title_tag = soup.find('title')
        if title_tag and title_tag.string:
            return title_tag.string.strip()
        return ''
    
    def _extract_content(self, soup, domain):
        if domain == 'www.sport-express.ru':
            main_content = soup.find(class_='se-material-page__body')
            if not main_content:
                return ''
            return main_content.get_text(separator='\n', strip=True)
        if domain == 'www.championat.com':
            main_content = soup.find(class_='page-main')
            if not main_content:
                return ''
            return main_content.get_text(separator='\n', strip=True)
        if domain == 'www.sovsport.ru':
            main_content = soup.find(id='content-column')
            if not main_content:
                return ''
            prefixes = ['news-by-id_navigation',
                        'news-by-id_header',
                        'content-controller_text-editor']
            pattern = re.compile(rf'^({"|".join(re.escape(p) for p in prefixes)})')
            matching_elements = main_content.find_all(class_=pattern)
            all_text = ""
            for elem in matching_elements:
                all_text += elem.get_text(separator='\n', strip=True) + '\n'
            return all_text
        
        main_content = soup.get_text(separator='\n', strip=True)
        if main_content:
            return main_content
        return ''
        
    def _hash_content(self, content):
        if not isinstance(content, str):
            return ''
        return sha256(content.encode('utf-8')).hexdigest()
    
    def process_item(self, item):
        html = item['html']
        soup = BeautifulSoup(html, 'html.parser')
        
        item['title'] = self._extract_title(soup)
        item['content'] = self._extract_content(soup, item['domain'])
        item['content_hash'] = self._hash_content(item['content'])
        
        return item


class TextProcessorPipeline:
    def process_item(self, item):
        processed_content = process_document(item['content'])
        item['terms'] = processed_content['terms']
        item['terms_count'] = processed_content['stats']['token_count']
        return item


class SaveMongoBooleanIndexPipeline:
    def __init__(self, uri, db, collection, index_api_url):
        self.uri = uri
        self.db = db
        self.collection_name = collection
        self.index_api_url = index_api_url
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            crawler.settings["MONGO_URI"],
            crawler.settings["MONGO_DATABASE"],
            crawler.settings["MONGO_COLLECTION"],
            crawler.settings.get("INDEX_API_URL", "http://localhost:8000"),
        )
        
    def open_spider(self):
        self.client = MongoClient(self.uri)
        self.collection = self.client[self.db][self.collection_name]
        self.collection.create_index("url", unique=True)
        self.collection.create_index("doc_id", unique=True)
        
        self.counter = self.client[self.db]['counter']
        self.counter.update_one(
            {'_id': 'doc_id'},
            {'$setOnInsert': {'seq': 0}},
            upsert=True
        )
    
    def _get_next_doc_id(self):
        counter = self.counter.find_one_and_update(
            {'_id': 'doc_id'},
            {'$inc': {'seq': 1}},
            return_document=True
        )
        if not counter:
            raise DropItem("Counter not found")
        return counter['seq']
        
    def _index_add(self, doc_id: int, terms: list[str]):
        url = f"{self.index_api_url}/document/{doc_id}"
        try:
            resp = requests.post(url, json=terms)
            resp.raise_for_status()
        except Exception as e:
            spider_logger = getattr(self, 'logger', None)
            if spider_logger:
                spider_logger.error(f"Error adding in index (doc_id={doc_id}): {e}")
            else:
                print(f"Error adding in index: {e}")

    def _index_remove(self, doc_id: int, terms: list[str]):
        url = f"{self.index_api_url}/document/{doc_id}"
        try:
            resp = requests.delete(url, json=terms)
            resp.raise_for_status()
        except Exception as e:
            spider_logger = getattr(self, 'logger', None)
            if spider_logger:
                spider_logger.error(f"Error removing from index (doc_id={doc_id}): {e}")
            else:
                print(f"Error removing from index: {e}")
    
    def process_item(self, item):
        url = item["url"]
        new_hash = item["content_hash"]
        new_terms = item["terms"]
        
        existing = self.collection.find_one({"url": url})
        
        if not existing:
            doc_id = self._get_next_doc_id()
            save_dict = {
                "doc_id": doc_id,
                "url": url,
                "normalized_url": item["normalized_url"],
                "domain": item["domain"],
                "title": item["title"],
                "content": item["content"],
                "terms": new_terms,
                "terms_count": item["terms_count"],
                "content_hash": new_hash,
                "last_crawled": item["last_crawled"],
            }
            self.collection.insert_one(save_dict)
            self._index_add(doc_id, new_terms)
        else:
            old_hash = existing.get("content_hash")
            old_terms = existing.get("terms", [])
            doc_id = existing["doc_id"]

            if old_hash == new_hash and old_terms == new_terms:
                pass
            else:
                self._index_remove(doc_id, old_terms)
                update_fields = {
                    "normalized_url": item["normalized_url"],
                    "domain": item["domain"],
                    "title": item["title"],
                    "content": item["content"],
                    "terms": new_terms,
                    "terms_count": item["terms_count"],
                    "content_hash": new_hash,
                    "last_crawled": item["last_crawled"],
                }
                self.collection.update_one({"url": url}, {"$set": update_fields})
                self._index_add(doc_id, new_terms)
        
        return item