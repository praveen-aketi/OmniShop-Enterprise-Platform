from flask import Flask, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
CORS(app)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')


@app.route('/')
def index():
    return jsonify({"service": "products-service", "message": "Product Service Operational"})


@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
