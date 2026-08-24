import pytest
from risk_engine import ShieldFlowEngine

@pytest.fixture
def engine():
    return ShieldFlowEngine()

def test_legitimate_transaction(engine):
    payload = {
        "transaction_id": "pay_test_01",
        "merchant_id": "acc_01",
        "amount": 999.0,
        "currency": "INR",
        "customer_email": "legit.user@gmail.com",
        "ip_address": "103.21.124.45",
        "historical_orders": 10,
        "is_cod": False,
        "shipping_address": "Indiranagar, Bengaluru",
        "billing_address": "Indiranagar, Bengaluru"
    }
    result = engine.evaluate(payload, velocity_count=1)
    assert result["risk_tier"] == "ALLOW"
    assert result["risk_score"] < 35
    assert result["latency_ms"] < 20.0

def test_disposable_email_block(engine):
    payload = {
        "transaction_id": "pay_test_02",
        "customer_email": "attacker@tempmail.com",
        "amount": 50000.0,
        "historical_orders": 0,
        "is_cod": True
    }
    result = engine.evaluate(payload, velocity_count=1)
    assert result["risk_tier"] in ["BLOCK", "MANUAL_REVIEW"]
    assert any("Disposable Email" in item["factor"] for item in result["risk_breakdown"])

def test_ml_anomaly_scoring(engine):
    score = engine.ml_model.predict_anomaly_score(amount=95000.0, velocity=8, history=0, is_cod=1)
    assert 0 <= score <= 100
