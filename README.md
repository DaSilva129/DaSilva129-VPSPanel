# DaSilva129-VPSPanel

Mini tableau de bord de monitoring pour serveur Linux : CPU, RAM, swap, disque, débit réseau, températures, GPU NVIDIA et top processus.

Pas de dépendance lourde : un seul script Python (`psutil`) et une page HTML qui se rafraîchit toutes les 2 secondes.

## Aperçu des métriques

| Carte | Source |
|---|---|
| CPU, charge moyenne | `psutil`, `os.getloadavg()` |
| RAM, swap | `psutil.virtual_memory()`, `psutil.swap_memory()` |
| Disque `/` | `psutil.disk_usage()` |
| Réseau (débit ↓ ↑, totaux) | `psutil.net_io_counters()` |
| Températures | `psutil.sensors_temperatures()` |
| GPU NVIDIA | `nvidia-smi` (si installé) |
| Top processus RAM | `psutil.process_iter()` |

## Installation rapide

```bash
git clone https://github.com/DaSilva129/DaSilva129-VPSPanel.git
cd DaSilva129-VPSPanel
sudo ./install.sh
```

Le script installe Python et `psutil`, copie les fichiers dans `/opt/vps-panel` et lance le panel en service systemd (redémarrage automatique au boot).

## Accès au panel

Le panel écoute uniquement en local (`127.0.0.1:8080`) pour ne pas être exposé sur internet. Depuis ton PC :

```bash
ssh -L 8080:127.0.0.1:8080 utilisateur@ip_du_vps
```

Puis ouvre http://localhost:8080 dans ton navigateur.

## Test sans installation

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python app.py
```

## Configuration

Variables d'environnement (à mettre dans le fichier service si besoin) :

| Variable | Défaut | Rôle |
|---|---|---|
| `PANEL_HOST` | `127.0.0.1` | Adresse d'écoute (`0.0.0.0` = accessible de partout, à éviter sans protection) |
| `PANEL_PORT` | `8080` | Port d'écoute |

## Remarques

- **Températures** : la plupart des VPS (virtualisés) n'exposent aucun capteur. La carte affichera alors un message, c'est normal.
- **GPU** : affiché seulement si `nvidia-smi` est disponible sur la machine.
- **Sécurité** : ce panel donne des informations sur ton serveur. Ne l'expose pas publiquement sans authentification (tunnel SSH, ou reverse proxy nginx avec mot de passe).

## Commandes utiles

```bash
systemctl status vps-panel      # statut
journalctl -u vps-panel -f      # logs
sudo systemctl restart vps-panel
```

## Désinstallation

```bash
sudo systemctl disable --now vps-panel
sudo rm /etc/systemd/system/vps-panel.service
sudo rm -rf /opt/vps-panel
sudo systemctl daemon-reload
```
