# OmniShop Dashboard

The **OmniShop Dashboard** is a modern, responsive Single Page Application (SPA) built with React and Vite. It serves as the unified management interface for the OmniShop Enterprise Platform, providing real-time visibility into orders, products, and system health.

## 🚀 Features

-   **Dashboard Overview**: Real-time metrics for revenue, active orders, and system status.
-   **Service Health Monitoring**: Live status checks for `orders-service` and `products-service`.
-   **Product Management**: View inventory levels, prices, and stock status (In Stock, Low Stock, Out of Stock).
-   **Order Management**: Track recent customer orders and their fulfillment status.
-   **Responsive Design**: Premium dark-mode UI optimized for desktop and tablet.

## 🛠️ Tech Stack

-   **Framework**: [React 18](https://reactjs.org/)
-   **Build Tool**: [Vite](https://vitejs.dev/)
-   **Styling**: CSS Modules with a custom dark-mode design system.
-   **HTTP Client**: [Axios](https://axios-http.com/) for API communication.

## ⚡ Getting Started

### Prerequisites

-   Node.js 18+
-   npm 9+

### Installation

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Start the development server:
    ```bash
    npm run dev
    ```

4.  Open your browser at `http://localhost:5173`.

## 🏗️ Build for Production

To create a production-ready build:

```bash
npm run build
```

The artifacts will be generated in the `dist/` directory, ready to be deployed to a static host (S3, Vercel, Netlify) or served via Nginx.

## 🔌 API Integration

The dashboard expects the backend services to be running locally for development:
-   **Orders Service**: `http://localhost:8080`
-   **Products Service**: `http://localhost:8081`

If these services are not running, the dashboard will gracefully handle errors but will not show live data.
