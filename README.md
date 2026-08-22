# 🛡️ ShieldFlow AI — Real-Time Payment Risk & Fraud Mitigation Engine

[![ShieldFlow AI CI Pipeline](https://github.com/suhanikri/shieldflow-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/suhanikri/shieldflow-ai/actions/workflows/ci.yml)
![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-Rate%20Limiting-DC382D?logo=redis&logoColor=white)
![Prometheus](https://img.shields.io/badge/Prometheus-Telemetry-E6522C?logo=prometheus&logoColor=white)

ShieldFlow AI is an ultra-low latency, production-grade fraud detection gateway designed to inspect inbound payment webhooks (Razorpay, Stripe) in real time. It features a two-tier evaluation architecture combining deterministic sub-10ms heuristics with deep threat intelligence agent workflows, backed by a human-in-the-loop (HITL) manual review console.

---

## 🏛️ System Architecture
+-----------------------+
                              |   Payment Webhook     |
                              |  (Razorpay / Stripe)  |
                              +-----------+-----------+
                                          |
                                          v
                          +-------------------------------+
                          |  FastAPI Ingestion Gateway    |
                          |  (HMAC SHA-256 Signature Auth)|
                          +---------------+---------------+
                                          |
                                          v
                     +----------------------------------------+
                     |       ShieldFlow Decision Engine       |
                     +--------------------+-------------------+
                                          |
                 +------------------------+------------------------+
                 |                                                 |
                 v                                                 v
   +----------------------------+                    +----------------------------+
   |   Tier 1: Fast-Path Rule   |                    |   Tier 2: Deep Agent Flow  |
   | - Redis Velocity Limiting  |                    | - Disposable Domain Check  |
   | - Address Mismatch Checks  |                    | - IP Proxy / TOR Check     |
   | - Latency: < 10ms          |                    | - High-Risk COD Scoring    |
   +--------------+-------------+                    +--------------+-------------+
                  |                                                 |
                  +-----------------------+-------------------------+
                                          |
                                          v
                          +-------------------------------+
                          | Persistent Audit Ledger (SQL) |
                          +---------------+---------------+
                                          |
                    +---------------------+---------------------+
                    |                                           |
                    v                                           v
     +-----------------------------+             +-----------------------------+
     |  Prometheus Metrics (/metrics)|           |  Streamlit Operations Desk  |
     |  - p95 Latency Histograms   |             |  - Real-time Visualizer     |
     |  - Fraud Verdict Counters   |             |  - HITL Manual Review Queue |
     +-----------------------------+             +-----------------------------+

     ---

## 🚀 Key Features
Sub-10ms Fast-Path Heuristics: Evaluates velocity spikes, address consistency, and purchase history.

Distributed Rate Limiting: Sliding-window rate limiting backed by Redis sorted sets.

Cryptographic Security: End-to-end HMAC SHA-256 payload authentication.

Human-in-the-Loop (HITL) Queue: Streamlit operations desk allowing risk analysts to override flagged transactions with persistent audit logs.

Observability: Native Prometheus instrumentation streaming throughput, latency percentiles, and risk distributions.

Multi-Container Architecture: Production-ready orchestration with Docker and Docker Compose.

.

## 🛠️ Quickstart with Docker Compose
1. Prerequisites
Docker Desktop installed and running.

Git

2. Launch Stack
Bash
git clone [https://github.com/suhanikri/shieldflow-ai.git](https://github.com/suhanikri/shieldflow-ai.git)
cd shieldflow-ai

# Build and start services in the background
docker compose up --build -d

## 3. Service Endpoints
# Analyst Operations Console: http://localhost:8501

# FastAPI Swagger Documentation: http://localhost:8000/docs

# Prometheus Metrics: http://localhost:8000/metrics

# Health Check: http://localhost:8000/health

health

## 🧪 Running Automated Tests
Run the test suite locally using pytest:

Bash
pytest -v test_shieldflow.py

## 📋 API Specification
POST /webhook/razorpay
Ingests and verifies signed payment gateway webhooks.

Headers:
# X-Razorpay-Signature: HMAC SHA-256 hex digest

Sample Response:

# JSON
{
  "status": "processed",
  "gateway_event": "payment.authorized",
  "pipeline_tier": "Tier 2: Deep Agent Evaluator",
  "mitigation_action": {
    "action": "AUTO_REFUND_EXECUTED",
    "payment_id": "pay_O9xK3B8Z11L",
    "status": "processed"
  },
  "risk_verdict": {
    "risk_score": 100,
    "risk_tier": "BLOCK",
    "detected_anomalies": [
      "Disposable/High-risk email domain: tempmail.com",
      "High-risk Proxy/TOR IP exit node detected: 185.220.101.5"
    ]
  },
  "pipeline_latency_ms": "3.42"
}
