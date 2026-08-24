# ShieldFlow AI 🛡️
> Sub-10ms Real-Time Payment Risk Decisioning & Fraud Mitigation Gateway

[![CI/CD Pipeline](https://github.com/suhanikri/shieldflow-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/suhanikri/shieldflow-ai/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-15-black.svg)](https://nextjs.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ⚡ Overview

ShieldFlow AI is a high-throughput, low-latency risk evaluation gateway built for high-volume payment ecosystems like Razorpay and Stripe.

In payment processing, deep neural networks introduce latency bottlenecks that cause checkout drop-offs, while basic rule engines generate high false-positive decline rates. ShieldFlow AI bridges this gap with a hybrid decisioning pipeline:

1. **Cryptographic Validation:** Instant HMAC SHA-256 webhook signature verification.
2. **Fast-Path Caching Layer:** Redis sliding-window velocity counters enforcing rate bounds in `< 2ms`.
3. **Dual-Stage ML & Heuristic Engine:** Unsupervised Isolation Forest Anomaly Detection combined with deterministic filters.
4. **Human-in-the-Loop (HITL) Desk:** Borderline transactions (scores 35–69) are flagged to an analyst operations desk with SQLite audit persistence.

---

## 🏛️ System Architecture

```mermaid
flowchart TD
    A[Inbound Webhook Payload] --> B[HMAC SHA-256 Signature Verification]
    B --> C[Fast-Path Redis Velocity Check]
    
    C -- Velocity Exceeded --> D[Instant BLOCK]
    C -- Velocity Normal --> E[Hybrid Decision Engine]
    
    E --> F[ML Anomaly Isolation Forest]
    E --> G[Deterministic Heuristics]
    
    F & G --> H{Risk Tier Evaluation}
    
    H -- "Score < 35" --> I[ALLOW: Instant Capture]
    H -- "Score 35-69" --> J[MANUAL REVIEW: Streamlit Analyst Desk]
    H -- "Score >= 70" --> K[BLOCK: Auto-Refund Triggered]
    
    J --> L[(SQLite Audit Ledger)]
    I --> L
    K --> L
```

---

## 🚀 Key Features

* **Sub-10ms Roundtrip Inference:** Optimized execution pipeline ensuring minimal checkout overhead.
* **Cryptographic Payload Verification:** Validates webhook signatures against symmetric API secrets.
* **Unsupervised Anomaly Scoring:** Scikit-Learn Isolation Forest detects statistical outliers.
* **Granular Explainability:** Quantified, SHAP-style risk attribution weights returned with every payload.
* **Analyst Ops Console:** Interactive Streamlit dashboard for real-time payload testing and overrides.
* **Real-Time Telemetry Dashboard:** Next.js + Tailwind CSS UI with continuous webhook simulation.
* **CI/CD Reliability:** GitHub Actions pipeline running automated Pytest suites against live Redis test containers.

---

## 🛠️ Tech Stack

* **Backend Engine:** Python 3.11, FastAPI, Uvicorn, Pydantic v2
* **Machine Learning:** Scikit-Learn (Isolation Forest), NumPy
* **Fast-Path Storage & Caching:** Redis (Sliding-window counters)
* **Persistent Storage:** SQLite3 (Audit logs, Analyst states)
* **Analyst Console:** Streamlit
* **Telemetry Dashboard:** Next.js 15, React 19, Tailwind CSS, Lucide Icons
* **Testing & CI:** Pytest, HTTPX, GitHub Actions, Docker Compose

---

## 💻 Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com/suhanikri/shieldflow-ai.git
cd shieldflow-ai
```

### 2. Configure Backend Virtual Environment
```bash
python -m venv venv
```

**Activate Environment:**
* Windows (PowerShell): `.\venv\Scripts\Activate.ps1`
* Linux / macOS: `source venv/bin/activate`

**Install dependencies:**
```bash
pip install -r requirements.txt
```

### 3. Launch the Backend API
```bash
uvicorn api:app --reload --port 8000
```
Interactive API Documentation (Swagger UI): `http://localhost:8000/docs`

### 4. Launch the Streamlit Analyst Ops Desk
```bash
streamlit run app.py
```
Operations Desk: `http://localhost:8501`

### 5. Launch the Next.js Telemetry Dashboard
```bash
cd frontend
npm install
npm run dev
```
Telemetry Dashboard: `http://localhost:3000`

---

## 🧪 Testing & Simulation

### Run Automated Unit Tests
```bash
pytest -v test_shieldflow.py
```

### Run Live Continuous Traffic Daemon
```bash
python simulate_webhook.py
```

---

## 📄 License
This project is open-source and licensed under the MIT License.
