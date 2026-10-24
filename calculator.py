"""Расчёты по ипотеке.

Модуль не зависит от Streamlit и Plotly: его можно использовать
в скриптах, тестах и любом другом интерфейсе.
"""

from __future__ import annotations

import calendar
import math
from dataclasses import dataclass, field, replace
from datetime import date
from typing import Literal

import pandas as pd

PaymentType = Literal["annuity", "differentiated"]

ANNUITY: PaymentType = "annuity"
DIFFERENTIATED: PaymentType = "differentiated"

PAYMENT_TYPES: dict[str, str] = {
    ANNUITY: "Аннуитетный",
    DIFFERENTIATED: "Дифференцированный",
}

MIN_TERM_MONTHS = 1
MAX_TERM_MONTHS = 600
MAX_ANNUAL_RATE = 100.0

SCHEDULE_COLUMNS: dict[str, str] = {
    "month": "Месяц",
    "payment_date": "Дата платежа",
    "payment": "Платёж",
    "interest": "Проценты",
    "principal": "Основной долг",
    "balance": "Остаток долга",
}


class ValidationError(ValueError):
    """Входные данные не прошли проверку."""


@dataclass(frozen=True)
class MortgageParams:
    """Параметры кредита в «сыром» виде.

    Проверка значений вынесена в :func:`validate`, чтобы интерфейс мог
    показать пользователю все ошибки сразу, а не первую из них.
    """

    price: float
    down_payment: float
    annual_rate: float
    term_months: int
    payment_type: PaymentType = ANNUITY
    start_date: date = field(default_factory=date.today)

    @property
    def loan_amount(self) -> float:
        """Сумма кредита: стоимость минус первоначальный взнос."""
        return round(self.price - self.down_payment, 2)

    @property
    def down_payment_ratio(self) -> float:
        """Доля первоначального взноса в процентах от стоимости."""
        if not _is_number(self.price) or self.price <= 0:
            return 0.0
        return self.down_payment / self.price * 100


@dataclass(frozen=True)
class MortgageResult:
    """Результат расчёта: график платежей и итоговые показатели."""

    params: MortgageParams
    schedule: pd.DataFrame
    monthly_payment: float
    last_payment: float
    min_payment: float
    max_payment: float
    total_paid: float
    total_interest: float
    total_principal: float
    overpayment_ratio: float

    @property
    def payment_label(self) -> str:
        """Подпись основного платежа для интерфейса."""
        if self.params.payment_type == DIFFERENTIATED:
            return "Первый платёж"
        return "Ежемесячный платёж"


def _is_number(value: object) -> bool:
    """True для конечного числа (bool и NaN отбрасываются)."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def validate(params: MortgageParams) -> list[str]:
    """Возвращает список ошибок. Пустой список — данные корректны."""
    errors: list[str] = []

    price_ok = _is_number(params.price)
    if not price_ok:
        errors.append("Стоимость недвижимости должна быть числом.")
    elif params.price <= 0:
        errors.append("Стоимость недвижимости должна быть больше нуля.")

    down_payment_ok = _is_number(params.down_payment)
    if not down_payment_ok:
        errors.append("Первоначальный взнос должен быть числом.")
    elif params.down_payment < 0:
        errors.append("Первоначальный взнос не может быть отрицательным.")
    elif price_ok and params.price > 0 and params.down_payment >= params.price:
        errors.append(
            "Первоначальный взнос должен быть меньше стоимости недвижимости."
        )

    if not _is_number(params.annual_rate):
        errors.append("Годовая ставка должна быть числом.")
    elif not 0 <= params.annual_rate <= MAX_ANNUAL_RATE:
        errors.append(
            f"Годовая ставка должна быть в диапазоне от 0 до {MAX_ANNUAL_RATE:.0f}%."
        )

    if isinstance(params.term_months, bool) or not isinstance(params.term_months, int):
        errors.append("Срок кредита должен быть целым числом месяцев.")
    elif not MIN_TERM_MONTHS <= params.term_months <= MAX_TERM_MONTHS:
        errors.append(
            f"Срок кредита должен быть от {MIN_TERM_MONTHS} до "
            f"{MAX_TERM_MONTHS} месяцев."
        )

    if params.payment_type not in PAYMENT_TYPES:
        errors.append("Неизвестный тип платежа.")

    if not isinstance(params.start_date, date):
        errors.append("Дата первого платежа должна быть датой.")

    return errors


def calculate(params: MortgageParams) -> MortgageResult:
    """Строит график платежей и итоговые показатели.

    Raises:
        ValidationError: если параметры некорректны.
    """
    errors = validate(params)
    if errors:
        raise ValidationError(" ".join(errors))

    if params.payment_type == ANNUITY:
        schedule = _annuity_schedule(params)
    else:
        schedule = _differentiated_schedule(params)

    return _build_result(params, schedule)


def compare_payment_types(params: MortgageParams) -> pd.DataFrame:
    """Сравнивает аннуитет и дифференцированный платёж при прочих равных."""
    rows: list[dict[str, object]] = []
    for payment_type, label in PAYMENT_TYPES.items():
        try:
            result = calculate(replace(params, payment_type=payment_type))
        except ValidationError:
            continue
        rows.append(
            {
                "payment_type": payment_type,
                "label": label,
                "first_payment": result.monthly_payment,
                "last_payment": result.last_payment,
                "max_payment": result.max_payment,
                "total_paid": result.total_paid,
                "total_interest": result.total_interest,
                "overpayment_ratio": result.overpayment_ratio,
            }
        )
    return pd.DataFrame(rows)


def _annuity_schedule(params: MortgageParams) -> pd.DataFrame:
    """Аннуитет: одинаковый платёж, последний месяц корректируется."""
    loan = params.loan_amount
    months = params.term_months
    monthly_rate = params.annual_rate / 100 / 12

    if monthly_rate == 0:
        base_payment = loan / months
    else:
        base_payment = loan * monthly_rate / (1 - (1 + monthly_rate) ** -months)
    base_payment = round(base_payment, 2)

    balance = loan
    rows: list[dict[str, object]] = []

    for month in range(1, months + 1):
        interest = round(balance * monthly_rate, 2)

        if month == months:
            principal = round(balance, 2)
            payment = round(principal + interest, 2)
        else:
            payment = base_payment
            principal = round(payment - interest, 2)
            # Страховка от накопленной погрешности округления.
            if principal >= balance:
                principal = round(balance, 2)
                payment = round(principal + interest, 2)

        balance = round(balance - principal, 2)
        rows.append(_schedule_row(params, month, payment, interest, principal, balance))

    return pd.DataFrame(rows)


def _differentiated_schedule(params: MortgageParams) -> pd.DataFrame:
    """Дифференцированный платёж: основной долг равными частями."""
    loan = params.loan_amount
    months = params.term_months
    monthly_rate = params.annual_rate / 100 / 12
    principal_part = round(loan / months, 2)

    balance = loan
    rows: list[dict[str, object]] = []

    for month in range(1, months + 1):
        interest = round(balance * monthly_rate, 2)
        if month == months:
            principal = round(balance, 2)
        else:
            principal = min(principal_part, round(balance, 2))

        payment = round(principal + interest, 2)
        balance = round(balance - principal, 2)
        rows.append(_schedule_row(params, month, payment, interest, principal, balance))

    return pd.DataFrame(rows)


def _schedule_row(
    params: MortgageParams,
    month: int,
    payment: float,
    interest: float,
    principal: float,
    balance: float,
) -> dict[str, object]:
    return {
        "month": month,
        "payment_date": _add_months(params.start_date, month - 1),
        "payment": payment,
        "interest": interest,
        "principal": principal,
        "balance": balance,
    }


def _build_result(params: MortgageParams, schedule: pd.DataFrame) -> MortgageResult:
    loan = params.loan_amount
    total_interest = round(float(schedule["interest"].sum()), 2)
    total_paid = round(float(schedule["payment"].sum()), 2)
    total_principal = round(float(schedule["principal"].sum()), 2)

    return MortgageResult(
        params=params,
        schedule=schedule,
        monthly_payment=float(schedule["payment"].iloc[0]),
        last_payment=float(schedule["payment"].iloc[-1]),
        min_payment=float(schedule["payment"].min()),
        max_payment=float(schedule["payment"].max()),
        total_paid=total_paid,
        total_interest=total_interest,
        total_principal=total_principal,
        overpayment_ratio=round(total_interest / loan * 100, 2) if loan > 0 else 0.0,
    )


def _add_months(start: date, months: int) -> date:
    """Прибавляет месяцы, подрезая день до конца месяца."""
    year, month_index = divmod(start.month - 1 + months, 12)
    year += start.year
    month = month_index + 1
    day = min(start.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)
