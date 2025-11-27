# Product Catalog Service (PCS)

Minimal Python Flask service acting as the Product Catalog Service for the OmniShop Enterprise Platform.

Run locally (PowerShell):

```powershell
cd products-service
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Build Docker image:

```powershell
docker build -t products-service:local .
docker run -p 8081:8081 products-service:local
```

Health endpoint: `http://localhost:8081/health`
