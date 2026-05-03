import os

class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    KAFKA_TOPIC_INTERSECTION_TRAFFIC = os.getenv('KAFKA_TOPIC_INTERSECTION_TRAFFIC', 'intersection-traffic-data')
    KAFKA_TOPIC_TRAFFIC_PREDICTION = os.getenv('KAFKA_TOPIC_TRAFFIC_PREDICTION', 'traffic-prediction-data')
    KAFKA_CONSUMER_GROUP_ID = os.getenv('KAFKA_CONSUMER_GROUP_ID', 'python-ml-service-group')
    KAFKA_AUTO_OFFSET_RESET = os.getenv('KAFKA_AUTO_OFFSET_RESET', 'latest')
    
    PREDICTION_WINDOW_MINUTES = int(os.getenv('PREDICTION_WINDOW_MINUTES', '15'))
    
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    MODEL_PATH = os.getenv('MODEL_PATH', 'models/traffic_prediction_model.pkl')
    HISTORY_DATA_SIZE = int(os.getenv('HISTORY_DATA_SIZE', '60'))
