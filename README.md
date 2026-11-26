# DaSilva129-VPSPanel

Mini tableau de bord de monitoring pour serveur Linux, pensé pour être léger et lisible.

- **Processeur** : utilisation, nombre de cœurs, charge moyenne, historique
- **Mémoire** : RAM et swap
- **Disque** : espace utilisé et libre
- **Réseau** : débit en direct (reçu / envoyé), historique et totaux
- **Températures** : si le matériel les expose
- **GPU NVIDIA** : utilisation, VRAM, température (si `nvidia-smi` est présent)
- **Programmes** : les plus gourmands en mémoire
- **Statuts clairs** : Normal, Élevé, Critique, avec une bannière de santé globale

Le serveur est un seul script Python (`psutil` est la seule dépendance) et une page HTML qui se met à jour toutes les 2 secondes.

## Prérequis

**Serveur**
- Linux Debian ou Ubuntu (testé sur Ubuntu 24.04, ARM64 et x86_64)
- Python 3.8 ou plus récent (présent par défaut sur Ubuntu 20.04+)
- Accès `sudo`
- Connexion internet pour installer `psutil`
- Facultatif : `nvidia-smi` pour afficher le GPU NVIDIA

**Poste local**
- Un client SSH (intégré sous Windows 10/11, macOS et Linux)
- Un navigateur web
- Facultatif : Git et VS Code pour gérer le dépôt

**Facultatif, pour l'accès depuis internet**
- Un nom de domaine (par exemple DuckDNS) pointant vers ton IP publique
- Une redirection de port sur ta box (TCP, port externe `4544` vers le port `4544` du serveur)
- nginx et `apache2-utils` pour ajouter un mot de passe

## Installation

```bash
git clone https://github.com/DaSilva129/DaSilva129-VPSPanel.git
cd DaSilva129-VPSPanel
sudo bash install.sh
```

Le script :
1. installe `python3` et `python3-venv` ;
2. copie les fichiers dans `/opt/vps-panel` ;
3. crée un environnement virtuel et installe `psutil` ;
4. crée et lance le service systemd `vps-panel` (démarrage automatique au boot).

Le panel écoute uniquement sur `127.0.0.1:8080`, donc il n'est pas exposé sur internet.

## Accès au panel

### Depuis ton PC, avec un tunnel SSH (recommandé)

```bash
ssh -L 8080:127.0.0.1:8080 utilisateur@ip_du_serveur
```

Puis ouvre http://localhost:8080. Garde le terminal ouvert tant que tu veux consulter le panel.

### Depuis internet, avec nginx et un mot de passe

Le panel n'a pas d'authentification intégrée. Si tu veux y accéder depuis n'importe où, passe par nginx avec un mot de passe.

```bash
sudo apt-get install -y nginx apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd-panel TON_UTILISATEUR
sudo nano /etc/nginx/sites-available/vps-panel
```

Contenu du fichier :

```nginx
server {
    listen 4544;
    server_name ton-domaine.duckdns.org;

    auth_basic "VPS Panel";
    auth_basic_user_file /etc/nginx/.htpasswd-panel;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
    }
}
```

Active la configuration, ouvre le port et recharge nginx :

```bash
sudo ln -sf /etc/nginx/sites-available/vps-panel /etc/nginx/sites-enabled/vps-panel
sudo nginx -t && sudo systemctl reload nginx
sudo ufw allow 4544/tcp    # seulement si ufw est actif
```

Puis ouvre `http://ton-domaine.duckdns.org:4544` et connecte-toi.

> **Sécurité** : sans HTTPS, le mot de passe circule en clair. Utilise un mot de passe unique et prévois un certificat (Let's Encrypt via `certbot`) si tu veux un accès durable. Ne laisse jamais `PANEL_HOST` sur `0.0.0.0` sans protection.

## Mise à jour

Quand le dépôt GitHub évolue, il faut récupérer les nouveaux fichiers sur le serveur.

### Mettre à jour uniquement l'interface (index.html)

```bash
cd ~/DaSilva129-VPSPanel
git pull
sudo cp index.html /opt/vps-panel/index.html
```

Le HTML est relu à chaque requête : aucun redémarrage n'est nécessaire. Dans le navigateur, fais `Ctrl+F5`.

### Mettre à jour le backend (app.py)

```bash
cd ~/DaSilva129-VPSPanel
git pull
sudo cp app.py /opt/vps-panel/app.py
sudo systemctl restart vps-panel
```

### Tout mettre à jour d'un coup

```bash
cd ~/DaSilva129-VPSPanel
git pull
sudo cp app.py index.html requirements.txt /opt/vps-panel/
sudo /opt/vps-panel/venv/bin/pip install -q -r /opt/vps-panel/requirements.txt
sudo systemctl restart vps-panel
```

### Forcer la mise à jour (en cas de conflit)

Cette commande écrase les modifications faites directement sur le serveur :

```bash
cd ~/DaSilva129-VPSPanel
git fetch origin
git reset --hard origin/main
sudo cp app.py index.html requirements.txt /opt/vps-panel/
sudo systemctl restart vps-panel
```

### Vérifier la version installée

```bash
diff ~/DaSilva129-VPSPanel/index.html /opt/vps-panel/index.html && echo "index.html à jour"
diff ~/DaSilva129-VPSPanel/app.py /opt/vps-panel/app.py && echo "app.py à jour"
```

## Commandes utiles

```bash
systemctl status vps-panel        # état du service
sudo systemctl restart vps-panel  # redémarrer le panel
journalctl -u vps-panel -f        # suivre les logs en direct
curl -s http://127.0.0.1:8080/api/metrics | head -c 200   # tester l'API
```

## Configuration

Variables d'environnement, à mettre dans `/etc/systemd/system/vps-panel.service` (section `[Service]`), puis `sudo systemctl daemon-reload && sudo systemctl restart vps-panel` :

| Variable | Défaut | Rôle |
|---|---|---|
| `PANEL_HOST` | `127.0.0.1` | Adresse d'écoute. Laisse la valeur par défaut sauf si tu sais ce que tu fais. |
| `PANEL_PORT` | `8080` | Port d'écoute du panel |

## Dépannage

**`sudo: ./install.sh: command not found`** : lance le script avec `sudo bash install.sh`. Si tu veux pouvoir utiliser `./install.sh`, rends-le exécutable sur ton PC avant de le pousser :
```bash
git update-index --chmod=+x install.sh
```

**`$'\r': command not found`** : le script a des fins de ligne Windows. Corrige-les sur le serveur :
```bash
sed -i 's/\r$//' install.sh
sudo bash install.sh
```

**`apt-get update` échoue à cause d'un dépôt tiers (Docker, etc.)** : le dépôt bloque la mise à jour des paquets. Désactive-le temporairement dans `/etc/apt/sources.list.d/` (ajoute `#` devant chaque ligne) puis relance `sudo apt-get update`.

**La page affiche « Hors ligne »** : vérifie `systemctl status vps-panel` et `curl -s http://127.0.0.1:8080/api/metrics`.

**La température affiche « non exposé »** : c'est normal sur la plupart des VPS, qui sont virtualisés et n'ont pas de capteurs.

**Le GPU n'apparaît pas** : `nvidia-smi` doit fonctionner sur le serveur (`nvidia-smi` dans le terminal).

**Pas d'accès depuis internet** : vérifie dans cet ordre : `curl -I -u TON_UTILISATEUR http://127.0.0.1:4544/` (doit répondre `200`), la redirection du port 4544 sur ta box, la correspondance entre ton domaine et ton IP publique (`nslookup ton-domaine.duckdns.org`), et le pare-feu (`sudo ufw status`).

## Désinstallation

```bash
sudo systemctl disable --now vps-panel
sudo rm /etc/systemd/system/vps-panel.service
sudo systemctl daemon-reload
sudo rm -rf /opt/vps-panel
sudo rm -f /etc/nginx/sites-enabled/vps-panel /etc/nginx/sites-available/vps-panel /etc/nginx/.htpasswd-panel
sudo nginx -t && sudo systemctl reload nginx
```

## Licence

Usage personnel. Libre d'adapter à tes besoins.
