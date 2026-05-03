"""
FastAPI 应用（优化版本）

核心优化：
1. 模型在应用启动时就预加载到内存（全局单例）
2. 请求时直接使用已加载的模型，完全避免重复加载
3. 毫秒级响应时间
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from singleton_model_manager import (
    SingletonModelManager,
    get_global_model,
    preload_global_model,
    is_model_ready
)
from traffic_model_optimized import CongestionLevel, OptimizedTrafficPredictionModel
from config import Config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期管理器
    
    在应用启动时预加载模型到内存，确保：
    1. 模型只加载一次
    2. 第一个请求到来时模型已就绪
    3. 完全避免请求时的模型加载开销
    """
    logger.info("=" * 60)
    logger.info("  FASTAPI APPLICATION STARTUP")
    logger.info("=" * 60)
    logger.info("Preloading traffic prediction model (GLOBAL SINGLETON)...")
    
    model = preload_global_model()
    
    model_id = SingletonModelManager.get_instance_id()
    logger.info(f"Model preloaded successfully!")
    logger.info(f"Model instance ID: {model_id}")
    logger.info(f"Model is preloaded: {SingletonModelManager.is_preloaded()}")
    logger.info("=" * 60)
    
    yield
    
    logger.info("=" * 60)
    logger.info("  FASTAPI APPLICATION SHUTDOWN")
    logger.info("=" * 60)


app = FastAPI(
    title="Traffic Prediction API",
    description="智慧城市交通拥堵预测服务（优化版本 - 全局单例模型）",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_model_dependency() -> OptimizedTrafficPredictionModel:
    """
    FastAPI 依赖注入：获取全局单例模型
    
    此函数确保：
    1. 如果模型已预加载，直接返回（毫秒级）
    2. 永远不会在请求时重新加载模型
    """
    if not is_model_ready():
        logger.error("Model not initialized! This should never happen with lifespan preload.")
        raise HTTPException(
            status_code=503,
            detail="Model not initialized. Please check application startup logs."
        )
    return get_global_model()


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    model_initialized: bool
    model_preloaded: bool
    model_instance_id: Optional[int]
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
    model_used: str


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
    """
    健康检查端点
    
    特别说明：
    - 此端点可用于验证模型是否已正确预加载
    - model_instance_id 是模型在内存中的地址，每次重启后会变化
    - 如果 model_preloaded 为 true，说明模型在启动时已预加载
    """
    model_id = SingletonModelManager.get_instance_id()
    model = get_global_model()
    cache_stats = model.get_cache_stats()
    
    return HealthResponse(
        status="healthy",
        service="traffic-prediction-service",
        version="2.1.0",
        model_initialized=SingletonModelManager.is_initialized(),
        model_preloaded=SingletonModelManager.is_preloaded(),
        model_instance_id=model_id,
        cache_stats=cache_stats
    )


@app.get("/api/predictions", response_model=AllPredictionsResponse)
async def get_all_predictions(
    model: OptimizedTrafficPredictionModel = Depends(get_model_dependency)
):
    """
    获取所有路口的预测结果
    
    性能优化：
    - 使用已预加载的全局单例模型（无加载开销）
    - 并行获取多个路口预测
    - 缓存命中时毫秒级响应
    """
    start_time = time.perf_counter()
    
    predictions = model.get_all_predictions()
    
    response_time_ms = (time.perf_counter() - start_time) * 1000
    
    model_id = SingletonModelManager.get_instance_id()
    
    logger.debug(
        f"get_all_predictions - "
        f"Model ID: {model_id}, "
        f"Count: {len(predictions)}, "
        f"Time: {response_time_ms:.2f}ms"
    )
    
    return AllPredictionsResponse(
        count=len(predictions),
        predictions=[PredictionResponse(**p) for p in predictions],
        response_time_ms=round(response_time_ms, 2),
        model_used=f"singleton_{model_id}"
    )


@app.get("/api/predictions/{intersection_id}", response_model=PredictionResponse)
async def get_prediction(
    intersection_id: str,
    model: OptimizedTrafficPredictionModel = Depends(get_model_dependency)
):
    """
    获取单个路口的预测结果
    
    性能优化：
    - 直接使用全局单例模型（毫秒级）
    - TTL 缓存机制避免重复计算
    - 完全避免模型加载开销
    """
    start_time = time.perf_counter()
    
    prediction = model.predict_congestion(intersection_id)
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"No prediction available for intersection {intersection_id}"
        )
    
    response_time_ms = (time.perf_counter() - start_time) * 1000
    
    model_id = SingletonModelManager.get_instance_id()
    
    logger.debug(
        f"get_prediction for {intersection_id} - "
        f"Model ID: {model_id}, "
        f"Time: {response_time_ms:.2f}ms"
    )
    
    return PredictionResponse(**prediction)


@app.get("/api/intersections", response_model=AllIntersectionsResponse)
async def get_intersections(
    model: OptimizedTrafficPredictionModel = Depends(get_model_dependency)
):
    """
    获取所有路口信息
    """
    intersections = model.get_all_intersections()
    
    return AllIntersectionsResponse(
        count=len(intersections),
        intersections=[IntersectionInfoResponse(**i) for i in intersections]
    )


@app.get("/api/intersections/{intersection_id}/history")
async def get_intersection_history(
    intersection_id: str,
    model: OptimizedTrafficPredictionModel = Depends(get_model_dependency)
):
    """
    获取路口的历史数据
    """
    history = model.get_prediction_history(intersection_id)
    
    return {
        "intersection_id": intersection_id,
        "history_count": len(history),
        "history": history
    }


@app.post("/api/cache/refresh")
async def refresh_cache(
    model: OptimizedTrafficPredictionModel = Depends(get_model_dependency)
):
    """
    刷新预测缓存
    """
    model.refresh_cache()
    return {
        "status": "success",
        "message": "Cache refreshed",
        "model_instance_id": SingletonModelManager.get_instance_id()
    }


@app.get("/api/cache/stats")
async def get_cache_stats(
    model: OptimizedTrafficPredictionModel = Depends(get_model_dependency)
):
    """
    获取缓存统计信息
    """
    stats = model.get_cache_stats()
    stats["model_instance_id"] = SingletonModelManager.get_instance_id()
    stats["model_preloaded"] = SingletonModelManager.is_preloaded()
    return stats


@app.get("/api/model/status")
async def get_model_status():
    """
    获取模型状态（用于调试）
    """
    return {
        "model_initialized": SingletonModelManager.is_initialized(),
        "model_preloaded": SingletonModelManager.is_preloaded(),
        "model_instance_id": SingletonModelManager.get_instance_id(),
        "message": "Model is a global singleton, loaded once at startup"
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
