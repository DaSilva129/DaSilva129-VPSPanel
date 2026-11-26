#!/usr/bin/env bash
# Installe le VPS Panel comme service systemd (démarrage automatique).
set -euo pipefail

cd "$(dirname "$0")"

APP_DIR="/opt/vps-panel"
SERVICE="vps-panel"
PORT="${PANEL_PORT:-8080}"

if [[ $EUID -ne 0 ]]; then
  echo "Lance ce script avec sudo : sudo ./install.sh" >&2
  exit 1
fi

echo "==> Installation de Python 3 et venv"
apt-get update -qq
apt-get install -y -qq python3 python3-venv

echo "==> Copie des fichiers dans $APP_DIR"
mkdir -p "$APP_DIR"
cp app.py index.html requirements.txt "$APP_DIR/"

echo "==> Création de l'environnement virtuel et installation de psutil"
python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -q -r "$APP_DIR/requirements.txt"

echo "==> Création du service systemd"
cat > "/etc/systemd/system/$SERVICE.service" <<EOF
[Unit]
Description=VPS Panel (monitoring)
After=network.target

[Service]
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/app.py
WorkingDirectory=$APP_DIR
Environment=PANEL_HOST=127.0.0.1
Environment=PANEL_PORT=$PORT
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now "$SERVICE"

echo
echo "✅ Panel installé et lancé sur 127.0.0.1:$PORT"
echo "   Accès depuis ton PC (tunnel SSH) :"
echo "   ssh -L $PORT:127.0.0.1:$PORT utilisateur@ip_du_vps"
echo "   puis ouvre http://localhost:$PORT"
echo
echo "   Statut : systemctl status $SERVICE"
echo "   Logs   : journalctl -u $SERVICE -f"
