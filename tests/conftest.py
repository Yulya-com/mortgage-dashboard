"""Общие фикстуры и настройка путей импорта."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from calculator import MortgageParams  # noqa: E402


@pytest.fixture
def base_params() -> MortgageParams:
    """Типовой кредит: 12 млн, взнос 2,4 млн, 12,5%, 20 лет."""
    return MortgageParams(
        price=12_000_000,
        down_payment=2_400_000,
        annual_rate=12.5,
        term_months=240,
        payment_type="annuity",
        start_date=date(2026, 1, 15),
    )
