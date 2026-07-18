#!/usr/bin/env python3
"""Build a byte-deterministic .ankiaddon zip from an add-on source directory.

Determinism: sorted arcnames, fixed timestamps/permissions, ZIP_STORED (the
files are tiny, and storing avoids output drift across zlib versions/OSes).

Excluded from the zip: __pycache__/, *.pyc, user_files/ and meta.json -
those are runtime state that must never ship.

With --top-dir, every arcname is prefixed with that directory ("folder
shaped" zip). The AnkiBlur launcher's extractor handles both flat and
folder-shaped zips, but legacy (pre-addon-redesign) launchers in the wild
download the committed zip from the main branch at runtime and can only
extract folder-shaped ones - so the committed copy must be built with
--top-dir. (Note: a folder-shaped zip cannot be installed through Anki's
own "Install from file..." UI, which requires the manifest at the zip root.)
"""

import argparse
import os
import sys
import zipfile

EXCLUDED_DIRS = {"__pycache__", "user_files"}
EXCLUDED_FILES = {"meta.json"}
EXCLUDED_SUFFIXES = (".pyc",)

# Fixed metadata for determinism.
FIXED_DATE_TIME = (2020, 1, 1, 0, 0, 0)
FIXED_EXTERNAL_ATTR = 0o644 << 16
FIXED_CREATE_SYSTEM = 3  # unix


def collect_files(source: str) -> list[str]:
    relpaths = []
    for root, dirs, files in os.walk(source):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED_DIRS)
        for name in files:
            if name in EXCLUDED_FILES or name.endswith(EXCLUDED_SUFFIXES):
                continue
            full = os.path.join(root, name)
            relpaths.append(os.path.relpath(full, source))
    return sorted(relpaths)


def build(source: str, output: str, top_dir: str | None) -> int:
    relpaths = collect_files(source)
    if not relpaths:
        print(f"error: no files found under {source}", file=sys.stderr)
        return 1

    out_parent = os.path.dirname(os.path.abspath(output))
    os.makedirs(out_parent, exist_ok=True)

    with zipfile.ZipFile(output, "w", zipfile.ZIP_STORED) as zf:
        for rel in relpaths:
            # Forward slashes in arcnames regardless of host OS.
            arcname = rel.replace(os.sep, "/")
            if top_dir:
                arcname = f"{top_dir}/{arcname}"
            info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE_TIME)
            info.external_attr = FIXED_EXTERNAL_ATTR
            info.create_system = FIXED_CREATE_SYSTEM
            info.compress_type = zipfile.ZIP_STORED
            with open(os.path.join(source, rel), "rb") as f:
                zf.writestr(info, f.read())

    print(f"wrote {output} ({len(relpaths)} files)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="add-on source directory")
    parser.add_argument("--output", required=True, help="output .ankiaddon path")
    parser.add_argument(
        "--top-dir",
        help="prefix every entry with this top-level directory (folder-shaped zip)",
    )
    args = parser.parse_args()

    if not os.path.isdir(args.source):
        print(f"error: source is not a directory: {args.source}", file=sys.stderr)
        return 1

    return build(args.source, args.output, args.top_dir)


if __name__ == "__main__":
    sys.exit(main())
