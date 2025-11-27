import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'

function App() {
  const [orderData, setOrderData] = useState(null)
  const [productData, setProductData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [ordersRes, productsRes] = await Promise.all([
          axios.get('http://localhost:8080/'),
          axios.get('http://localhost:8081/')
        ])
        setOrderData(ordersRes.data)
        setProductData(productsRes.data)
      } catch (error) {
        console.error("Error fetching data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <div className="dashboard">
      <header className="header">
        <h1>OmniShop Enterprise</h1>
        <div className="status-badge">System Operational</div>
      </header>

      <main className="main-content">
        <div className="card orders-card">
          <h2>Order Management System</h2>
          {loading ? <div className="loader"></div> : (
            <div className="card-content">
              <div className="metric">
                <span className="label">Service Status</span>
                <span className="value active">Active</span>
              </div>
              <div className="metric">
                <span className="label">Service Name</span>
                <span className="value">{orderData?.service || 'N/A'}</span>
              </div>
              <div className="message-box">
                {orderData?.message || 'No data available'}
              </div>
            </div>
          )}
        </div>

        <div className="card products-card">
          <h2>Product Catalog Service</h2>
          {loading ? <div className="loader"></div> : (
            <div className="card-content">
              <div className="metric">
                <span className="label">Service Status</span>
                <span className="value active">Active</span>
              </div>
              <div className="metric">
                <span className="label">Service Name</span>
                <span className="value">{productData?.service || 'N/A'}</span>
              </div>
              <div className="message-box">
                {productData?.message || 'No data available'}
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="footer">
        <p>OmniShop Platform Dashboard v1.0.0</p>
      </footer>
    </div>
  )
}

export default App
