import hmac
import hashlib
import json
import requests

WEBHOOK_URL = "http://localhost:8000/webhook/razorpay"
SECRET = "shieldflow_secret_key_prod_99"

payload_dict = {
    "entity": "event",
    "account_id": "acc_razorpay_merchant_live",
    "event": "payment.authorized",
    "payload": {
        "payment": {
            "entity": {
                "id": "pay_O9xK3B8Z11L",
                "amount": 1250000,
                "currency": "INR",
                "status": "authorized",
                "method": "cod",
                "email": "quickbuyer88@tempmail.com",
                "notes": {
                    "ip_address": "185.220.101.5",
                    "device_fingerprint": "dev_fp_anom_7749",
                    "shipping_address": "Plot 99, Industrial Area, Noida",
                    "billing_address": "Unspecified Commercial Hub, Delhi",
                    "historical_order_count": 0,
                    "is_cod": True
                }
            }
        }
    }
}

raw_body = json.dumps(payload_dict)

signature = hmac.new(
    key=SECRET.encode("utf-8"),
    msg=raw_body.encode("utf-8"),
    digestmod=hashlib.sha256
).hexdigest()

headers = {
    "Content-Type": "application/json",
    "X-Razorpay-Signature": signature
}

try:
    response = requests.post(WEBHOOK_URL, data=raw_body, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.ConnectionError:
    print("Error: Could not reach FastAPI at http://localhost:8000. Make sure uvicorn is running.")
