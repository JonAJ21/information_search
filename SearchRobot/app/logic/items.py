from scrapy import Item, Field

class PageItem(Item):
    url = Field()
    normalized_url = Field()
    domain = Field()
    html = Field()
    last_crawled = Field()
    
    title = Field()
    content = Field()
    content_hash = Field()
    terms = Field()
    terms_count = Field()    

    