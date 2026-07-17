# AnkiBlur self-check tripwire.
#
# Never silently ship unblurred: shortly after the main window is up, verify
# that every blur operation actually engaged. On failure, log full detail to
# stdout and show a one-time, NON-MODAL warning dialog (once per
# (anki_version, failure-set) - re-armed by version changes or new failure
# modes). Anki keeps working un-blurred either way.

import json
import os
import traceback

from aqt import mw, gui_hooks
from aqt.qt import Qt, QMessageBox, QTimer

ISSUES_URL = "https://github.com/NullGates/AnkiBlur/issues"

# Delay after main_window_did_init before checking: comfortably clears the
# native-effect retry windows in window_effects (150 ms + 15 x 100 ms).
CHECK_DELAY_MS = 3000


def _anki_version() -> str:
    try:
        from anki.buildinfo import version
        return version
    except Exception:
        pass
    try:
        from aqt import appVersion
        return appVersion
    except Exception:
        return "unknown"


def _state_path() -> str:
    # user_files/ is preserved by Anki's add-on updater and by the AnkiBlur
    # launcher's installer, so the "already warned" memory survives updates.
    return os.path.join(os.path.dirname(__file__), "user_files",
                        "ankiblur-state.json")


def _load_state() -> dict:
    try:
        with open(_state_path(), encoding="utf-8") as f:
            state = json.load(f)
            if isinstance(state, dict):
                return state
    except Exception:
        pass
    return {}


def _write_state(state: dict) -> None:
    try:
        path = _state_path()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, sort_keys=True)
    except Exception:
        traceback.print_exc()


def _show_warning(text: str) -> None:
    """Non-modal, non-blocking warning parented to the main window."""
    try:
        box = QMessageBox(mw)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("AnkiBlur")
        box.setText(text)
        box.setWindowModality(Qt.WindowModality.NonModal)
        box.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        box.show()  # never .exec(): must not block Anki
    except Exception:
        traceback.print_exc()


def arm(ops: dict) -> None:
    """Schedule the post-startup self-check."""
    gui_hooks.main_window_did_init.append(
        lambda: QTimer.singleShot(CHECK_DELAY_MS, lambda: check(ops))
    )


def check(ops: dict) -> None:
    try:
        _check_inner(ops)
    except Exception:
        traceback.print_exc()


def _check_inner(ops: dict) -> None:
    from . import window_effects

    failing = {op: status for op, status in ops.items() if status != "ok"}

    # Computed probes, independent of what the ops recorded:
    # 1. main-window translucency must actually be set - unless the
    #    platform backend deliberately cleared it after giving up (that
    #    give-up is already a failing op).
    try:
        if window_effects.translucency_expected() and not mw.testAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        ):
            failing["probe_window_translucent"] = (
                "failed: WA_TranslucentBackground not set on the main window"
            )
    except Exception as e:
        failing["probe_window_translucent"] = f"failed: {e}"

    # 2. the main webview page background must be fully transparent. This is
    #    the detection net for upstream standard_css / page-background drift.
    try:
        alpha = mw.web.page().backgroundColor().alpha()
        if alpha != 0:
            failing["probe_page_alpha"] = (
                f"failed: main webview page background alpha is {alpha}, "
                "expected 0"
            )
    except Exception as e:
        failing["probe_page_alpha"] = f"failed: {e}"

    anki_version = _anki_version()
    state = _load_state()
    state["anki_version"] = anki_version
    state["ops"] = dict(ops)

    if not failing:
        _write_state(state)
        print("[AnkiBlur] self-check passed: all ops ok")
        return

    # Full detail on stdout, always.
    print("[AnkiBlur] SELF-CHECK FAILED - the blur/tint may not be active:")
    for op, status in sorted(failing.items()):
        print(f"[AnkiBlur]   {op}: {status}")

    failing_ops = sorted(failing)
    warned = state.get("warned") or {}
    already_warned = (
        warned.get("anki_version") == anki_version
        and warned.get("failing_ops") == failing_ops
    )
    if not already_warned:
        detail = "\n".join(f"  - {op}: {failing[op]}" for op in failing_ops)
        _show_warning(
            "AnkiBlur could not fully enable its blur/transparency effects "
            f"on this Anki version ({anki_version}).\n\n"
            f"Failing checks:\n{detail}\n\n"
            "Anki keeps working normally, just without the blur.\n"
            f"Please report this at:\n{ISSUES_URL}"
        )
        state["warned"] = {
            "anki_version": anki_version,
            "failing_ops": failing_ops,
        }

    _write_state(state)


def report_fatal(exc: BaseException) -> None:
    """Called when the add-on failed to initialize at all. Schedules a
    non-modal warning for after the main window is up (never Anki's
    add-on-crash traceback dialog, never a silent no-op)."""
    message = (
        "The AnkiBlur background theme add-on failed to start:\n\n"
        f"{type(exc).__name__}: {exc}\n\n"
        "Anki keeps working normally, just without the blur.\n"
        f"Please report this at:\n{ISSUES_URL}"
    )
    print(f"[AnkiBlur] FATAL: add-on failed to initialize: {exc!r}")

    def _later() -> None:
        QTimer.singleShot(1000, lambda: _show_warning(message))

    try:
        gui_hooks.main_window_did_init.append(_later)
    except Exception:
        traceback.print_exc()
        # Last resort: try to show it immediately.
        _show_warning(message)
