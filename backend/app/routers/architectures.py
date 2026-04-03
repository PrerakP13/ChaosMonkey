from app.db.database import get_db
from app.models.architecture import Architecture
from app.schemas.architecture import ArchitectureCreate, ArchitectureRead
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter(prefix="/architectures", tags=["Architectures"])


@router.post("", response_model=ArchitectureRead)
def create_architecture(payload: ArchitectureCreate, db: Session = Depends(get_db)):
    architecture = Architecture(name=payload.name)
    db.add(architecture)
    db.commit()
    db.refresh(architecture)
    return architecture


@router.get("/{architecture_id}", response_model=ArchitectureRead)
def get_architecture(architecture_id: int, db: Session = Depends(get_db)):
    architecture = db.query(Architecture).filter(Architecture.id == architecture_id).first()
    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")
    return architecture


@router.get("", response_model=list[ArchitectureRead])
def list_architectures(db: Session = Depends(get_db)):
    return db.query(Architecture).all()


@router.delete("/{architecture_id}")
def delete_architecture(architecture_id: int, db: Session = Depends(get_db)):
    architecture = db.query(Architecture).filter(Architecture.id == architecture_id).first()
    if not architecture:
        raise HTTPException(status_code=404, detail="Architecture not found")
    db.delete(architecture)
    db.commit()
    return {"message": "Architecture deleted"}