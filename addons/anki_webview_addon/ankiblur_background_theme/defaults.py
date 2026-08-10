# AnkiBlur platform-aware theme defaults.
#
# config.json ships ONE cross-platform set of defaults (the .ankiaddon is
# byte-identical on every OS - CI enforces it), so per-platform defaults
# must be layered on at runtime. On macOS the Liquid Glass backend renders
# the frosted material itself, so the tint overlay defaults to fully
# transparent (alpha 0); the colors only become visible if the user raises
# the alpha (red on light / blue on dark).

import sys

MAC_THEME_DEFAULTS = {
    "light_theme": {"color": "#ff0000", "alpha": 0},
    "dark_theme": {"color": "#0000ff", "alpha": 0},
}


def theme_fallback(is_dark: bool) -> dict:
    """Fallback theme entry when the config is missing a theme key."""
    if sys.platform == "darwin":
        return dict(MAC_THEME_DEFAULTS["dark_theme" if is_dark else "light_theme"])
    return {
        "color": "#000000" if is_dark else "#ffffff",
        "alpha": 30 if is_dark else 15,
    }


def effective_config(addon_manager, module: str) -> dict:
    """getConfig() with macOS defaults for theme keys the user never set.

    Anki's getConfig() merges config.json defaults under the user's stored
    overrides, so the merged dict cannot distinguish "user chose the shipped
    default" from "user never configured this key". Read the user-only
    config out of meta.json (same lookup getConfig itself does) to make
    that call; an explicit user choice always wins over the macOS defaults.
    """
    config = dict(addon_manager.getConfig(module) or {})
    if sys.platform != "darwin":
        return config

    try:
        addon = addon_manager.addonFromModule(module)
        user_conf = addon_manager.addonMeta(addon).get("config") or {}
    except Exception:
        # If meta.json is unreadable, assume nothing was user-set.
        user_conf = {}

    for key, mac_default in MAC_THEME_DEFAULTS.items():
        if key not in user_conf:
            config[key] = dict(mac_default)
    return config
