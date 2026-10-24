"""Тесты расчётов: формулы, границы, валидация."""

from __future__ import annotations

from dataclasses import replace
from datetime import date

import pytest

from calculator import (
    ANNUITY,
    DIFFERENTIATED,
    MAX_TERM_MONTHS,
    MortgageParams,
    ValidationError,
    calculate,
    compare_payment_types,
    validate,
)
from utils import format_money, format_percent, schedule_for_display, schedule_to_csv


def test_annuity_payment_matches_formula() -> None:
    """1 млн под 12% на год: платёж ≈ 88 848,79 ₽."""
    params = MortgageParams(
        price=1_000_000,
        down_payment=0,
        annual_rate=12,
        term_months=12,
        start_date=date(2026, 1, 31),
    )
    result = calculate(params)

    assert result.monthly_payment == pytest.approx(88_848.79, abs=0.5)
    assert result.last_payment == pytest.approx(result.monthly_payment, abs=0.5)


def test_loan_amount_and_down_payment_ratio(base_params: MortgageParams) -> None:
    assert base_params.loan_amount == 9_600_000
    assert base_params.down_payment_ratio == pytest.approx(20.0)


def test_schedule_is_balanced(base_params: MortgageParams) -> None:
    """Сумма основного долга равна кредиту, остаток в конце — ноль."""
    result = calculate(base_params)
    schedule = result.schedule

    assert len(schedule) == base_params.term_months
    assert schedule["principal"].sum() == pytest.approx(9_600_000, abs=0.5)
    assert schedule["balance"].iloc[-1] == pytest.approx(0, abs=0.01)
    assert result.total_paid == pytest.approx(
        result.total_principal + result.total_interest, abs=1
    )


def test_balance_decreases_monotonically(base_params: MortgageParams) -> None:
    balances = calculate(base_params).schedule["balance"].tolist()
    assert all(later <= earlier for earlier, later in zip(balances, balances[1:]))


def test_zero_rate_splits_loan_evenly(base_params: MortgageParams) -> None:
    result = calculate(replace(base_params, annual_rate=0))
    assert result.total_interest == 0
    assert result.monthly_payment == pytest.approx(40_000, abs=0.01)
    assert result.total_paid == pytest.approx(9_600_000, abs=1)


def test_differentiated_payment_decreases(base_params: MortgageParams) -> None:
    result = calculate(replace(base_params, payment_type=DIFFERENTIATED))
    payments = result.schedule["payment"]

    assert result.max_payment == pytest.approx(payments.iloc[0])
    assert result.min_payment == pytest.approx(payments.iloc[-1])
    assert payments.iloc[0] > payments.iloc[-1]
    assert result.schedule["principal"].sum() == pytest.approx(9_600_000, abs=1)
    assert result.schedule["balance"].iloc[-1] == pytest.approx(0, abs=0.01)


def test_differentiated_cheaper_than_annuity(base_params: MortgageParams) -> None:
    annuity = calculate(base_params)
    differentiated = calculate(replace(base_params, payment_type=DIFFERENTIATED))

    assert differentiated.total_interest < annuity.total_interest
    assert differentiated.max_payment > annuity.monthly_payment


def test_single_month_term() -> None:
    params = MortgageParams(
        price=100_000,
        down_payment=0,
        annual_rate=12,
        term_months=1,
        start_date=date(2026, 3, 1),
    )
    result = calculate(params)
    assert len(result.schedule) == 1
    assert result.total_interest == pytest.approx(1_000, abs=0.01)


def test_payment_dates_shift_monthly(base_params: MortgageParams) -> None:
    dates = calculate(base_params).schedule["payment_date"].tolist()
    assert dates[0] == date(2026, 1, 15)
    assert dates[1] == date(2026, 2, 15)
    assert dates[12] == date(2027, 1, 15)


def test_date_clamps_to_month_end() -> None:
    params = MortgageParams(
        price=500_000,
        down_payment=0,
        annual_rate=10,
        term_months=3,
        start_date=date(2026, 1, 31),
    )
    dates = calculate(params).schedule["payment_date"].tolist()
    assert dates == [date(2026, 1, 31), date(2026, 2, 28), date(2026, 3, 31)]


@pytest.mark.parametrize(
    ("overrides", "fragment"),
    [
        ({"price": 0}, "Стоимость"),
        ({"price": -1}, "Стоимость"),
        ({"price": float("nan")}, "числом"),
        ({"down_payment": -5}, "отрицательным"),
        ({"down_payment": 12_000_000}, "меньше стоимости"),
        ({"annual_rate": -1}, "ставка"),
        ({"annual_rate": 150}, "ставка"),
        ({"term_months": 0}, "Срок"),
        ({"term_months": MAX_TERM_MONTHS + 1}, "Срок"),
        ({"payment_type": "unknown"}, "тип платежа"),
    ],
)
def test_validation_reports_errors(base_params: MortgageParams, overrides, fragment):
    errors = validate(replace(base_params, **overrides))
    assert errors
    assert any(fragment.lower() in error.lower() for error in errors)


def test_calculate_raises_on_invalid(base_params: MortgageParams) -> None:
    with pytest.raises(ValidationError):
        calculate(replace(base_params, down_payment=base_params.price))


def test_valid_params_have_no_errors(base_params: MortgageParams) -> None:
    assert validate(base_params) == []


def test_compare_payment_types_returns_both(base_params: MortgageParams) -> None:
    comparison = compare_payment_types(base_params)
    assert set(comparison["payment_type"]) == {ANNUITY, DIFFERENTIATED}
    assert (comparison["total_interest"] > 0).all()


def test_display_table_and_csv(base_params: MortgageParams) -> None:
    result = calculate(base_params)
    table = schedule_for_display(result)

    assert list(table.columns) == [
        "Месяц",
        "Дата платежа",
        "Платёж",
        "Проценты",
        "Основной долг",
        "Остаток долга",
    ]
    assert table["Дата платежа"].iloc[0] == "15.01.2026"

    csv_bytes = schedule_to_csv(table)
    assert csv_bytes.startswith(b"\xef\xbb\xbf")
    decoded = csv_bytes.decode("utf-8-sig")
    assert decoded.splitlines()[0].startswith("Месяц;Дата платежа")
    assert "15.01.2026" in decoded
    assert "109069,49" in decoded.replace(" ", "")


def test_formatting_helpers() -> None:
    assert format_money(1_234_567) == "1 234 567 ₽"
    assert format_money(1_234_567.5, 2) == "1 234 567,50 ₽"
    assert format_percent(12.345) == "12,3 %"
    assert format_money(None) == "—"
