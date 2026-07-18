#!/bin/bash
# AnkiBlur Linux launcher build script.
#
# At CI time this file replaces upstream's qt/launcher/lin/build.sh inside the
# anki-source checkout (see .github/workflows/build-linux.yml), and is executed
# from qt/launcher/lin. It builds a single native launcher instead of
# upstream's dual-arch cross build.
#
# Required environment:
#   RUST_TARGET         e.g. x86_64-unknown-linux-gnu / aarch64-unknown-linux-gnu
#   ARCH_SUFFIX         e.g. amd64 / arm64 (binary + tarball name suffix)
#   ANKIBLUR_REPO_ROOT  absolute path to the AnkiBlur repo checkout (for
#                       bundling LICENSE/NOTICE into the launcher payload)
set -euo pipefail

RUST_TARGET="${RUST_TARGET:?RUST_TARGET must be set}"
ARCH_SUFFIX="${ARCH_SUFFIX:?ARCH_SUFFIX must be set}"
ANKIBLUR_REPO_ROOT="${ANKIBLUR_REPO_ROOT:?ANKIBLUR_REPO_ROOT must be set}"

# Add Rust target
rustup target add "$RUST_TARGET"

# Define output paths
OUTPUT_DIR="../../../out/launcher"
ANKI_VERSION=$(cat ../../../.version | tr -d '\n')
LAUNCHER_DIR="$OUTPUT_DIR/anki-launcher-$ANKI_VERSION-linux-$ARCH_SUFFIX"

# Clean and create output directory
rm -rf "$LAUNCHER_DIR"
mkdir -p "$LAUNCHER_DIR"

# Build native binary
cargo build -p launcher --release --target "$RUST_TARGET"

# Copy binaries and support files
TARGET_DIR=${CARGO_TARGET_DIR:-../../../target}
# Copy launcher with architecture-specific name (expected by anki script)
cp "$TARGET_DIR/$RUST_TARGET/release/launcher" "$LAUNCHER_DIR/launcher.$ARCH_SUFFIX"
# Copy UV with architecture-specific name
cp "../../../out/extracted/uv/uv" "$LAUNCHER_DIR/uv.$ARCH_SUFFIX"

# Copy support files from lin directory
for file in README.md anki.1 anki.desktop anki.png anki.xml anki.xpm install.sh uninstall.sh anki; do
    [ -f "$file" ] && cp "$file" "$LAUNCHER_DIR/" || echo "Warning: $file not found"
done

# Copy additional files from parent directory
[ -f "../pyproject.toml" ] && cp ../pyproject.toml "$LAUNCHER_DIR/"
[ -f "../../../.python-version" ] && cp ../../../.python-version "$LAUNCHER_DIR/"
[ -f "../versions.py" ] && cp ../versions.py "$LAUNCHER_DIR/"

# Bundle the license texts (AGPL conveyance: the tarball/deb/rpm/AppImage
# payloads must carry the license alongside the program).
cp "$ANKIBLUR_REPO_ROOT/LICENSE" "$ANKIBLUR_REPO_ROOT/NOTICE" "$LAUNCHER_DIR/"

# No runtime patch staging: the blur payload ships as an Anki addon embedded
# in the launcher binary (include_bytes! in addon.rs), staged into
# qt/launcher/addon/ by scripts/validate-and-apply-patches.sh before the
# cargo build above.

# Set executable permissions
chmod +x "$LAUNCHER_DIR/launcher.$ARCH_SUFFIX" "$LAUNCHER_DIR/uv.$ARCH_SUFFIX" "$LAUNCHER_DIR/anki" || true
chmod +x "$LAUNCHER_DIR/install.sh" "$LAUNCHER_DIR/uninstall.sh" || true

# Set proper permissions and create tarball
chmod -R a+r "$LAUNCHER_DIR"

ZSTD="zstd -c --long -T0 -18"
TRANSFORM="s%^.%anki-launcher-$ANKI_VERSION-linux-$ARCH_SUFFIX%S"
TARBALL="$OUTPUT_DIR/anki-launcher-$ANKI_VERSION-linux-$ARCH_SUFFIX.tar.zst"

tar -I "$ZSTD" --transform "$TRANSFORM" -cf "$TARBALL" -C "$LAUNCHER_DIR" .

echo "Build complete:"
echo "Launcher: $LAUNCHER_DIR"
echo "Tarball: $TARBALL"
