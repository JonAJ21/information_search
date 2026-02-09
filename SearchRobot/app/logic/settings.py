
def scrapy_settings(cfg: dict) -> dict:
    return {
        "BOT_NAME": "search_robot",

        "ROBOTSTXT_OBEY": True,
        "DOWNLOAD_DELAY": cfg["logic"]["download_delay"],
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1.0,
        "AUTOTHROTTLE_MAX_DELAY": 10.0,

        "CONCURRENT_REQUESTS": 16,
        "CONCURRENT_REQUESTS_PER_DOMAIN":
            cfg["logic"]["concurrent_requests_per_domain"],
        
        "USER_AGENT": "SearchRobot/1.0",

        "ITEM_PIPELINES": {
            "logic.pipelines.ExtractContentPipeline": 100,
            "logic.pipelines.TextProcessorPipeline": 200,
            "logic.pipelines.SaveMongoBooleanIndexPipeline": 300,
        },

        "MONGO_URI": cfg["db"]["mongo_uri"],
        "MONGO_DATABASE": cfg["db"]["database"],
        "MONGO_COLLECTION": cfg["db"]["collection"],
        
        "REDIS_URL": cfg["redis"]["redis_url"],
        "SCHEDULER": "scrapy_redis.scheduler.Scheduler",
        "DUPEFILTER_CLASS": "scrapy_redis.dupefilter.RFPDupeFilter",
        "SCHEDULER_PERSIST": True,
        "REDIS_DUPEFILTER_KEY": "crawler:dupefilter",
        
        
        "LOG_LEVEL": "INFO",
    }
