from cpp.boolean_index_cpp import BooleanIndex
from cpp.text_processor_cpp import process_query
from logic import db

index = None

def get_boolean_index():
    global index
    if index is None:
        client, collection = db.mongo_client, db.mongo_collection
        if not client:
            print("MongoBooleanIndex not initialized")
            return None   
        index = MongoBooleanIndex(collection)
    return index


class MongoBooleanIndex:
    def __init__(self, collection):
        self.collection = collection
        self.index = BooleanIndex()
        
        batch_size = 1000
        print("MongoBooleanIndex initializing...")
        total = 0
        cursor = self.collection.find(
            {},
            {"doc_id": 1, "terms": 1},
            batch_size=batch_size
        )
        for doc in cursor:
            doc_id = doc.get("doc_id")
            terms = doc.get("terms", [])
            
            if doc_id is None:
                continue
            
            self.index.add_document(doc_id, terms)
            total += 1
            
            if total % batch_size == 0:
                print(f"  Loaded {total} docs...")
        print("MongoBooleanIndex has been initialized")
    
    def _fetch_urls_by_doc_ids(self, doc_ids, offset=0, limit=100):
        doc_ids = doc_ids[offset:offset+limit]
        
        cursor = self.collection.find(
            {"doc_id": {"$in": doc_ids}},
            {"doc_id": 1, "url": 1}
        )
        res = [{"doc_id": doc["doc_id"], "url": doc["url"]} for doc in cursor]
        print(res)
        return res
        
    def search(self, query, offset=0, limit=100):
        doc_ids = self.index.search(process_query(query)["terms"])
        return self._fetch_urls_by_doc_ids(doc_ids, offset, limit)
    
    def get_document_count(self):
        return self.index.get_document_count()
    
    def get_term_count(self):
        return self.index.get_term_count()
    
    def get_document_terms(self, doc_id):
        return self.index.get_document_terms(doc_id)
    
    def add_document(self, doc_id, terms):
        self.index.add_document(doc_id, terms)
        
    def remove_document(self, doc_id, terms):
        self.index.remove_document(doc_id, terms)
        
    def clear(self):
        self.index.clear()
        
        
        
    
        
        
    