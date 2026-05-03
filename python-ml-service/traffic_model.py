import json
import uuid
from datetime import datetime, timedelta
from collections import defaultdict, deque
from typing import Dict, List, Optional
from enum import Enum
import numpy as np

from config import Config


class CongestionLevel(Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    SEVERE = "SEVERE"


class TrafficPredictionModel:
    def __init__(self):
        self.history_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=Config.HISTORY_DATA_SIZE))
        self.intersection_info: Dict[str, dict] = {}
        self._initialize_intersections()

    def _initialize_intersections(self):
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

        self.history_data[intersection_id].append({
            "timestamp": data.get("timestamp"),
            "bus_count": data.get("bus_count", 0),
            "average_speed": data.get("average_speed", 0.0)
        })

    def predict_congestion(self, intersection_id: str) -> Optional[dict]:
        history = list(self.history_data.get(intersection_id, []))
        if len(history) < 5:
            return None

        info = self.intersection_info.get(intersection_id)
        if not info:
            return None

        recent_data = history[-min(30, len(history)):]

        bus_counts = [d.get("bus_count", 0) for d in recent_data]
        speeds = [d.get("average_speed", 0.0) for d in recent_data]

        avg_bus_count = np.mean(bus_counts)
        avg_speed = np.mean(speeds)
        std_speed = np.std(speeds) if len(speeds) > 1 else 0

        trend = "stable"
        if len(bus_counts) >= 10:
            recent = bus_counts[-5:]
            earlier = bus_counts[-10:-5]
            if np.mean(recent) > np.mean(earlier) * 1.2:
                trend = "increasing"
            elif np.mean(recent) < np.mean(earlier) * 0.8:
                trend = "decreasing"

        predicted_bus_count = self._predict_future_bus_count(bus_counts, trend)
        predicted_speed = self._predict_future_speed(speeds, trend)

        congestion_level, confidence = self._calculate_congestion_level(
            predicted_bus_count, predicted_speed, trend
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

        return prediction

    def _predict_future_bus_count(self, history: List[int], trend: str) -> float:
        if len(history) < 5:
            return np.mean(history) if history else 0

        recent = history[-10:]
        base = np.mean(recent)

        if trend == "increasing":
            return base * 1.3
        elif trend == "decreasing":
            return base * 0.7
        else:
            return base + np.random.normal(0, 2)

    def _predict_future_speed(self, history: List[float], trend: str) -> float:
        if len(history) < 5:
            return np.mean(history) if history else 30.0

        recent = history[-10:]
        base = np.mean(recent)

        if trend == "increasing":
            return max(5, base * 0.7)
        elif trend == "decreasing":
            return min(80, base * 1.2)
        else:
            return base + np.random.normal(0, 3)

    def _calculate_congestion_level(self, bus_count: float, speed: float, trend: str) -> tuple:
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
            congestion = CongestionLevel(congestion.value)
            if congestion == CongestionLevel.LOW:
                congestion = CongestionLevel.MEDIUM
            elif congestion == CongestionLevel.MEDIUM:
                congestion = CongestionLevel.HIGH

        return congestion, round(confidence, 2)

    def get_all_intersections(self) -> List[dict]:
        return list(self.intersection_info.values())

    def get_prediction_history(self, intersection_id: str) -> List[dict]:
        return list(self.history_data.get(intersection_id, []))
