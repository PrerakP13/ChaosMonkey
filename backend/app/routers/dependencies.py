from app.db.database import get_db
from app.models.dependency import Dependency
from app.schemas.dependency import DependencyCreate, DependencyRead
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/dependencies", tags=["Dependencies"])


@router.post("", response_model=DependencyRead)
def create_dependency(payload: DependencyCreate, db: Session = Depends(get_db)):
    dependency = Dependency(**payload.model_dump())
    db.add(dependency)
    db.commit()
    db.refresh(dependency)
    return dependency


@router.get("/architecture/{architecture_id}", response_model=list[DependencyRead])
def list_dependencies(architecture_id: int, db: Session = Depends(get_db)):
    return (
        db.query(Dependency)
        .join(Dependency.source_service)
        .filter(Dependency.source_service.has(architecture_id=architecture_id))
        .all()
    )


@router.delete("/{dependency_id}")
def delete_dependency(dependency_id: int, db: Session = Depends(get_db)):
    dependency = db.query(Dependency).filter(Dependency.id == dependency_id).first()
    if not dependency:
        raise HTTPException(status_code=404, detail="Dependency not found")
    db.delete(dependency)
    db.commit()
    return {"message": "Dependency deleted"}