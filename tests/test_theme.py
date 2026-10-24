"""Тесты тем: палитры, CSS, контраст по WCAG."""

from __future__ import annotations

import pytest

from theme import (
    AA_GRAPHICS,
    AA_TEXT,
    DARK,
    DEFAULT_THEME,
    LIGHT,
    THEMES,
    contrast_ratio,
    css,
    get_theme,
)

ALL_THEMES = [LIGHT, DARK]


def test_themes_registered() -> None:
    assert set(THEMES) == {"light", "dark"}
    assert get_theme("dark") is DARK
    assert get_theme("light") is LIGHT


def test_unknown_theme_falls_back_to_light() -> None:
    assert get_theme("neon") is LIGHT
    assert get_theme(None) is LIGHT
    assert get_theme("") is LIGHT
    assert DEFAULT_THEME == "light"


def test_themes_have_distinct_surfaces() -> None:
    assert LIGHT.background != DARK.background
    assert LIGHT.text != DARK.text
    assert LIGHT.surface != DARK.surface


def test_css_uses_theme_variables() -> None:
    light_css = css(LIGHT)
    dark_css = css(DARK)

    assert f"--mc-bg: {LIGHT.background}" in light_css
    assert f"--mc-bg: {DARK.background}" in dark_css
    assert "--mc-control" in light_css
    assert light_css != dark_css
    assert "<style>" in light_css


@pytest.mark.parametrize("theme", ALL_THEMES, ids=lambda t: t.key)
@pytest.mark.parametrize("surface", ["background", "surface"])
def test_text_contrast_passes_aa(theme, surface) -> None:
    """Основной текст читается на фоне и на карточке."""
    ratio = contrast_ratio(theme.text, getattr(theme, surface))
    assert ratio >= AA_TEXT, f"{theme.key}: text/{surface} = {ratio:.2f}"


@pytest.mark.parametrize("theme", ALL_THEMES, ids=lambda t: t.key)
@pytest.mark.parametrize("surface", ["background", "surface"])
def test_muted_contrast_passes_aa(theme, surface) -> None:
    """Приглушённые подписи и подписи осей остаются читаемыми."""
    ratio = contrast_ratio(theme.muted, getattr(theme, surface))
    assert ratio >= AA_TEXT, f"{theme.key}: muted/{surface} = {ratio:.2f}"


@pytest.mark.parametrize("theme", ALL_THEMES, ids=lambda t: t.key)
@pytest.mark.parametrize("surface", ["background", "surface"])
def test_control_border_is_visible(theme, surface) -> None:
    """Границы полей ввода различимы как элемент управления."""
    ratio = contrast_ratio(theme.control, getattr(theme, surface))
    assert ratio >= AA_GRAPHICS, f"{theme.key}: control/{surface} = {ratio:.2f}"


@pytest.mark.parametrize("theme", ALL_THEMES, ids=lambda t: t.key)
@pytest.mark.parametrize("color", ["primary", "accent", "secondary"])
def test_chart_colors_visible_on_background(theme, color) -> None:
    """Линии и столбцы графиков различимы на фоне."""
    ratio = contrast_ratio(getattr(theme, color), theme.background)
    assert ratio >= AA_GRAPHICS, f"{theme.key}: {color} = {ratio:.2f}"


def test_contrast_ratio_extremes() -> None:
    assert contrast_ratio("#000000", "#FFFFFF") == pytest.approx(21, abs=0.01)
    assert contrast_ratio("#FFFFFF", "#FFFFFF") == pytest.approx(1, abs=0.001)


def test_secondary_colors_were_darkened_for_light_theme() -> None:
    """Регрессия: янтарный #F59E0B давал 1.99:1 и был почти невидим."""
    assert contrast_ratio(LIGHT.secondary, LIGHT.background) > 4.5
    assert contrast_ratio(LIGHT.accent, LIGHT.background) > 4.5


@pytest.mark.parametrize("theme", ALL_THEMES, ids=lambda t: t.key)
def test_active_toggle_text_readable_on_primary(theme) -> None:
    """Регрессия: белый текст на #60A5FA в тёмной теме давал 2.5:1."""
    ratio = contrast_ratio(theme.on_primary, theme.primary)
    assert ratio >= AA_TEXT, f"{theme.key}: on_primary/primary = {ratio:.2f}"
