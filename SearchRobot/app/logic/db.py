
from pymongo import MongoClient
from redis import Redis

mongo_client = None
mongo_collection = None
redis = None

def get_mongo(mongo_uri: str, database: str, collection: str):
    global mongo_client
    global mongo_collection
    if not mongo_client or not mongo_collection:
        mongo_client = MongoClient(mongo_uri)
        mongo_collection = mongo_client[database][collection] 
    return mongo_client, mongo_collection

def get_redis(redis_url):
    global redis
    if redis is None:
        redis = Redis.from_url(redis_url)
    return redis

