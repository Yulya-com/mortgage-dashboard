"""Светлая и тёмная темы: палитры, CSS интерфейса, проверка контраста."""

from __future__ import annotations

from dataclasses import dataclass

# Пороги WCAG 2.1: обычный текст и элементы управления.
AA_TEXT = 4.5
AA_GRAPHICS = 3.0


@dataclass(frozen=True)
class Theme:
    """Набор цветов и подписей для одной темы.

    Поля ``text``/``muted``/``control`` проверяются тестами на контраст:
    они используются для текста и границ интерактивных элементов.
    """

    key: str
    label: str
    icon: str
    primary: str
    primary_soft: str
    accent: str
    secondary: str
    text: str
    muted: str
    background: str
    surface: str
    border: str
    control: str
    grid: str
    on_primary: str


LIGHT = Theme(
    key="light",
    label="Светлая",
    icon="☀️",
    primary="#2563EB",
    primary_soft="rgba(37, 99, 235, 0.14)",
    accent="#047857",
    secondary="#B45309",
    text="#101828",
    muted="#556070",
    background="#F4F6FB",
    surface="#FFFFFF",
    border="#D5DAE3",
    control="#7B8798",
    grid="#EEF1F6",
    on_primary="#FFFFFF",
)

DARK = Theme(
    key="dark",
    label="Тёмная",
    icon="🌙",
    primary="#60A5FA",
    primary_soft="rgba(96, 165, 250, 0.18)",
    accent="#34D399",
    secondary="#FBBF24",
    text="#E6EDF7",
    muted="#93A4BF",
    background="#0B1220",
    surface="#131C2E",
    border="#2F3E55",
    control="#5B6E8C",
    grid="#1E2A3E",
    on_primary="#0B1220",
)

THEMES: dict[str, Theme] = {theme.key: theme for theme in (LIGHT, DARK)}
DEFAULT_THEME = LIGHT.key


def get_theme(key: str | None) -> Theme:
    """Возвращает тему по ключу, иначе светлую."""
    return THEMES.get(key or DEFAULT_THEME, LIGHT)


def _srgb_to_linear(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(hex_color: str) -> float:
    """Относительная яркость цвета по WCAG 2.1."""
    value = hex_color.lstrip("#")
    red, green, blue = (int(value[index : index + 2], 16) for index in (0, 2, 4))
    return (
        0.2126 * _srgb_to_linear(red)
        + 0.7152 * _srgb_to_linear(green)
        + 0.0722 * _srgb_to_linear(blue)
    )


def contrast_ratio(first: str, second: str) -> float:
    """Коэффициент контраста двух цветов: от 1.0 до 21.0."""
    lighter, darker = sorted(
        (relative_luminance(first), relative_luminance(second)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


def css(theme: Theme) -> str:
    """CSS, перекрашивающий основные поверхности Streamlit под тему."""
    return f"""
    <style>
    :root {{
        --mc-bg: {theme.background};
        --mc-surface: {theme.surface};
        --mc-text: {theme.text};
        --mc-muted: {theme.muted};
        --mc-border: {theme.border};
        --mc-control: {theme.control};
        --mc-primary: {theme.primary};
        --mc-on-primary: {theme.on_primary};
    }}

    .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    [data-testid="stMainBlockContainer"],
    section.main {{
        background-color: var(--mc-bg) !important;
        color: var(--mc-text) !important;
    }}

    [data-testid="stHeader"],
    [data-testid="stToolbar"] {{
        background-color: transparent !important;
    }}

    [data-testid="stSidebar"],
    [data-testid="stSidebarContent"],
    [data-testid="stSidebarUserContent"] {{
        background-color: var(--mc-surface) !important;
        border-right: 1px solid var(--mc-border);
    }}

    [data-testid="stSidebar"] * {{
        color: var(--mc-text);
    }}

    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
    .stApp p, .stApp label, .stApp li {{
        color: var(--mc-text);
    }}

    [data-testid="stCaptionContainer"] p,
    [data-testid="stCaptionContainer"],
    .stCaption,
    small {{
        color: var(--mc-muted) !important;
    }}

    /* Переключатель темы */
    [data-testid="stSidebar"] [role="radiogroup"] {{
        gap: 6px;
    }}

    [data-testid="stSidebar"] [role="radiogroup"] label {{
        background-color: var(--mc-bg);
        border: 1px solid var(--mc-control);
        border-radius: 10px;
        padding: 4px 10px;
        color: var(--mc-text) !important;
        font-weight: 500;
    }}

    [data-testid="stSidebar"] [role="radiogroup"] label:hover {{
        border-color: var(--mc-primary);
    }}

    /* Карточки показателей */
    [data-testid="stMetric"] {{
        background-color: var(--mc-surface) !important;
        border: 1px solid var(--mc-border);
        border-radius: 14px;
        padding: 14px 16px;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
    }}

    [data-testid="stMetricLabel"] p {{
        color: var(--mc-muted) !important;
        font-size: 0.82rem;
        font-weight: 500;
    }}

    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] div {{
        color: var(--mc-text) !important;
    }}

    [data-testid="stMetricDelta"] {{
        color: var(--mc-muted) !important;
    }}

    /* Поля ввода: граница заметна в обеих темах */
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stDateInput"] input,
    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="select"] > div {{
        background-color: var(--mc-surface) !important;
        color: var(--mc-text) !important;
        border-color: var(--mc-control) !important;
    }}

    [data-testid="stNumberInput"] button {{
        background-color: var(--mc-surface) !important;
        color: var(--mc-text) !important;
        border-color: var(--mc-control) !important;
    }}

    /* Кнопки */
    .stButton > button,
    .stDownloadButton > button {{
        background-color: var(--mc-surface) !important;
        color: var(--mc-text) !important;
        border: 1px solid var(--mc-control);
        border-radius: 10px;
        font-weight: 500;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        border-color: var(--mc-primary);
        color: var(--mc-primary) !important;
    }}

    /* Переключатель разделов */
    [data-testid="stButtonGroup"] button {{
        background-color: var(--mc-surface) !important;
        color: var(--mc-text) !important;
        border-color: var(--mc-border) !important;
    }}

    [data-testid="stButtonGroup"] button[aria-checked="true"],
    [data-testid="stButtonGroup"] button[aria-pressed="true"],
    [data-testid="stButtonGroup"] button[kind="segmented_controlActive"] {{
        background-color: var(--mc-primary) !important;
        color: var(--mc-on-primary) !important;
        border-color: var(--mc-primary) !important;
        font-weight: 600;
    }}

    /* Раскрывающиеся блоки */
    [data-testid="stExpander"] details {{
        background-color: var(--mc-surface) !important;
        border: 1px solid var(--mc-border) !important;
        border-radius: 12px;
    }}

    /* Таблица */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrameResizable"] {{
        border: 1px solid var(--mc-border);
        border-radius: 12px;
        overflow: hidden;
    }}

    /* Сообщения */
    [data-testid="stAlert"] {{
        border-radius: 12px;
    }}

    hr {{
        border-color: var(--mc-border);
    }}
    </style>
    """


def apply_theme(st, theme: Theme) -> None:
    """Вставляет CSS темы в страницу."""
    st.markdown(css(theme), unsafe_allow_html=True)
