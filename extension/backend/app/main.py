import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ---------------------------------------------------------
# FIX: Ensure backend/ is added to PYTHONPATH BEFORE imports
# ---------------------------------------------------------
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_ROOT not in sys.path:
    sys.path.insert(0, BACKEND_ROOT)

# Now imports work correctly
from app.routers import scan, analyze, simulate, recommend

# ---------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------
app = FastAPI(title="Chaos VSCode Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
print("[Backend] Registering routers...")
app.include_router(scan.router)
print("[Backend] Scan router registered")
app.include_router(analyze.router)
print("[Backend] Analyze router registered")
app.include_router(simulate.router)
print("[Backend] Simulate router registered")
app.include_router(recommend.router)
print("[Backend] Recommend router registered")

@app.get("/")
def root():
    return {"status": "ok", "message": "Chaos backend is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("BACKEND_PORT", "8000"))
    print(f"[Backend] Starting server on port {port}")
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=port,
        reload=False
    )
