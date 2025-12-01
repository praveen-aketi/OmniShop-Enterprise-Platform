import React, { useState, useEffect } from 'react';
import axios from 'axios';

const OrderList = () => {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchOrders = async () => {
            try {
                const response = await axios.get('http://localhost:8080/api/orders');
                setOrders(response.data);
                setError(null);
            } catch (err) {
                console.error("Error fetching orders:", err);
                setError("Failed to load orders. Service might be unavailable.");
            } finally {
                setLoading(false);
            }
        };

        fetchOrders();
    }, []);

    if (loading) return <div className="loader"></div>;
    if (error) return <div className="message-box"><p>{error}</p></div>;

    return (
        <div className="data-view">
            <div className="card">
                <h3>Recent Orders</h3>
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Customer</th>
                            <th>Total</th>
                            <th>Status</th>
                            <th>Date</th>
                        </tr>
                    </thead>
                    <tbody>
                        {orders.map(order => (
                            <tr key={order.id}>
                                <td>{order.id}</td>
                                <td>{order.customer}</td>
                                <td>${order.total.toFixed(2)}</td>
                                <td>
                                    <span className={`status-pill ${order.status.toLowerCase()}`}>
                                        {order.status}
                                    </span>
                                </td>
                                <td>{order.date}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default OrderList;
