from flask import Flask, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
CORS(app)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Sample Data
orders = [
    {"id": "ORD-001", "customer": "Alice Johnson", "total": 450.00, "status": "Completed", "date": "2023-10-25"},
    {"id": "ORD-002", "customer": "Bob Smith", "total": 120.50, "status": "Processing", "date": "2023-10-26"},
    {"id": "ORD-003", "customer": "Charlie Brown", "total": 89.99, "status": "Shipped", "date": "2023-10-26"},
    {"id": "ORD-004", "customer": "Diana Prince", "total": 1200.00, "status": "Pending", "date": "2023-10-27"},
    {"id": "ORD-005", "customer": "Evan Wright", "total": 65.00, "status": "Completed", "date": "2023-10-28"}
]

@app.route('/')
def index():
    return jsonify({"service": "orders-service", "message": "Order Management System Operational"})

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/orders')
def get_orders():
    return jsonify(orders)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
