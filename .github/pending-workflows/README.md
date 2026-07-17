# Pending workflow updates (blocked on `workflow` token scope)

The files in this directory are the intended `.github/workflows/` contents for
the addon-embed redesign. They are parked here because pushes from the current
automation credentials (a gh OAuth token without the `workflow` scope) are
rejected by GitHub whenever a commit touches `.github/workflows/*`. The active
workflows on this branch are therefore kept byte-identical to `main`, and the
redesign was adapted so the unmodified workflows still build it correctly:

- The deterministic `.ankiaddon` build + `include_bytes!` staging happens in
  `scripts/validate-and-apply-patches.sh`, which every build workflow already
  invokes, so no workflow edit is needed to produce a working launcher.
- The now-vestigial runtime patch files under `patches/0B_*`/`patches/0C_*`
  are retained (identical to `main`) solely because the unmodified workflows
  `cp` them under `bash -e` and ship them next to the launcher. The redesigned
  launcher has no runtime patcher and ignores them; they are a few KB of inert
  bytes in the artifacts.

## To apply (requires a push with `workflow`-scoped credentials)

Someone pushing with `workflow` scope (e.g. after
`gh auth refresh -h github.com -s workflow`, or via SSH) should, in one commit:

1. `cp .github/pending-workflows/build-*.yml .github/pending-workflows/probe-aqt-symbols.yml .github/workflows/`
2. `git rm -r patches/0B_LINUX_anki_qt_window_main patches/0B_MACOS_anki_qt_window_main patches/0B_WINDOWS_anki_qt_window_main patches/0C_anki_qt_window_webview`
   (the pending workflows drop the "Setup … patches" copy steps, so the files
   must be deleted in the same commit or they simply go back to being unused)
3. `git rm -r .github/pending-workflows`

What the pending versions change relative to `main`:

- drop the runtime-patch copy/stage/NSIS-manifest steps (payload is the
  embedded addon now)
- pin `UV_VERSION` in the three non-Windows workflows (report H7)
- add `addons/**` to the trigger paths
- bump `actions/checkout` and `actions/upload-artifact` to v5 (report L14)
- add `probe-aqt-symbols.yml` (per-PR probe of the pinned aqt release plus a
  weekly probe of the newest release that opens a drift issue; report §3)

Until then, the only functional losses are: uv is unpinned in three workflows,
addon-only changes don't auto-trigger builds (use `workflow_dispatch`), and the
symbol probe only runs locally (`python3 scripts/probe-aqt-symbols.py`).
