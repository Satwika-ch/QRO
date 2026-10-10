# 🚚 QuantumRoute
### Quantum-Enhanced Last-Mile Route Optimisation

**Problem Statement:** VNQFF-08  
**Category:** Quantum Computing · Logistics · Route Optimisation

QuantumRoute is a route optimisation prototype designed to help logistics and e-commerce businesses plan efficient last-mile deliveries. It combines a classical optimisation baseline with a QAOA-based quantum optimisation approach to explore delivery routes while considering delivery demand, vehicle capacity, distance, and cost.

---

## 📌 Table of Contents

- [Overview](#-overview)
- [Problem Statement](#-problem-statement)
- [Objectives](#-objectives)
- [Key Features](#-key-features)
- [How It Works](#-how-it-works)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Prerequisites](#-prerequisites)
- [Installation and Setup](#-installation-and-setup)
- [API Endpoints](#-api-endpoints)
- [Optimisation Approaches](#-optimisation-approaches)
- [Results and Evaluation](#-results-and-evaluation)
- [Limitations](#-limitations)
- [Future Enhancements](#-future-enhancements)
- [Target Users](#-target-users)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🌍 Overview

Last-mile delivery is one of the most challenging and expensive stages of logistics. Delivery providers must determine efficient routes while managing vehicle capacity, customer locations, delivery demand, fuel consumption, and operational costs.

QuantumRoute provides a prototype environment to compare classical route optimisation with a QAOA-based approach. Its dashboard presents optimisation results and route information to help users understand the differences between the approaches.

The project is developed as part of **VNQFF-08: Quantum-Enhanced Last-Mile Route Optimisation**.

## 🎯 Problem Statement

Traditional last-mile delivery planning can become difficult when the number of delivery locations, vehicles, and operational constraints increases. Inefficient routing may lead to:

- Increased travel distance.
- Higher fuel and transportation costs.
- Longer delivery times.
- Inefficient use of vehicle capacity.
- Difficulty comparing alternative routing strategies.

QuantumRoute explores how classical optimisation and quantum optimisation techniques can be used to address these challenges.

## 🎯 Objectives

1. Generate delivery routes from user-provided locations.
2. Consider delivery demand and vehicle capacity.
3. Establish a classical optimisation baseline.
4. Explore a QAOA-based approach to route optimisation.
5. Compare route distance and estimated cost.
6. Display optimisation results through a web dashboard.
7. Investigate the potential of quantum computing for logistics optimisation.

## ✨ Key Features

- **Delivery management:** Add and remove delivery locations.
- **Capacity validation:** Consider delivery demand and vehicle capacity.
- **Classical optimisation:** Generate a baseline route for comparison.
- **QAOA-based optimisation:** Explore a quantum approximate optimisation approach.
- **Route comparison:** Compare classical and quantum-based results.
- **Cost and distance metrics:** Display estimated route distance and cost.
- **Dashboard:** Present optimisation metrics and results.
- **Route visualisation:** Display delivery locations and routes using the available map interface.
- **REST API:** Connect the frontend to the Python backend.
- **Quantum simulation support:** Qiskit and Qiskit Aer are installed in the development environment for quantum circuit and simulator experimentation.

> **Implementation note:** Qiskit integration into the active route optimiser must be verified against the current source code before describing the results as produced by a Qiskit circuit.

## ⚙️ How It Works

1. **Enter delivery details:** Add the depot and delivery locations, including demand.
2. **Validate constraints:** Check the provided delivery information and vehicle capacity.
3. **Run classical optimisation:** Generate a baseline route.
4. **Run the quantum-based approach:** Evaluate the configured QAOA or quantum-inspired optimisation method.
5. **Compare results:** Review distance, estimated cost, and available optimisation metrics.
6. **Visualise the output:** Inspect the results in the dashboard.

### Workflow

`Delivery Input → Constraint Validation → Classical Optimisation → Quantum-Based Optimisation → Comparison → Dashboard`

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Backend and optimisation logic |
| Flask | REST API and backend services |
| HTML | Web page structure |
| CSS | Styling and responsive layout |
| JavaScript | Frontend interactions and API communication |
| Qiskit | Quantum circuit development |
| Qiskit Aer | Quantum circuit simulation |
| NumPy / SciPy | Numerical computation where used by the implementation |
| Leaflet / OpenStreetMap | Map visualisation, where configured |

The technologies listed above should be retained only where they are actually used in the current codebase. Qiskit and Qiskit Aer are installed in the development environment; their use in the active optimisation pipeline should be confirmed separately.

## 📁 Project Structure

The project is organised into backend and frontend components.

```text
QRO/
├── backend/
│   ├── algorithms/
│   │   ├── qaoa_optimizer.py
│   │   └── classical_optimizer.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   └── app.py
│
└── frontend/
    ├── index.html
    ├── assets/
    │   ├── icons/
    │   └── images/
    ├── css/
    ├── js/
    │   └── app.js
    └── pages/
        ├── dashboard.html
        ├── routes.html
        └── results.html
```

*This is the intended high-level layout. Verify the actual filenames and folders in your GitHub repository before publishing.*

## 📋 Prerequisites

- Python installed on your system.
- pip package manager.
- Visual Studio Code or another code editor.
- A modern web browser.
- Git for version control.

For the quantum simulator experiments, the development environment currently reports:

- Qiskit `2.5.2`
- Qiskit Aer `0.17.2`

Package availability may differ across Python versions and operating systems.

## 🚀 Installation and Setup

### 1. Clone the repository

Replace the placeholder with your GitHub repository URL.

```bash
git clone YOUR_GITHUB_REPOSITORY_URL
cd QRO
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

Install the packages required by the project:

```bash
python -m pip install Flask flask-cors numpy scipy qiskit qiskit-aer
```

If the existing code imports additional packages, install those as well. A verified `requirements.txt` is recommended for reproducible setup.

### 4. Start the backend

Open a terminal in the backend directory:

```powershell
cd backend
python app.py
```

The backend is expected to run at:

```text
http://127.0.0.1:5000
```

Check the health endpoint:

```text
http://127.0.0.1:5000/api/health
```

A successful response should indicate that the backend is running.

### 5. Start the frontend

Open a second terminal:

```powershell
cd frontend
python -m http.server 5500
```

Open the dashboard in your browser:

```text
http://127.0.0.1:5500/pages/dashboard.html
```

Keep both servers running while using the application.

## 🔌 API Endpoints

The backend exposes the following routes in the current project configuration:

| Endpoint | Purpose |
|---|---|
| `GET /api/health` | Check backend status |
| `GET /api/vehicles` | Retrieve vehicle information |
| `GET /api/locations` | Retrieve location information |
| `POST /api/optimize` | Run optimisation and return comparison results |
| `POST /api/classical-optimize` | Run the classical optimisation endpoint |
| `GET /` | Backend root endpoint |
| `GET /health` | Health-check endpoint |

Exact request fields and response formats are defined in the backend route implementation.

## 🧠 Optimisation Approaches

### Classical Optimisation

The classical approach serves as a baseline for evaluating route quality. It processes the delivery information and produces route metrics according to the implemented constraints and algorithm.

### Quantum Approximate Optimisation Algorithm (QAOA)

QAOA is a hybrid quantum-classical optimisation algorithm. It uses a parameterised quantum circuit and classical parameter updates to search for good solutions to a formulated optimisation problem.

In QuantumRoute, the QAOA-based approach is intended to explore route optimisation using quantum circuit simulation. Qiskit provides circuit-building tools, while Qiskit Aer provides simulator backends.

**Important distinction:** Installing Qiskit does not automatically convert an existing custom QAOA implementation into a Qiskit implementation. The active optimiser must explicitly build and execute Qiskit circuits for the application to claim that it uses Qiskit for its optimisation results.

For larger instances, a classical or quantum-inspired fallback may be used if configured in the source code.

## 📊 Results and Evaluation

QuantumRoute presents the available classical and quantum-based optimisation metrics so that users can compare the resulting routes.

Potential evaluation metrics include:

- Total route distance.
- Estimated transportation cost.
- Route feasibility.
- Delivery demand and vehicle capacity.
- QAOA parameters and measurement statistics, when provided by the implementation.
- Runtime and solution quality for different problem sizes.

No claim is made that quantum optimisation always outperforms classical optimisation. The results depend on the problem formulation, algorithm configuration, simulator, and input data.

## ⚠️ Limitations

- This is a prototype intended for experimentation and demonstration.
- Simulating quantum circuits on a classical computer is resource-intensive as circuit size increases.
- QAOA does not guarantee the globally optimal solution for every input.
- Route quality depends on the implemented objective function and constraints.
- Real-time traffic, road closures, and live delivery data may not be incorporated.
- Simulator results are not evidence of execution on physical quantum hardware.
- Qiskit integration and its effect on the active optimiser must be verified against the current implementation.

## 🔮 Future Enhancements

- Complete and validate Qiskit-based QAOA integration.
- Compare the custom simulation and Qiskit Aer simulation.
- Evaluate the approach on larger delivery instances.
- Add real-world traffic and travel-time data.
- Extend support for multiple vehicles and time-window constraints.
- Add benchmark datasets and repeatable performance evaluations.
- Explore execution on real quantum hardware when suitable access is available.
- Improve route visualisation and reporting.

## 👥 Target Users

QuantumRoute may be useful for exploring route planning concepts in:

- E-commerce delivery operations.
- Courier and parcel services.
- Logistics and supply-chain management.
- Fleet management.
- Academic research and quantum optimisation education.

## 🤝 Contributing

Contributions, bug reports, and suggestions are welcome.

1. Fork the repository.
2. Create a feature branch.
3. Make and test your changes.
4. Submit a pull request with a clear description.

## 📄 License

No license has been specified yet. Add an appropriate open-source license, such as MIT, only after deciding how you want others to use and distribute this project.

---

## 👩‍💻 Project Information

**Project:** QuantumRoute  
**Problem Statement:** VNQFF-08 — Quantum-Enhanced Last-Mile Route Optimisation  
**Focus:** Classical and quantum-based optimisation for last-mile delivery planning

*Developed as an academic prototype exploring the application of quantum optimisation techniques to real-world logistics challenges.*
