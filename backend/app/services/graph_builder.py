from sqlalchemy.orm import Session

from app.models.dependency import Dependency
from app.models.service import Service


def build_graph(db: Session, architecture_id: int):
    # Fetch all services in this architecture
    services = (
        db.query(Service)
        .filter(Service.architecture_id == architecture_id)
        .all()
    )

    service_ids = [s.id for s in services]

    # Fetch all dependencies
    dependencies = (
        db.query(Dependency)
        .join(Dependency.source_service)
        .filter(Service.architecture_id == architecture_id)
        .all()
    )

    # Build graphs
    dependency_graph = {sid: [] for sid in service_ids}
    reverse_graph = {sid: [] for sid in service_ids}

    for dep in dependencies:
        dependency_graph[dep.source_service_id].append(dep.target_service_id)
        reverse_graph[dep.target_service_id].append(dep.source_service_id)

    return dependency_graph, reverse_graph, services