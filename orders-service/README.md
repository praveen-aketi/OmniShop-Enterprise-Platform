# Order Management Service (OMS)

Minimal Python Flask service acting as the Order Management System for the OmniShop Enterprise Platform.

Run locally (PowerShell):

```powershell
cd orders-service
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Build Docker image:

```powershell
docker build -t orders-service:local .
docker run -p 8080:8080 orders-service:local
```

Health endpoint: `http://localhost:8080/health`
