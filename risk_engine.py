import time
import numpy as np
from typing import Dict, Any, List, Tuple
from sklearn.ensemble import IsolationForest

class MLAnomalyDetector:
    """Pre-trained unsupervised isolation forest for payment anomaly detection."""
    def __init__(self):
        # Synthetic baseline training on standard transaction behavior
        np.random.seed(42)
        # Features: [amount_scaled, velocity_count, order_history, is_cod]
        normal_traffic = np.column_stack([
            np.random.exponential(scale=1500, size=1000),  # typical amount
            np.random.poisson(lam=1.2, size=1000),         # typical velocity
            np.random.randint(1, 25, size=1000),          # typical history
            np.random.choice([0, 1], p=[0.85, 0.15], size=1000) # COD flag
        ])
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.model.fit(normal_traffic)

    def predict_anomaly_score(self, amount: float, velocity: int, history: int, is_cod: int) -> float:
        """Returns anomaly score normalized from 0 (normal) to 100 (severe outlier)."""
        features = np.array([[amount, velocity, history, is_cod]])
        raw_score = self.model.score_samples(features)[0] # negative values: more anomalous
        # Normalize typical Isolation Forest output (-0.8 to -0.3) to 0-100 scale
        normalized = float(np.clip(((-raw_score - 0.35) / 0.45) * 100, 0, 100))
        return round(normalized, 2)

class ShieldFlowEngine:
    DISPOSABLE_DOMAINS = {
        "tempmail.com", "throwawaymail.com", "guerrillamail.com", 
        "10minutemail.com", "disposable-inbox.com", "sharklasers.com"
    }
    DATACENTER_IP_PREFIXES = ["104.", "198.", "185.", "45."]

    def __init__(self):
        self.ml_model = MLAnomalyDetector()

    def evaluate(self, payload: Dict[str, Any], velocity_count: int = 1) -> Dict[str, Any]:
        start_time = time.perf_counter()
        breakdown: List[Dict[str, Any]] = []
        total_risk_score = 0

        # Heuristic 1: Disposable Email Detection
        email = payload.get("customer_email", "").lower()
        domain = email.split("@")[-1] if "@" in email else ""
        if domain in self.DISPOSABLE_DOMAINS:
            pts = 40
            total_risk_score += pts
            breakdown.append({"factor": "Disposable Email Domain", "weight": f"+{pts} pts", "severity": "HIGH"})

        # Heuristic 2: Datacenter / TOR Node Proxy
        ip = payload.get("ip_address", "")
        if any(ip.startswith(prefix) for prefix in self.DATACENTER_IP_PREFIXES):
            pts = 30
            total_risk_score += pts
            breakdown.append({"factor": "Datacenter / TOR Exit Node ASN", "weight": f"+{pts} pts", "severity": "HIGH"})

        # Heuristic 3: Sliding Window Velocity Spike
        if velocity_count > 3:
            pts = min(velocity_count * 8, 35)
            total_risk_score += pts
            breakdown.append({"factor": f"Velocity Surge ({velocity_count} tx / 60s)", "weight": f"+{pts} pts", "severity": "MEDIUM"})

        # ML Anomaly Inference
        amount = float(payload.get("amount", 0))
        history = int(payload.get("historical_orders", 0))
        is_cod = 1 if payload.get("is_cod", False) else 0

        ml_score = self.ml_model.predict_anomaly_score(amount, velocity_count, history, is_cod)
        if ml_score > 60:
            pts = int(ml_score * 0.3)
            total_risk_score += pts
            breakdown.append({"factor": f"ML Outlier Isolation Index ({ml_score}/100)", "weight": f"+{pts} pts", "severity": "HIGH"})

        # Address Consistency Check
        shipping = payload.get("shipping_address", "").strip().lower()
        billing = payload.get("billing_address", "").strip().lower()
        if shipping and billing and shipping != billing:
            pts = 15
            total_risk_score += pts
            breakdown.append({"factor": "Billing / Shipping Mismatch", "weight": f"+{pts} pts", "severity": "LOW"})

        # Final Decision Tier
        final_score = min(total_risk_score, 100)
        if final_score >= 70:
            tier = "BLOCK"
            action = "AUTO_REFUND_EXECUTED"
        elif final_score >= 35:
            tier = "MANUAL_REVIEW"
            action = "HELD_FOR_ANALYST_QUEUE"
        else:
            tier = "ALLOW"
            action = "APPROVED_INSTANT"

        latency_ms = (time.perf_counter() - start_time) * 1000

        return {
            "transaction_id": payload.get("transaction_id"),
            "risk_score": final_score,
            "risk_tier": tier,
            "recommended_action": action,
            "ml_anomaly_score": ml_score,
            "risk_breakdown": breakdown,
            "latency_ms": round(latency_ms, 2)
        }
