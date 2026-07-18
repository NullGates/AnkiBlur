#!/usr/bin/env python3
"""Probe an aqt (and anki) release for the symbols the AnkiBlur add-on relies on.

The AnkiBlur runtime payload lives entirely in the bundled add-on, which
monkeypatches/wraps a small set of stable aqt APIs (see
addons/anki_webview_addon/ankiblur_background_theme/). Those wraps are guarded
at runtime (the add-on's tripwire), but this probe is the *build-time /
scheduled* detection net: it downloads a given aqt release from PyPI and
statically asserts every wrapped symbol still exists, so upstream drift is
caught the day it lands instead of on end users' machines.

Static AST analysis is used on purpose: importing aqt would require PyQt6 +
QtWebEngine at runtime; parsing the wheel needs nothing but pip and stdlib.

Usage:
    probe-aqt-symbols.py --version 25.9.2      # probe a pinned release
    probe-aqt-symbols.py --latest              # probe the newest PyPI release
    probe-aqt-symbols.py --site-packages PATH  # probe an existing install

Exit status: 0 if every symbol is present, 1 otherwise (missing symbols are
listed on stdout), 2 on operational errors (download failure etc.).
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

# Every (module, kind, target) the add-on touches.
# kind is one of:
#   module_name  - top-level assignment / def / class / import alias
#   hook_name    - like module_name, but also resolved through a
#                  `from X import *` re-export (aqt/gui_hooks.py re-exports
#                  the generated hook objects from _aqt/hooks.py)
#   method       - "Class.method" function defined in the class body
#   self_attr    - "Class.attr" assigned via self.<attr> somewhere in the class
#   class_member - "Class.MEMBER" assigned in the class body (enum members)
CHECKS: list[tuple[str, str, str]] = [
    # aqt/__init__.py — entry points used by every add-on module
    ("aqt/__init__.py", "module_name", "mw"),
    ("aqt/__init__.py", "module_name", "appVersion"),
    # aqt/webview.py — wrapped by webview_transparency.py
    ("aqt/webview.py", "module_name", "AnkiWebView"),
    ("aqt/webview.py", "method", "AnkiWebView.__init__"),
    ("aqt/webview.py", "method", "AnkiWebView.on_theme_did_change"),
    ("aqt/webview.py", "method", "AnkiWebView.standard_css"),
    ("aqt/webview.py", "self_attr", "AnkiWebView._kind"),
    ("aqt/webview.py", "class_member", "AnkiWebViewKind.MAIN"),
    ("aqt/webview.py", "class_member", "AnkiWebViewKind.TOP_TOOLBAR"),
    ("aqt/webview.py", "class_member", "AnkiWebViewKind.BOTTOM_TOOLBAR"),
    # aqt/main.py — the Windows-native strategy (win_native.py) hangs its
    # state off mw and reads these AnkiQt attributes
    ("aqt/main.py", "module_name", "AnkiQt"),
    ("aqt/main.py", "self_attr", "AnkiQt.form"),
    ("aqt/main.py", "self_attr", "AnkiQt.fullscreen"),
    # aqt/gui_hooks.py — hooks appended by __init__.py and tripwire.py
    ("aqt/gui_hooks.py", "hook_name", "main_window_did_init"),
    ("aqt/gui_hooks.py", "hook_name", "webview_will_set_content"),
    ("aqt/gui_hooks.py", "hook_name", "theme_did_change"),
    # aqt/overview.py — wrapped for the finished/congrats screen
    ("aqt/overview.py", "method", "Overview._show_finished_screen"),
    # misc singletons / helpers imported by the add-on
    ("aqt/theme.py", "module_name", "theme_manager"),
    ("aqt/utils.py", "module_name", "showInfo"),
    # anki/hooks.py — anki.hooks.wrap powers every monkeypatch above
    ("anki/hooks.py", "module_name", "wrap"),
]


def _top_level_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                names.add(alias.asname or alias.name.split(".")[0])
    return names


def _star_import_sources(tree: ast.Module) -> list[str]:
    """Module names star-imported at the top level ('from X import *')."""
    return [
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
        and node.module
        and any(alias.name == "*" for alias in node.names)
    ]


def _find_class(tree: ast.Module, name: str) -> ast.ClassDef | None:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node
    return None


def _class_has_method(cls: ast.ClassDef, method: str) -> bool:
    return any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == method
        for node in cls.body
    )


def _class_has_member(cls: ast.ClassDef, member: str) -> bool:
    for node in cls.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == member:
                    return True
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name) and node.target.id == member:
                return True
    return False


def _class_sets_self_attr(cls: ast.ClassDef, attr: str) -> bool:
    for node in ast.walk(cls):
        if isinstance(node, ast.Attribute) and node.attr == attr:
            if isinstance(node.value, ast.Name) and node.value.id == "self":
                if isinstance(node.ctx, ast.Store):
                    return True
    return False


def check_symbols(site_packages: Path) -> list[str]:
    """Return a list of failure descriptions (empty means all symbols exist)."""
    failures: list[str] = []
    trees: dict[str, ast.Module | None] = {}

    def _tree_for(module: str) -> ast.Module | None:
        if module not in trees:
            path = site_packages / module
            if not path.is_file():
                trees[module] = None
            else:
                trees[module] = ast.parse(path.read_text(encoding="utf-8"))
        return trees[module]

    def _name_visible(module: str, name: str, depth: int = 0) -> bool:
        """True if `name` is defined in `module` or one of its star-imports."""
        tree = _tree_for(module)
        if tree is None or depth > 2:
            return False
        if name in _top_level_names(tree):
            return True
        for source in _star_import_sources(tree):
            source_file = source.replace(".", "/") + ".py"
            if _name_visible(source_file, name, depth + 1):
                return True
        return False

    for module, kind, target in CHECKS:
        tree = _tree_for(module)
        if tree is None:
            failures.append(f"{module}: file missing (needed for {kind} {target})")
            continue

        ok = False
        if kind == "module_name":
            ok = target in _top_level_names(tree)
        elif kind == "hook_name":
            ok = _name_visible(module, target)
        else:
            cls_name, _, member = target.partition(".")
            cls = _find_class(tree, cls_name)
            if cls is None:
                failures.append(f"{module}: class {cls_name} missing ({kind} {target})")
                continue
            if kind == "method":
                ok = _class_has_method(cls, member)
            elif kind == "self_attr":
                ok = _class_sets_self_attr(cls, member)
            elif kind == "class_member":
                ok = _class_has_member(cls, member)
            else:
                raise ValueError(f"unknown check kind: {kind}")
        if not ok:
            failures.append(f"{module}: {kind} {target} not found")

    return failures


def _download_and_extract(package: str, version: str | None, dest: Path) -> str:
    """pip-download the wheel for `package` and extract its .py files into dest.

    Returns the downloaded wheel's version string.
    """
    spec = f"{package}=={version}" if version else package
    dl_dir = dest / f"_dl_{package}"
    dl_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable, "-m", "pip", "download",
        "--no-deps", "--only-binary", ":all:",
        "--dest", str(dl_dir), spec,
    ]
    print(f"[probe] $ {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr, file=sys.stderr)
        raise RuntimeError(f"pip download failed for {spec}")

    wheels = sorted(dl_dir.glob(f"{package}-*.whl"))
    if not wheels:
        raise RuntimeError(f"no wheel downloaded for {spec} in {dl_dir}")
    wheel = wheels[-1]
    wheel_version = wheel.name.split("-")[1]
    print(f"[probe] extracting {wheel.name}")
    # The aqt wheel ships both aqt/ and the generated _aqt/ package (the
    # gui_hooks re-export source); extract .py sources from both.
    prefixes = (f"{package}/", f"_{package}/")
    with zipfile.ZipFile(wheel) as zf:
        for name in zf.namelist():
            # Only the packages' own .py sources are needed for AST checks.
            if name.startswith(prefixes) and name.endswith(".py"):
                zf.extract(name, dest)
    return wheel_version


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--version", help="probe this exact aqt release from PyPI")
    group.add_argument("--latest", action="store_true",
                       help="probe the newest aqt release on PyPI")
    group.add_argument("--site-packages", type=Path,
                       help="probe an existing site-packages directory instead")
    args = parser.parse_args()

    if args.site_packages:
        site_packages = args.site_packages
        label = str(site_packages)
        if not (site_packages / "aqt").is_dir():
            print(f"[probe] ERROR: no aqt package under {site_packages}")
            return 2
    else:
        tmp = tempfile.mkdtemp(prefix="ankiblur-probe-")
        site_packages = Path(tmp)
        try:
            aqt_version = _download_and_extract(
                "aqt", args.version, site_packages)
            # anki.hooks.wrap comes from the anki wheel; match aqt's version.
            _download_and_extract("anki", aqt_version, site_packages)
        except RuntimeError as e:
            print(f"[probe] ERROR: {e}")
            return 2
        label = f"aqt {aqt_version}"

    failures = check_symbols(site_packages)
    if failures:
        print(f"[probe] FAILED against {label}: "
              f"{len(failures)} missing symbol(s):")
        for failure in failures:
            print(f"[probe]   - {failure}")
        print("[probe] The AnkiBlur add-on wraps these symbols; upstream has "
              "drifted. Update the add-on before shipping against this aqt.")
        return 1

    print(f"[probe] OK against {label}: all {len(CHECKS)} wrapped symbols present")
    return 0


if __name__ == "__main__":
    sys.exit(main())
