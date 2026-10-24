"""Интерактивные графики Plotly.

Модуль не зависит от Streamlit: функции принимают результат расчёта
и тему, возвращают готовую фигуру.
"""

from __future__ import annotations

import math

import plotly.graph_objects as go

from calculator import (
    ANNUITY,
    DIFFERENTIATED,
    PAYMENT_TYPES,
    MortgageResult,
    compare_payment_types,
)
from theme import Theme


def _base_layout(theme: Theme, title: str, height: int = 380) -> dict:
    """Общие настройки оформления под выбранную тему."""
    return {
        "title": {"text": title, "font": {"size": 16, "color": theme.text}},
        "height": height,
        "margin": {"l": 10, "r": 10, "t": 48, "b": 10},
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {"color": theme.text, "family": "Inter, Segoe UI, sans-serif"},
        "hoverlabel": {
            "bgcolor": theme.surface,
            "bordercolor": theme.border,
            "font": {"color": theme.text},
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
            "font": {"color": theme.muted},
        },
    }


def _style_axes(fig: go.Figure, theme: Theme) -> None:
    """Сетка и подписи осей в цветах темы."""
    fig.update_xaxes(
        showgrid=False,
        linecolor=theme.border,
        tickfont={"color": theme.muted},
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True,
        gridcolor=theme.grid,
        linecolor=theme.border,
        tickfont={"color": theme.muted},
        zeroline=False,
    )


def _money_scale(max_value: float) -> tuple[float, str, int]:
    """Подбирает делитель и подпись для оси: млн / тыс / рубли."""
    if max_value >= 1_000_000:
        return 1_000_000, " млн ₽", 1
    if max_value >= 10_000:
        return 1_000, " тыс ₽", 0
    return 1, " ₽", 0


def _nice_step(max_value: float, target_ticks: int = 6) -> float:
    """Круглый шаг сетки: 1, 1.5, 2, 2.5 или 5 на нужном порядке."""
    if max_value <= 0:
        return 1.0
    raw = max_value / target_ticks
    magnitude = 10 ** math.floor(math.log10(raw))
    for multiplier in (1, 1.5, 2, 2.5, 5, 10):
        step = multiplier * magnitude
        if step >= raw:
            return step
    return 10 * magnitude


def _money_axis(fig: go.Figure, max_value: float) -> None:
    """Русские подписи оси Y: «2,5 млн ₽» вместо «2.5M ₽»."""
    divisor, suffix, decimals = _money_scale(max_value)
    step = _nice_step(max_value / divisor)
    count = int(max_value / divisor / step) + 1

    tickvals = [index * step * divisor for index in range(count + 1) if index * step <= max_value / divisor + 1e-9]
    ticktext = []
    for value in tickvals:
        scaled = value / divisor
        label = f"{scaled:.{decimals}f}".replace(".", ",")
        if decimals and label.endswith(",0"):
            label = label[:-2]
        ticktext.append(f"{label}{suffix}")

    fig.update_yaxes(tickvals=tickvals, ticktext=ticktext)


def balance_chart(result: MortgageResult, theme: Theme) -> go.Figure:
    """Остаток долга и накопленные выплаты по месяцам."""
    schedule = result.schedule
    paid_principal = schedule["principal"].cumsum()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=schedule["month"],
            y=schedule["balance"],
            name="Остаток долга",
            mode="lines",
            line={"color": theme.primary, "width": 2.5},
            fill="tozeroy",
            fillcolor=theme.primary_soft,
            hovertemplate="Месяц %{x}<br>Остаток: %{y:,.0f} ₽<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=schedule["month"],
            y=paid_principal,
            name="Выплачено основного долга",
            mode="lines",
            line={"color": theme.accent, "width": 2, "dash": "dot"},
            hovertemplate="Месяц %{x}<br>Выплачено: %{y:,.0f} ₽<extra></extra>",
        )
    )

    fig.update_layout(**_base_layout(theme, "Остаток долга по месяцам"))
    _style_axes(fig, theme)
    _money_axis(fig, float(schedule["balance"].max()))
    fig.update_xaxes(title_text="Месяц", title_font={"color": theme.muted})
    return fig


def payment_structure_chart(result: MortgageResult, theme: Theme) -> go.Figure:
    """Структура каждого платежа: проценты и основной долг."""
    schedule = result.schedule

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=schedule["month"],
            y=schedule["principal"],
            name="Основной долг",
            marker={"color": theme.primary},
            hovertemplate="Месяц %{x}<br>Основной долг: %{y:,.0f} ₽<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            x=schedule["month"],
            y=schedule["interest"],
            name="Проценты",
            marker={"color": theme.secondary},
            hovertemplate="Месяц %{x}<br>Проценты: %{y:,.0f} ₽<extra></extra>",
        )
    )

    fig.update_layout(
        **_base_layout(theme, "Из чего состоит платёж"),
        barmode="stack",
        bargap=0.15,
    )
    _style_axes(fig, theme)
    _money_axis(fig, float(schedule["payment"].max()))
    fig.update_xaxes(title_text="Месяц", title_font={"color": theme.muted})
    return fig


def total_cost_chart(result: MortgageResult, theme: Theme) -> go.Figure:
    """Кольцевая диаграмма: тело кредита против переплаты."""
    fig = go.Figure(
        go.Pie(
            labels=["Основной долг", "Переплата по процентам"],
            values=[result.total_principal, result.total_interest],
            hole=0.62,
            marker={"colors": [theme.primary, theme.secondary]},
            textinfo="percent",
            textfont={"color": theme.text, "size": 13},
            hovertemplate="%{label}<br>%{value:,.0f} ₽<br>%{percent}<extra></extra>",
            sort=False,
        )
    )

    total = f"{result.total_paid:,.0f}".replace(",", " ")
    fig.update_layout(
        **_base_layout(theme, "Структура общей стоимости", height=340),
        annotations=[
            {
                "text": (
                    f"<span style='font-size:12px;color:{theme.muted}'>Всего</span><br>"
                    f"<b style='font-size:17px;color:{theme.text}'>{total} ₽</b>"
                ),
                "showarrow": False,
                "x": 0.5,
                "y": 0.5,
                "xref": "paper",
                "yref": "paper",
                "font": {"color": theme.text},
            }
        ],
    )
    return fig


def payment_type_comparison_chart(result: MortgageResult, theme: Theme) -> go.Figure:
    """Сравнение аннуитета и дифференцированного платежа."""
    comparison = compare_payment_types(result.params)
    colors = {ANNUITY: theme.primary, DIFFERENTIATED: theme.accent}

    fig = go.Figure()
    for _, row in comparison.iterrows():
        payment_type = row["payment_type"]
        fig.add_trace(
            go.Scatter(
                x=[1, result.params.term_months],
                y=[row["first_payment"], row["last_payment"]],
                name=PAYMENT_TYPES[payment_type],
                mode="lines+markers",
                line={"color": colors.get(payment_type, theme.primary), "width": 2.5},
                hovertemplate=(
                    f"{PAYMENT_TYPES[payment_type]}<br>"
                    "Месяц %{x}<br>Платёж: %{y:,.0f} ₽<extra></extra>"
                ),
            )
        )

    fig.update_layout(**_base_layout(theme, "Платёж в начале и в конце срока"))
    _style_axes(fig, theme)
    _money_axis(fig, float(comparison["first_payment"].max()))
    fig.update_xaxes(
        title_text="Месяц",
        title_font={"color": theme.muted},
        range=[0, result.params.term_months + 1],
        dtick=max(1, result.params.term_months // 12),
    )
    return fig


def comparison_table_columns() -> dict[str, str]:
    """Русские подписи для таблицы сравнения типов платежа."""
    return {
        "label": "Тип платежа",
        "first_payment": "Первый платёж",
        "last_payment": "Последний платёж",
        "total_interest": "Переплата",
        "total_paid": "Всего выплат",
    }


def build_all_charts(result: MortgageResult, theme: Theme) -> dict[str, go.Figure]:
    """Все графики одним словарём — удобно для вкладок интерфейса."""
    return {
        "balance": balance_chart(result, theme),
        "structure": payment_structure_chart(result, theme),
        "cost": total_cost_chart(result, theme),
        "comparison": payment_type_comparison_chart(result, theme),
    }
