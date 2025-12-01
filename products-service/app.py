from flask import Flask, jsonify
from flask_cors import CORS
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
CORS(app)
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Sample Data
products = [
    {"id": 1, "name": "Premium Wireless Headphones", "price": 299.99, "stock": 45, "status": "In Stock"},
    {"id": 2, "name": "Ergonomic Office Chair", "price": 199.50, "stock": 12, "status": "Low Stock"},
    {"id": 3, "name": "Mechanical Keyboard", "price": 149.99, "stock": 0, "status": "Out of Stock"},
    {"id": 4, "name": "4K Monitor", "price": 399.00, "stock": 28, "status": "In Stock"},
    {"id": 5, "name": "USB-C Docking Station", "price": 89.99, "stock": 150, "status": "In Stock"}
]

@app.route('/')
def index():
    return jsonify({"service": "products-service", "message": "Product Catalog Service Operational"})

@app.route('/health')
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/api/products')
def get_products():
    return jsonify(products)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
