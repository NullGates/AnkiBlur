#!/bin/bash
# dev_patch_local_macos.sh
#
# Applique les patches AnkiBlur (main + webview) sur une install locale macOS
# pour tester le glassmorphism sans rebuild complet via la CI.
#
# Usage:
#   ./scripts/dev_patch_local_macos.sh
#   ./scripts/dev_patch_local_macos.sh /chemin/vers/AnkiBlur.app
#
# Le script:
#   1. localise l'install AnkiBlur.app (ou Anki.app)
#   2. trouve le .venv embarqué (créé par le launcher au 1er lancement)
#   3. restaure les .py originaux depuis les .backup si présents
#   4. applique les patches
#   5. relance l'app

set -euo pipefail

RED=$'\033[0;31m'; GREEN=$'\033[0;32m'; YELLOW=$'\033[1;33m'; BLUE=$'\033[0;34m'; NC=$'\033[0m'
log()  { echo "${BLUE}[..]${NC} $*"; }
ok()   { echo "${GREEN}[ok]${NC} $*"; }
warn() { echo "${YELLOW}[!!]${NC} $*"; }
err()  { echo "${RED}[KO]${NC} $*" >&2; }

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MAIN_PATCH="$REPO_ROOT/patches/0B_MACOS_anki_qt_window_main/anki_qt_window_lib_main.patch"
WEBVIEW_PATCH="$REPO_ROOT/patches/0C_anki_qt_window_webview/anki_qt_window_lib_webview.patch"

[[ -f "$MAIN_PATCH" ]]   || { err "patch introuvable: $MAIN_PATCH"; exit 1; }
[[ -f "$WEBVIEW_PATCH" ]] || { err "patch introuvable: $WEBVIEW_PATCH"; exit 1; }

# --- 1. localiser l'app -----------------------------------------------------
APP="${1:-}"
if [[ -z "$APP" ]]; then
    for cand in "/Applications/AnkiBlur.app" "/Applications/Anki.app" \
                "$HOME/Applications/AnkiBlur.app" "$HOME/Applications/Anki.app"; do
        if [[ -d "$cand" ]]; then APP="$cand"; break; fi
    done
fi
[[ -d "$APP" ]] || { err "Aucune AnkiBlur.app trouvée. Passe le chemin en argument."; exit 1; }
ok "App: $APP"

# --- 2. trouver le venv ------------------------------------------------------
# Le launcher (uv) installe le venv dans le data dir d'Anki, pas dans le bundle.
# On scanne les emplacements typiques.
VENV=""
for cand in \
    "$HOME/Library/Application Support/AnkiBlur/.venv" \
    "$HOME/Library/Application Support/Anki2/.venv" \
    "$HOME/Library/Application Support/Anki/.venv" \
    "$HOME/.local/share/AnkiBlur/.venv" \
    "$HOME/Library/Caches/AnkiBlur/.venv" ; do
    if [[ -d "$cand" ]]; then VENV="$cand"; break; fi
done

if [[ -z "$VENV" ]]; then
    # plan B: scan dynamique
    log "Scan dynamique du venv (peut prendre quelques secondes)..."
    VENV="$(find "$HOME/Library" -maxdepth 6 -type d -name ".venv" 2>/dev/null \
            | xargs -I{} sh -c 'test -f "{}/lib/python3.13/site-packages/aqt/main.py" && echo {}' \
            | head -1)"
fi

if [[ -z "$VENV" ]]; then
    err "Pas de .venv trouvé. As-tu déjà lancé AnkiBlur au moins une fois ?"
    err "Le launcher crée le venv au 1er démarrage."
    exit 1
fi
ok "Venv: $VENV"

MAIN_PY="$VENV/lib/python3.13/site-packages/aqt/main.py"
WEBVIEW_PY="$VENV/lib/python3.13/site-packages/aqt/webview.py"
[[ -f "$MAIN_PY" ]]    || { err "$MAIN_PY introuvable"; exit 1; }
[[ -f "$WEBVIEW_PY" ]] || { err "$WEBVIEW_PY introuvable"; exit 1; }

# --- 3. restaurer les backups si présents -----------------------------------
restore() {
    local f="$1"
    local b="${f}.py.backup"     # convention launcher (avec extension répétée)
    local b2="${f}.backup"
    for cand in "$b" "$b2"; do
        if [[ -f "$cand" ]]; then
            log "Restore $(basename "$f") depuis $(basename "$cand")"
            cp "$cand" "$f"
            return
        fi
    done
    # pas de backup → on crée un .ankiblur_orig avant la 1re application
    if [[ ! -f "${f}.ankiblur_orig" ]]; then
        cp "$f" "${f}.ankiblur_orig"
        ok "Backup créé: ${f}.ankiblur_orig"
    else
        cp "${f}.ankiblur_orig" "$f"
        log "Restored from .ankiblur_orig"
    fi
}
restore "$MAIN_PY"
restore "$WEBVIEW_PY"

# --- 4. quitter Anki s'il tourne --------------------------------------------
if pgrep -fl "AnkiBlur\.app|Anki\.app" >/dev/null; then
    warn "Anki tourne, on le ferme..."
    osascript -e 'quit app "AnkiBlur"' 2>/dev/null || true
    osascript -e 'quit app "Anki"'     2>/dev/null || true
    sleep 1
fi

# --- 5. appliquer les patches -----------------------------------------------
log "Patch main.py..."
patch -p4 -d "$VENV" < "$MAIN_PATCH" || { err "main patch failed"; exit 1; }
log "Patch webview.py..."
patch -p4 -d "$VENV" < "$WEBVIEW_PATCH" || { err "webview patch failed"; exit 1; }

# --- 6. vérifier qu'on a bien pyobjc dans le venv ---------------------------
PYBIN="$VENV/bin/python3"
if [[ -x "$PYBIN" ]]; then
    if "$PYBIN" -c "import Cocoa, objc" 2>/dev/null; then
        ok "pyobjc OK"
    else
        warn "pyobjc absent du venv -> on l'installe"
        "$PYBIN" -m pip install pyobjc-core pyobjc-framework-Cocoa pyobjc-framework-Quartz \
            --quiet --disable-pip-version-check 2>&1 | tail -3
    fi
fi

# --- 7. relancer ------------------------------------------------------------
ok "Tous les patches appliqués. Relancement de l'app..."
open "$APP"
echo ""
ok "Pour voir les logs [AnkiBlur] en live, lance dans un autre terminal:"
echo "    log stream --predicate 'eventMessage CONTAINS \"AnkiBlur\"' --info"
