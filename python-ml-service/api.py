from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

from traffic_model import TrafficPredictionModel
from config import Config

logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

model = TrafficPredictionModel()


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'traffic-prediction-service'
    })


@app.route('/api/predictions', methods=['GET'])
def get_all_predictions():
    intersections = model.get_all_intersections()
    predictions = []
    
    for info in intersections:
        prediction = model.predict_congestion(info.get("intersection_id"))
        if prediction:
            predictions.append(prediction)
    
    return jsonify({
        'count': len(predictions),
        'predictions': predictions
    })


@app.route('/api/predictions/<intersection_id>', methods=['GET'])
def get_prediction(intersection_id):
    prediction = model.predict_congestion(intersection_id)
    
    if prediction:
        return jsonify(prediction)
    else:
        return jsonify({
            'error': f'No prediction available for intersection {intersection_id}'
        }), 404


@app.route('/api/intersections', methods=['GET'])
def get_intersections():
    intersections = model.get_all_intersections()
    return jsonify({
        'count': len(intersections),
        'intersections': intersections
    })


@app.route('/api/intersections/<intersection_id>/history', methods=['GET'])
def get_intersection_history(intersection_id):
    history = model.get_prediction_history(intersection_id)
    return jsonify({
        'intersection_id': intersection_id,
        'history_count': len(history),
        'history': history
    })


def create_app():
    return app


if __name__ == '__main__':
    app.run(
        host=Config.FLASK_HOST,
        port=Config.FLASK_PORT,
        debug=Config.FLASK_DEBUG
    )
