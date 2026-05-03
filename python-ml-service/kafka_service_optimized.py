import json
import logging
import threading
import time
from typing import Callable, Optional, Dict, Any

from kafka import KafkaConsumer, KafkaProducer

from config import Config

logger = logging.getLogger(__name__)


class OptimizedTrafficKafkaConsumer:
    def __init__(self):
        self.consumer: Optional[KafkaConsumer] = None
        self.running: bool = False
        self._lock: threading.Lock = threading.Lock()
        self._initialize_consumer()

    def _initialize_consumer(self) -> None:
        try:
            self.consumer = KafkaConsumer(
                Config.KAFKA_TOPIC_INTERSECTION_TRAFFIC,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=Config.KAFKA_CONSUMER_GROUP_ID,
                auto_offset_reset=Config.KAFKA_AUTO_OFFSET_RESET,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                enable_auto_commit=True,
                max_poll_records=500,
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000
            )
            logger.info(f"Optimized Kafka Consumer initialized. Topic: {Config.KAFKA_TOPIC_INTERSECTION_TRAFFIC}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Consumer: {e}")
            raise

    def consume(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        if not self.consumer:
            logger.error("Consumer not initialized")
            return

        self.running = True
        logger.info("Starting to consume messages (optimized mode)...")
        
        try:
            while self.running:
                try:
                    with self._lock:
                        records = self.consumer.poll(timeout_ms=1000)
                    
                    for topic_partition, messages in records.items():
                        for message in messages:
                            try:
                                data = message.value
                                callback(data)
                            except Exception as e:
                                logger.error(f"Error processing message: {e}")
                                
                except Exception as e:
                    logger.error(f"Error in poll loop: {e}")
                    time.sleep(0.1)
                    
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        finally:
            self.close()

    def stop(self) -> None:
        self.running = False

    def close(self) -> None:
        self.running = False
        if self.consumer:
            try:
                self.consumer.close()
            except Exception as e:
                logger.error(f"Error closing consumer: {e}")
            logger.info("Kafka Consumer closed")


class OptimizedTrafficKafkaProducer:
    def __init__(self):
        self.producer: Optional[KafkaProducer] = None
        self._lock: threading.Lock = threading.Lock()
        self._initialize_producer()

    def _initialize_producer(self) -> None:
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                acks=1,
                retries=3,
                max_in_flight_requests_per_connection=1,
                linger_ms=5,
                batch_size=16384
            )
            logger.info(f"Optimized Kafka Producer initialized. Topic: {Config.KAFKA_TOPIC_TRAFFIC_PREDICTION}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Producer: {e}")
            raise

    def send_prediction(self, prediction: Dict[str, Any]) -> None:
        if not self.producer:
            logger.error("Producer not initialized")
            return

        try:
            with self._lock:
                future = self.producer.send(
                    Config.KAFKA_TOPIC_TRAFFIC_PREDICTION,
                    value=prediction
                )
                future.get(timeout=5)
            
            logger.debug(f"Prediction sent for intersection: {prediction.get('intersection_id')}")
        except Exception as e:
            logger.error(f"Failed to send prediction: {e}")

    def flush(self) -> None:
        if self.producer:
            with self._lock:
                self.producer.flush()

    def close(self) -> None:
        if self.producer:
            try:
                with self._lock:
                    self.producer.flush()
                    self.producer.close()
            except Exception as e:
                logger.error(f"Error closing producer: {e}")
            logger.info("Kafka Producer closed")
