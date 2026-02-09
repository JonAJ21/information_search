import yaml
from contextlib import asynccontextmanager
from fastapi import FastAPI
from logic.db import get_mongo
from api.v1.crawler import router as crawler_router
from api.v1.index import router as index_router
from logic.boolean_index import get_boolean_index


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_path = "/app/config/config.yaml"
    print(config_path)
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    
    print ("Config loaded")
    client, _ = get_mongo(
        mongo_uri=cfg["db"]["mongo_uri"],
        database=cfg["db"]["database"],
        collection=cfg["db"]["collection"],
    )
    index = get_boolean_index()
    yield
    
    client.close()
    
    
def create_app() -> FastAPI:
    app = FastAPI(
        title="MAI IR",
        docs_url="/api/docs",
        description="",
        lifespan=lifespan,
    )

    app.include_router(crawler_router)
    app.include_router(index_router)
    return app