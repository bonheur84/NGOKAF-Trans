# NGOKAF TRANS

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)

🚌 **Application desktop Windows professionnelle de gestion de billets et bagages pour l'agence de transport NGOKAF TRANS**

Système complet de gestion de transport avec interface moderne, gestion des utilisateurs, facturation, et rapports détaillés.

---

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Captures d'écran](#-captures-d'écran)
- [Prérequis](#-prérequis)
- [Installation](#-installation)
- [Utilisation](#-utilisation)
- [Configuration](#-configuration)
- [Développement](#-développement)
- [Build de distribution](#-build-de-distribution)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Fonctionnalités

### 🎯 Gestion des opérations
- **Vente de billets** : Système de caisse intuitif pour les caissiers
- **Gestion des bagages** : Enregistrement et suivi des bagages
- **Gestion des trajets** : Création et modification des itinéraires
- **Gestion des bus** : Parc automobile complet
- **Gestion des conducteurs** : Base de données du personnel

### 👥 Gestion des utilisateurs
- **Rôles personnalisés** : Administrateur et Caissier
- **Contrôle d'accès** : Permissions par rôle
- **Sécurité** : Authentification sécurisée

### 💰 Facturation et rapports
- **Facturation automatique** : Génération de factures
- **Statistiques** : Tableau de bord avec KPIs
- **Rapports détaillés** : Export des données
- **Sauvegarde automatique** : Backup de la base de données

### 🔧 Configuration
- **Multi-terminal** : Support de plusieurs points de vente
- **Configuration flexible** : Fichiers .env et config.ini
- **Personnalisation** : Informations de l'agence configurables

---

## 🖼️ Captures d'écran

*(Ajouter des captures d'écran de l'application)*

---

## 📦 Prérequis

### Pour les utilisateurs finaux (installation via setup)
- **Windows 10 / 11 64 bits**
- **MySQL Server 8.0+** (local ou en réseau)
- **Microsoft .NET Framework** (généralement inclus dans Windows)
- **Python n'est PAS requis** avec l'installateur

### Pour les développeurs
- **Python 3.10+** 64-bit
- **MySQL Server 8.0+**
- **Inno Setup 6** (pour créer l'installateur)
- **Git** (pour le versionnement)

---

## 🚀 Installation

### Méthode 1 : Via l'installateur Windows (Recommandé)

1. Téléchargez la dernière version depuis [GitHub Releases](https://github.com/bonheur84/Ngokaf-Trans/releases)
2. Exécutez `Setup_Ngokaf_Trans.exe`
3. Suivez les instructions de l'installateur
4. Configurez la connexion MySQL dans le fichier `.env`
5. Lancez l'application depuis le Bureau ou le Menu Démarrer

### Méthode 2 : Pour les développeurs

```bash
# Cloner le repository
git clone https://github.com/bonheur84/Ngokaf-Trans.git
cd Ngokaf-Trans

# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres MySQL

# Lancer l'application
python main.py
```

---

## 🎮 Utilisation

### Compte administrateur par défaut

- **Identifiant** : `admin`
- **Mot de passe** : `admin123`

⚠️ **Important** : Changez immédiatement ce mot de passe après la première connexion !

### Rôles utilisateurs

| Rôle | Permissions |
|------|-------------|
| **Administrateur** | Accès complet : Tableau de bord, Trajets, Bus, Conducteurs, Utilisateurs, Rapports, Paramètres |
| **Caissier** | Ventes et bagages uniquement |

### Premier lancement

1. L'application crée automatiquement la base de données `ngokaf_trans`
2. Les tables nécessaires sont initialisées
3. Le compte administrateur par défaut est créé
4. Configurez votre agence dans les Paramètres

---

## ⚙️ Configuration

### Fichier .env

Localisation : `C:\Users\[VotreNom]\AppData\Local\NGOKAF_TRANS\.env`

```env
# Configuration MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=ngokaf_trans

# Configuration de l'agence
AGENCY_NAME=NGOKAF TRANS
AGENCY_ADDRESS=Votre adresse
AGENCY_PHONE=Votre numéro
TERMINAL_NAME=TERMINAL PRINCIPAL
```

### Fichier config.ini

Pour les paramètres avancés, voir `config.ini.example`

---

## 💻 Développement

### Structure du projet

```
Ngokaf-Trans/
├── src/                 # Code source principal
├── models/              # Modèles de données
├── controllers/         # Logique de contrôle
├── services/            # Services métier
├── views/               # Interface utilisateur
├── database/            # Scripts de base de données
├── assets/              # Images, icônes, ressources
├── installer/           # Scripts de création du setup
├── config/              # Fichiers de configuration
├── utils/               # Utilitaires
├── reports/             # Génération de rapports
├── Documentation/       # Documentation utilisateur
├── main.py              # Point d'entrée
├── requirements.txt     # Dépendances Python
├── README.md            # Ce fichier
├── CHANGELOG.md         # Historique des versions
└── LICENSE              # Licence MIT
```

### Lancer en mode développement

```bash
# Installer les dépendances
pip install -r requirements.txt

# Configurer l'environnement
cp .env.example .env
# Éditer .env avec vos paramètres MySQL

# Lancer l'application
python main.py
```

---

## 🏗️ Build de distribution

### Prérequis de compilation

1. Python **3.10+** 64-bit (PATH)
2. [Inno Setup 6](https://jrsoftware.org/isdl.php) (`ISCC.exe` — souvent sous `%LocalAppData%\Programs\Inno Setup 6\` ou `Program Files`)
3. MySQL disponible pour les tests

### Une seule commande

```bat
build.bat
```

ou PowerShell :

```powershell
.\build.ps1
```

### Résultat

| Fichier | Description |
|---------|-------------|
| `dist\NGOKAF_TRANS\NGOKAF_TRANS.exe` | Application portable (dossier complet à conserver) |
| `installer\Output\Setup_Ngokaf_Trans.exe` | **Installateur Windows professionnel** à distribuer |

Le setup crée les raccourcis Bureau / Menu Démarrer, les dossiers `logs`, `backups`, `reports`, `temp`, un désinstalleur, et propose de lancer l'application à la fin.

### Fichiers de build

- [`main.spec`](main.spec) — PyInstaller
- [`installer/setup.iss`](installer/setup.iss) — Inno Setup
- [`scripts/make_icon.py`](scripts/make_icon.py) / [`scripts/export_brand.py`](scripts/export_brand.py) — identité visuelle (`assets/brand/`) + `assets/icons/ngokaf.ico` + `assets/images/logo.png`

### Identité visuelle

Dossier [`assets/brand/`](assets/brand/) :

| Variante | Fichiers |
|----------|----------|
| Symbole | `ngokaf_symbol.svg`, `png/symbol_*.png`, `pdf/ngokaf_symbol.pdf` |
| App (coins arrondis) | `ngokaf_app_icon.svg`, `png/app_icon_*.png` |
| Ronde | `ngokaf_circle.svg`, `png/circle_*.png` |
| Lockup texte | `ngokaf_lockup.svg`, `png/lockup_*.png` |
| Windows | `ngokaf.ico` (aussi copié dans `assets/icons/`) |

Régénérer : `python scripts/make_icon.py`

---

## 🤝 Contributing

Les contributions sont les bienvenues ! Voici comment contribuer :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add some AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Convention de commits

- `feat:` : Nouvelle fonctionnalité
- `fix:` : Correction de bug
- `docs:` : Documentation uniquement
- `style:` : Changements de style (formatage, etc.)
- `refactor:` : Refactoring du code
- `test:` : Ajout de tests
- `chore:` : Tâches de maintenance

---

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

## 📞 Support

Pour obtenir de l'aide :

- Consultez la [Documentation](Documentation/)
- Vérifiez le [CHANGELOG](CHANGELOG.md) pour les dernières mises à jour
- Ouvrez une [Issue](https://github.com/bonheur84/Ngokaf-Trans/issues) sur GitHub

---

## 🙏 Remerciements

- PyQt5 pour l'interface graphique
- MySQL pour la base de données
- Inno Setup pour l'installateur Windows
- La communauté open source

---

## 📊 Statistiques du projet

![GitHub Stars](https://img.shields.io/github/stars/bonheur84/Ngokaf-Trans?style=social)
![GitHub Forks](https://img.shields.io/github/forks/bonheur84/Ngokaf-Trans?style=social)
![GitHub Issues](https://img.shields.io/github/issues/bonheur84/Ngokaf-Trans)

---

**Développé avec ❤️ par [Bonheur84](https://github.com/bonheur84)**
