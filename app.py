"""Ипотечный калькулятор с дашбордом.

Точка входа Streamlit. Здесь только интерфейс: расчёты берутся из
``calculator``, графики — из ``charts``, оформление — из ``theme``.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

import charts
from calculator import (
    ANNUITY,
    DIFFERENTIATED,
    MAX_ANNUAL_RATE,
    MAX_TERM_MONTHS,
    PAYMENT_TYPES,
    MortgageParams,
    MortgageResult,
    ValidationError,
    calculate,
    compare_payment_types,
    validate,
)
from theme import DEFAULT_THEME, THEMES, apply_theme, get_theme
from utils import format_money, format_percent, schedule_for_display, schedule_to_csv

st.set_page_config(
    page_title="Ипотечный калькулятор",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULTS = {
    "price": 12_000_000.0,
    "down_payment": 2_400_000.0,
    "annual_rate": 12.5,
    "term_years": 20,
    "payment_type": ANNUITY,
    "start_date": date.today().replace(day=1),
}

SECTION_CHARTS = "📊 Графики"
SECTION_SCHEDULE = "📋 График платежей"
SECTION_COMPARE = "⚖️ Сравнение"


def init_state() -> None:
    """Заполняет состояние значениями по умолчанию.

    Сброс выполняется здесь, до создания виджетов: менять состояние
    виджета после его отрисовки в том же прогоне нельзя.
    """
    if st.session_state.pop("_reset_requested", False):
        for key, value in DEFAULTS.items():
            st.session_state[key] = value

    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)
    st.session_state.setdefault("theme", DEFAULT_THEME)


def sidebar() -> None:
    """Панель параметров кредита и переключатель темы."""
    with st.sidebar:
        st.markdown("### 🎨 Тема оформления")
        st.radio(
            "Оформление",
            options=list(THEMES),
            format_func=lambda key: f"{THEMES[key].icon} {THEMES[key].label}",
            key="theme",
            horizontal=True,
            label_visibility="collapsed",
        )

        st.divider()
        st.markdown("### 🏠 Параметры кредита")

        st.number_input(
            "Стоимость недвижимости, ₽",
            min_value=0.0,
            step=100_000.0,
            format="%.0f",
            key="price",
            help="Полная цена объекта.",
        )
        st.number_input(
            "Первоначальный взнос, ₽",
            min_value=0.0,
            step=50_000.0,
            format="%.0f",
            key="down_payment",
            help="Сумма, которую вы платите сразу.",
        )

        price = st.session_state["price"]
        down = st.session_state["down_payment"]
        if price > 0 and 0 <= down < price:
            share = f"{down / price * 100:.1f}".replace(".", ",")
            st.caption(f"Взнос: {share}% · кредит {format_money(price - down)}")
        else:
            st.caption("Стоимость и взнос будут проверены при расчёте.")

        st.slider(
            "Годовая ставка, %",
            min_value=0.0,
            max_value=MAX_ANNUAL_RATE,
            step=0.1,
            key="annual_rate",
        )
        st.slider(
            "Срок, лет",
            min_value=1,
            max_value=MAX_TERM_MONTHS // 12,
            step=1,
            key="term_years",
        )
        st.radio(
            "Тип платежа",
            options=list(PAYMENT_TYPES),
            format_func=lambda key: PAYMENT_TYPES[key],
            key="payment_type",
            horizontal=True,
        )
        st.date_input("Дата первого платежа", key="start_date")

        st.divider()
        if st.button("🔄 Сбросить параметры", width="stretch"):
            st.session_state["_reset_requested"] = True
            st.rerun()

        st.caption("Все расчёты выполняются локально. Данные никуда не отправляются.")


def current_params() -> MortgageParams:
    """Собирает параметры кредита из состояния сессии."""
    return MortgageParams(
        price=float(st.session_state["price"]),
        down_payment=float(st.session_state["down_payment"]),
        annual_rate=float(st.session_state["annual_rate"]),
        term_months=int(st.session_state["term_years"]) * 12,
        payment_type=st.session_state["payment_type"],
        start_date=st.session_state["start_date"],
    )


def hero(theme) -> None:
    """Заголовок страницы."""
    st.markdown(
        f"""
        <div style="
            background: linear-gradient(120deg, {theme.primary_soft}, transparent);
            border: 1px solid {theme.border};
            border-radius: 18px;
            padding: 22px 26px;
            margin-bottom: 18px;
        ">
            <div style="font-size: 1.65rem; font-weight: 700; color: {theme.text};">
                Ипотечный калькулятор
            </div>
            <div style="color: {theme.muted}; margin-top: 6px;">
                График платежей, переплата и сравнение типов платежа — в одном дашборде.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_errors(errors: list[str]) -> None:
    """Показывает список ошибок ввода."""
    st.error("Проверьте параметры кредита:")
    for message in errors:
        st.markdown(f"- {message}")


def metrics(result: MortgageResult) -> None:
    """Ключевые показатели кредита."""
    params = result.params
    columns = st.columns(4)
    columns[0].metric(
        result.payment_label,
        format_money(result.monthly_payment, 2),
        help=(
            "Платёж одинаковый весь срок."
            if params.payment_type == ANNUITY
            else "Дальше платёж постепенно уменьшается."
        ),
    )
    columns[1].metric(
        "Сумма кредита",
        format_money(params.loan_amount),
        delta=f"взнос {format_percent(params.down_payment_ratio)}",
        delta_color="off",
    )
    columns[2].metric(
        "Переплата по процентам",
        format_money(result.total_interest),
        delta=f"+{format_percent(result.overpayment_ratio)} к сумме кредита",
        delta_color="inverse",
    )
    columns[3].metric(
        "Всего выплат",
        format_money(result.total_paid),
        delta=f"{params.term_months // 12} лет",
        delta_color="off",
    )


def payment_summary(result: MortgageResult) -> None:
    """Короткая справка о платежах."""
    params = result.params
    if params.payment_type == DIFFERENTIATED:
        text = (
            f"Платёж уменьшается с {format_money(result.max_payment)} "
            f"до {format_money(result.min_payment)}."
        )
    else:
        text = (
            f"Платёж фиксированный: {format_money(result.monthly_payment, 2)} "
            f"ежемесячно, последний — {format_money(result.last_payment, 2)}."
        )
    first = params.start_date.strftime("%d.%m.%Y")
    last = result.schedule["payment_date"].iloc[-1].strftime("%d.%m.%Y")
    st.caption(f"{text} Первый платёж {first}, последний — {last}.")


def charts_tab(result: MortgageResult, theme) -> None:
    """Вкладка с интерактивными графиками.

    Ключи виджетам не задаются сознательно: идентификатор элемента
    выводится из содержимого фигуры, поэтому при изменении входных данных
    или темы график гарантированно перерисовывается и сбрасывает
    сохранённый пользователем зум.
    """
    figures = charts.build_all_charts(result, theme)

    left, right = st.columns([2, 1])
    with left:
        st.plotly_chart(figures["balance"], width="stretch")
    with right:
        st.plotly_chart(figures["cost"], width="stretch")

    st.plotly_chart(figures["structure"], width="stretch")


def schedule_tab(result: MortgageResult) -> None:
    """Вкладка с таблицей платежей и экспортом в CSV."""
    table = schedule_for_display(result)

    st.download_button(
        "⬇️ Скачать таблицу в CSV",
        data=schedule_to_csv(table),
        file_name="grafik_platezhey.csv",
        mime="text/csv",
        help="Файл открывается в Excel без настройки кодировки.",
    )

    st.dataframe(
        table,
        width="stretch",
        hide_index=True,
        height=520,
        column_config={
            "Месяц": st.column_config.NumberColumn(width="small"),
            "Дата платежа": st.column_config.TextColumn(width="small"),
            "Платёж": st.column_config.NumberColumn(format="%.2f ₽"),
            "Проценты": st.column_config.NumberColumn(format="%.2f ₽"),
            "Основной долг": st.column_config.NumberColumn(format="%.2f ₽"),
            "Остаток долга": st.column_config.NumberColumn(format="%.2f ₽"),
        },
    )

    with st.expander("Итоги по годам"):
        yearly = (
            result.schedule.assign(
                year=pd.to_datetime(result.schedule["payment_date"]).dt.year
            )
            .groupby("year", as_index=False)
            .agg(
                payments=("payment", "sum"),
                interest=("interest", "sum"),
                principal=("principal", "sum"),
            )
            .rename(
                columns={
                    "year": "Год",
                    "payments": "Выплачено",
                    "interest": "Проценты",
                    "principal": "Основной долг",
                }
            )
        )
        st.dataframe(
            yearly,
            width="stretch",
            hide_index=True,
            column_config={
                "Выплачено": st.column_config.NumberColumn(format="%.0f ₽"),
                "Проценты": st.column_config.NumberColumn(format="%.0f ₽"),
                "Основной долг": st.column_config.NumberColumn(format="%.0f ₽"),
            },
        )


def comparison_tab(result: MortgageResult, theme) -> None:
    """Вкладка сравнения типов платежа."""
    comparison = compare_payment_types(result.params)

    if comparison.empty:
        st.info("Недостаточно данных для сравнения.")
        return

    view = comparison.rename(columns=charts.comparison_table_columns())
    for column in ("Первый платёж", "Последний платёж", "Переплата", "Всего выплат"):
        view[column] = view[column].map(lambda value: format_money(value, 2))

    st.dataframe(view, width="stretch", hide_index=True)
    st.plotly_chart(
        charts.payment_type_comparison_chart(result, theme), width="stretch"
    )

    annuity = comparison.loc[comparison["payment_type"] == ANNUITY]
    differentiated = comparison.loc[comparison["payment_type"] == DIFFERENTIATED]
    if not annuity.empty and not differentiated.empty:
        saving = (
            annuity["total_interest"].iloc[0] - differentiated["total_interest"].iloc[0]
        )
        extra = (
            differentiated["first_payment"].iloc[0] - annuity["first_payment"].iloc[0]
        )
        if saving > 0 and extra > 0:
            st.info(
                f"Дифференцированный платёж экономит {format_money(saving)} "
                f"на процентах, но первый платёж выше на {format_money(extra)}."
            )


def main() -> None:
    init_state()
    theme = get_theme(st.session_state["theme"])
    apply_theme(st, theme)

    sidebar()
    hero(theme)

    params = current_params()
    errors = validate(params)
    if errors:
        show_errors(errors)
        st.stop()

    try:
        result = calculate(params)
    except ValidationError as error:
        show_errors([str(error)])
        st.stop()
    except (ZeroDivisionError, OverflowError, ArithmeticError) as error:
        st.error(f"Ошибка расчёта: {error}")
        st.stop()

    metrics(result)
    payment_summary(result)

    section = st.segmented_control(
        "Раздел",
        options=[SECTION_CHARTS, SECTION_SCHEDULE, SECTION_COMPARE],
        default=SECTION_CHARTS,
        key="section",
        label_visibility="collapsed",
    )
    section = section or SECTION_CHARTS

    # Рендерим только активный раздел: графики в скрытых вкладках
    # пересчитывают размеры при нулевой ширине и падают в консоли.
    if section == SECTION_CHARTS:
        charts_tab(result, theme)
    elif section == SECTION_SCHEDULE:
        schedule_tab(result)
    else:
        comparison_tab(result, theme)


if __name__ == "__main__":
    main()
