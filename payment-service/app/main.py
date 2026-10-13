from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from shared.fundit_common import (
    PaymentCreateRequest,
    PaymentMethod,
    PaymentRecord,
    PaymentStatus,
    RefundRequest,
    Role,
    Settings,
    commission_amount,
    fraud_risk_score,
    has_permission,
    payment_parallel_plan,
)

settings = Settings(service_name="payment-service", service_port=8502)
app = FastAPI(title="FundIt Payment Service", version="1.0.0")

payments: dict[str, PaymentRecord] = {}
project_income: dict[str, float] = {"PRJ-DEMO": 612_800.0}


class ProjectFailureRefundRequest(BaseModel):
    project_id: str
    reason: str = Field(min_length=3)
    actor_id: str
    actor_role: Role


class SimulateBatchRequest(BaseModel):
    total_payments: int = Field(ge=0)
    workers: int = Field(ge=1)


ProjectFailureRefundRequest.model_rebuild()
SimulateBatchRequest.model_rebuild()



def _assert_permission(role: Role, action: str) -> None:
    if not has_permission(role, action):
        raise HTTPException(status_code=403, detail=f"Role {role.value} cannot perform {action}")



def _now() -> datetime:
    return datetime.now(UTC)



def _commission_rate(method: PaymentMethod) -> float:
    return {
        PaymentMethod.CARD: 0.049,
        PaymentMethod.YOOMONEY: 0.039,
        PaymentMethod.EWALLET: 0.029,
    }[method]



def _processor_name(method: PaymentMethod) -> str:
    return {
        PaymentMethod.CARD: "Stripe",
        PaymentMethod.YOOMONEY: "YooMoney",
        PaymentMethod.EWALLET: "Wallet Gateway",
    }[method]



def _apply_refund(payment: PaymentRecord) -> None:
    if payment.status != PaymentStatus.SUCCEEDED:
        raise HTTPException(status_code=409, detail="Only succeeded payments can be refunded")
    payment.status = PaymentStatus.REFUNDED
    payment.refunded_at = _now()
    new_income = max(project_income.get(payment.project_id, 0.0) - payment.net_amount, 0.0)
    project_income[payment.project_id] = round(new_income, 2)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.post("/payments")
async def create_payment(request: PaymentCreateRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "payment:create")
    commission = commission_amount(request.amount, _commission_rate(request.method))
    net = round(request.amount - commission, 2)

    payment = PaymentRecord(
        payment_id=str(uuid4()),
        user_id=request.user_id,
        project_id=request.project_id,
        amount=request.amount,
        currency=request.currency,
        method=request.method,
        commission_fee=commission,
        net_amount=net,
        status=PaymentStatus.SUCCEEDED,
    )
    payments[payment.payment_id] = payment
    project_income[payment.project_id] = round(project_income.get(payment.project_id, 0.0) + net, 2)

    return {
        **payment.model_dump(mode="json"),
        "processor": _processor_name(request.method),
        "commission_rate": _commission_rate(request.method),
    }


@app.get("/payments/{payment_id}")
async def get_payment(payment_id: str) -> dict[str, Any]:
    payment = payments.get(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    return payment.model_dump(mode="json")


@app.get("/projects/{project_id}/payments")
async def list_project_payments(project_id: str, status: PaymentStatus | None = None) -> dict[str, Any]:
    items = [
        payment.model_dump(mode="json")
        for payment in payments.values()
        if payment.project_id == project_id and (status is None or payment.status == status)
    ]
    items.sort(key=lambda item: item["created_at"], reverse=True)
    total_gross = round(sum(item["amount"] for item in items), 2)
    total_fee = round(sum(item["commission_fee"] for item in items), 2)
    return {
        "items": items,
        "count": len(items),
        "total_gross": total_gross,
        "total_fee": total_fee,
        "total_net": round(total_gross - total_fee, 2),
    }


@app.post("/payments/{payment_id}/refund")
async def refund_payment(payment_id: str, request: RefundRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "payment:refund")
    payment = payments.get(payment_id)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found")

    _apply_refund(payment)
    return {
        "payment": payment.model_dump(mode="json"),
        "reason": request.reason,
        "actor_id": request.actor_id,
    }


@app.post("/refunds/project-failure")
async def refund_project_failure(request: ProjectFailureRefundRequest) -> dict[str, Any]:
    _assert_permission(request.actor_role, "payment:refund")
    refunded: list[dict[str, Any]] = []

    for payment in payments.values():
        if payment.project_id != request.project_id:
            continue
        if payment.status != PaymentStatus.SUCCEEDED:
            continue
        _apply_refund(payment)
        refunded.append(payment.model_dump(mode="json"))

    return {
        "project_id": request.project_id,
        "refunded_count": len(refunded),
        "items": refunded,
        "reason": request.reason,
    }


@app.get("/fees/estimate")
async def fee_estimate(amount: float, method: PaymentMethod = PaymentMethod.CARD) -> dict[str, Any]:
    fee = commission_amount(amount, _commission_rate(method))
    return {
        "amount": amount,
        "method": method,
        "commission_fee": fee,
        "net_amount": round(amount - fee, 2),
    }


@app.get("/payments/throughput/plan")
async def throughput_plan(target_per_minute: int = 1000, workers_hint: int = 8) -> dict[str, Any]:
    return payment_parallel_plan(target_per_minute, workers_hint)


@app.post("/payments/throughput/simulate")
async def simulate_batch(request: SimulateBatchRequest) -> dict[str, Any]:
    safe_workers = max(1, request.workers)
    batch = max(1, request.total_payments // safe_workers) if request.total_payments else 0
    return {
        "workers": safe_workers,
        "batch_size": batch,
        "total_payments": request.total_payments,
    }


@app.get("/fraud/check")
async def fraud_check(
    goal_amount: float,
    avg_pledge: float,
    pledge_spike_ratio: float,
    account_age_days: int,
) -> dict[str, Any]:
    score = fraud_risk_score(goal_amount, avg_pledge, pledge_spike_ratio, account_age_days)
    decision = "review" if score >= 0.65 else "allow"
    return {"risk_score": score, "decision": decision}
