from fastapi import APIRouter

from logic.managers import CrawlerManager, RQSchedulerManager, RQWorkerManager

router = APIRouter(
    tags=["crawler"],
)

@router.post("/start")
async def start_crawler():
    return {"RQSchedulerManager": RQSchedulerManager.start(config_path="/app/config/config.yaml"),
        "RQWorkerManager": RQWorkerManager.start(config_path="/app/config/config.yaml"),
        "CrawlerManager": CrawlerManager.start(config_path="/app/config/config.yaml")}

@router.post("/stop")
async def stop_crawler():
    return {"RQSchedulerManager": RQSchedulerManager.stop(),
        "RQWorkerManager": RQWorkerManager.stop(),
        "CrawlerManager": CrawlerManager.stop()}