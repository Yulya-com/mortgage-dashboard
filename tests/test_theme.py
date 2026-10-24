"""Тесты тем: палитры, CSS и переключение."""

from __future__ import annotations

from theme import DARK, DEFAULT_THEME, LIGHT, THEMES, css, get_theme


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
    assert light_css != dark_css
    assert "<style>" in light_css
