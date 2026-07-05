const cyContainer = document.getElementById("cy");

let cy = cytoscape({
  container: cyContainer,
  style: [
    {
      selector: "node",
      style: {
        "background-color": "#4FC3F7",
        label: "data(label)",
        "font-size": 10,
        "text-valign": "center",
        "text-halign": "center",
        color: "#fff"
      }
    },
    {
      selector: "edge",
      style: {
        width: 2,
        "line-color": "#90A4AE",
        "target-arrow-color": "#90A4AE",
        "target-arrow-shape": "triangle"
      }
    },
    {
      selector: ".failed",
      style: {
        "background-color": "#E53935"
      }
    },
    {
      selector: ".degraded",
      style: {
        "background-color": "#FB8C00"
      }
    }
  ],
  layout: { name: "cose" }
});

async function scan() {
  const res = await fetch("http://localhost:8000/scan/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path: WORKSPACE_PATH })
  });
  const data = await res.json();
  renderGraph(data.graph);
}

function renderGraph(graph) {
  cy.elements().remove();

  const nodes = graph.nodes.map((n) => ({
    data: { id: n.id, label: n.label }
  }));

  const edges = graph.edges.map((e) => ({
    data: { id: e.source + "->" + e.target, source: e.source, target: e.target }
  }));

  cy.add(nodes);
  cy.add(edges);
  cy.layout({ name: "cose" }).run();
}

async function simulateRandomFailure() {
  const nodes = cy.nodes();
  if (nodes.length === 0) return;

  const randomNode = nodes[Math.floor(Math.random() * nodes.length)];
  const failedId = randomNode.id();

  const services = nodes.map((n) => n.id());
  const edges = cy.edges().map((e) => ({
    source: e.source().id(),
    target: e.target().id()
  }));

  const res = await fetch("http://localhost:8000/simulate/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      services,
      dependencies: edges.map((e) => [e.source, e.target]),
      failed: [failedId]
    })
  });

  const data = await res.json();
  applySimulation(data);
}

function applySimulation(result) {
  cy.nodes().removeClass("failed").removeClass("degraded");

  result.dynamic_effects.forEach((eff) => {
    const node = cy.getElementById(eff.service);
    if (!node) return;
    if (eff.status === "FAILED") node.addClass("failed");
    if (eff.status === "DEGRADED") node.addClass("degraded");
  });
}

document.getElementById("scanBtn").addEventListener("click", scan);
document.getElementById("simulateBtn").addEventListener("click", simulateRandomFailure);

// initial load
scan();
