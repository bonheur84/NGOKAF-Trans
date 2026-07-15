# Documentation Technique - NGOKAF TRANS

## Table des matières

1. [Architecture du projet](#architecture-du-projet)
2. [Structure des dossiers](#structure-des-dossiers)
3. [Technologies utilisées](#technologies-utilisées)
4. [Base de données](#base-de-données)
5. [Services](#services)
6. [Contrôleurs](#contrôleurs)
7. [Vues](#vues)
8. [Modèles](#modèles)
9. [Configuration](#configuration)
10. [Déploiement](#déploiement)

---

## Architecture du projet

NGOKAF TRANS suit une architecture MVC (Modèle-Vue-Contrôleur) avec une séparation claire des responsabilités.

### Couches de l'application

- **Modèles (models/)** : Définition des structures de données
- **Vues (views/)** : Interface utilisateur PyQt/PySide6
- **Contrôleurs (controllers/)** : Logique métier
- **Services (services/)** : Fonctionnalités réutilisables
- **Base de données (database/)** : Connexion et initialisation

### Flux de données

```
Vue → Contrôleur → Service → Modèle → Base de données
```

---

## Structure des dossiers

```
ngokaf-trans/
├── main.py                    # Point d'entrée
├── main.spec                  # Configuration PyInstaller
├── requirements.txt           # Dépendances Python
├── .env                       # Configuration environnement
├── config.ini                 # Configuration avancée
├── assets/                    # Ressources statiques
│   ├── images/               # Images (logos, icônes)
│   ├── icons/                # Icônes de l'application
│   ├── brand/                # Identité visuelle
│   └── fonts/                # Polices personnalisées
├── config/                    # Configuration
│   └── settings.py           # Gestion des paramètres
├── database/                  # Base de données
│   ├── connection.py         # Connexion MySQL
│   ├── session.py            # Gestion des sessions SQLAlchemy
│   ├── init_db.py            # Initialisation de la base
│   └── migrate.py            # Migrations
├── models/                    # Modèles de données
│   ├── user.py               # Utilisateurs
│   ├── ticket.py             # Billets
│   ├── bus.py                # Bus
│   ├── route.py              # Trajets
│   ├── driver.py             # Conducteurs
│   ├── luggage.py            # Bagages
│   ├── notification.py       # Notifications
│   └── audit.py              # Journal d'audit
├── services/                  # Services métier
│   ├── auth_service.py       # Authentification
│   ├── sale_service.py       # Ventes
│   ├── luggage_service.py    # Bagages
│   ├── bus_service.py        # Gestion des bus
│   ├── driver_service.py     # Gestion des conducteurs
│   ├── backup_service.py     # Sauvegardes
│   ├── auto_backup_service.py # Sauvegardes automatiques
│   ├── notification_service.py # Notifications
│   └── ...
├── controllers/               # Contrôleurs
│   ├── auth_controller.py    # Authentification
│   ├── ventes_controller.py  # Ventes
│   └── bagages_controller.py # Bagages
├── views/                     # Interface utilisateur
│   ├── login/                # Écran de connexion
│   ├── main_window/          # Fenêtre principale (caissier)
│   └── admin/                # Interface administrateur
│       ├── admin_window.py   # Fenêtre admin
│       ├── dashboard_view.py # Tableau de bord
│       ├── trajets_view.py   # Gestion des trajets
│       ├── bus_view.py       # Gestion des bus
│       ├── conducteurs_view.py # Gestion des conducteurs
│       ├── users_view.py     # Gestion des utilisateurs
│       ├── rapports_view.py  # Rapports
│       ├── parametres_view.py # Paramètres
│       └── notifications_dialog.py # Notifications
├── utils/                     # Utilitaires
│   ├── logging_setup.py     # Configuration des logs
│   ├── fonts.py              # Chargement des polices
│   ├── styles.py             # Styles CSS
│   ├── icons.py              # Gestion des icônes
│   ├── formatters.py         # Formatage des données
│   └── runtime_bootstrap.py  # Initialisation runtime
├── resources/                 # Ressources Qt
│   └── theme.py              # Thème de l'interface
├── reports/                   # Rapports générés
├── backups/                   # Sauvegardes
├── logs/                      # Journaux
└── temp/                      # Fichiers temporaires
```

---

## Technologies utilisées

### Backend

- **Python 3.10+** : Langage principal
- **SQLAlchemy** : ORM pour la base de données
- **PyMySQL** : Driver MySQL
- **bcrypt** : Hachage des mots de passe
- **python-dotenv** : Gestion des variables d'environnement

### Frontend

- **PySide6 (Qt6)** : Framework GUI
- **qtawesome** : Icônes FontAwesome
- **matplotlib** : Graphiques et visualisations

### Génération de documents

- **reportlab** : Génération PDF
- **openpyxl** : Génération Excel
- **barcode** : Génération de codes-barres
- **qrcode** : Génération de QR codes

### Base de données

- **MySQL 8.0+** : SGBD relationnel

### Build

- **PyInstaller** : Création de l'exécutable
- **Inno Setup 6** : Création de l'installateur Windows

---

## Base de données

### Schéma

#### Utilisateurs (users)

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('administrateur', 'caissier') NOT NULL,
    email VARCHAR(150),
    adresse VARCHAR(255),
    photo_path VARCHAR(512),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Billets (tickets)

```sql
CREATE TABLE tickets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    passenger_name VARCHAR(100) NOT NULL,
    passenger_phone VARCHAR(20),
    route_id INT NOT NULL,
    bus_id INT NOT NULL,
    seat_number INT NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    luggage_count INT DEFAULT 0,
    status ENUM('valide', 'annule', 'utilise') DEFAULT 'valide',
    sold_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    sold_by INT,
    FOREIGN KEY (route_id) REFERENCES routes(id),
    FOREIGN KEY (bus_id) REFERENCES buses(id),
    FOREIGN KEY (sold_by) REFERENCES users(id)
);
```

#### Bus (buses)

```sql
CREATE TABLE buses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    plaque VARCHAR(40) UNIQUE,
    marque VARCHAR(80),
    modele VARCHAR(80),
    annee INT,
    capacite INT NOT NULL,
    couleur VARCHAR(40),
    photo_path VARCHAR(512),
    date_achat DATE,
    statut ENUM('actif', 'maintenance', 'hors_service') DEFAULT 'actif',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Trajets (routes)

```sql
CREATE TABLE routes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    origine VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    heure_depart TIME NOT NULL,
    heure_arrivee TIME,
    distance_km DECIMAL(10,2),
    prix DECIMAL(10,2) NOT NULL,
    driver_id INT,
    statut ENUM('actif', 'inactif') DEFAULT 'actif',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (driver_id) REFERENCES drivers(id)
);
```

#### Conducteurs (drivers)

```sql
CREATE TABLE drivers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    nom VARCHAR(100) NOT NULL,
    telephone VARCHAR(20),
    permis VARCHAR(50),
    permis_expiration DATE,
    statut ENUM('actif', 'indisponible') DEFAULT 'actif',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### Bagages (luggage)

```sql
CREATE TABLE luggage (
    id INT PRIMARY KEY AUTO_INCREMENT,
    luggage_number VARCHAR(20) UNIQUE NOT NULL,
    ticket_id INT NOT NULL,
    poids DECIMAL(5,2) NOT NULL,
    frais DECIMAL(10,2) NOT NULL,
    enregistre_par INT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ticket_id) REFERENCES tickets(id),
    FOREIGN KEY (enregistre_par) REFERENCES users(id)
);
```

#### Notifications (notifications)

```sql
CREATE TABLE notifications (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notif_type VARCHAR(50) DEFAULT 'info',
    icon VARCHAR(50) DEFAULT 'bell',
    lu BOOLEAN DEFAULT FALSE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Audit (audit_logs)

```sql
CREATE TABLE audit_logs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    action VARCHAR(50) NOT NULL,
    entity VARCHAR(50) NOT NULL,
    entity_id INT,
    user_id INT,
    details TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## Services

### auth_service.py

Gestion de l'authentification :

- `ensure_default_admin()` : Crée l'admin par défaut
- `authenticate()` : Vérifie les identifiants
- `change_admin_password()` : Modifie le mot de passe admin

### backup_service.py

Gestion des sauvegardes :

- `backup_database()` : Crée une sauvegarde MySQL
- `backup_reports()` : Sauvegarde les rapports
- `restore_database()` : Restaure une sauvegarde
- `list_backups()` : Liste les sauvegardes disponibles

### auto_backup_service.py

Sauvegardes automatiques :

- `AutoBackupService` : Service Qt pour les sauvegardes automatiques
- Planifie les sauvegardes à 00h00
- Notifie en cas de succès/échec

### notification_service.py

Gestion des notifications :

- `notify()` : Crée une notification générique
- `notify_bus_full()` : Notification bus complet
- `notify_seats_low()` : Notification sièges limités
- `notify_backup_success()` : Notification sauvegarde réussie
- `notify_backup_failed()` : Notification échec sauvegarde
- Et autres notifications spécialisées

### sale_service.py

Gestion des ventes :

- `create_ticket()` : Crée un nouveau billet
- `cancel_ticket()` : Annule un billet
- `get_available_seats()` : Sièges disponibles
- `validate_ticket()` : Valide un billet

### luggage_service.py

Gestion des bagages :

- `register_luggage()` : Enregistre un bagage
- `calculate_fee()` : Calcule les frais
- `get_luggage_by_ticket()` : Bagages d'un billet

---

## Contrôleurs

### auth_controller.py

Logique d'authentification :

- `login()` : Connexion utilisateur
- `logout()` : Déconnexion
- `validate_session()` : Validation de session

### ventes_controller.py

Logique des ventes :

- `process_sale()` : Traite une vente
- `select_seat()` : Sélectionne un siège
- `generate_ticket()` : Génère le ticket

### bagages_controller.py

Logique des bagages :

- `process_luggage()` : Traite un bagage
- `weigh_luggage()` : Pèse un bagage
- `print_label()` : Imprime l'étiquette

---

## Vues

### Structure

Les vues utilisent PySide6 (Qt6) avec :

- **QMainWindow** : Fenêtres principales
- **QWidget** : Composants personnalisés
- **QDialog** : Boîtes de dialogue
- **QStackedWidget** : Navigation entre pages

### admin_window.py

Fenêtre principale administrateur :

- Sidebar avec navigation
- Header avec notifications
- StackedWidget pour les modules
- Timer pour l'horloge
- Timer pour les notifications

### dashboard_view.py

Tableau de bord :

- Indicateurs clés (KPIs)
- Graphiques matplotlib
- Statistiques en temps réel

### parametres_view.py

Gestion des paramètres :

- Profil agence
- Paramètres d'impression
- Gestion des sauvegardes
- Changement de mot de passe

---

## Modèles

### user.py

Modèle Utilisateur :

- Champs : id, username, password_hash, full_name, role, etc.
- Méthodes : `check_password()`, `set_password()`

### ticket.py

Modèle Billet :

- Champs : id, ticket_number, passenger_name, route_id, etc.
- Relations : route, bus, sold_by

### notification.py

Modèle Notification :

- Champs : id, user_id, title, message, notif_type, icon, lu
- Types : INFO, SUCCESS, WARNING, ERROR, BUS_FULL, etc.

---

## Configuration

### settings.py

Gestion centralisée des paramètres :

- `_project_root()` : Dossier d'installation
- `_resource_root()` : Dossier des ressources
- `Settings` : Classe avec tous les paramètres

### Variables d'environnement

Chargées depuis `.env` :

- DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
- AGENCY_NAME, AGENCY_ADDRESS, AGENCY_PHONE
- TERMINAL_NAME, SESSION_TIMEOUT_MINUTES
- LUGGAGE_BASE_FEE, LUGGAGE_WEIGHT_RATE

### runtime_bootstrap.py

Initialisation au premier lancement :

- Crée les dossiers runtime
- Copie .env.example vers .env
- Copie config.ini.example vers config.ini

---

## Déploiement

### Build avec PyInstaller

```bash
python -m PyInstaller --noconfirm main.spec
```

Le fichier `main.spec` configure :

- Exclusions (tkinter, tests, etc.)
- Imports cachés (matplotlib, pymysql, etc.)
- Données à inclure (assets, resources)
- Icône de l'application

### Création de l'installateur

```bash
ISCC.exe installer\setup.iss
```

Le fichier `setup.iss` configure Inno Setup :

- Nom de l'application
- Dossier d'installation
- Raccourcis (Bureau, Menu Démarrer)
- Désinstalleur

### Distribution

Fichiers générés :

- `dist/NGOKAF_TRANS/` : Application portable
- `installer/Output/Setup_Ngokaf_Trans.exe` : Installateur Windows

### Prérequis pour les clients

- Windows 10/11 64 bits
- MySQL Server accessible
- Python NON requis (inclus dans l'exécutable)

---

## Sécurité

### Authentification

- Mots de passe hachés avec bcrypt
- Session gérée via `session_store`
- Pas de déconnexion automatique (désactivée)

### Permissions

- Rôles : Administrateur, Caissier
- Contrôle d'accès dans les vues
- Validation des permissions dans les contrôleurs

### Audit

- Toutes les actions critiques sont loguées
- Journal d'audit dans la base de données
- Consultation via l'interface admin

---

## Performance

### Optimisations

- Pool de connexions SQLAlchemy
- Indexation des tables MySQL
- Chargement différé des données
- Cache des configurations

### Surveillance

- Journaux détaillés dans `logs/`
- Rotation des journaux (max 2 Mo, 5 fichiers)
- Niveaux de log configurables

---

## Maintenance

### Mises à jour

1. Sauvegarder la base de données
2. Installer la nouvelle version
3. Exécuter les migrations
4. Vérifier la configuration
5. Tester les fonctionnalités

### Sauvegardes

- Automatiques : Quotidiennes à 00h00
- Manuelles : Via l'interface admin
- Stockage : `backups/YYYY/MM/DD/`

---

## Support technique

### Journaux

- `logs/ngokaf.log` : Journal principal
- `logs/` : Rotation automatique

### Debug

Mode debug activable via `config.ini` :

```ini
[logging]
level=DEBUG
```

### Contact

Pour le support technique, fournissez :

- Version du logiciel
- Fichier journal
- Capture d'écran
- Description du problème

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
