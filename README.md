Set-Content -Path "README.md" -Encoding utf8 -Value @'
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

* **Inbound Ingestion:** FastAPI gateway verifying Razorpay & Stripe webhooks via cryptographic HMAC SHA-256 signatures.
* **Tier 1 (Fast-Path Rules):** Sub-10ms evaluation checking Redis sliding-window velocity limits, purchase frequency, and address consistency.
* **Tier 2 (Deep Risk Intelligence):** Evaluates disposable email patterns, IP proxy/TOR exit nodes, and Cash-on-Delivery (COD) anomalies.
* **Audit & Storage:** SQLite/SQLAlchemy persistent transaction ledger storing latencies, risk scores, and reasons.
* **Observability & Ops:** Standard Prometheus `/metrics` telemetry alongside a Streamlit Human-in-the-Loop review console.

---

## 🚀 Key Features

* **Sub-10ms Fast-Path Heuristics:** Evaluates velocity spikes, address consistency, and purchase history.
* **Distributed Rate Limiting:** Sliding-window rate limiting backed by Redis sorted sets.
* **Cryptographic Security:** End-to-end HMAC SHA-256 payload authentication.
* **Human-in-the-Loop (HITL) Queue:** Streamlit operations desk allowing risk analysts to override flagged transactions with persistent audit logs.
* **Observability:** Native Prometheus instrumentation streaming throughput, latency percentiles, and risk distributions.
* **Multi-Container Architecture:** Production-ready orchestration with Docker and Docker Compose.

---

## 🛠️ Quickstart with Docker Compose

**1. Prerequisites**
* Docker Desktop installed and running.
* Git

**2. Launch Stack**
> `git clone https://github.com/suhanikri/shieldflow-ai.git`  
> `cd shieldflow-ai`  
> `docker compose up --build -d`  

**3. Service Endpoints**
* **Analyst Operations Console:** http://localhost:8501
* **FastAPI Swagger Documentation:** http://localhost:8000/docs
* **Prometheus Metrics:** http://localhost:8000/metrics
* **Health Check:** http://localhost:8000/health

---

## 🧪 Running Automated Tests

Run the test suite locally:
> `pytest -v test_shieldflow.py`

---

## 📋 API Specification

### POST /webhook/razorpay

Ingests and verifies signed payment gateway webhooks.

* **Header:** `X-Razorpay-Signature` (HMAC SHA-256 hex digest)
* **Risk Tiers:** `ALLOW`, `MANUAL_REVIEW`, `BLOCK`
* **Features Inspected:** Velocity limits, disposable email detection, IP proxy/TOR identification, and address consistency.
