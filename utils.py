"""Форматирование значений и экспорт графика платежей."""

from __future__ import annotations

import pandas as pd

from calculator import SCHEDULE_COLUMNS, MortgageResult


def format_money(value: float, decimals: int = 0) -> str:
    """Форматирует сумму в рублях: «33 034 ₽» или «33 034,44 ₽»."""
    if value is None or pd.isna(value):
        return "—"
    if decimals:
        text = f"{value:,.{decimals}f}".replace(",", " ").replace(".", ",")
    else:
        text = f"{value:,.0f}".replace(",", " ")
    return f"{text} ₽"


def format_percent(value: float, decimals: int = 1) -> str:
    """Форматирует процент с запятой в качестве разделителя."""
    if value is None or pd.isna(value):
        return "—"
    return f"{value:.{decimals}f}".replace(".", ",") + " %"


def schedule_for_display(result: MortgageResult) -> pd.DataFrame:
    """Таблица платежей с русскими колонками и датами строкой."""
    table = result.schedule.rename(columns=SCHEDULE_COLUMNS).copy()
    table["Дата платежа"] = pd.to_datetime(table["Дата платежа"]).dt.strftime(
        "%d.%m.%Y"
    )
    return table


def schedule_to_csv(table: pd.DataFrame) -> bytes:
    """CSV для Excel: разделитель «;», десятичная запятая, BOM UTF-8."""
    csv_text = table.to_csv(
        index=False,
        sep=";",
        decimal=",",
        float_format="%.2f",
        lineterminator="\r\n",
    )
    return ("\ufeff" + csv_text).encode("utf-8")
