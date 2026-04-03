from app.db.database import Base, engine
from app.routers import architectures, dependencies, simulations, services
from fastapi import FastAPI

# Create tables (temporary — later you will use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Architecture Failure Simulator")


# Register routers
app.include_router(architectures.router)
app.include_router(services.router)
app.include_router(dependencies.router)
app.include_router(simulations.router)


@app.get("/")
def root():
    return {"message": "Chaos Monkey is awake!!!"}