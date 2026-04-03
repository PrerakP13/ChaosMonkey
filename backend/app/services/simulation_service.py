from sqlalchemy.orm import Session

from app.models.simulation import Simulation
from app.models.simulation_result import SimulationResult
from app.services.graph_builder import build_graph


def run_simulation(db: Session, architecture_id: int, failed_service_id: int):
    # Build dependency + reverse graph
    dependency_graph, reverse_graph, services = build_graph(db, architecture_id)

    # BFS failure propagation
    failed = set()
    queue = [failed_service_id]
    failed.add(failed_service_id)

    while queue:
        current = queue.pop(0)
        for dependent in reverse_graph.get(current, []):
            if dependent not in failed:
                failed.add(dependent)
                queue.append(dependent)

    # Determine service states
    all_ids = [s.id for s in services]

    failed_list = list(failed)
    healthy_list = [sid for sid in all_ids if sid not in failed_list]
    degraded_list = []  # Future logic for replicas

    # Save simulation
    simulation = Simulation(
        architecture_id=architecture_id,
        failed_service_id=failed_service_id,
    )
    db.add(simulation)
    db.commit()
    db.refresh(simulation)

    # Save results
    for sid in failed_list:
        db.add(SimulationResult(
            simulation_id=simulation.id,
            service_id=sid,
            status="FAILED"
        ))

    for sid in healthy_list:
        db.add(SimulationResult(
            simulation_id=simulation.id,
            service_id=sid,
            status="HEALTHY"
        ))

    db.commit()
    db.refresh(simulation)

    return simulation