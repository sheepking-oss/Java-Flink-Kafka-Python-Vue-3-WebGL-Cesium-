import logging
import threading
import sys

from config import Config
from traffic_model import TrafficPredictionModel
from kafka_service import TrafficKafkaConsumer, TrafficKafkaProducer
from api import app

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrafficPredictionService:
    def __init__(self):
        self.model = TrafficPredictionModel()
        self.consumer = None
        self.producer = None
        self.running = False

    def process_traffic_data(self, data: dict) -> None:
        try:
            self.model.add_traffic_data(data)
            
            intersection_id = data.get("intersection_id")
            if intersection_id:
                prediction = self.model.predict_congestion(intersection_id)
                
                if prediction:
                    if self.producer:
                        self.producer.send_prediction(prediction)
                    
                    logger.info(
                        f"Prediction for {intersection_id}: "
                        f"congestion={prediction['congestion_level']}, "
                        f"confidence={prediction['confidence']}"
                    )
        except Exception as e:
            logger.error(f"Error processing traffic data: {e}")

    def start_kafka_consumer(self) -> None:
        try:
            self.consumer = TrafficKafkaConsumer()
            self.running = True
            self.consumer.consume(self.process_traffic_data)
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")
            self.running = False

    def start(self) -> None:
        logger.info("=" * 50)
        logger.info("  Smart City Traffic Prediction Service")
        logger.info("=" * 50)
        logger.info(f"Kafka Bootstrap Servers: {Config.KAFKA_BOOTSTRAP_SERVERS}")
        logger.info(f"Prediction Window: {Config.PREDICTION_WINDOW_MINUTES} minutes")
        logger.info(f"Flask API: http://{Config.FLASK_HOST}:{Config.FLASK_PORT}")
        logger.info("=" * 50)

        try:
            self.producer = TrafficKafkaProducer()
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            sys.exit(1)

        consumer_thread = threading.Thread(target=self.start_kafka_consumer, daemon=True)
        consumer_thread.start()

        try:
            app.run(
                host=Config.FLASK_HOST,
                port=Config.FLASK_PORT,
                debug=Config.FLASK_DEBUG,
                use_reloader=False
            )
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        finally:
            self.stop()

    def stop(self) -> None:
        logger.info("Stopping Traffic Prediction Service...")
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        
        if self.producer:
            self.producer.close()
        
        logger.info("Traffic Prediction Service stopped.")


def main():
    service = TrafficPredictionService()
    service.start()


if __name__ == '__main__':
    main()
