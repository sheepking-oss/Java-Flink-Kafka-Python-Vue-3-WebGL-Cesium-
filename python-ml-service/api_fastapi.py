import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import Config
from traffic_model_optimized import OptimizedTrafficPredictionModel, CongestionLevel

logger = logging.getLogger(__name__)

model: Optional[OptimizedTrafficPredictionModel] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    logger.info("Initializing OptimizedTrafficPredictionModel...")
    start_time = time.time()
    
    model = OptimizedTrafficPredictionModel()
    
    init_time = time.time() - start_time
    logger.info(f"OptimizedTrafficPredictionModel initialized in {init_time:.3f} seconds")
    
    yield
    
    logger.info("Shutting down service...")


app = FastAPI(
    title="Traffic Prediction API",
    description="智慧城市交通拥堵预测服务（优化版本）",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_model() -> OptimizedTrafficPredictionModel:
    if model is None:
        raise HTTPException(status_code=503, detail="Model not initialized")
    return model


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    cache_stats: Dict[str, Any]


class PredictionResponse(BaseModel):
    prediction_id: str
    intersection_id: str
    intersection_name: str
    latitude: float
    longitude: float
    prediction_timestamp: str
    prediction_window_minutes: int
    congestion_level: str
    confidence: float
    predicted_bus_count: int
    predicted_average_speed: float
    polygon_coordinates: List[List[float]]
    is_glowing: bool


class AllPredictionsResponse(BaseModel):
    count: int
    predictions: List[PredictionResponse]
    response_time_ms: float


class IntersectionInfoResponse(BaseModel):
    intersection_id: str
    name: str
    latitude: float
    longitude: float
    radius: float
    polygon_coordinates: List[List[float]]


class AllIntersectionsResponse(BaseModel):
    count: int
    intersections: List[IntersectionInfoResponse]


@app.get("/health", response_model=HealthResponse)
async def health_check():
    m = get_model()
    cache_stats = m.get_cache_stats()
    
    return HealthResponse(
        status="healthy",
        service="traffic-prediction-service",
        version="2.0.0",
        cache_stats=cache_stats
    )


@app.get("/api/predictions", response_model=AllPredictionsResponse)
async def get_all_predictions():
    start_time = time.time()
    m = get_model()
    
    predictions = m.get_all_predictions()
    
    response_time_ms = (time.time() - start_time) * 1000
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"get_all_predictions took {response_time_ms:.2f} ms, count: {len(predictions)}")
    
    return AllPredictionsResponse(
        count=len(predictions),
        predictions=[PredictionResponse(**p) for p in predictions],
        response_time_ms=round(response_time_ms, 2)
    )


@app.get("/api/predictions/{intersection_id}", response_model=PredictionResponse)
async def get_prediction(intersection_id: str):
    start_time = time.time()
    m = get_model()
    
    prediction = m.predict_congestion(intersection_id)
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"No prediction available for intersection {intersection_id}"
        )
    
    response_time_ms = (time.time() - start_time) * 1000
    
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"get_prediction for {intersection_id} took {response_time_ms:.2f} ms")
    
    return PredictionResponse(**prediction)


@app.get("/api/intersections", response_model=AllIntersectionsResponse)
async def get_intersections():
    m = get_model()
    intersections = m.get_all_intersections()
    
    return AllIntersectionsResponse(
        count=len(intersections),
        intersections=[IntersectionInfoResponse(**i) for i in intersections]
    )


@app.get("/api/intersections/{intersection_id}/history")
async def get_intersection_history(intersection_id: str):
    m = get_model()
    history = m.get_prediction_history(intersection_id)
    
    return {
        "intersection_id": intersection_id,
        "history_count": len(history),
        "history": history
    }


@app.post("/api/cache/refresh")
async def refresh_cache():
    m = get_model()
    m.refresh_cache()
    return {"status": "success", "message": "Cache refreshed"}


@app.get("/api/cache/stats")
async def get_cache_stats():
    m = get_model()
    return m.get_cache_stats()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
