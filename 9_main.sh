#!/bin/bash
# =============================================================================
#  9_main.sh
#  -----------------------
#  Objectif :
#     Script de lancement “clé en main” du **mode robot** (version finale) :
#     démarre l’application principale du projet en utilisant le **Python du venv**
#     et en garantissant que l’on est dans le bon dossier projet.
#
#  Usage :
#     - Par défaut (ROOT) :
#         ./9_main.sh
#         -> lance avec `sudo -E` (utile NeoPixel / /dev/mem / DMA)
#
#     - Forcer NON-ROOT (debug / test) :
#         ./9_main.sh --no-sudo
#         ./9_main.sh --user
#
#  Notes :
#     - Si exécuté déjà en root (id -u = 0), le script ne relance pas sudo.
#     - `exec` remplace le process shell par Python (meilleur pour systemd).
# =============================================================================

set -e

echo "📺 Lancement de l'écran (menu) + pipeline..."

VENV_DIR="/home/rubik/rubik-env"
PROJECT_DIR="/home/rubik/rubiks-robot"

MODULE="Ecran.main"
VENV_PY="$VENV_DIR/bin/python3"

# -------------------------
# Mode privilèges
# -------------------------
# Par défaut : sudo (root)
# Option : --no-sudo / --user => non-root
USE_SUDO=1
if [[ "${1:-}" == "--no-sudo" || "${1:-}" == "--user" ]]; then
  USE_SUDO=0
fi

# Si on est déjà root, inutile de relancer sudo
if [ "$(id -u)" -eq 0 ]; then
  USE_SUDO=0
fi

# -------------------------
# Checks
# -------------------------
if [ ! -x "$VENV_PY" ]; then
  echo "❌ Python du venv introuvable/exécutable : $VENV_PY"
  exit 1
fi

cd "$PROJECT_DIR" || { echo "❌ Projet introuvable : $PROJECT_DIR"; exit 1; }

if [ ! -f "Ecran/main.py" ]; then
  echo "❌ Fichier Ecran/main.py introuvable dans le projet."
  exit 1
fi

# -------------------------
# Run
# -------------------------
echo "🖥️  Démarrage de $MODULE (python du venv)..."

if [ "$USE_SUDO" -eq 1 ]; then
  echo "🔐 Mode root (par défaut via sudo -E)."
  exec sudo -E "$VENV_PY" -m "$MODULE"
else
  echo "👤 Mode non-root."
  exec "$VENV_PY" -m "$MODULE"
fi
