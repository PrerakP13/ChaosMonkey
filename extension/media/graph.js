const vscode = acquireVsCodeApi();

let cy = null;
let currentServices = [];
let currentDependencies = [];
let reportStatusTimer = null;

function setReportStatus(message, { loading = false, autoHide = false, timeout = 2500 } = {}) {
    const status = document.getElementById("report-status");
    const recommendBtn = document.getElementById("recommendBtn");

    if (!status) return;

    if (reportStatusTimer) {
        clearTimeout(reportStatusTimer);
        reportStatusTimer = null;
    }

    if (loading) {
        status.classList.add("loading");
        status.style.display = "flex";
        status.innerHTML = `
            <span class="spinner" aria-hidden="true"></span>
            <span>${escapeHtml(message || "Generating report… This may take a few minutes.")}</span>
        `;
        if (recommendBtn) {
            recommendBtn.disabled = true;
            recommendBtn.textContent = "Generating…";
        }
        return;
    }

    status.classList.remove("loading");
    status.style.display = "flex";
    status.textContent = message || "Report ready!";

    if (recommendBtn) {
        recommendBtn.disabled = false;
        recommendBtn.textContent = "Write Report";
    }

    if (autoHide) {
        reportStatusTimer = setTimeout(() => {
            status.style.display = "none";
        }, timeout);
    }
}

// Receive messages from extension
window.addEventListener("message", (event) => {
    const msg = event.data;

    if (msg.type === "reportGenerated") {
        setReportStatus("Report ready!", { autoHide: true });
    }

    if (msg.type === "scanResult") {
        const payload = msg.payload || {};
        const results = payload.results || payload;
        currentServices = results.services || [];
        currentDependencies = results.dependencies || [];
        const graph = payload.graph || results.graph || {};
        window.latestGraph = graph;
        window.latestVulnerabilities = (results.vulnerabilities && results.vulnerabilities.level2 ? results.vulnerabilities.level2.vulnerabilities : []) || [];
        window.latestChains = (results.vulnerabilities && results.vulnerabilities.level5 ? results.vulnerabilities.level5.chains : []) || [];
        window.latestAnalysis = {};
        renderGraph(graph);
        updateAnalysisPanel({
            type: "scan",
            graph,
            vulnerabilities: window.latestVulnerabilities,
            chains: window.latestChains
        });
    }

    if (msg.type === "simulateResult") {
        console.log("[Webview] Received simulateResult:", msg.payload);
        applySimulationEffects(msg.payload);
        updateAnalysisPanel({
            type: "simulate",
            data: msg.payload
        });
    }

    if (msg.type === "analysisResult") {
        window.latestAnalysis = msg.payload;
        updateAnalysisPanel(msg.payload);
    }

    if (msg.type === "reportResult") {
        const panel = document.getElementById("analysis-panel");
        const payload = msg.payload || {};

        if (panel) {
            panel.innerHTML = `
                <h3>Report Generated</h3>
                <p>${escapeHtml(payload.report_path || "Report generated.")}</p>
                <pre>${escapeHtml(payload.report_text || "")}</pre>
            `;
        }

        if (payload.error) {
            setReportStatus(`Report failed: ${payload.error}`, { autoHide: true, timeout: 4000 });
            return;
        }

        setReportStatus("Report ready!", { autoHide: true });
    }
});

// -----------------------------------------------------
// 1. Render Graph (minimal + safe)
// -----------------------------------------------------
function renderGraph(graph) {
    const nodes = graph.nodes
        .map(n => n.data)
        .filter(n => n && n.id && n.label)
        .map(n => ({ data: n }));

    const edges = graph.edges
        .map(e => e.data)
        .filter(e => e && e.id && e.source && e.target)
        .map(e => ({ data: e }));

    const elements = [...nodes, ...edges];

    if (!cy) {
        cy = cytoscape({
            container: document.getElementById("cy"),
            elements,
            style: [
                {
                    selector: "node",
                    style: {
                        'background-color': 'data(color)',
                        'border-width': 3,
                        'border-color': 'data(borderColor)'
                    }
                },
                {
                    selector: "node[label]",
                    style: {
                        'label': 'data(label)',
                        'color': '#fff',
                        'text-outline-color': '#1e1e1e',
                        'text-outline-width': 2,
                        'font-size': 10,
                        'text-wrap': 'wrap',
                        'text-max-width': 80
                    }
                },
                {
                    selector: "edge",
                    style: {
                        "line-color": "data(color)",
                        "target-arrow-color": "data(color)",
                        "target-arrow-shape": "triangle"
                    }
                }
            ],
            layout: { name: "cose" }
        });
        console.log(
    cy.nodes().map(n => ({
        id: n.id(),
        label: n.data("label")
    }))
);

        cy.on("tap", "node", evt => showNodeDetails(evt.target.data()));

    } else {
        cy.elements().remove();
        cy.add(elements);
        cy.layout({ name: "cose" }).run();
    }
}

// -----------------------------------------------------
// 2. Apply Simulation Effects
// -----------------------------------------------------
function applySimulationEffects(result) {
    if (!cy) return;

    // Reset all nodes
    cy.nodes().data("status", "OK");

    // Reset visual styles for nodes and edges to their data defaults
    cy.nodes().forEach(n => {
        n.style({
            'border-color': n.data('borderColor') || '#555'
        });
    });

    cy.edges().forEach(e => {
        e.style({
            'line-color': e.data('color') || '#999',
            'width': 2
        });
    });

    // Apply failures
    (result.effects ?? []).forEach((eff, i) => {
        const node = cy.getElementById(eff.service);
        if (node.empty()) return;

        node.data("status", eff.status);
        node.animate({
            style: { "border-color": eff.status === "FAILED" ? "#d32f2f" : "#f57c00" },
            duration: 300
        }, { queue: true, delay: i * 120 });
    });

    // removed invalid debug log that referenced undefined variables

    // Highlight chains
    (result.chains ?? []).forEach(chain => {
        const color = {
            "TAINT_CHAIN": "#7b1fa2",
            "CHAOS_CHAIN": "#d32f2f"
        }[chain.kind] || "#c2185b";

        chain.chain.slice(0, -1).forEach((src, i) => {
            const edge = cy.getElementById(`${src}_${chain.chain[i + 1]}`);
            if (!edge.empty()) {
                edge.animate({
                    style: { "line-color": color, "width": 5 },
                    duration: 200
                });
            }
        });
    });
}


// -----------------------------------------------------
// 3. Node Details Panel
// -----------------------------------------------------
function showNodeDetails(data) {
    const panel = document.getElementById("analysis-panel");
    if (!panel) return;

    panel.innerHTML = `
        <h2>${data.label}</h2>
        <p><strong>Status:</strong> ${data.status}</p>
        <p><strong>Severity:</strong> ${data.severity}</p>
        <p><strong>Risk Score:</strong> ${data.risk_score}</p>
        <p><strong>Fan-In:</strong> ${data.fan_in}</p>
        <p><strong>Fan-Out:</strong> ${data.fan_out}</p>
        <p><strong>Depth:</strong> ${data.depth}</p>
        <p><strong>Centrality:</strong> ${data.centrality}</p>
        <h3>Vulnerabilities</h3>
        <pre>${escapeHtml(JSON.stringify(data.vulns, null, 2))}</pre>
        <h3>Chains</h3>
        <pre>${escapeHtml(JSON.stringify(data.chains, null, 2))}</pre>
    `;
}

// -----------------------------------------------------
// 4. Analysis Panel
// -----------------------------------------------------
function updateAnalysisPanel(analysis) {
    const panel = document.getElementById("analysis-panel");
    console.log("[Webview] updateAnalysisPanel called with type:", analysis?.type);
    console.log("[Webview] analysis-panel element exists?", panel ? "yes" : "NO");
    
    if (!panel) {
        console.error("[Webview] analysis-panel not found in DOM!");
        return;
    }

    // Simulation results
    if (analysis && analysis.type === "simulate") {
    const data = analysis.data || {};
    const effects = data.effects || [];
    const chains = data.chains || [];
    const failed = data.failed || [];
    const detailed = data.detailed || [];
    const resilience = data.resilience || 0;

    let html = `
        <h3>Simulation Results</h3>
        <p><strong>Resilience Score:</strong> 
            <span style="color: ${resilience > 70 ? '#4caf50' : resilience > 40 ? '#ff9800' : '#d32f2f'}">
                ${resilience}%
            </span>
        </p>
        <p><strong>Failed Services:</strong> ${failed.length}</p>
        <p><strong>Affected Services:</strong> ${effects.length}</p>

        <h4>Effects (${effects.length})</h4>
        ${
            effects.length
                ? `<ul>${effects.map(e =>
                    `<li><strong>${escapeHtml(e.service || '')}</strong>: ${escapeHtml(e.status || 'UNKNOWN')}
                     ${e.reason ? `— ${escapeHtml(e.reason)}` : ''}
                     (depth: ${e.depth}, fanout: ${e.fanout})</li>`
                ).join('')}</ul>`
                : '<p><em>No effects detected.</em></p>'
        }

        <h4>Propagation Chains (${chains.length})</h4>
        ${
            chains.length
                ? `<ul>${chains.map(c =>
                    `<li><strong>${escapeHtml(c.kind || 'chain')}</strong> (score: ${c.score}): 
                     ${escapeHtml((c.chain || []).join(' → '))}</li>`
                ).join('')}</ul>`
                : '<p><em>No chains detected.</em></p>'
        }
    `;

    // ⭐ NEW: Detailed breakdown
    if (detailed.length > 0) {
        html += `<h3>Detailed Breakdown</h3>`;

        detailed.forEach(item => {
            html += `
                <div class="detail-block" style="margin-bottom: 1em; padding: 0.5em; border-left: 3px solid #888;">
                    <h4>${item.service}</h4>
                    <p><strong>Status:</strong> ${item.status}</p>
                    <p><strong>Reason:</strong> ${item.reason}</p>

                    <h5>Architecture</h5>
                    <p>Fan-In: ${item.architecture.fan_in}</p>
                    <p>Fan-Out: ${item.architecture.fan_out}</p>
                    <p>Depth: ${item.architecture.depth}</p>
                    <p>Centrality: ${item.architecture.centrality}</p>
                    <p>Risk Score: ${item.architecture.risk_score}</p>

                    <h5>Runtime</h5>
                    <p>Failure Depth: ${item.runtime.failure_depth}</p>
                    <p>Failure Fanout: ${item.runtime.failure_fanout}</p>

                    <h5>Chains</h5>
                    ${
                        item.chains.length
                            ? `<pre>${escapeHtml(JSON.stringify(item.chains, null, 2))}</pre>`
                            : "<p>No chain involvement.</p>"
                    }
                </div>
            `;
        });
    }

    console.log("[Webview] Setting analysis panel HTML (simulate)");
    console.log("[Webview] HTML length:", html.length, "bytes");
    panel.innerHTML = html;
    console.log("[Webview] Panel HTML set successfully");
    return;
}


    // If this is a scan summary
    if (analysis && analysis.type === "scan") {
        const graph = analysis.graph || {};
        const graphNodes = graph.nodes || [];

        const vulns = (analysis.vulnerabilities || []).length
            ? analysis.vulnerabilities
            : graphNodes.flatMap((n) => {
                const node = n.data ? n.data : n;
                return node.vulns || [];
            });

        const chains = (analysis.chains || []).length
            ? analysis.chains
            : graphNodes.flatMap((n) => {
                const node = n.data ? n.data : n;
                return node.chains || [];
            });

        const vulnBySeverity = vulns.reduce((acc, v) => {
            const sev = v.severity || "UNKNOWN";
            acc[sev] = (acc[sev] || 0) + 1;
            return acc;
        }, {});

        panel.innerHTML = `
            <h3>Scan Summary</h3>
            <p><strong>Vulnerabilities:</strong> ${vulns.length}</p>
            <p>${Object.entries(vulnBySeverity).map(([s,c])=>`<strong>${s}:</strong> ${c}`).join(' • ')}</p>
            <h4>Top Vulnerabilities</h4>
            <ul>${vulns.slice(0,10).map(v=>`<li>${escapeHtml(v.file || v.id || '')} — ${escapeHtml(v.message || v.kind || '')} <em>(${escapeHtml(v.severity || 'UNKNOWN')})</em></li>`).join('')}</ul>
            <h4>Chains</h4>
            ${chains.length ? `<ul>${chains.slice(0,10).map(c=>`<li><strong>${escapeHtml(c.kind || c.score || 'chain')}</strong>: ${escapeHtml((c.chain || c.path || []).join(' → '))}</li>`).join('')}</ul>` : '<p><em>No attack chains found.</em></p>'}
        `;
        return;
    }

    // Default analysis object (from analyze endpoint)
    panel.innerHTML = `
        <h3>Analysis Results</h3>
        <p><strong>Cycles:</strong> ${escapeHtml(JSON.stringify(analysis.cycles || []))}</p>
        <p><strong>Hotspots:</strong> ${escapeHtml(JSON.stringify(analysis.hotspots || []))}</p>
        <p><strong>Orphans:</strong> ${escapeHtml(JSON.stringify(analysis.orphans || []))}</p>
        <p><strong>Leaf Nodes:</strong> ${escapeHtml(JSON.stringify(analysis.leaf_nodes || []))}</p>
        <h4>Deep Static Findings</h4>
        <pre>${escapeHtml(JSON.stringify(analysis.deep_static || analysis, null, 2))}</pre>
    `;
}

function escapeHtml(str) {
    return str
        ? str.replace(/&/g, "&amp;")
             .replace(/</g, "&lt;")
             .replace(/>/g, "&gt;")
        : "";
}

// -----------------------------------------------------
// 5. Buttons
// -----------------------------------------------------
console.log("[Webview] Initializing button handlers...");

setTimeout(() => {
    const scanBtn = document.getElementById("scanBtn");
    const simulateBtn = document.getElementById("simulateBtn");
    const analyzeBtn = document.getElementById("analyzeBtn");
    const recommendBtn = document.getElementById("recommendBtn");
    
    console.log("[Webview] DOM Ready Check: scanBtn=" + (scanBtn ? "✓" : "✗"), "simulateBtn=" + (simulateBtn ? "✓" : "✗"));
    
    if (scanBtn) {
        scanBtn.onclick = () => {
            console.log("[Webview] Scan button clicked");
            vscode.postMessage({
                type: "scan",
                payload: {
                    path: window.projectPath || null
                }
            });
        };
    }
    
    if (simulateBtn) {
        simulateBtn.onclick = () => {
            console.log("[Webview] Simulate button clicked");
            console.log("[Webview] currentServices:", currentServices);
            
            if (!currentServices || currentServices.length === 0) {
                console.error("[Webview] No services available. Run Scan first.");
                alert("No services available. Please run Scan first.");
                return;
            }
            
            // Automatically fail the first service
            const failed = [currentServices[0]];
            console.log("[Webview] Simulating failure for:", failed);
            
            vscode.postMessage({
                type: "simulate",
                payload: {
                    services: currentServices,
                    dependencies: currentDependencies,
                    failed: failed
                }
            });
        };
    }
    
    if (analyzeBtn) {
        analyzeBtn.onclick = () => {
            vscode.postMessage({
                type: "analyze",
                payload: {
                    services: currentServices,
                    dependencies: currentDependencies
                }
            });
        };
    }
    
    if (recommendBtn) {
        recommendBtn.onclick = () => {
            setReportStatus("Generating report… This may take a few minutes.", { loading: true });
            vscode.postMessage({
                type: "generateReport",
                payload: {
                    project_path: window.projectPath || null,
                    services: currentServices,
                    dependencies: currentDependencies,
                    graph: window.latestGraph || {},
                    vulnerabilities: window.latestVulnerabilities || [],
                    chains: window.latestChains || [],
                    analysis: window.latestAnalysis || {}
                }
            });
        };
    }
}, 500);
