import os
from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    KAFKA_BOOTSTRAP_SERVERS: str = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    KAFKA_TOPIC_INTERSECTION_TRAFFIC: str = os.getenv("KAFKA_TOPIC_INTERSECTION_TRAFFIC", "intersection-traffic-data")
    KAFKA_TOPIC_TRAFFIC_PREDICTION: str = os.getenv("KAFKA_TOPIC_TRAFFIC_PREDICTION", "traffic-prediction-data")
    KAFKA_CONSUMER_GROUP_ID: str = os.getenv("KAFKA_CONSUMER_GROUP_ID", "python-ml-service-group")
    KAFKA_AUTO_OFFSET_RESET: str = os.getenv("KAFKA_AUTO_OFFSET_RESET", "latest")
    
    PREDICTION_WINDOW_MINUTES: int = int(os.getenv("PREDICTION_WINDOW_MINUTES", "15"))
    PREDICTION_CACHE_TTL_SECONDS: int = int(os.getenv("PREDICTION_CACHE_TTL_SECONDS", "5"))
    PREDICTION_BATCH_INTERVAL_SECONDS: int = int(os.getenv("PREDICTION_BATCH_INTERVAL_SECONDS", "2"))
    
    FASTAPI_HOST: str = os.getenv("FASTAPI_HOST", "0.0.0.0")
    FASTAPI_PORT: int = int(os.getenv("FASTAPI_PORT", "5000"))
    FASTAPI_WORKERS: int = int(os.getenv("FASTAPI_WORKERS", "1"))
    
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/traffic_prediction_model.pkl")
    HISTORY_DATA_SIZE: int = int(os.getenv("HISTORY_DATA_SIZE", "60"))
    
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


Config = get_settings()
