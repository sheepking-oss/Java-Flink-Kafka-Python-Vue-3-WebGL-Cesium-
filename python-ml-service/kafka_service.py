import json
import logging
from kafka import KafkaConsumer, KafkaProducer
from typing import Callable, Optional

from config import Config

logger = logging.getLogger(__name__)


class TrafficKafkaConsumer:
    def __init__(self):
        self.consumer = None
        self._initialize_consumer()

    def _initialize_consumer(self) -> None:
        try:
            self.consumer = KafkaConsumer(
                Config.KAFKA_TOPIC_INTERSECTION_TRAFFIC,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=Config.KAFKA_CONSUMER_GROUP_ID,
                auto_offset_reset=Config.KAFKA_AUTO_OFFSET_RESET,
                value_deserializer=lambda x: json.loads(x.decode('utf-8')),
                enable_auto_commit=True
            )
            logger.info(f"Kafka Consumer initialized. Topic: {Config.KAFKA_TOPIC_INTERSECTION_TRAFFIC}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Consumer: {e}")
            raise

    def consume(self, callback: Callable[[dict], None]) -> None:
        if not self.consumer:
            logger.error("Consumer not initialized")
            return

        logger.info("Starting to consume messages...")
        try:
            for message in self.consumer:
                try:
                    data = message.value
                    callback(data)
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except KeyboardInterrupt:
            logger.info("Consumer stopped by user")
        except Exception as e:
            logger.error(f"Error in consumer loop: {e}")
        finally:
            self.close()

    def close(self) -> None:
        if self.consumer:
            self.consumer.close()
            logger.info("Kafka Consumer closed")


class TrafficKafkaProducer:
    def __init__(self):
        self.producer = None
        self._initialize_producer()

    def _initialize_producer(self) -> None:
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            logger.info(f"Kafka Producer initialized. Topic: {Config.KAFKA_TOPIC_TRAFFIC_PREDICTION}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka Producer: {e}")
            raise

    def send_prediction(self, prediction: dict) -> None:
        if not self.producer:
            logger.error("Producer not initialized")
            return

        try:
            future = self.producer.send(
                Config.KAFKA_TOPIC_TRAFFIC_PREDICTION,
                value=prediction
            )
            future.get(timeout=10)
            logger.debug(f"Prediction sent for intersection: {prediction.get('intersection_id')}")
        except Exception as e:
            logger.error(f"Failed to send prediction: {e}")

    def flush(self) -> None:
        if self.producer:
            self.producer.flush()

    def close(self) -> None:
        if self.producer:
            self.producer.flush()
            self.producer.close()
            logger.info("Kafka Producer closed")
