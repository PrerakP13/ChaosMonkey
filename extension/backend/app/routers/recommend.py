from pathlib import Path
from fastapi import APIRouter, Request
from app.services.analyzer import generate_recommendation_report
import json

router = APIRouter(prefix="/recommend", tags=["Recommend"])

@router.post("/")
async def recommend_endpoint(request: Request):
    print("[Backend] /recommend endpoint called")
    payload = await request.json()
    print(f"[Backend] Recommend payload keys: {list(payload.keys())}")
    print(f"[Backend] Payload: {json.dumps(payload, default=str, indent=2)[:500]}...")
    
    project_path = payload.get("project_path")
    analysis = payload.get("analysis", {})
    services = payload.get("services", [])
    dependencies = payload.get("dependencies", [])
    graph = payload.get("graph", {})
    vulnerabilities = payload.get("vulnerabilities", [])
    chains = payload.get("chains", [])
    
    print(f"[Backend] Analysis: {analysis}")
    print(f"[Backend] Services count: {len(services)}")
    print(f"[Backend] Dependencies count: {len(dependencies)}")
    print(f"[Backend] Vulnerabilities count: {len(vulnerabilities)}")
    print(f"[Backend] Chains count: {len(chains)}")

    report_text = generate_recommendation_report(
        analysis=analysis,
        services=services,
        dependencies=dependencies,
        graph=graph,
        vulnerabilities=vulnerabilities,
        chains=chains,
    )
    
    print(f"[Backend] Generated report (first 500 chars): {report_text[:500]}...")

    if project_path:
        report_file = Path(project_path) / "chaos-report.txt"
        report_file.write_text(report_text, encoding="utf-8")
        print(f"[Backend] Report saved to: {report_file}")
        return {"report_path": str(report_file), "report_text": report_text}

    return {"report_text": report_text}
