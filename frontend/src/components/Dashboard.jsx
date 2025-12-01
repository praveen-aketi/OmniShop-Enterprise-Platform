import React from 'react';

const StatCard = ({ title, value, change, icon }) => (
    <div className="stat-card">
        <div className="stat-icon">{icon}</div>
        <div className="stat-info">
            <h3>{title}</h3>
            <p className="stat-value">{value}</p>
            <p className={`stat-change ${change >= 0 ? 'positive' : 'negative'}`}>
                {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
            </p>
        </div>
    </div>
);

const Dashboard = ({ orderData, productData }) => {
    return (
        <div className="dashboard-view">
            <div className="stats-grid">
                <StatCard title="Total Revenue" value="$45,231.89" change={20.1} icon="💰" />
                <StatCard title="Active Orders" value="356" change={-5.4} icon="📦" />
                <StatCard title="Total Products" value="1,205" change={12.5} icon="🏷️" />
                <StatCard title="System Status" value="Operational" change={0} icon="✅" />
            </div>

            <div className="content-grid">
                <div className="card service-status">
                    <h3>Service Health</h3>
                    <div className="status-item">
                        <span>Order Service</span>
                        <span className={`status-badge ${orderData ? 'active' : 'inactive'}`}>
                            {orderData ? 'Online' : 'Offline'}
                        </span>
                    </div>
                    <div className="status-item">
                        <span>Product Service</span>
                        <span className={`status-badge ${productData ? 'active' : 'inactive'}`}>
                            {productData ? 'Online' : 'Offline'}
                        </span>
                    </div>
                    <div className="message-box">
                        <p><strong>Order Service Message:</strong> {orderData?.message || 'No data'}</p>
                        <p><strong>Product Service Message:</strong> {productData?.message || 'No data'}</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
