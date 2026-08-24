import time
import random
import hmac
import hashlib
import json
import requests

API_URL = "http://localhost:8000/webhook/razorpay"
WEBHOOK_SECRET = "sec_live_shieldflow_webhook_9921"

LEGIT_EMAILS = ["priya.patel@gmail.com", "arjun.nair@outlook.com", "rahul.verma@yahoo.com", "sneha.k@gmail.com"]
FRAUD_EMAILS = ["burner91@tempmail.com", "exploit_user@disposable-inbox.com", "botnet@sharklasers.com"]

def generate_payload():
    is_fraud = random.random() < 0.25 # 25% anomaly rate
    tx_id = f"pay_{random.randint(100000, 999999)}"
    
    if is_fraud:
        return {
            "transaction_id": tx_id,
            "merchant_id": "acc_live_merchant_ind_01",
            "amount": float(random.choice([25000, 48000, 75000, 99000])),
            "currency": "INR",
            "customer_email": random.choice(FRAUD_EMAILS),
            "ip_address": random.choice(["104.28.19.4", "185.220.101.5", "45.33.32.156"]),
            "historical_orders": random.randint(0, 1),
            "is_cod": random.choice([True, False]),
            "device_fingerprint": f"dev_tor_{random.randint(100, 999)}",
            "shipping_address": "Flat 801, Bandra West, Mumbai, 400050",
            "billing_address": "PO Box 991, Delaware, USA"
        }
    else:
        return {
            "transaction_id": tx_id,
            "merchant_id": "acc_live_merchant_ind_01",
            "amount": float(random.randint(499, 4500)),
            "currency": "INR",
            "customer_email": random.choice(LEGIT_EMAILS),
            "ip_address": f"103.21.{random.randint(10, 200)}.{random.randint(1, 250)}",
            "historical_orders": random.randint(3, 20),
            "is_cod": False,
            "device_fingerprint": f"dev_legit_{random.randint(1000, 9999)}",
            "shipping_address": "Plot 12, Indiranagar, Bengaluru, 560038",
            "billing_address": "Plot 12, Indiranagar, Bengaluru, 560038"
        }

def send_signed_webhook(payload):
    body = json.dumps(payload)
    signature = hmac.new(
        WEBHOOK_SECRET.encode("utf-8"),
        body.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": signature
    }
    
    res = requests.post(API_URL, data=body, headers=headers)
    return res.status_code, res.json()

if __name__ == "__main__":
    print("=" * 60)
    print("🛡️  ShieldFlow AI — Continuous Live Webhook Stream")
    print("   Streaming synthetic payment transactions to http://localhost:8000")
    print("   Press Ctrl + C to stop.")
    print("=" * 60)

    count = 1
    while True:
        payload = generate_payload()
        try:
            status, response = send_signed_webhook(payload)
            tier = response.get("risk_tier", "UNKNOWN")
            score = response.get("risk_score", 0)
            latency = response.get("latency_ms", 0.0)
            
            icon = "🟢" if tier == "ALLOW" else ("🟡" if tier == "MANUAL_REVIEW" else "🔴")
            print(f"[{count:03d}] {icon} {tier:<14} | Score: {score:>3}/100 | Latency: {latency:>5.2f}ms | {payload['customer_email']} (₹{payload['amount']})")
            count += 1
        except Exception as e:
            print(f"⚠️ Gateway unreachable: {e}. Make sure FastAPI is running on port 8000.")
            time.sleep(3)
        
        time.sleep(random.uniform(0.8, 2.0))
