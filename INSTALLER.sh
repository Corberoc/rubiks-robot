#!/bin/bash
# ============================================================================
#  INSTALLER.sh  (v2 - pipeline + tools/services)
#  ------------------------------------------------
#  Objectif :
#     Point d’entrée “install” unique du projet Rubik’s Cube.
#     1) Lance l’installation du pipeline (apt + venv + requirements) via
#        `0_install_pipeline.sh`.
#     2) (Optionnel) Installe/active les outils + services systemd du dossier
#        `tools/` :
#         - wrapper safe shutdown : /usr/local/bin/rbx_safe_shutdown.sh
#         - service app au boot   : /etc/systemd/system/rbx-app.service
#         - service bouton GPIO3  : /etc/systemd/system/rbx-gpio3-shutdown.service
#     3) (Optionnel) Désactive l’audio onboard (dtparam=audio=off).
#
#  Usage :
#     ./INSTALLER.sh [--fast] [--tools|--no-tools] [--enable-services|--no-enable-services]
#                   [--disable-audio|--no-disable-audio]
#
#  Notes :
#     - Les actions “tools/services” utilisent sudo car elles touchent /etc et /usr/local.
#     - Par défaut, si le script est lancé en interactif, il proposera les options.
# ============================================================================

set -euo pipefail

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$BASE_DIR"
TOOLS_DIR="$PROJECT_DIR/tools"

VENV_DIR="${RUBIK_VENV_DIR:-$HOME/rubik-env}"

PIPELINE_ARGS=()
INSTALL_TOOLS_MODE="ask"     # ask|yes|no
ENABLE_SERVICES_MODE="ask"   # ask|yes|no (pertinent seulement si tools=yes)
DISABLE_AUDIO_MODE="ask"     # ask|yes|no

# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------
log()  { echo -e "🔹 $*"; }
ok()   { echo -e "✅ $*"; }
warn() { echo -e "⚠️  $*"; }
err()  { echo -e "❌ $*" >&2; }

is_tty() { [ -t 0 ]; }

ask_yn() {
  # ask_yn "question" "default"  -> echo yes|no
  # default: y|n
  local q="$1"
  local def="${2:-n}"
  local prompt=""
  local ans=""
  if [ "$def" = "y" ]; then
    prompt="[O/n]"
  else
    prompt="[o/N]"
  fi
  while true; do
    read -r -p "$q $prompt " ans || true
    ans="${ans:-}"
    if [ -z "$ans" ]; then
      if [ "$def" = "y" ]; then echo "yes"; else echo "no"; fi
      return 0
    fi
    case "${ans,,}" in
      o|oui|y|yes) echo "yes"; return 0 ;;
      n|non|no)    echo "no";  return 0 ;;
      *) echo "Répondre par o/oui ou n/non." ;;
    esac
  done
}

usage() {
  cat <<'USAGE'
Usage:
  ./INSTALLER.sh [--fast] [--tools|--no-tools] [--enable-services|--no-enable-services]
                 [--disable-audio|--no-disable-audio]

Options:
  --fast                 Passe --fast à 0_install_pipeline.sh (saute apt update/upgrade)
  --tools / --no-tools    Installe les outils/services du dossier tools/ (systemd + wrapper)
  --enable-services        Active + démarre les services systemd (si --tools)
  --no-enable-services     Installe les unités sans les activer (si --tools)
  --disable-audio          Applique dtparam=audio=off dans config.txt (reboot requis)
  --no-disable-audio       Ne touche pas à l'audio
USAGE
}

# --------------------------------------------------------------------
# Audio off
# --------------------------------------------------------------------
disable_audio() {
    local CONFIG="/boot/firmware/config.txt"
    [ ! -f "$CONFIG" ] && CONFIG="/boot/config.txt"

    if [ ! -f "$CONFIG" ]; then
        err "[ERROR] config.txt introuvable"
        return 1
    fi

    sudo cp "$CONFIG" "${CONFIG}.bak"

    if grep -q "dtparam=audio=on" "$CONFIG"; then
        sudo sed -i 's/dtparam=audio=on/dtparam=audio=off/' "$CONFIG"
        ok "Audio désactivé (reboot requis)"
    elif grep -q "dtparam=audio=off" "$CONFIG"; then
        warn "Audio déjà désactivé"
    else
        echo "dtparam=audio=off" | sudo tee -a "$CONFIG" > /dev/null
        ok "Ligne audio ajoutée (reboot requis)"
    fi
}

# --------------------------------------------------------------------
# Install tools/services
# --------------------------------------------------------------------
install_tools_services() {
  log "Installation tools/services (safe shutdown + systemd)…"

  if [ ! -d "$TOOLS_DIR" ]; then
    err "Dossier tools/ introuvable : $TOOLS_DIR"
    return 1
  fi
  if [ ! -f "$TOOLS_DIR/rbx_safe_shutdown.py" ] || [ ! -f "$TOOLS_DIR/gpio3_button.py" ]; then
    err "Fichiers tools manquants (rbx_safe_shutdown.py / gpio3_button.py)."
    return 1
  fi

  # 0) chmod sur les scripts du repo (best-effort)
  chmod +x "$PROJECT_DIR"/*.sh 2>/dev/null || true
  chmod +x "$TOOLS_DIR"/*.sh 2>/dev/null || true

  # 1) Wrapper safe shutdown généré dynamiquement (chemins réels injectés)
  local TMP_WRAPPER
  TMP_WRAPPER="$(mktemp)"
  cat > "$TMP_WRAPPER" <<EOF
#!/bin/bash
set -e
# Auto-généré par INSTALLER.sh — ne pas éditer manuellement
export RBX_CONFIG="${PROJECT_DIR}/config.json"
systemctl stop rbx-app.service || true
"${VENV_PY}" "${PROJECT_DIR}/tools/rbx_safe_shutdown.py" || true
/sbin/poweroff
EOF
  sudo install -m 755 "$TMP_WRAPPER" /usr/local/bin/rbx_safe_shutdown.sh
  rm -f "$TMP_WRAPPER"
  ok "Wrapper installé : /usr/local/bin/rbx_safe_shutdown.sh"

  # 2) Units systemd (générées sans BOM)
  sudo tee /etc/systemd/system/rbx-app.service >/dev/null <<EOF
[Unit]
Description=Rubiks Robot - App principale (9_main.sh)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${PROJECT_DIR}
ExecStart=/bin/bash ${PROJECT_DIR}/9_main.sh --no-sudo
Restart=on-failure
RestartSec=2
TimeoutStopSec=3
KillSignal=SIGTERM
Environment=RBX_CONFIG=${PROJECT_DIR}/config.json

[Install]
WantedBy=multi-user.target
EOF
  ok "Unit installée : /etc/systemd/system/rbx-app.service"

  sudo tee /etc/systemd/system/rbx-gpio3-shutdown.service >/dev/null <<EOF
[Unit]
Description=Rubiks Robot - GPIO3 button (short restart / long shutdown)
After=multi-user.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/tools/gpio3_button.py
Restart=always
RestartSec=0.2

[Install]
WantedBy=multi-user.target
EOF
  ok "Unit installée : /etc/systemd/system/rbx-gpio3-shutdown.service"

  # 3) Reload
  sudo systemctl daemon-reload
  sudo systemctl reset-failed rbx-app.service rbx-gpio3-shutdown.service 2>/dev/null || true
  ok "systemd: daemon-reload + reset-failed"

  return 0
}

enable_tools_services() {
  log "Activation + démarrage des services (bouton puis app)…"
  sudo systemctl enable rbx-gpio3-shutdown.service
  sudo systemctl enable rbx-app.service
  ok "Services activés"

  echo
  echo "🧪 Validation rapide :"
  echo "  - Logs bouton : sudo journalctl -u rbx-gpio3-shutdown.service -f"
  echo "  - Logs app    : sudo journalctl -u rbx-app.service -n 50 --no-pager"
}

# --------------------------------------------------------------------
# Parse args
# --------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    --fast)
      PIPELINE_ARGS+=("--fast")
      shift
      ;;
    --tools)
      INSTALL_TOOLS_MODE="yes"
      shift
      ;;
    --no-tools)
      INSTALL_TOOLS_MODE="no"
      shift
      ;;
    --enable-services)
      ENABLE_SERVICES_MODE="yes"
      shift
      ;;
    --no-enable-services)
      ENABLE_SERVICES_MODE="no"
      shift
      ;;
    --disable-audio)
      DISABLE_AUDIO_MODE="yes"
      shift
      ;;
    --no-disable-audio)
      DISABLE_AUDIO_MODE="no"
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      # on passe tout le reste à 0_install_pipeline.sh
      PIPELINE_ARGS+=("$1")
      shift
      ;;
  esac
done

echo "============================================================"
echo "🚀 Installation du pipeline Rubik's Cube (Linux / Raspberry Pi)"
echo "============================================================"
echo "📁 Projet      : $PROJECT_DIR"
echo "🧰 Tools       : $TOOLS_DIR"
echo "🐍 Venv        : $VENV_DIR"
echo "============================================================"
echo

# --------------------------------------------------------------------
# 1) Pipeline install
# --------------------------------------------------------------------
if [ -f "$PROJECT_DIR/0_install_pipeline.sh" ]; then
  log "Lancement de 0_install_pipeline.sh ${PIPELINE_ARGS[*]:-} ..."
  bash "$PROJECT_DIR/0_install_pipeline.sh" "${PIPELINE_ARGS[@]}"
  ok "Pipeline installé"
else
  err "Fichier 0_install_pipeline.sh introuvable."
  exit 1
fi

# Résolution de VENV_PY ici : le venv vient d'être créé par 0_install_pipeline.sh
VENV_PY="$VENV_DIR/bin/python3"
if [ ! -x "$VENV_PY" ]; then
  warn "Venv introuvable après installation : $VENV_PY"
  warn "Fallback sur /usr/bin/python3 — vérifie l'étape venv dans 0_install_pipeline.sh"
  VENV_PY="/usr/bin/python3"
fi
log "Python pour les services : $VENV_PY"

# --------------------------------------------------------------------
# 2.1) Maj du main
# --------------------------------------------------------------------
# Patch 9_main.sh avec les chemins réels
if [ -f "$PROJECT_DIR/9_main.sh" ]; then
  sed -i "s|VENV_DIR=.*|VENV_DIR=\"${VENV_DIR}\"|" "$PROJECT_DIR/9_main.sh"
  sed -i "s|PROJECT_DIR=.*|PROJECT_DIR=\"${PROJECT_DIR}\"|" "$PROJECT_DIR/9_main.sh"
  ok "9_main.sh patché avec les chemins réels"
else
  warn "9_main.sh introuvable, patch ignoré"
fi
# --------------------------------------------------------------------
# 2.2) Optional audio disable
# --------------------------------------------------------------------
if [ "$DISABLE_AUDIO_MODE" = "ask" ] && is_tty; then
  if [ "$(ask_yn "🔇 Désactiver l'audio onboard (dtparam=audio=off) ?" "n")" = "yes" ]; then
    DISABLE_AUDIO_MODE="yes"
  else
    DISABLE_AUDIO_MODE="no"
  fi
fi

if [ "$DISABLE_AUDIO_MODE" = "yes" ]; then
  disable_audio || true
fi

# --------------------------------------------------------------------
# 3) Optional tools/services install
# --------------------------------------------------------------------
if [ "$INSTALL_TOOLS_MODE" = "ask" ] && is_tty; then
  if [ "$(ask_yn "🧩 Installer aussi les services systemd + safe shutdown (tools/) ?" "y")" = "yes" ]; then
    INSTALL_TOOLS_MODE="yes"
  else
    INSTALL_TOOLS_MODE="no"
  fi
fi

if [ "$INSTALL_TOOLS_MODE" = "yes" ]; then
  install_tools_services

  if [ "$ENABLE_SERVICES_MODE" = "ask" ] && is_tty; then
    if [ "$(ask_yn "▶️  Activer + démarrer les services maintenant ?" "y")" = "yes" ]; then
      ENABLE_SERVICES_MODE="yes"
    else
      ENABLE_SERVICES_MODE="no"
    fi
  fi

  if [ "$ENABLE_SERVICES_MODE" = "yes" ]; then
    enable_tools_services
  else
    warn "Services installés mais NON activés."
    echo "Pour activer plus tard :"
    echo "  sudo systemctl enable --now rbx-gpio3-shutdown.service"
    echo "  sudo systemctl enable --now rbx-app.service"
  fi
else
  warn "Tools/services non installés (tu peux relancer avec --tools)."
fi

echo
echo "✅ Installation terminée."
echo "============================================================"