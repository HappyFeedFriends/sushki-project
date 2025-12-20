# backend/app/quickcalc.py
"""
QuickCalc — кредитный калькулятор для интеграции в backend/app.
Модуль не использует CLI; функции возвращают структуры данных JSON-serializable.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import List, Dict, Optional

class QuickCalc:
    """Встроенный кредитный калькулятор (без интерактивности)."""

    def __init__(self) -> None:
        self.loan_history: List[Dict] = []

    def _validate_positive(self, **kwargs) -> None:
        for name, value in kwargs.items():
            if value is None:
                raise ValueError(f"'{name}' is required")
            if isinstance(value, (int, float)) and value < 0:
                raise ValueError(f"'{name}' must be non-negative")

    def calculate_monthly_payment(
        self,
        loan_amount: float,
        annual_rate: float,
        loan_term_years: int,
        payment_type: str = "annuity",
    ) -> Dict:
        """
        Рассчитать ежемесячный платёж и общие показатели.
        payment_type: "annuity" или "diff"
        Возвращает словарь с результатами.
        """
        self._validate_positive(loan_amount=loan_amount, annual_rate=annual_rate, loan_term_years=loan_term_years)

        if loan_term_years <= 0:
            raise ValueError("loan_term_years must be > 0")

        pt = (payment_type or "annuity").lower()
        if pt not in ("annuity", "diff"):
            raise ValueError("payment_type must be 'annuity' or 'diff'")

        monthly_rate = annual_rate / 100.0 / 12.0
        months = int(loan_term_years * 12)

        if pt == "annuity":
            if monthly_rate == 0:
                monthly_payment = loan_amount / months
            else:
                factor = math.pow(1 + monthly_rate, months)
                monthly_payment = loan_amount * monthly_rate * factor / (factor - 1)

            total_payment = monthly_payment * months
            overpayment = total_payment - loan_amount

            result = {
                "monthly_payment": round(monthly_payment, 2),
                "total_payment": round(total_payment, 2),
                "overpayment": round(overpayment, 2),
                "payment_type": "аннуитетный",
                "details": f"Ежемесячный платёж: {round(monthly_payment, 2)} ₽",
                "months": months,
                "annual_rate": annual_rate,
                "loan_amount": loan_amount,
            }
        else:
            payments: List[float] = []
            remaining_debt = loan_amount
            main_debt_part = loan_amount / months
            total_payment = 0.0

            for month in range(1, months + 1):
                interest_part = remaining_debt * monthly_rate
                monthly_payment = main_debt_part + interest_part
                total_payment += monthly_payment
                payments.append(monthly_payment)
                remaining_debt -= main_debt_part

            first_payment = payments[0] if payments else 0.0
            last_payment = payments[-1] if payments else 0.0
            avg_payment = total_payment / months if months else 0.0
            overpayment = total_payment - loan_amount

            result = {
                "first_payment": round(first_payment, 2),
                "last_payment": round(last_payment, 2),
                "avg_payment": round(avg_payment, 2),
                "total_payment": round(total_payment, 2),
                "overpayment": round(overpayment, 2),
                "payment_type": "дифференцированный",
                "details": f"Первый платёж: {round(first_payment, 2)} ₽, последний: {round(last_payment, 2)} ₽",
                "months": months,
                "annual_rate": annual_rate,
                "loan_amount": loan_amount,
            }

        self.loan_history.append({"timestamp": datetime.utcnow().isoformat(), "result": result})
        return result

    def generate_payment_schedule(
        self,
        loan_amount: float,
        annual_rate: float,
        loan_term_years: int,
        start_date: Optional[datetime] = None,
        payment_type: str = "annuity",
    ) -> List[Dict]:
        """
        Вернуть график платежей (список словарей).
        Элемент: {month, date(DD.MM.YYYY), payment, main_debt, interest, remaining_debt}
        """
        self._validate_positive(loan_amount=loan_amount, annual_rate=annual_rate, loan_term_years=loan_term_years)
        if loan_term_years <= 0:
            raise ValueError("loan_term_years must be > 0")

        pt = (payment_type or "annuity").lower()
        if pt not in ("annuity", "diff"):
            raise ValueError("payment_type must be 'annuity' or 'diff'")

        if start_date is None:
            start_date = datetime.now()

        monthly_rate = annual_rate / 100.0 / 12.0
        months = int(loan_term_years * 12)

        schedule: List[Dict] = []
        remaining_debt = loan_amount

        if pt == "annuity":
            if monthly_rate == 0:
                monthly_payment = loan_amount / months
            else:
                factor = math.pow(1 + monthly_rate, months)
                monthly_payment = loan_amount * monthly_rate * factor / (factor - 1)

            for month in range(1, months + 1):
                interest_part = remaining_debt * monthly_rate
                main_debt_part = monthly_payment - interest_part

                if month == months:
                    main_debt_part = remaining_debt
                    monthly_payment = main_debt_part + interest_part

                remaining_debt -= main_debt_part
                payment_date = start_date + timedelta(days=30 * month)

                schedule.append({
                    "month": month,
                    "date": payment_date.strftime("%d.%m.%Y"),
                    "payment": round(monthly_payment, 2),
                    "main_debt": round(main_debt_part, 2),
                    "interest": round(interest_part, 2),
                    "remaining_debt": round(max(remaining_debt, 0.0), 2),
                })
        else:
            main_debt_part = loan_amount / months
            for month in range(1, months + 1):
                interest_part = remaining_debt * monthly_rate
                monthly_payment = main_debt_part + interest_part
                remaining_debt -= main_debt_part
                payment_date = start_date + timedelta(days=30 * month)

                schedule.append({
                    "month": month,
                    "date": payment_date.strftime("%d.%m.%Y"),
                    "payment": round(monthly_payment, 2),
                    "main_debt": round(main_debt_part, 2),
                    "interest": round(interest_part, 2),
                    "remaining_debt": round(max(remaining_debt, 0.0), 2),
                })

        return schedule

    def refinancing_benefit(
        self,
        current_loan: Dict,
        new_rate: float,
        new_term_years: Optional[int] = None,
        early_repayment: float = 0.0,
    ) -> Dict:
        """
        Рассчитать выгоду рефинансирования.
        current_loan: {'remaining_debt': float, 'annual_rate': float, 'remaining_months': int}
        """
        if not isinstance(current_loan, dict):
            raise ValueError("current_loan must be a dict with keys ['remaining_debt','annual_rate','remaining_months']")

        remaining_debt = float(current_loan.get("remaining_debt", 0.0))
        current_rate = float(current_loan.get("annual_rate", 0.0))
        remaining_months = int(current_loan.get("remaining_months", 0))

        self._validate_positive(remaining_debt=remaining_debt, current_rate=current_rate, remaining_months=remaining_months)
        if remaining_months <= 0:
            raise ValueError("remaining_months must be > 0")

        remaining_debt_after_prepay = max(remaining_debt - float(early_repayment or 0.0), 0.0)

        if new_term_years is None:
            new_term_years = remaining_months / 12.0

        new_months = int(new_term_years * 12)
        if new_months <= 0:
            raise ValueError("new_term_years leads to non-positive months")

        monthly_rate_current = current_rate / 100.0 / 12.0
        if monthly_rate_current == 0:
            current_monthly_payment = remaining_debt_after_prepay / remaining_months
        else:
            factor_cur = math.pow(1 + monthly_rate_current, remaining_months)
            current_monthly_payment = remaining_debt_after_prepay * monthly_rate_current * factor_cur / (factor_cur - 1)

        current_total_payment = current_monthly_payment * remaining_months

        monthly_rate_new = float(new_rate) / 100.0 / 12.0
        if monthly_rate_new == 0:
            new_monthly_payment = remaining_debt_after_prepay / new_months
        else:
            factor_new = math.pow(1 + monthly_rate_new, new_months)
            new_monthly_payment = remaining_debt_after_prepay * monthly_rate_new * factor_new / (factor_new - 1)

        new_total_payment = new_monthly_payment * new_months

        monthly_saving = current_monthly_payment - new_monthly_payment
        total_saving = current_total_payment - new_total_payment
        benefit_percentage = (total_saving / current_total_payment * 100.0) if current_total_payment > 0 else 0.0

        result = {
            "current_monthly_payment": round(current_monthly_payment, 2),
            "new_monthly_payment": round(new_monthly_payment, 2),
            "monthly_saving": round(monthly_saving, 2),
            "total_saving": round(total_saving, 2),
            "benefit_percentage": round(benefit_percentage, 2),
            "recommendation": "Рекомендуется рефинансирование" if total_saving > 0 else "Рефинансирование невыгодно",
            "remaining_debt_before": round(remaining_debt, 2),
            "remaining_debt_after_prepay": round(remaining_debt_after_prepay, 2),
            "remaining_months": remaining_months,
            "new_months": new_months,
        }

        self.loan_history.append({"timestamp": datetime.utcnow().isoformat(), "refinance_result": result})
        return result
