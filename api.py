import hmac
import hashlib
import json
import time
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, Header, Response, status
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from schemas import TransactionPayload, RiskAssessmentResult
from risk_engine import ShieldFlowEngine
from database import log_transaction_verdict, update_review_decision, SessionLocal, TransactionLedger

app = FastAPI(
    title="ShieldFlow AI Gateway API",
    description="Real-time risk scoring and fraud mitigation backend with Prometheus telemetry.",
    version="1.1.0"
)

RAZORPAY_WEBHOOK_SECRET = "shieldflow_secret_key_prod_99"

# --- Prometheus Metrics Definitions ---
WEBHOOK_REQUESTS_TOTAL = Counter(
    "shieldflow_requests_total",
    "Total incoming webhook requests handled by the risk gateway",
    ["event_type", "status"]
)

RISK_VERDICTS_TOTAL = Counter(
    "shieldflow_fraud_verdict_total",
    "Total fraud risk verdicts partitioned by tier",
    ["risk_tier", "pipeline_tier"]
)

PIPELINE_LATENCY_HISTOGRAM = Histogram(
    "shieldflow_evaluation_latency_seconds",
    "Time spent evaluating transaction risk across engine tiers",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
)

RISK_SCORE_HISTOGRAM = Histogram(
    "shieldflow_score_distribution",
    "Distribution of calculated fraud risk scores",
    buckets=[10, 25, 35, 50, 75, 90, 100]
)


class ReviewActionPayload(BaseModel):
    transaction_id: str
    action: str
    notes: str = ""


class GatewayActionClient:
    @staticmethod
    def void_or_refund_payment(payment_id: str, reason: str) -> dict:
        return {
            "action": "AUTO_REFUND_EXECUTED",
            "payment_id": payment_id,
            "refund_id": f"rfnd_{payment_id[4:]}_auto",
            "status": "processed",
            "reason": reason,
            "timestamp": time.time()
        }

    @staticmethod
    def trigger_step_up_challenge(payment_id: str, email: str) -> dict:
        return {
            "action": "OTP_DISPATCHED",
            "payment_id": payment_id,
            "recipient": email,
            "status": "pending_verification"
        }


def verify_razorpay_signature(raw_body: bytes, signature: str, secret: str) -> bool:
    if not signature:
        return False
    expected_signature = hmac.new(
        key=secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)


@app.get("/metrics")
async def metrics_endpoint():
    """Exposes standard Prometheus scrape metrics."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/webhook/razorpay", status_code=status.HTTP_200_OK)
async def razorpay_webhook_listener(
    request: Request,
    x_razorpay_signature: str = Header(default="")
):
    raw_body = await request.body()
    
    if not verify_razorpay_signature(raw_body, x_razorpay_signature, RAZORPAY_WEBHOOK_SECRET):
        WEBHOOK_REQUESTS_TOTAL.labels(event_type="unknown", status="unauthorized_signature").inc()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Razorpay HMAC signature"
        )

    event_data = json.loads(raw_body)
    event_type = event_data.get("event", "unknown")

    if event_type in ["payment.authorized", "payment.captured", "order.paid"]:
        payment_info = event_data.get("payload", {}).get("payment", {}).get("entity", {})
        notes = payment_info.get("notes", {})

        normalized_payload = TransactionPayload(
            transaction_id=payment_info.get("id", "pay_unknown"),
            merchant_id=event_data.get("account_id", "acc_default"),
            amount=float(payment_info.get("amount", 0)) / 100.0,
            currency=payment_info.get("currency", "INR"),
            customer_email=payment_info.get("email", "buyer@example.com"),
            ip_address=notes.get("ip_address", request.client.host if request.client else "127.0.0.1"),
            device_fingerprint=notes.get("device_fingerprint", "dev_fp_generic"),
            shipping_address=notes.get("shipping_address", "Unspecified Shipping Address"),
            billing_address=notes.get("billing_address", "Unspecified Billing Address"),
            historical_order_count=int(notes.get("historical_order_count", 0)),
            is_cod=bool(payment_info.get("method") == "cod" or notes.get("is_cod", False))
        )

        with PIPELINE_LATENCY_HISTOGRAM.time():
            assessment, tier_used, latency_ms = ShieldFlowEngine.process_transaction(normalized_payload)

        # Increment Prometheus telemetry
        WEBHOOK_REQUESTS_TOTAL.labels(event_type=event_type, status="processed").inc()
        RISK_VERDICTS_TOTAL.labels(risk_tier=assessment.risk_tier.value, pipeline_tier=tier_used).inc()
        RISK_SCORE_HISTOGRAM.observe(assessment.risk_score)

        log_transaction_verdict(normalized_payload, assessment, tier_used, latency_ms)

        mitigation_details = {}
        if assessment.risk_tier.value == "BLOCK":
            mitigation_details = GatewayActionClient.void_or_refund_payment(
                payment_id=normalized_payload.transaction_id,
                reason=f"Risk Score {assessment.risk_score}: {'; '.join(assessment.detected_anomalies)}"
            )
        elif assessment.risk_tier.value == "STEP_UP_OTP":
            mitigation_details = GatewayActionClient.trigger_step_up_challenge(
                payment_id=normalized_payload.transaction_id,
                email=normalized_payload.customer_email
            )
        else:
            mitigation_details = {"action": "SETTLEMENT_CLEARED", "status": "approved"}

        return {
            "status": "processed",
            "gateway_event": event_type,
            "pipeline_tier": tier_used,
            "mitigation_action": mitigation_details,
            "risk_verdict": assessment.model_dump(),
            "pipeline_latency_ms": f"{latency_ms:.2f}"
        }

    WEBHOOK_REQUESTS_TOTAL.labels(event_type=event_type, status="ignored").inc()
    return {"status": "ignored", "detail": f"Event {event_type} ignored"}


@app.post("/webhook/evaluate-transaction", response_model=RiskAssessmentResult)
async def evaluate_transaction_webhook(payload: TransactionPayload):
    with PIPELINE_LATENCY_HISTOGRAM.time():
        assessment, tier_used, latency_ms = ShieldFlowEngine.process_transaction(payload)
    
    WEBHOOK_REQUESTS_TOTAL.labels(event_type="direct_eval", status="processed").inc()
    RISK_VERDICTS_TOTAL.labels(risk_tier=assessment.risk_tier.value, pipeline_tier=tier_used).inc()
    RISK_SCORE_HISTOGRAM.observe(assessment.risk_score)

    log_transaction_verdict(payload, assessment, tier_used, latency_ms)
    return assessment


@app.get("/ledger/history", status_code=200)
async def get_ledger_history(limit: int = 50):
    session = SessionLocal()
    try:
        rows = session.query(TransactionLedger).order_by(TransactionLedger.id.desc()).limit(limit).all()
        results = []
        for r in rows:
            created_str = r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else ""
            results.append({
                "id": r.id,
                "transaction_id": r.transaction_id or "",
                "amount": f"{r.currency or 'INR'} {r.amount or 0.0:,.2f}",
                "customer_email": r.customer_email or "",
                "risk_tier": r.risk_tier or "ALLOW",
                "risk_score": r.risk_score or 0,
                "pipeline_tier": r.pipeline_tier or "Tier 1",
                "review_status": r.review_status or "AUTO_RESOLVED",
                "analyst_notes": r.analyst_notes or "None",
                "latency_ms": r.latency_ms or 0.0,
                "created_at": created_str
            })
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database query error: {str(e)}")
    finally:
        session.close()


@app.post("/analyst/review-action", status_code=200)
async def submit_analyst_review(action_data: ReviewActionPayload):
    success = update_review_decision(action_data.transaction_id, action_data.action, action_data.notes)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found in ledger")
    return {"status": "updated", "transaction_id": action_data.transaction_id, "new_status": action_data.action}


@app.get("/health", status_code=200)
async def health_check():
    return {"status": "healthy", "engine": "ShieldFlow AI active"}
