import sys, os
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware


# Import routers cleanly
from backend.app.routers import scan, analyze, simulate, recommend

app = FastAPI(title="Chaos VSCode Backend")
# Ensure backend/ is on the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(scan.router)
app.include_router(analyze.router)
app.include_router(simulate.router)
app.include_router(recommend.router)

