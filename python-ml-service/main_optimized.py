"""
优化版本的主程序（全局单例模型）

核心特性：
1. 模型在应用启动时就预加载到内存（全局单例）
2. Kafka 消费者和 FastAPI 共享同一个模型实例
3. 完全避免任何请求时的模型加载开销
4. 毫秒级预测响应时间
"""
import logging
import threading
import sys
import time
from typing import Optional

from config import Config
from singleton_model_manager import (
    SingletonModelManager,
    get_global_model,
    preload_global_model,
    is_model_ready
)
from kafka_service_optimized import OptimizedTrafficKafkaConsumer, OptimizedTrafficKafkaProducer

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OptimizedTrafficPredictionService:
    """
    优化版本的交通预测服务
    
    关键改进：
    1. 使用全局单例模型管理器，确保模型只加载一次
    2. 模型在服务启动时就预加载到内存
    3. Kafka 消费者和 API 共享同一个模型实例
    4. 完全避免任何运行时的模型加载开销
    """
    
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
        
        self.consumer: Optional[OptimizedTrafficKafkaConsumer] = None
        self.producer: Optional[OptimizedTrafficKafkaProducer] = None
        self.running: bool = False
        self._consumer_thread: Optional[threading.Thread] = None
        self._batch_update_thread: Optional[threading.Thread] = None

    def _initialize_services(self) -> None:
        """
        初始化服务
        
        关键步骤：
        1. 预加载全局单例模型到内存（这是最重要的一步）
        2. 初始化 Kafka 生产者
        """
        logger.info("=" * 60)
        logger.info("  INITIALIZING OPTIMIZED TRAFFIC PREDICTION SERVICE")
        logger.info("=" * 60)
        logger.info("Step 1: Preloading global singleton model...")
        
        start_time = time.time()
        
        model = preload_global_model()
        
        model_load_time = time.time() - start_time
        
        model_id = SingletonModelManager.get_instance_id()
        
        logger.info(f"Model preloaded successfully in {model_load_time:.3f} seconds")
        logger.info(f"Model instance ID: {model_id}")
        logger.info(f"Model is preloaded: {SingletonModelManager.is_preloaded()}")
        
        logger.info("Step 2: Initializing Kafka producer...")
        
        try:
            self.producer = OptimizedTrafficKafkaProducer()
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            sys.exit(1)
        
        logger.info("=" * 60)
        logger.info("  ALL SERVICES INITIALIZED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Global model instance ID: {model_id}")
        logger.info(f"Model will be used for ALL predictions and Kafka processing")
        logger.info("=" * 60)

    def process_traffic_data(self, data: dict) -> None:
        """
        处理来自 Kafka 的交通数据
        
        关键优化：
        - 使用全局单例模型，无需每次加载
        - 毫秒级处理时间
        - 模型状态（缓存、统计信息）在所有请求间共享
        """
        try:
            if not is_model_ready():
                logger.error("Global model not ready! This should never happen.")
                return
            
            model = get_global_model()
            
            model.add_traffic_data(data)
            
            intersection_id = data.get("intersection_id")
            if intersection_id:
                prediction = model.predict_congestion(intersection_id)
                
                if prediction:
                    if self.producer:
                        self.producer.send_prediction(prediction)
                    
                    if logger.isEnabledFor(logging.DEBUG):
                        model_id = SingletonModelManager.get_instance_id()
                        logger.debug(
                            f"Prediction using global model {model_id} - "
                            f"Intersection: {intersection_id}, "
                            f"Congestion: {prediction['congestion_level']}, "
                            f"Confidence: {prediction['confidence']}"
                        )
        except Exception as e:
            logger.error(f"Error processing traffic data: {e}")

    def _batch_update_worker(self) -> None:
        """
        批量更新线程
        
        定期在后台计算所有路口的预测
        确保重要预测主动发送到 Kafka
        """
        logger.info(f"Batch update thread started (interval: {Config.PREDICTION_BATCH_INTERVAL_SECONDS}s)")
        
        while self.running:
            try:
                time.sleep(Config.PREDICTION_BATCH_INTERVAL_SECONDS)
                
                if not is_model_ready():
                    continue
                
                model = get_global_model()
                
                predictions = model.get_all_predictions()
                
                for prediction in predictions:
                    if prediction.get("is_glowing") and self.producer:
                        self.producer.send_prediction(prediction)
                
            except Exception as e:
                logger.error(f"Error in batch update: {e}")

    def start_kafka_consumer(self) -> None:
        """
        启动 Kafka 消费者
        """
        try:
            self.consumer = OptimizedTrafficKafkaConsumer()
            self.running = True
            self.consumer.consume(self.process_traffic_data)
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self.running = False

    def start(self) -> None:
        """
        启动服务
        
        启动顺序：
        1. 预加载全局单例模型（这是最先执行的）
        2. 初始化 Kafka 生产者
        3. 启动 Kafka 消费者线程
        4. 启动批量更新线程
        5. 启动 FastAPI 服务
        """
        logger.info("=" * 60)
        logger.info("  SMART CITY TRAFFIC PREDICTION SERVICE (OPTIMIZED v2.1)")
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
            
            logger.info(f"Starting FastAPI server on http://{Config.FASTAPI_HOST}:{Config.FASTAPI_PORT}")
            logger.info("Global singleton model is ready for all requests!")
            
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
        """
        停止服务
        """
        logger.info("Stopping Optimized Traffic Prediction Service...")
        self.running = False
        
        if self.consumer:
            self.consumer.stop()
            self.consumer.close()
        
        if self.producer:
            self.producer.close()
        
        model_id = SingletonModelManager.get_instance_id()
        logger.info(f"Global model instance {model_id} will be cleaned up by system")
        
        logger.info("Optimized Traffic Prediction Service stopped.")


def main():
    """
    主函数
    
    关键：创建服务实例时，会预加载全局单例模型
    """
    service = OptimizedTrafficPredictionService()
    service.start()


if __name__ == '__main__':
    main()
