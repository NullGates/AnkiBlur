#!/usr/bin/env bash
#
# package-linux.sh
# Turn a built AnkiBlur launcher directory into the Linux package formats most
# commonly used in the wild: .deb (Debian/Ubuntu/Mint/Pop!_OS), .rpm
# (Fedora/RHEL/openSUSE) and .AppImage (distro-agnostic, portable).
#
# The AnkiBlur "launcher" is a small Rust binary plus a bundled `uv`. On first
# run it builds a Python venv under ~/.local/share/AnkiBlurProgramFiles, installs
# Anki + PyQt6 and applies the blur patches. So every package here ships only the
# launcher payload (tens of MB); the Qt/Python runtime is fetched on first launch.
#
# Usage:
#   scripts/package-linux.sh --launcher-dir DIR --arch amd64|arm64 \
#                            --version 25.09 [--outdir artifacts] \
#                            [--formats deb,rpm,appimage]
#
# Environment:
#   ANKIBLUR_REQUIRE_ALL=1   fail if a requested format's tooling is missing
#                            (CI sets this; locally we skip-and-warn instead).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ASSETS_DIR="$REPO_ROOT/packaging/linux"

# ---------------------------------------------------------------------------- #
# Logging
# ---------------------------------------------------------------------------- #
RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; BLUE=$'\033[0;34m'; NC=$'\033[0m'
log()  { echo "${BLUE}[package-linux]${NC} $*"; }
ok()   { echo "${GREEN}[package-linux]${NC} $*"; }
warn() { echo "${YELLOW}[package-linux]${NC} $*" >&2; }
err()  { echo "${RED}[package-linux]${NC} $*" >&2; }

# ---------------------------------------------------------------------------- #
# Metadata (shared across formats)
# ---------------------------------------------------------------------------- #
PKG_NAME="ankiblur"
APP_ID="net.ankiblur.AnkiBlur"
MAINTAINER="AnkiBlur Maintainers <ankiblur@users.noreply.github.com>"
HOMEPAGE="https://github.com/NullGates/AnkiBlur"
SUMMARY="Spaced-repetition flashcards with a translucent, blurred window"

# Where the launcher payload is installed on disk (deb/rpm). The `anki`
# entrypoint resolves its own real path, so a /usr/bin symlink into here works.
PRIV_DIR="/usr/lib/${PKG_NAME}"

# Files in the launcher dir that belong in /usr/share (or are installer cruft),
# i.e. NOT part of the runtime payload that lives in $PRIV_DIR.
NON_RUNTIME_FILES=(install.sh uninstall.sh README.md anki.desktop anki.png anki.xpm anki.xml anki.1)

# ---------------------------------------------------------------------------- #
# Argument parsing
# ---------------------------------------------------------------------------- #
LAUNCHER_DIR=""
ARCH=""
VERSION=""
OUTDIR="$REPO_ROOT/artifacts"
FORMATS="deb,rpm,appimage"

usage() {
    cat <<'USAGE'
Usage: package-linux.sh --launcher-dir DIR --arch amd64|arm64 --version VER
                        [--outdir artifacts] [--formats deb,rpm,appimage]

Builds .deb, .rpm and .AppImage packages from a built AnkiBlur launcher dir.
Set ANKIBLUR_REQUIRE_ALL=1 to fail (instead of skip) when tooling is missing.
USAGE
    exit "${1:-1}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --launcher-dir) LAUNCHER_DIR="$2"; shift 2 ;;
        --arch)         ARCH="$2"; shift 2 ;;
        --version)      VERSION="$2"; shift 2 ;;
        --outdir)       OUTDIR="$2"; shift 2 ;;
        --formats)      FORMATS="$2"; shift 2 ;;
        -h|--help)      usage 0 ;;
        *) err "Unknown argument: $1"; usage 1 ;;
    esac
done

[[ -n "$LAUNCHER_DIR" ]] || { err "--launcher-dir is required"; usage 1; }
[[ -n "$ARCH" ]]         || { err "--arch is required"; usage 1; }
[[ -n "$VERSION" ]]      || { err "--version is required"; usage 1; }
[[ -d "$LAUNCHER_DIR" ]] || { err "launcher dir not found: $LAUNCHER_DIR"; exit 1; }
LAUNCHER_DIR="$(cd "$LAUNCHER_DIR" && pwd)"

# Architecture name mapping: launcher suffix / deb / rpm / appimage.
case "$ARCH" in
    amd64|x86_64)
        ARCH=amd64; LAUNCHER_SUFFIX=amd64; DEB_ARCH=amd64; RPM_ARCH=x86_64; AI_ARCH=x86_64 ;;
    arm64|aarch64)
        ARCH=arm64; LAUNCHER_SUFFIX=arm64; DEB_ARCH=arm64; RPM_ARCH=aarch64; AI_ARCH=aarch64 ;;
    *) err "Unsupported --arch: $ARCH (expected amd64 or arm64)"; exit 1 ;;
esac

LAUNCHER_BIN="$LAUNCHER_DIR/launcher.$LAUNCHER_SUFFIX"
[[ -f "$LAUNCHER_DIR/anki" ]]   || { err "launcher dir missing 'anki' entrypoint: $LAUNCHER_DIR"; exit 1; }
[[ -f "$LAUNCHER_BIN" ]]        || { err "launcher binary missing: $LAUNCHER_BIN"; exit 1; }

REQUIRE_ALL="${ANKIBLUR_REQUIRE_ALL:-0}"

mkdir -p "$OUTDIR"
OUTDIR="$(cd "$OUTDIR" && pwd)"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/ankiblur-pkg.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT

log "Packaging AnkiBlur $VERSION ($ARCH)"
log "  launcher dir : $LAUNCHER_DIR"
log "  output dir   : $OUTDIR"
log "  formats      : $FORMATS"

# ---------------------------------------------------------------------------- #
# Locate shared source assets in the launcher payload
# ---------------------------------------------------------------------------- #
ICON_SRC="$LAUNCHER_DIR/anki.png"
MIME_SRC="$LAUNCHER_DIR/anki.xml"
MAN_SRC="$LAUNCHER_DIR/anki.1"
[[ -f "$ICON_SRC" ]] || warn "icon source not found ($ICON_SRC); packages will ship without an icon"
[[ -f "$MIME_SRC" ]] || warn "mime source not found ($MIME_SRC); skipping MIME registration"

want() { [[ ",$FORMATS," == *",$1,"* ]]; }

# Generate the AppStream metainfo with the real version/date substituted in.
render_metainfo() {
    local dest="$1" date
    date="$(date -u +%Y-%m-%d)"
    sed -e "s/@VERSION@/$VERSION/g" -e "s/@DATE@/$date/g" \
        "$ASSETS_DIR/$APP_ID.metainfo.xml.in" > "$dest"
}

# Lay out the FHS tree that the .deb and .rpm both install.
#   $1 = destdir (the "/" of the package)
stage_fhs_tree() {
    local dest="$1"

    # 1. Runtime payload -> /usr/lib/ankiblur (strip installer cruft + /usr/share assets)
    install -d "$dest$PRIV_DIR"
    cp -a "$LAUNCHER_DIR/." "$dest$PRIV_DIR/"
    local f
    for f in "${NON_RUNTIME_FILES[@]}"; do
        rm -f "$dest$PRIV_DIR/$f"
    done
    chmod 0755 "$dest$PRIV_DIR/anki" "$dest$PRIV_DIR/launcher.$LAUNCHER_SUFFIX" 2>/dev/null || true
    [[ -f "$dest$PRIV_DIR/uv.$LAUNCHER_SUFFIX" ]] && chmod 0755 "$dest$PRIV_DIR/uv.$LAUNCHER_SUFFIX"

    # 2. /usr/bin/ankiblur -> ../lib/ankiblur/anki
    install -d "$dest/usr/bin"
    ln -sf "../lib/${PKG_NAME}/anki" "$dest/usr/bin/${PKG_NAME}"

    # 3. Desktop entry
    install -d "$dest/usr/share/applications"
    install -m 0644 "$ASSETS_DIR/$APP_ID.desktop" "$dest/usr/share/applications/$APP_ID.desktop"

    # 4. Icon
    if [[ -f "$ICON_SRC" ]]; then
        install -d "$dest/usr/share/icons/hicolor/256x256/apps"
        install -m 0644 "$ICON_SRC" "$dest/usr/share/icons/hicolor/256x256/apps/${PKG_NAME}.png"
    fi

    # 5. AppStream metainfo
    install -d "$dest/usr/share/metainfo"
    render_metainfo "$dest/usr/share/metainfo/$APP_ID.metainfo.xml"

    # 6. MIME types (apkg/colpkg/ankiaddon). Registered, but we do NOT steal the
    #    default handler from a co-installed Anki.
    if [[ -f "$MIME_SRC" ]]; then
        install -d "$dest/usr/share/mime/packages"
        install -m 0644 "$MIME_SRC" "$dest/usr/share/mime/packages/$APP_ID.xml"
    fi

    # 7. Man page
    if [[ -f "$MAN_SRC" ]]; then
        install -d "$dest/usr/share/man/man1"
        gzip -9 -c "$MAN_SRC" > "$dest/usr/share/man/man1/${PKG_NAME}.1.gz"
    fi

    # 8. License / docs
    install -d "$dest/usr/share/doc/${PKG_NAME}"
    [[ -f "$REPO_ROOT/LICENSE" ]] && install -m 0644 "$REPO_ROOT/LICENSE" "$dest/usr/share/doc/${PKG_NAME}/copyright"
}

# Post-install / post-remove body shared by deb maintainer scripts and rpm
# scriptlets: refresh the desktop, icon and MIME caches. Never fail the install.
refresh_caches_snippet() {
    cat <<'SNIP'
command -v update-desktop-database >/dev/null 2>&1 && update-desktop-database -q /usr/share/applications || true
command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache -q -t -f /usr/share/icons/hicolor || true
command -v update-mime-database >/dev/null 2>&1 && update-mime-database /usr/share/mime >/dev/null 2>&1 || true
SNIP
}

checksum() {
    local file="$1"
    ( cd "$(dirname "$file")" && sha256sum "$(basename "$file")" > "$(basename "$file").sha256" )
}

# ---------------------------------------------------------------------------- #
# .deb (dpkg-deb)
# ---------------------------------------------------------------------------- #
build_deb() {
    if ! command -v dpkg-deb >/dev/null 2>&1; then
        if [[ "$REQUIRE_ALL" == "1" ]]; then err "dpkg-deb not found"; return 1; fi
        warn "dpkg-deb not found; skipping .deb"; return 0
    fi
    log "Building .deb ..."

    local root="$WORK/deb"
    rm -rf "$root"; mkdir -p "$root/DEBIAN"
    stage_fhs_tree "$root"

    # Installed-Size is the on-disk footprint of the *installed* files only, so
    # measure the payload tree and not the DEBIAN control area.
    local size_kb
    size_kb="$(du -sk "$root/usr" | cut -f1)"

    # The libc6 (>= 2.36) floor is INTENTIONAL: the launcher itself bails on
    # startup with "AnkiBlur requires glibc 2.36 or later"
    # (ensure_os_supported() in qt/launcher/src/platform/unix.rs, kept by the
    # branding patch). Declaring it lets apt refuse a broken install up front
    # rather than letting the app fail at first launch. Do NOT lower it.
    cat > "$root/DEBIAN/control" <<EOF
Package: $PKG_NAME
Version: $VERSION
Architecture: $DEB_ARCH
Maintainer: $MAINTAINER
Installed-Size: $size_kb
Depends: libc6 (>= 2.36)
Recommends: libegl1, libgl1, fontconfig, libxcb-cursor0, libxkbcommon0, libnss3, libasound2, mpv, lame
Section: education
Priority: optional
Homepage: $HOMEPAGE
Description: $SUMMARY
 AnkiBlur is the Anki spaced-repetition flashcard program with a translucent,
 blurred window effect. It is built automatically from each upstream Anki
 release and is fully compatible with your existing collection, add-ons and
 AnkiWeb sync.
 .
 The window is made transparent and the compositor is asked to blur whatever is
 behind it, so a compositor that implements background blur is required to see
 the effect. The Python/Qt runtime is downloaded on first launch.
EOF

    { echo "#!/bin/sh"; echo "set -e"
      echo 'if [ "$1" = "configure" ]; then'
      refresh_caches_snippet
      echo "fi"; echo "exit 0"; } > "$root/DEBIAN/postinst"

    { echo "#!/bin/sh"; echo "set -e"
      echo 'if [ "$1" = "remove" ] || [ "$1" = "purge" ]; then'
      refresh_caches_snippet
      echo "fi"; echo "exit 0"; } > "$root/DEBIAN/postrm"
    chmod 0755 "$root/DEBIAN/postinst" "$root/DEBIAN/postrm"

    local out="$OUTDIR/${PKG_NAME}_${VERSION}_${DEB_ARCH}.deb"
    dpkg-deb --root-owner-group --build "$root" "$out" >/dev/null
    checksum "$out"
    ok ".deb  -> $(basename "$out")"
}

# ---------------------------------------------------------------------------- #
# .rpm (rpmbuild, packaging a pre-built tree)
# ---------------------------------------------------------------------------- #
build_rpm() {
    if ! command -v rpmbuild >/dev/null 2>&1; then
        if [[ "$REQUIRE_ALL" == "1" ]]; then err "rpmbuild not found"; return 1; fi
        warn "rpmbuild not found; skipping .rpm"; return 0
    fi
    log "Building .rpm ..."

    local stage="$WORK/rpm-stage"
    rm -rf "$stage"; mkdir -p "$stage"
    stage_fhs_tree "$stage"

    local topdir="$WORK/rpmbuild"
    mkdir -p "$topdir"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    local spec="$topdir/SPECS/$PKG_NAME.spec"

    {
        # Ship the pre-built launcher binary verbatim: no stripping, no debuginfo.
        echo '%global __os_install_post %{nil}'
        echo '%global debug_package %{nil}'
        echo ''
        echo "Name:    $PKG_NAME"
        echo "Version: $VERSION"
        echo "Release: 1%{?dist}"
        echo "Summary: $SUMMARY"
        echo 'License: AGPL-3.0-or-later'
        echo "URL:     $HOMEPAGE"
        echo "BuildArch: $RPM_ARCH"
        echo 'Recommends: mesa-libEGL, mesa-libGL, fontconfig, xcb-util-cursor, libxkbcommon, nss, alsa-lib, mpv, lame'
        echo ''
        echo '%description'
        echo 'AnkiBlur is the Anki spaced-repetition flashcard program with a translucent,'
        echo 'blurred window effect, built automatically from each upstream Anki release and'
        echo 'fully compatible with your existing collection, add-ons and AnkiWeb sync. The'
        echo 'Python/Qt runtime is downloaded on first launch.'
        echo ''
        echo '%install'
        echo 'cp -a %{stagedir}/. %{buildroot}/'
        echo ''
        echo '%files'
        echo "$PRIV_DIR"
        echo "/usr/bin/$PKG_NAME"
        echo "/usr/share/applications/$APP_ID.desktop"
        echo "/usr/share/metainfo/$APP_ID.metainfo.xml"
        [[ -f "$ICON_SRC" ]] && echo "/usr/share/icons/hicolor/256x256/apps/$PKG_NAME.png"
        [[ -f "$MIME_SRC" ]] && echo "/usr/share/mime/packages/$APP_ID.xml"
        [[ -f "$MAN_SRC" ]]  && echo "/usr/share/man/man1/$PKG_NAME.1.gz"
        # Only declared when staged (stage_fhs_tree ships copyright iff LICENSE
        # exists); an unguarded %license would hard-fail rpmbuild if it vanished.
        if [[ -f "$REPO_ROOT/LICENSE" ]]; then
            echo "%dir /usr/share/doc/$PKG_NAME"
            echo "%license /usr/share/doc/$PKG_NAME/copyright"
        fi
        echo ''
        echo '%post'
        refresh_caches_snippet
        echo ''
        echo '%postun'
        echo 'if [ "$1" = "0" ]; then'
        refresh_caches_snippet
        echo 'fi'
    } > "$spec"

    rpmbuild -bb "$spec" \
        --define "_topdir $topdir" \
        --define "stagedir $stage" \
        --define "_build_id_links none" \
        --target "$RPM_ARCH" >/dev/null

    local built
    built="$(find "$topdir/RPMS" -name "*.rpm" -type f | head -1)"
    [[ -n "$built" ]] || { err "rpmbuild produced no .rpm"; return 1; }
    local out="$OUTDIR/${PKG_NAME}-${VERSION}-1.${RPM_ARCH}.rpm"
    cp "$built" "$out"
    checksum "$out"
    ok ".rpm  -> $(basename "$out")"
}

# ---------------------------------------------------------------------------- #
# .AppImage (appimagetool)
# ---------------------------------------------------------------------------- #
resolve_appimagetool() {
    if command -v appimagetool >/dev/null 2>&1; then
        echo "appimagetool"; return 0
    fi
    # Fetch and extract (avoids needing FUSE on CI runners).
    local url="https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-${AI_ARCH}.AppImage"
    local dl="$WORK/appimagetool.AppImage"
    log "Fetching appimagetool ($AI_ARCH) ..." >&2
    if ! curl -fsSL "$url" -o "$dl"; then
        return 1
    fi
    chmod +x "$dl"
    ( cd "$WORK" && "$dl" --appimage-extract >/dev/null 2>&1 ) || return 1
    echo "$WORK/squashfs-root/AppRun"
}

build_appimage() {
    local tool
    if ! tool="$(resolve_appimagetool)" || [[ -z "$tool" ]]; then
        if [[ "$REQUIRE_ALL" == "1" ]]; then err "appimagetool unavailable"; return 1; fi
        warn "appimagetool unavailable; skipping .AppImage"; return 0
    fi
    log "Building .AppImage ..."

    local appdir="$WORK/AppDir"
    rm -rf "$appdir"
    stage_fhs_tree "$appdir"

    # AppRun: resolve our own dir, then hand off to the arch-aware `anki` script.
    cat > "$appdir/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/lib/ankiblur/anki" "$@"
EOF
    chmod 0755 "$appdir/AppRun"

    # appimagetool expects a top-level desktop file + icon.
    cp "$appdir/usr/share/applications/$APP_ID.desktop" "$appdir/$APP_ID.desktop"
    if [[ -f "$ICON_SRC" ]]; then
        cp "$ICON_SRC" "$appdir/${PKG_NAME}.png"
        cp "$ICON_SRC" "$appdir/.DirIcon"
    fi

    local out="$OUTDIR/AnkiBlur-${VERSION}-${AI_ARCH}.AppImage"
    # Skip AppStream validation when supported, so we don't hard-depend on
    # appstreamcli being installed on the runner.
    local ai_flags=()
    if "$tool" --help 2>&1 | grep -q -- '--no-appstream'; then
        ai_flags+=(--no-appstream)
    fi
    if ! ARCH="$AI_ARCH" "$tool" "${ai_flags[@]}" "$appdir" "$out" >/dev/null 2>"$WORK/appimage.log"; then
        err "appimagetool failed:"; cat "$WORK/appimage.log" >&2
        if [[ "$REQUIRE_ALL" == "1" ]]; then return 1; fi
        warn "skipping .AppImage"; return 0
    fi
    chmod +x "$out"
    checksum "$out"
    ok ".AppImage -> $(basename "$out")"
}

# ---------------------------------------------------------------------------- #
# Run
# ---------------------------------------------------------------------------- #
rc=0
want deb      && { build_deb      || rc=1; }
want rpm      && { build_rpm      || rc=1; }
want appimage && { build_appimage || rc=1; }

echo ""
log "Artifacts in $OUTDIR:"
find "$OUTDIR" -maxdepth 1 -type f \( -name "*.deb" -o -name "*.rpm" -o -name "*.AppImage" \) \
    -print 2>/dev/null | sort | sed 's/^/    /'

exit $rc
