import hmac
import hashlib
import json
import pytest
from fastapi.testclient import TestClient
from api import app, RAZORPAY_WEBHOOK_SECRET
from schemas import TransactionPayload, RiskTier
from risk_engine import ShieldFlowEngine

client = TestClient(app)


# --- 1. Unit Tests: Risk Engine ---

def test_fast_path_clean_transaction():
    """Verify clean transaction clears Tier 1 with low score."""
    payload = TransactionPayload(
        transaction_id="tx_test_clean_01",
        merchant_id="acc_unit_test",
        amount=500.0,
        currency="INR",
        customer_email="verified.user@gmail.com",
        ip_address="103.21.124.45",
        device_fingerprint="fp_clean_device_1",
        shipping_address="Street 1, Bangalore",
        billing_address="Street 1, Bangalore",
        historical_order_count=10,
        is_cod=False
    )
    result, tier, latency = ShieldFlowEngine.process_transaction(payload)
    assert result.risk_tier == RiskTier.ALLOW
    assert result.risk_score <= 15
    assert tier == "Tier 1: Fast-Path Heuristics"


def test_deep_path_disposable_email_detection():
    """Verify disposable email triggers Tier 2 escalation and anomalies."""
    payload = TransactionPayload(
        transaction_id="tx_test_fraud_01",
        merchant_id="acc_unit_test",
        amount=12000.0,
        currency="INR",
        customer_email="fraudster@tempmail.com",
        ip_address="185.220.101.5",
        device_fingerprint="fp_disposable_device_2",
        shipping_address="Delivery St, Noida",
        billing_address="Different St, Delhi",
        historical_order_count=0,
        is_cod=True
    )
    result, tier, latency = ShieldFlowEngine.process_transaction(payload)
    assert result.risk_tier == RiskTier.BLOCK
    assert result.risk_score >= 75
    assert any("tempmail.com" in a for a in result.detected_anomalies)


# --- 2. Integration Tests: API & HMAC Verification ---

def test_webhook_invalid_signature():
    """Verify forged/missing signature returns 401 Unauthorized."""
    payload = {"entity": "event", "event": "payment.authorized", "payload": {}}
    response = client.post(
        "/webhook/razorpay",
        json=payload,
        headers={"X-Razorpay-Signature": "invalid_signature_hash"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid Razorpay HMAC signature"


def test_webhook_valid_signature_execution():
    """Verify cryptographically signed webhook executes full pipeline."""
    payload_dict = {
        "entity": "event",
        "account_id": "acc_test_merchant",
        "event": "payment.authorized",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_test_webhook_99",
                    "amount": 250000,
                    "currency": "INR",
                    "status": "authorized",
                    "email": "customer@legitstore.com",
                    "notes": {
                        "ip_address": "103.21.124.45",
                        "device_fingerprint": "fp_test_sig_device",
                        "shipping_address": "Road 5, Mumbai",
                        "billing_address": "Road 5, Mumbai",
                        "historical_order_count": 5,
                        "is_cod": False
                    }
                }
            }
        }
    }
    raw_body = json.dumps(payload_dict)
    valid_signature = hmac.new(
        key=RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
        msg=raw_body.encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()

    response = client.post(
        "/webhook/razorpay",
        data=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": valid_signature
        }
    )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "processed"
    assert "risk_verdict" in res_json


# --- 3. End-to-End Test: Ledger & Analyst Action ---

def test_ledger_history_and_review_override():
    """Verify ledger recording and analyst decision override workflow."""
    # Check history endpoint
    res = client.get("/ledger/history")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # Perform an analyst action on the test transaction
    action_payload = {
        "transaction_id": "pay_test_webhook_99",
        "action": "APPROVED",
        "notes": "Automated test analyst approval"
    }
    action_res = client.post("/analyst/review-action", json=action_payload)
    assert action_res.status_code == 200
    assert action_res.json()["new_status"] == "APPROVED"
