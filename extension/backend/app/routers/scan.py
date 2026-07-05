from fastapi import APIRouter, Request, HTTPException
from backend.app.services.orchestrator.scan import scan
from backend.app.services.graph_builder import build_graph

router = APIRouter(prefix="/scan", tags=["Scan"])

@router.post("/")
async def scan_endpoint(request: Request):
    payload = await request.json()
    path = payload.get("path")

    if not path:
        raise HTTPException(status_code=400, detail="Missing 'path' in request body")

    services, dependencies, vuln_results = scan(path)
    graph = build_graph(services, dependencies, vuln_results)

    return {
        "services": services,
        "dependencies": dependencies,
        "vulnerabilities": vuln_results,
        "graph": graph
    }
