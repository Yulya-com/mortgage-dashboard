"""Светлая и тёмная темы: палитры, CSS интерфейса, шаблон Plotly."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Theme:
    """Набор цветов и подписей для одной темы."""

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
    grid: str


LIGHT = Theme(
    key="light",
    label="Светлая",
    icon="☀️",
    primary="#2563EB",
    primary_soft="rgba(37, 99, 235, 0.14)",
    accent="#0E9F6E",
    secondary="#F59E0B",
    text="#101828",
    muted="#667085",
    background="#F4F6FB",
    surface="#FFFFFF",
    border="#E4E7EC",
    grid="#EEF1F6",
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
    border="#243248",
    grid="#1E2A3E",
)

THEMES: dict[str, Theme] = {theme.key: theme for theme in (LIGHT, DARK)}
DEFAULT_THEME = LIGHT.key


def get_theme(key: str | None) -> Theme:
    """Возвращает тему по ключу, иначе светлую."""
    return THEMES.get(key or DEFAULT_THEME, LIGHT)


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
        --mc-primary: {theme.primary};
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

    /* Поля ввода и выпадающие списки */
    [data-testid="stNumberInput"] input,
    [data-testid="stTextInput"] input,
    [data-testid="stDateInput"] input,
    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="select"] > div {{
        background-color: var(--mc-surface) !important;
        color: var(--mc-text) !important;
        border-color: var(--mc-border) !important;
    }}

    [data-testid="stNumberInput"] button {{
        background-color: var(--mc-surface) !important;
        color: var(--mc-text) !important;
        border-color: var(--mc-border) !important;
    }}

    /* Кнопки */
    .stButton > button,
    .stDownloadButton > button {{
        background-color: var(--mc-surface) !important;
        color: var(--mc-text) !important;
        border: 1px solid var(--mc-border);
        border-radius: 10px;
        font-weight: 500;
    }}

    .stButton > button:hover,
    .stDownloadButton > button:hover {{
        border-color: var(--mc-primary);
        color: var(--mc-primary) !important;
    }}

    /* Вкладки */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 4px;
        border-bottom: 1px solid var(--mc-border);
    }}

    .stTabs [data-baseweb="tab"] {{
        color: var(--mc-muted) !important;
        font-weight: 500;
    }}

    .stTabs [aria-selected="true"] {{
        color: var(--mc-primary) !important;
    }}

    /* Таблица */
    [data-testid="stDataFrame"],
    [data-testid="stDataFrameResizable"] {{
        border: 1px solid var(--mc-border);
        border-radius: 12px;
        overflow: hidden;
    }}

    /* Раскрывающиеся блоки */
    [data-testid="stExpander"] details {{
        background-color: var(--mc-surface) !important;
        border: 1px solid var(--mc-border) !important;
        border-radius: 12px;
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
