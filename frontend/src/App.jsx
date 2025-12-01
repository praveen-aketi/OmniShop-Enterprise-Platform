import { useState, useEffect } from 'react'
import axios from 'axios'
import Sidebar from './components/Sidebar'
import Header from './components/Header'
import Dashboard from './components/Dashboard'
import ProductList from './components/ProductList'
import OrderList from './components/OrderList'
import './App.css'

function App() {
  const [orderData, setOrderData] = useState(null)
  const [productData, setProductData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')

  useEffect(() => {
    const fetchData = async () => {
      try {
        // We'll try to fetch, but if it fails we'll just show the dashboard without live data
        // or with mock data if needed.
        const [ordersRes, productsRes] = await Promise.allSettled([
          axios.get('http://a4d3a58d9e69b48a88e5542dc3736b7e-1901851160.us-east-1.elb.amazonaws.com'),
          // Placeholder for products service until exposed
          axios.get('http://localhost:8081/')
        ])

        if (ordersRes.status === 'fulfilled') setOrderData(ordersRes.value.data)
        if (productsRes.status === 'fulfilled') setProductData(productsRes.value.data)

      } catch (error) {
        console.error("Error fetching data:", error)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const renderContent = () => {
    switch (activeTab) {
      case 'dashboard':
        return <Dashboard orderData={orderData} productData={productData} />
      case 'products':
        return <ProductList />
      case 'orders':
        return <OrderList />
      case 'settings':
        return <div className="card"><h3>Settings</h3><p>System configuration options will appear here.</p></div>
      default:
        return <Dashboard orderData={orderData} productData={productData} />
    }
  }

  return (
    <div className="app-container">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <div className="main-wrapper">
        <Header title={activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} />
        <main className="main-content-area">
          {loading ? <div className="loader"></div> : renderContent()}
        </main>
      </div>
    </div>
  )
}

export default App
