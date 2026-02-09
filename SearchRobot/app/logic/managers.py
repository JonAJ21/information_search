import subprocess

import yaml

class CrawlerManager:
    process: subprocess.Popen | None = None
    @classmethod
    def start(cls, config_path: str) -> bool:
        if cls.process and cls.process.poll() is None:
            return False

        cls.process = subprocess.Popen(
            ["python", "-m", "logic.run_crawler", config_path]
        )
        return True

    @classmethod
    def stop(cls) -> bool:
        if cls.process is None:
            return False      
        try:
            cls.process.kill()
            cls.process.wait()
            return True
        except Exception:
            return False
        finally:
            cls.process = None

class RQSchedulerManager:
    process: subprocess.Popen | None = None
    @classmethod
    def start(cls, config_path: str, interval: int=60) -> bool:
        if cls.process and cls.process.poll() is None:
            return False
        
        with open(config_path) as f:
            cfg = yaml.safe_load(f)
        
        redis_url = cfg["redis"]["redis_url"]
        if not redis_url:
            return False
        
        cls.process = subprocess.Popen([
            "rqscheduler",
            "--url", redis_url,
            "--interval", str(interval)
        ])
        return True
    
    @classmethod
    def stop(cls) -> bool:
        if cls.process is None:
            return False      
        try:
            cls.process.kill()
            cls.process.wait()
            return True
        except Exception:
            return False
        finally:
            cls.process = None
            
            
class RQWorkerManager:
    process: subprocess.Popen | None = None
    @classmethod
    def start(cls, config_path: str) -> bool:
        if cls.process and cls.process.poll() is None:
            return False

        cls.process = subprocess.Popen(
            ["python", "-m", "logic.run_rqworker", config_path]
        )
        return True
    
    @classmethod
    def stop(cls) -> bool:
        if cls.process is None:
            return False      
        try:
            cls.process.kill()
            cls.process.wait()
            return True
        except Exception:
            return False
        finally:
            cls.process = None
            
            

