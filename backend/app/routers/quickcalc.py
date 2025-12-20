# backend/app/routers/quickcalc.py
"""
FastAPI роутер для QuickCalc.
Пример использования: в основном приложении (например backend/main.py) сделать:
    from fastapi import FastAPI
    from backend.app.routers.quickcalc import router as quickcalc_router
    app = FastAPI()
    app.include_router(quickcalc_router)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, PositiveInt, NonNegativeFloat

from ..quickcalc import QuickCalc

router = APIRouter(prefix="/quickcalc", tags=["quickcalc"])
_calc = QuickCalc()


class CalculateRequest(BaseModel):
    loan_amount: NonNegativeFloat = Field(..., description="Сумма кредита в рублях")
    annual_rate: NonNegativeFloat = Field(..., description="Годовая ставка в %")
    loan_term_years: PositiveInt = Field(..., description="Срок в годах (целое положительное)")
    payment_type: Optional[str] = Field("annuity", description="Тип платежа: 'annuity' или 'diff'")


class ScheduleRequest(BaseModel):
    loan_amount: NonNegativeFloat = Field(..., description="Сумма кредита в рублях")
    annual_rate: NonNegativeFloat = Field(..., description="Годовая ставка в %")
    loan_term_years: PositiveInt = Field(..., description="Срок в годах (целое положительное)")
    payment_type: Optional[str] = Field("annuity", description="Тип платежа: 'annuity' или 'diff'")
    start_date: Optional[datetime] = Field(None, description="Дата начала (ISO формат), если не передана — текущая дата")


class RefinanceRequest(BaseModel):
    remaining_debt: NonNegativeFloat = Field(..., description="Остаток долга в рублях")
    current_rate: NonNegativeFloat = Field(..., description="Текущая годовая ставка %")
    remaining_months: PositiveInt = Field(..., description="Остаток месяцев выплат")
    new_rate: NonNegativeFloat = Field(..., description="Новая годовая ставка %")
    new_term_years: Optional[PositiveInt] = Field(None, description="Новый срок в годах (опционально)")
    early_repayment: Optional[NonNegativeFloat] = Field(0.0, description="Сумма досрочного погашения при рефинансировании")


@router.post("/calculate", summary="Рассчитать ежемесячный платёж")
def calculate(req: CalculateRequest) -> Dict[str, Any]:
    try:
        result = _calc.calculate_monthly_payment(
            loan_amount=req.loan_amount,
            annual_rate=req.annual_rate,
            loan_term_years=req.loan_term_years,
            payment_type=req.payment_type or "annuity",
        )
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/schedule", summary="Получить график платежей")
def schedule(req: ScheduleRequest) -> Dict[str, List[Dict[str, Any]]]:
    try:
        schedule_list = _calc.generate_payment_schedule(
            loan_amount=req.loan_amount,
            annual_rate=req.annual_rate,
            loan_term_years=req.loan_term_years,
            start_date=req.start_date,
            payment_type=req.payment_type or "annuity",
        )
        return {"schedule": schedule_list}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/refinance", summary="Рассчитать выгоду рефинансирования")
def refinance(req: RefinanceRequest) -> Dict[str, Any]:
    current_loan = {
        "remaining_debt": float(req.remaining_debt),
        "annual_rate": float(req.current_rate),
        "remaining_months": int(req.remaining_months),
    }
    try:
        result = _calc.refinancing_benefit(
            current_loan=current_loan,
            new_rate=float(req.new_rate),
            new_term_years=int(req.new_term_years) if req.new_term_years is not None else None,
            early_repayment=float(req.early_repayment or 0.0),
        )
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/examples", summary="Примеры расчётов")
def examples() -> Dict[str, Any]:
    examples_data = [
        {"name": "Ипотека на квартиру", "amount": 3_000_000, "rate": 7.5, "years": 20, "type": "annuity"},
        {"name": "Автокредит", "amount": 1_500_000, "rate": 12.9, "years": 5, "type": "annuity"},
        {"name": "Потребительский кредит", "amount": 500_000, "rate": 15.5, "years": 3, "type": "diff"},
    ]

    results = []
    for ex in examples_data:
        res = _calc.calculate_monthly_payment(
            loan_amount=ex["amount"],
            annual_rate=ex["rate"],
            loan_term_years=ex["years"],
            payment_type=ex["type"],
        )
        results.append({"example": ex, "result": res})

    return {"examples": results}
