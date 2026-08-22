import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import requests
import uuid
import time

FASTAPI_URL = "http://localhost:8000/webhook/evaluate-transaction"
HISTORY_URL = "http://localhost:8000/ledger/history"
REVIEW_ACTION_URL = "http://localhost:8000/analyst/review-action"

st.set_page_config(page_title="ShieldFlow AI | Risk Operations Center", layout="wide")

st.title("🛡️ ShieldFlow AI — Risk Operations Console")
st.markdown("Real-time fraud decisioning gateway with Human-in-the-Loop Analyst Override.")

PRESETS = {
    "Legitimate Normal Checkout": {
        "amount": 1499.00,
        "currency": "INR",
        "customer_email": "ananya.sharma@gmail.com",
        "ip_address": "103.21.124.45",
        "device_fingerprint": "dev_fp_legit_9921",
        "shipping_address": "Flat 402, Lotus Towers, Indiranagar, Bengaluru, 560038",
        "billing_address": "Flat 402, Lotus Towers, Indiranagar, Bengaluru, 560038",
        "historical_order_count": 8,
        "is_cod": False
    },
    "Borderline Velocity Spike": {
        "amount": 4200.00,
        "currency": "INR",
        "customer_email": "rahul.v@outlook.com",
        "ip_address": "49.207.198.112",
        "device_fingerprint": "dev_fp_velocity_rapid_01",
        "shipping_address": "Room 12, Sunrise Residency, Andheri East, Mumbai, 400069",
        "billing_address": "House 45, Sector 14, Gurugram, 122001",
        "historical_order_count": 1,
        "is_cod": False
    },
    "High-Risk Disposable RTO Fraud": {
        "amount": 12500.00,
        "currency": "INR",
        "customer_email": "quickbuyer88@tempmail.com",
        "ip_address": "185.220.101.5",
        "device_fingerprint": "dev_fp_anom_7749",
        "shipping_address": "Plot 99, Industrial Area Phase 2, Noida, 201301",
        "billing_address": "Unspecified Commercial Hub, New Delhi, 110001",
        "historical_order_count": 0,
        "is_cod": True
    }
}

if "payload_data" not in st.session_state:
    st.session_state.payload_data = PRESETS["Legitimate Normal Checkout"]

st.sidebar.header("Scenario Presets")
for preset_name, data in PRESETS.items():
    if st.sidebar.button(f"Load: {preset_name}", use_container_width=True):
        st.session_state.payload_data = data
        st.rerun()

tab_eval, tab_desk, tab_logs = st.tabs(["⚡ Live Evaluator", "🕵️ Analyst Review Desk", "📋 Audit Ledger"])

with tab_eval:
    col_input, col_output = st.columns([1.1, 1], gap="large")

    with col_input:
        st.subheader("Inbound Transaction Payload")
        
        with st.form("transaction_form"):
            tx_id = st.text_input("Transaction ID", value=f"pay_{uuid.uuid4().hex[:10]}")
            merchant_id = st.text_input("Merchant ID", value="acc_live_merchant_ind_01")
            
            c1, c2 = st.columns(2)
            with c1:
                amount = st.number_input("Amount", value=float(st.session_state.payload_data["amount"]), min_value=1.0)
                currency = st.selectbox("Currency", ["INR", "USD", "EUR"], index=0)
                historical_orders = st.number_input("Historical Orders", value=int(st.session_state.payload_data["historical_order_count"]), min_value=0)
            with c2:
                customer_email = st.text_input("Customer Email", value=st.session_state.payload_data["customer_email"])
                ip_address = st.text_input("IP Address", value=st.session_state.payload_data["ip_address"])
                is_cod = st.checkbox("Cash on Delivery (COD)", value=st.session_state.payload_data["is_cod"])

            device_fp = st.text_input("Device Fingerprint", value=st.session_state.payload_data["device_fingerprint"])
            shipping_addr = st.text_area("Shipping Address", value=st.session_state.payload_data["shipping_address"], height=70)
            billing_addr = st.text_area("Billing Address", value=st.session_state.payload_data["billing_address"], height=70)
            
            submitted = st.form_submit_button("Evaluate via Gateway", use_container_width=True)

    with col_output:
        st.subheader("Gateway Risk Verdict")

        if submitted:
            payload = {
                "transaction_id": tx_id,
                "merchant_id": merchant_id,
                "amount": amount,
                "currency": currency,
                "customer_email": customer_email,
                "ip_address": ip_address,
                "device_fingerprint": device_fp,
                "shipping_address": shipping_addr,
                "billing_address": billing_addr,
                "historical_order_count": historical_orders,
                "is_cod": is_cod
            }

            t_start = time.perf_counter()
            try:
                response = requests.post(FASTAPI_URL, json=payload, timeout=5)
                roundtrip_latency = (time.perf_counter() - t_start) * 1000

                if response.status_code == 200:
                    result = response.json()
                    risk_score = result["risk_score"]
                    risk_tier = result["risk_tier"]

                    gauge_color = "#10B981" if risk_score < 35 else "#F59E0B" if risk_score < 75 else "#EF4444"
                    fig = go.Figure(go.Indicator(
                        mode="gauge+number",
                        value=risk_score,
                        title={'text': f"Risk Score: {risk_score}/100", 'font': {'size': 20}},
                        gauge={
                            'axis': {'range': [0, 100]},
                            'bar': {'color': gauge_color},
                            'steps': [
                                {'range': [0, 35], 'color': "rgba(16, 185, 129, 0.15)"},
                                {'range': [35, 75], 'color': "rgba(245, 158, 11, 0.15)"},
                                {'range': [75, 100], 'color': "rgba(239, 68, 68, 0.15)"}
                            ]
                        }
                    ))
                    fig.update_layout(height=260, margin=dict(l=20, r=20, t=40, b=10))
                    st.plotly_chart(fig, use_container_width=True)

                    st.markdown(f"**Gateway Decision:** `{risk_tier}` | **Latency:** `{roundtrip_latency:.2f} ms`")
                    st.info(result["plain_text_reasoning"])
                else:
                    st.error(f"API Error: {response.text}")
            except Exception as e:
                st.error(f"Backend offline: {e}")
        else:
            st.info("Submit a transaction to inspect the live engine verdict.")

with tab_desk:
    st.subheader("🕵️ Pending Manual Review Queue")
    try:
        res = requests.get(HISTORY_URL, timeout=3)
        if res.status_code == 200:
            ledger_data = res.json()
            pending_items = [item for item in ledger_data if item.get("review_status") == "PENDING_REVIEW"]
            
            if pending_items:
                st.warning(f"⚠️ You have **{len(pending_items)}** transactions requiring human analyst review.")
                
                selected_tx_id = st.selectbox(
                    "Select Transaction to Inspect", 
                    options=[item["transaction_id"] for item in pending_items],
                    format_func=lambda x: next(f"{item['transaction_id']} | {item['amount']} | Score: {item['risk_score']} ({item['risk_tier']})" for item in pending_items if item["transaction_id"] == x)
                )

                selected_record = next(item for item in pending_items if item["transaction_id"] == selected_tx_id)

                d1, d2, d3 = st.columns(3)
                d1.metric("Customer Email", selected_record["customer_email"])
                d2.metric("Amount", selected_record["amount"])
                d3.metric("Assigned Risk", f"{selected_record['risk_score']}/100 ({selected_record['risk_tier']})")

                notes = st.text_input("Analyst Justification / Audit Reason", value="Reviewed verification documents. Cleared for manual fulfillment.")
                
                b1, b2 = st.columns(2)
                with b1:
                    if st.button("✅ Approve & Release Hold", use_container_width=True):
                        requests.post(REVIEW_ACTION_URL, json={"transaction_id": selected_tx_id, "action": "APPROVED", "notes": notes})
                        st.success(f"Transaction {selected_tx_id} APPROVED.")
                        time.sleep(0.5)
                        st.rerun()
                with b2:
                    if st.button("🚫 Confirm Fraud & Reject", use_container_width=True):
                        requests.post(REVIEW_ACTION_URL, json={"transaction_id": selected_tx_id, "action": "REJECTED", "notes": notes})
                        st.error(f"Transaction {selected_tx_id} REJECTED.")
                        time.sleep(0.5)
                        st.rerun()
            else:
                st.success("✅ Clean queue. No transactions are pending manual review.")
        else:
            st.error("Failed to fetch pending transactions.")
    except Exception as e:
        st.warning(f"Could not connect to database backend: {e}")

with tab_logs:
    st.subheader("Persistent SQLite Audit Ledger")
    try:
        res = requests.get(HISTORY_URL, timeout=3)
        if res.status_code == 200:
            ledger_data = res.json()
            if ledger_data:
                st.dataframe(pd.DataFrame(ledger_data), use_container_width=True, hide_index=True)
            else:
                st.info("No records logged in database yet.")
    except Exception:
        st.warning("Backend API is currently offline.")
