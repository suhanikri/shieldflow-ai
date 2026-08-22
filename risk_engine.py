import os
import json
import time
from collections import defaultdict
from typing import Dict, List, Tuple, Any
from schemas import (
    TransactionPayload,
    RiskAssessmentResult,
    RiskTier,
    FastPathVerdict,
    FastPathResult,
)

# Optional Redis Connection for Distributed Deployments
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
redis_client = None

try:
    import redis
    client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True, socket_connect_timeout=0.2)
    client.ping()
    redis_client = client
except Exception:
    redis_client = None

# In-memory fallback
LOCAL_VELOCITY_CACHE: Dict[str, List[float]] = defaultdict(list)
VELOCITY_WINDOW_SECONDS = 60
VELOCITY_THRESHOLD_COUNT = 3

DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwawaymail.com", "guerrillamail.com", 
    "sharklasers.com", "10minutemail.com", "mailinator.com"
}


def check_device_velocity(device_fingerprint: str) -> int:
    """Sliding-window velocity counter using Redis ZSETs (O(log(N)) with local memory fallback."""
    current_time = time.time()
    cutoff_time = current_time - VELOCITY_WINDOW_SECONDS

    if redis_client:
        try:
            key = f"velocity:device:{device_fingerprint}"
            pipeline = redis_client.pipeline()
            # 1. Prune older entries outside sliding window
            pipeline.zremrangebyscore(key, 0, cutoff_time)
            # 2. Add current transaction timestamp
            pipeline.zadd(key, {str(current_time): current_time})
            # 3. Count events in the active window
            pipeline.zcard(key)
            # 4. Set key TTL
            pipeline.expire(key, VELOCITY_WINDOW_SECONDS + 10)
            results = pipeline.execute()
            return int(results[2])
        except Exception:
            pass

    # Fallback to in-memory sliding window
    timestamps = LOCAL_VELOCITY_CACHE[device_fingerprint]
    valid_timestamps = [t for t in timestamps if t > cutoff_time]
    valid_timestamps.append(current_time)
    LOCAL_VELOCITY_CACHE[device_fingerprint] = valid_timestamps
    return len(valid_timestamps)


def lookup_ip_intelligence(ip_address: str) -> Dict[str, Any]:
    known_tor_proxies = {"185.220.101.5", "192.42.116.16", "45.154.255.89"}
    if ip_address in known_tor_proxies:
        return {"is_vpn_or_proxy": True, "ip_risk_score": 95, "asn": "TOR-EXIT-NODE", "country": "RU"}
    return {"is_vpn_or_proxy": False, "ip_risk_score": 10, "asn": "AIRTEL-BROADBAND-IN", "country": "IN"}


class FastPathEngine:
    @staticmethod
    def evaluate(payload: TransactionPayload) -> FastPathResult:
        anomalies: List[str] = []
        base_score = 5

        # 1. Disposable Email Check
        email_domain = payload.customer_email.split("@")[-1].lower()
        if email_domain in DISPOSABLE_DOMAINS:
            anomalies.append(f"High-risk disposable email domain detected: @{email_domain}")
            base_score += 45

        # 2. Distributed Sliding Window Device Velocity Check
        event_count = check_device_velocity(payload.device_fingerprint)
        if event_count >= VELOCITY_THRESHOLD_COUNT:
            anomalies.append(f"Device velocity spike: {event_count} orders in {VELOCITY_WINDOW_SECONDS}s")
            base_score += 40

        # 3. Address Mismatch Check
        norm_shipping = "".join(payload.shipping_address.lower().split())
        norm_billing = "".join(payload.billing_address.lower().split())
        if norm_shipping != norm_billing:
            anomalies.append("Shipping and billing addresses do not match")
            base_score += 15

        # 4. First-time COD High-Value Risk
        if payload.is_cod and payload.historical_order_count == 0 and payload.amount > 5000:
            anomalies.append("First-time customer high-value Cash on Delivery (RTO Risk)")
            base_score += 25

        if base_score <= 15 and not anomalies:
            return FastPathResult(verdict=FastPathVerdict.CLEAN, heuristics_triggered=[], initial_score=5)
        
        return FastPathResult(
            verdict=FastPathVerdict.NEEDS_DEEP_EVALUATION,
            heuristics_triggered=anomalies,
            initial_score=min(base_score, 100)
        )


class DeepAgentEvaluator:
    @staticmethod
    def evaluate(payload: TransactionPayload, fast_path: FastPathResult) -> RiskAssessmentResult:
        score = fast_path.initial_score
        anomalies = list(fast_path.heuristics_triggered)

        ip_data = lookup_ip_intelligence(payload.ip_address)
        if ip_data["is_vpn_or_proxy"]:
            anomalies.append(f"Threat Intel: Originating IP is an active {ip_data['asn']} (IP Risk: {ip_data['ip_risk_score']}/100)")
            score += 35

        if payload.historical_order_count > 10:
            score = max(0, score - 20)
            reasoning_prefix = "Established customer history helps mitigate transaction anomalies."
        else:
            reasoning_prefix = "New customer profile increases risk exposure."

        score = min(score, 100)

        if score >= 75:
            tier = RiskTier.BLOCK
            reasoning = f"{reasoning_prefix} Multiple severe fraud indicators identified: {'; '.join(anomalies)}."
        elif score >= 35:
            tier = RiskTier.STEP_UP_OTP
            reasoning = f"{reasoning_prefix} Moderate risk detected requiring two-factor verification: {'; '.join(anomalies)}."
        else:
            tier = RiskTier.ALLOW
            reasoning = "Transaction falls within acceptable variance limits."

        return RiskAssessmentResult(
            transaction_id=payload.transaction_id,
            risk_tier=tier,
            risk_score=score,
            detected_anomalies=anomalies,
            plain_text_reasoning=reasoning,
            confidence_score=0.95
        )


class ShieldFlowEngine:
    @staticmethod
    def process_transaction(payload: TransactionPayload) -> Tuple[RiskAssessmentResult, str, float]:
        start_time = time.perf_counter()
        
        fast_path = FastPathEngine.evaluate(payload)
        
        if fast_path.verdict == FastPathVerdict.CLEAN:
            elapsed_ms = (time.perf_counter() - start_time) * 1000
            result = RiskAssessmentResult(
                transaction_id=payload.transaction_id,
                risk_tier=RiskTier.ALLOW,
                risk_score=fast_path.initial_score,
                detected_anomalies=[],
                plain_text_reasoning="Fast-path clearance: No identity, velocity, or geolocation anomalies.",
                confidence_score=0.99
            )
            return result, "Tier 1: Fast-Path Heuristics", elapsed_ms

        result = DeepAgentEvaluator.evaluate(payload, fast_path)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        return result, "Tier 2: Deep Agent Evaluator", elapsed_ms
