# AnkiBlur Windows dev-tests (NOT shipped)

Windows-only, interactive verification suite for the native blur/frameless
window implemented in
`../ankiblur_background_theme/win_native.py`. Handed off together with
`docs/WINDOWS_IMPLEMENTATION.md` (read it first - especially the "Verified
findings" section).

**RELEASE GATE:** the transplanted add-on version of the Windows code has
never been executed on a real Windows machine (only the original inline
implementation was). Before it ships in any release, a human MUST run
`native_test.py` against a live AnkiBlur on real Windows and get >= 18/19
(the snap-layouts flyout check needs a real mouse - finding 9).

These files live OUTSIDE the add-on source directory on purpose:
`scripts/build-addon-zip.py` packages only
`addons/anki_webview_addon/ankiblur_background_theme/`, so nothing here can
end up in the shipped `.ankiaddon` (CI cmp-checks the zip byte-for-byte).

They are NOT run in CI: they simulate real user input (SetCursorPos /
mouse_event / keybd_event) against a live, visible Anki window on a real
Windows desktop.

| File | Purpose |
|---|---|
| `native_test.py` | 19-check behavior suite: hit-test map, dbl-click / max-button / system-menu / snap / drag / minimize paths. Run against a running AnkiBlur; expect >= 18/19 - the snap-layouts-flyout check needs a human mouse (finding 9: injected input cannot trigger the flyout). Close other windows overlapping 400,300-1400,1000 first. |
| `close_anki.py` | Helper: politely close the Anki window. |
| `discover.py` | Helper: enumerate candidate windows / dump styles. |
| `dbl_probe.py` | Isolated double-click gesture probe (shows the WindowFromPoint-verify pattern - finding 10: injected clicks can silently land on the wrong window). |
| `flyout_truth.py` | Ground-truth probe proving the snap flyout is untriggerable by injected hover, even on stock Notepad (finding 9). |

Usage on a Windows machine:

```
# start AnkiBlur normally, wait for the main window, then:
python native_test.py
```

Debug channel: set `ANKIBLUR_NC_LOG=<path>` (env var) to make
`win_native.py` append every non-client mouse message + hit-test
classification to that file. If the launcher does not forward env vars,
temporarily hardcode the default next to `_ANKIBLUR_NC_LOG` in
`win_native.py`.
