import json
import uuid
import threading
import time
import logging
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
from cachetools import TTLCache, cached

from config import Config

logger = logging.getLogger(__name__)


class CongestionLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


@dataclass
class IntersectionStats:
    intersection_id: str
    bus_counts: deque = field(default_factory=lambda: deque(maxlen=30))
    speeds: deque = field(default_factory=lambda: deque(maxlen=30))
    avg_bus_count: float = 0.0
    avg_speed: float = 0.0
    std_speed: float = 0.0
    trend: str = "stable"
    last_update_time: float = 0.0


@dataclass
class CachedPrediction:
    prediction: dict
    cache_time: float
    ttl_seconds: int


class OptimizedTrafficPredictionModel:
    _instance: Optional['OptimizedTrafficPredictionModel'] = None
    _lock: threading.Lock = threading.Lock()
    _initialized: bool = False

    def __new__(cls) -> 'OptimizedTrafficPredictionModel':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        
        with self._lock:
            if self._initialized:
                return
            
            self._initialized = True
            
            self.history_data: Dict[str, deque] = defaultdict(
                lambda: deque(maxlen=Config.HISTORY_DATA_SIZE)
            )
            self.intersection_stats: Dict[str, IntersectionStats] = {}
            self.intersection_info: Dict[str, dict] = {}
            
            self._prediction_cache: TTLCache = TTLCache(
                maxsize=1000,
                ttl=Config.PREDICTION_CACHE_TTL_SECONDS
            )
            
            self._stats_lock: threading.Lock = threading.Lock()
            self._cache_lock: threading.Lock = threading.Lock()
            
            self._executor: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=4)
            
            self._initialize_intersections()
            
            logger.info("OptimizedTrafficPredictionModel initialized as singleton")
            logger.info(f"Prediction cache TTL: {Config.PREDICTION_CACHE_TTL_SECONDS} seconds")

    def _initialize_intersections(self) -> None:
        self.intersection_info = {
            "INT-001": {
                "name": "天安门东",
                "latitude": 39.9060,
                "longitude": 116.4090,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9060, 116.4090, 150)
            },
            "INT-002": {
                "name": "天安门西",
                "latitude": 39.9060,
                "longitude": 116.4020,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9060, 116.4020, 150)
            },
            "INT-003": {
                "name": "王府井",
                "latitude": 39.9100,
                "longitude": 116.4110,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9100, 116.4110, 150)
            },
            "INT-004": {
                "name": "前门",
                "latitude": 39.8980,
                "longitude": 116.4050,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.8980, 116.4050, 150)
            },
            "INT-005": {
                "name": "建国门",
                "latitude": 39.9080,
                "longitude": 116.4350,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9080, 116.4350, 150)
            },
            "INT-006": {
                "name": "复兴门",
                "latitude": 39.9080,
                "longitude": 116.3620,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9080, 116.3620, 150)
            },
            "INT-007": {
                "name": "西单",
                "latitude": 39.9120,
                "longitude": 116.3710,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9120, 116.3710, 150)
            },
            "INT-008": {
                "name": "东单",
                "latitude": 39.9120,
                "longitude": 116.4210,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9120, 116.4210, 150)
            },
            "INT-009": {
                "name": "朝阳门",
                "latitude": 39.9230,
                "longitude": 116.4320,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9230, 116.4320, 150)
            },
            "INT-010": {
                "name": "阜成门",
                "latitude": 39.9230,
                "longitude": 116.3560,
                "radius": 150,
                "polygon_coordinates": self._generate_polygon(39.9230, 116.3560, 150)
            }
        }
        
        for intersection_id in self.intersection_info:
            self.intersection_stats[intersection_id] = IntersectionStats(
                intersection_id=intersection_id
            )

    def _generate_polygon(self, latitude: float, longitude: float, radius: float) -> List[List[float]]:
        polygon = []
        sides = 8
        lat_per_meter = 1.0 / 111000.0
        lng_per_meter = 1.0 / (111000.0 * np.cos(np.radians(latitude)))

        for i in range(sides):
            angle = 2 * np.pi * i / sides
            d_lat = radius * lat_per_meter * np.cos(angle)
            d_lng = radius * lng_per_meter * np.sin(angle)
            polygon.append([longitude + d_lng, latitude + d_lat])

        if polygon:
            polygon.append(polygon[0])
        return polygon

    def add_traffic_data(self, data: dict) -> None:
        intersection_id = data.get("intersection_id")
        if not intersection_id:
            return

        with self._stats_lock:
            bus_count = data.get("bus_count", 0)
            average_speed = data.get("average_speed", 0.0)
            timestamp = data.get("timestamp")

            self.history_data[intersection_id].append({
                "timestamp": timestamp,
                "bus_count": bus_count,
                "average_speed": average_speed
            })

            stats = self.intersection_stats.get(intersection_id)
            if stats:
                stats.bus_counts.append(bus_count)
                stats.speeds.append(average_speed)
                stats.avg_bus_count = np.mean(stats.bus_counts) if stats.bus_counts else 0.0
                stats.avg_speed = np.mean(stats.speeds) if stats.speeds else 0.0
                stats.std_speed = np.std(stats.speeds) if len(stats.speeds) > 1 else 0.0
                stats.trend = self._calculate_trend(stats.bus_counts)
                stats.last_update_time = time.time()

            with self._cache_lock:
                if intersection_id in self._prediction_cache:
                    del self._prediction_cache[intersection_id]

    def _calculate_trend(self, bus_counts: deque) -> str:
        if len(bus_counts) < 10:
            return "stable"

        recent = list(bus_counts)[-5:]
        earlier = list(bus_counts)[-10:-5]
        
        recent_mean = np.mean(recent)
        earlier_mean = np.mean(earlier)

        if recent_mean > earlier_mean * 1.2:
            return "increasing"
        elif recent_mean < earlier_mean * 0.8:
            return "decreasing"
        else:
            return "stable"

    def predict_congestion(self, intersection_id: str) -> Optional[dict]:
        with self._cache_lock:
            if intersection_id in self._prediction_cache:
                return self._prediction_cache[intersection_id]

        with self._stats_lock:
            stats = self.intersection_stats.get(intersection_id)
            if not stats:
                info = self.intersection_info.get(intersection_id)
                if not info:
                    return None
                return self._generate_default_prediction(intersection_id, info)

            info = self.intersection_info.get(intersection_id)
            if not info:
                return None

            if len(stats.bus_counts) < 5:
                return self._generate_default_prediction(intersection_id, info)

            predicted_bus_count = self._predict_future_bus_count_fast(stats)
            predicted_speed = self._predict_future_speed_fast(stats)

            congestion_level, confidence = self._calculate_congestion_level_fast(
                predicted_bus_count, predicted_speed, stats.trend
            )

            is_glowing = congestion_level in [CongestionLevel.HIGH, CongestionLevel.SEVERE]

            prediction = {
                "prediction_id": str(uuid.uuid4()),
                "intersection_id": intersection_id,
                "intersection_name": info.get("name"),
                "latitude": info.get("latitude"),
                "longitude": info.get("longitude"),
                "prediction_timestamp": datetime.utcnow().isoformat() + "Z",
                "prediction_window_minutes": Config.PREDICTION_WINDOW_MINUTES,
                "congestion_level": congestion_level.value,
                "confidence": confidence,
                "predicted_bus_count": int(predicted_bus_count),
                "predicted_average_speed": round(predicted_speed, 2),
                "polygon_coordinates": info.get("polygon_coordinates"),
                "is_glowing": is_glowing
            }

            with self._cache_lock:
                self._prediction_cache[intersection_id] = prediction

            return prediction

    def _generate_default_prediction(self, intersection_id: str, info: dict) -> dict:
        return {
            "prediction_id": str(uuid.uuid4()),
            "intersection_id": intersection_id,
            "intersection_name": info.get("name"),
            "latitude": info.get("latitude"),
            "longitude": info.get("longitude"),
            "prediction_timestamp": datetime.utcnow().isoformat() + "Z",
            "prediction_window_minutes": Config.PREDICTION_WINDOW_MINUTES,
            "congestion_level": CongestionLevel.LOW.value,
            "confidence": 0.5,
            "predicted_bus_count": 5,
            "predicted_average_speed": 40.0,
            "polygon_coordinates": info.get("polygon_coordinates"),
            "is_glowing": False
        }

    def _predict_future_bus_count_fast(self, stats: IntersectionStats) -> float:
        base = stats.avg_bus_count

        if stats.trend == "increasing":
            return base * 1.3
        elif stats.trend == "decreasing":
            return base * 0.7
        else:
            return base

    def _predict_future_speed_fast(self, stats: IntersectionStats) -> float:
        base = stats.avg_speed

        if stats.trend == "increasing":
            return max(5, base * 0.7)
        elif stats.trend == "decreasing":
            return min(80, base * 1.2)
        else:
            return base

    def _calculate_congestion_level_fast(
        self, bus_count: float, speed: float, trend: str
    ) -> Tuple[CongestionLevel, float]:
        if speed <= 10:
            congestion = CongestionLevel.SEVERE
            confidence = 0.9
        elif speed <= 20:
            congestion = CongestionLevel.HIGH
            confidence = 0.8
        elif speed <= 35:
            congestion = CongestionLevel.MEDIUM
            confidence = 0.7
        else:
            congestion = CongestionLevel.LOW
            confidence = 0.7

        if trend == "increasing":
            if congestion == CongestionLevel.LOW:
                congestion = CongestionLevel.MEDIUM
            elif congestion == CongestionLevel.MEDIUM:
                congestion = CongestionLevel.HIGH
            elif congestion == CongestionLevel.HIGH:
                congestion = CongestionLevel.SEVERE
            confidence = min(0.95, confidence + 0.1)
        elif trend == "decreasing":
            if congestion == CongestionLevel.SEVERE:
                congestion = CongestionLevel.HIGH
            elif congestion == CongestionLevel.HIGH:
                congestion = CongestionLevel.MEDIUM
            elif congestion == CongestionLevel.MEDIUM:
                congestion = CongestionLevel.LOW
            confidence = min(0.95, confidence + 0.1)

        if bus_count > 15 and congestion != CongestionLevel.SEVERE:
            if congestion == CongestionLevel.LOW:
                congestion = CongestionLevel.MEDIUM
            elif congestion == CongestionLevel.MEDIUM:
                congestion = CongestionLevel.HIGH

        return congestion, round(confidence, 2)

    def get_all_predictions(self) -> List[dict]:
        predictions = []
        intersection_ids = list(self.intersection_info.keys())

        futures = [
            self._executor.submit(self.predict_congestion, intersection_id)
            for intersection_id in intersection_ids
        ]

        for future in as_completed(futures):
            try:
                prediction = future.result()
                if prediction:
                    predictions.append(prediction)
            except Exception as e:
                logger.error(f"Error getting prediction: {e}")

        return predictions

    def get_all_intersections(self) -> List[dict]:
        return list(self.intersection_info.values())

    def get_prediction_history(self, intersection_id: str) -> List[dict]:
        return list(self.history_data.get(intersection_id, []))

    def refresh_cache(self) -> None:
        with self._cache_lock:
            self._prediction_cache.clear()
        logger.info("Prediction cache refreshed")

    def get_cache_stats(self) -> dict:
        with self._cache_lock:
            return {
                "cache_size": len(self._prediction_cache),
                "max_size": self._prediction_cache.maxsize,
                "ttl_seconds": Config.PREDICTION_CACHE_TTL_SECONDS
            }
