# ChaosMonkey for VS Code

ChaosMonkey is a VS Code extension that analyzes your project’s internal structure, visualizes module/service dependencies, simulates failures, and provides actionable recommendations to improve resilience.

This extension is designed for developers who want deep insight into how their codebase behaves under stress, failure, and architectural weaknesses.

---

## 🚀 Features

### 🔍 Project Scanner
- Automatically scans your workspace
- Detects modules, imports, and dependency relationships
- Builds a full dependency graph

### 🕸 Interactive Graph Visualization
- Powered by Cytoscape.js
- Click nodes to inspect services
- Visualize failure propagation
- Side panel shows analysis and results

### ⚡ Chaos Simulation
- Simulate random service failures
- Observe cascading effects
- Identify single points of failure

### 🧠 Architecture Analysis
- Detect cycles
- Identify hotspots
- Find unreachable or overly‑connected modules

### 💡 Recommendations Engine
- Provides improvement suggestions
- Highlights structural risks
- Helps guide refactoring decisions

---

## 📦 Commands

| Command | Description |
|--------|-------------|
| `Chaos: Scan Project` | Scans the workspace and updates the dependency graph |
| `Chaos: Open Graph` | Opens the interactive dependency graph panel |

---

## 🖼 Screenshots
![alt text](<Screenshot 2026-06-07 224850.png>)

---

## 🛠 Requirements

- Python 3.8+
- No manual setup required — backend auto‑starts with the extension

---

## 📁 Folder Structure

extension/
src/
out/
backend/
media/


---

## 🧪 Testing

1. Run the extension using `F5`
2. Use **Chaos: Scan Project**
3. Open the graph view
4. Simulate failures or run analysis

---

## 📝 License

MIT
