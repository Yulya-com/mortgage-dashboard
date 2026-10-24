"""Тесты визуализации: фигуры строятся и подчиняются теме."""

from __future__ import annotations

from datetime import date

import plotly.graph_objects as go

from calculator import MortgageParams, calculate
from charts import (
    balance_chart,
    build_all_charts,
    payment_structure_chart,
    payment_type_comparison_chart,
    total_cost_chart,
)
from theme import DARK, LIGHT


def _result(payment_type: str = "annuity"):
    return calculate(
        MortgageParams(
            price=10_000_000,
            down_payment=2_000_000,
            annual_rate=11,
            term_months=120,
            payment_type=payment_type,
            start_date=date(2026, 1, 10),
        )
    )


def test_all_charts_are_figures() -> None:
    figures = build_all_charts(_result(), LIGHT)
    assert set(figures) == {"balance", "structure", "cost", "comparison"}
    assert all(isinstance(fig, go.Figure) for fig in figures.values())


def test_balance_chart_has_two_traces() -> None:
    fig = balance_chart(_result(), DARK)
    assert len(fig.data) == 2
    assert fig.data[0].name == "Остаток долга"
    assert len(fig.data[0].x) == 120


def test_structure_chart_is_stacked() -> None:
    fig = payment_structure_chart(_result(), LIGHT)
    assert fig.layout.barmode == "stack"
    assert len(fig.data) == 2


def test_cost_chart_uses_totals() -> None:
    result = _result()
    fig = total_cost_chart(result, LIGHT)
    assert list(fig.data[0].values) == [
        result.total_principal,
        result.total_interest,
    ]


def test_comparison_chart_has_both_types() -> None:
    fig = payment_type_comparison_chart(_result(), LIGHT)
    assert len(fig.data) == 2
    names = {trace.name for trace in fig.data}
    assert names == {"Аннуитетный", "Дифференцированный"}


def test_dark_theme_changes_colors() -> None:
    light = balance_chart(_result(), LIGHT)
    dark = balance_chart(_result(), DARK)
    assert light.data[0].line.color != dark.data[0].line.color
    assert dark.layout.paper_bgcolor == "rgba(0,0,0,0)"


def test_theme_changes_all_chart_palettes() -> None:
    """Все четыре графика перекрашиваются при смене темы."""
    light = build_all_charts(_result(), LIGHT)
    dark = build_all_charts(_result(), DARK)

    for name in light:
        assert light[name].layout.font.color != dark[name].layout.font.color, name

    assert light["balance"].layout.xaxis.linecolor != dark["balance"].layout.xaxis.linecolor
    assert light["structure"].data[0].marker.color != dark["structure"].data[0].marker.color
    assert light["cost"].data[0].marker.colors != dark["cost"].data[0].marker.colors
    assert light["comparison"].data[1].line.color != dark["comparison"].data[1].line.color


def test_charts_react_to_new_input() -> None:
    """Новые параметры дают другие данные, а не прежнюю фигуру."""
    base = build_all_charts(_result(), LIGHT)
    changed = build_all_charts(
        calculate(
            MortgageParams(
                price=10_000_000,
                down_payment=2_000_000,
                annual_rate=11,
                term_months=60,
                payment_type="annuity",
                start_date=date(2026, 1, 10),
            )
        ),
        LIGHT,
    )

    assert len(base["balance"].data[0].x) == 120
    assert len(changed["balance"].data[0].x) == 60
    assert base["cost"].data[0].values != changed["cost"].data[0].values
    assert base["comparison"].data[0].x != changed["comparison"].data[0].x


def test_charts_react_to_payment_type() -> None:
    """Смена типа платежа меняет форму столбцов и итоги."""
    annuity = payment_structure_chart(_result("annuity"), LIGHT)
    differentiated = payment_structure_chart(_result("differentiated"), LIGHT)

    assert list(annuity.data[0].y) != list(differentiated.data[0].y)
    assert list(annuity.data[1].y) != list(differentiated.data[1].y)


def test_money_axis_uses_russian_labels() -> None:
    fig = balance_chart(_result(), LIGHT)
    assert fig.layout.yaxis.tickvals[0] == 0
    assert fig.layout.yaxis.ticktext[1] == "1,5 млн ₽"
