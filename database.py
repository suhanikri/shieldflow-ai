import json
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./shieldflow_ledger_v2.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TransactionLedger(Base):
    __tablename__ = "transaction_ledger"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(64), unique=True, index=True)
    merchant_id = Column(String(64), default="acc_default")
    amount = Column(Float, default=0.0)
    currency = Column(String(8), default="INR")
    customer_email = Column(String(128), default="")
    ip_address = Column(String(64), default="")
    risk_tier = Column(String(16), default="ALLOW")
    risk_score = Column(Integer, default=0)
    detected_anomalies = Column(Text, default="[]")
    reasoning = Column(Text, default="")
    pipeline_tier = Column(String(64), default="Tier 1")
    latency_ms = Column(Float, default=0.0)
    review_status = Column(String(32), default="AUTO_RESOLVED")
    analyst_notes = Column(Text, default="")
    created_at = Column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)


def log_transaction_verdict(payload, assessment, pipeline_tier: str, latency_ms: float):
    session = SessionLocal()
    try:
        tier_str = getattr(assessment.risk_tier, "value", str(assessment.risk_tier))
        initial_status = "PENDING_REVIEW" if tier_str in ["STEP_UP_OTP", "BLOCK"] else "AUTO_RESOLVED"
        
        record = TransactionLedger(
            transaction_id=str(payload.transaction_id),
            merchant_id=str(payload.merchant_id),
            amount=float(payload.amount),
            currency=str(payload.currency),
            customer_email=str(payload.customer_email),
            ip_address=str(payload.ip_address),
            risk_tier=tier_str,
            risk_score=int(assessment.risk_score),
            detected_anomalies=json.dumps(getattr(assessment, "detected_anomalies", [])),
            reasoning=str(getattr(assessment, "plain_text_reasoning", "")),
            pipeline_tier=str(pipeline_tier),
            latency_ms=float(latency_ms),
            review_status=initial_status,
            analyst_notes=""
        )
        session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"[DB Error] Logging failed: {e}")
    finally:
        session.close()


def update_review_decision(transaction_id: str, new_status: str, notes: str):
    session = SessionLocal()
    try:
        tx = session.query(TransactionLedger).filter(TransactionLedger.transaction_id == transaction_id).first()
        if tx:
            tx.review_status = new_status
            tx.analyst_notes = notes
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"[DB Error] Update failed: {e}")
        return False
    finally:
        session.close()
