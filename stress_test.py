import hmac
import hashlib
import json
import requests
import time

WEBHOOK_URL = "http://localhost:8000/webhook/razorpay"
SECRET = "shieldflow_secret_key_prod_99"

device_id = "device_fp_carding_bot_441"

print("--- Simulating rapid carding bot attack (5 requests in 1 second) ---")

for i in range(1, 6):
    payload_dict = {
        "entity": "event",
        "account_id": "acc_razorpay_merchant_live",
        "event": "payment.authorized",
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_burst_test_00{i}",
                    "amount": 99900,
                    "currency": "INR",
                    "status": "authorized",
                    "method": "card",
                    "email": f"card_test_{i}@gmail.com",
                    "notes": {
                        "ip_address": "49.207.198.112",
                        "device_fingerprint": device_id,
                        "shipping_address": "Sample Address, Indiranagar, Bangalore",
                        "billing_address": "Sample Address, Indiranagar, Bangalore",
                        "historical_order_count": 0,
                        "is_cod": False
                    }
                }
            }
        }
    }

    raw_body = json.dumps(payload_dict)
    signature = hmac.new(key=SECRET.encode("utf-8"), msg=raw_body.encode("utf-8"), digestmod=hashlib.sha256).hexdigest()
    headers = {"Content-Type": "application/json", "X-Razorpay-Signature": signature}

    res = requests.post(WEBHOOK_URL, data=raw_body, headers=headers)
    data = res.json()
    verdict = data.get("risk_verdict", {})
    tier = verdict.get("risk_tier", "N/A")
    score = verdict.get("risk_score", 0)
    print(f"Request #{i} -> Decision: {tier} (Risk Score: {score}/100)")
    time.sleep(0.1)
