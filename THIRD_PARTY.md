# Third-party binaries vendored in this repository

## nsProcess.dll

- Path: `/nsProcess.dll`
- sha256: `579a034ff5ab9b732a318b1636c2902840f604e8e664f5b93c07a99253b3c9cf`
- Provenance: extracted byte-identical from the official Anki 25.09 Windows
  installer (as noted in the "Copy NSIS Plugins" step of
  `.github/workflows/build-windows.yml`). It is the NSIS *nsProcess* plugin,
  distributed under a zlib-style free license by Instrumental Services Inc. /
  Shengalts Aleksander. It is used only at Windows-installer build time so the
  NSIS installer/uninstaller can detect running Anki processes.

## TODO

- Installer-embedded license text pending: the Windows NSIS installer does not
  yet display/ship the AGPL-3.0 text inside the `.exe`; this is deferred to the
  launcher redesign track's NSIS work. Meanwhile the CI artifacts and GitHub
  release assets carry `LICENSE` and `NOTICE` alongside the installer.
