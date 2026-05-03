import logging
import threading
import sys
import time
import os
from typing import Optional

from config import Config
from traffic_model_optimized import OptimizedTrafficPredictionModel
from kafka_service_optimized import OptimizedTrafficKafkaConsumer, OptimizedTrafficKafkaProducer

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizedTrafficPredictionService:
    _instance: Optional['OptimizedTrafficPredictionService'] = None
    _lock: threading.Lock = threading.Lock()

    def __new__(cls) -> 'OptimizedTrafficPredictionService':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
        
        self._initialized = True
        
        self.model: Optional[OptimizedTrafficPredictionModel] = None
        self.consumer: Optional[OptimizedTrafficKafkaConsumer] = None
        self.producer: Optional[OptimizedTrafficKafkaProducer] = None
        self.running: bool = False
        self._consumer_thread: Optional[threading.Thread] = None
        self._batch_update_thread: Optional[threading.Thread] = None

    def _initialize_services(self) -> None:
        logger.info("Initializing optimized services...")
        start_time = time.time()
        
        self.model = OptimizedTrafficPredictionModel()
        
        model_init_time = time.time() - start_time
        logger.info(f"Model initialized in {model_init_time:.3f} seconds")
        
        try:
            self.producer = OptimizedTrafficKafkaProducer()
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            sys.exit(1)

    def process_traffic_data(self, data: dict) -> None:
        try:
            if not self.model:
                return
            
            self.model.add_traffic_data(data)
            
            intersection_id = data.get("intersection_id")
            if intersection_id:
                prediction = self.model.predict_congestion(intersection_id)
                
                if prediction:
                    if self.producer:
                        self.producer.send_prediction(prediction)
                    
                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            f"Prediction for {intersection_id}: "
                            f"congestion={prediction['congestion_level']}, "
                            f"confidence={prediction['confidence']}"
                        )
        except Exception as e:
            logger.error(f"Error processing traffic data: {e}")

    def _batch_update_worker(self) -> None:
        logger.info(f"Batch update thread started (interval: {Config.PREDICTION_BATCH_INTERVAL_SECONDS}s)")
        
        while self.running:
            try:
                time.sleep(Config.PREDICTION_BATCH_INTERVAL_SECONDS)
                
                if not self.model:
                    continue
                
                predictions = self.model.get_all_predictions()
                
                for prediction in predictions:
                    if prediction.get("is_glowing") and self.producer:
                        self.producer.send_prediction(prediction)
                
            except Exception as e:
                logger.error(f"Error in batch update: {e}")

    def start_kafka_consumer(self) -> None:
        try:
            self.consumer = OptimizedTrafficKafkaConsumer()
            self.running = True
            self.consumer.consume(self.process_traffic_data)
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self.running = False

    def start(self) -> None:
        logger.info("=" * 60)
        logger.info("  Smart City Traffic Prediction Service (Optimized v2.0)")
        logger.info("=" * 60)
        logger.info(f"Kafka Bootstrap Servers: {Config.KAFKA_BOOTSTRAP_SERVERS}")
        logger.info(f"Prediction Window: {Config.PREDICTION_WINDOW_MINUTES} minutes")
        logger.info(f"Prediction Cache TTL: {Config.PREDICTION_CACHE_TTL_SECONDS} seconds")
        logger.info(f"FastAPI: http://{Config.FASTAPI_HOST}:{Config.FASTAPI_PORT}")
        logger.info("=" * 60)

        self._initialize_services()

        self._consumer_thread = threading.Thread(
            target=self.start_kafka_consumer,
            daemon=True,
            name="kafka-consumer-thread"
        )
        self._consumer_thread.start()

        self._batch_update_thread = threading.Thread(
            target=self._batch_update_worker,
            daemon=True,
            name="batch-update-thread"
        )
        self._batch_update_thread.start()

        try:
            import uvicorn
            from api_fastapi import app as fastapi_app
            
            uvicorn.run(
                fastapi_app,
                host=Config.FASTAPI_HOST,
                port=Config.FASTAPI_PORT,
                log_level=Config.LOG_LEVEL.lower(),
                access_log=True
            )
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except ImportError:
            logger.error("uvicorn not installed. Please install with: pip install uvicorn")
            sys.exit(1)
        finally:
            self.stop()

    def stop(self) -> None:
        logger.info("Stopping Optimized Traffic Prediction Service...")
        self.running = False
        
        if self.consumer:
            self.consumer.stop()
            self.consumer.close()
        
        if self.producer:
            self.producer.close()
        
        logger.info("Optimized Traffic Prediction Service stopped.")


def main():
    service = OptimizedTrafficPredictionService()
    service.start()


if __name__ == '__main__':
    main()
