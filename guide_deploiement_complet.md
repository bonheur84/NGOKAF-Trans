# 🚀 Guide Complet — NGOKAF TRANS en ligne

### Rédigé comme un ingénieur dev & base de données qui t'explique tout

---

## 🧠 Comprendre d'abord (très important !)

Avant de toucher à quoi que ce soit, comprends ce schéma. C'est toute l'architecture :

```
┌────────────────────────────────────────────────────────┐
│               SERVEUR CLOUD (DigitalOcean)              │
│                                                        │
│   ┌─────────────────────┐   ┌────────────────────────┐ │
│   │   API FastAPI        │──►│   Base de données MySQL│ │
│   │ api.ngokaftrans.com  │   │   (ngokaf_trans)       │ │
│   └─────────────────────┘   └────────────────────────┘ │
│              ▲                                          │
└──────────────┼──────────────────────────────────────────┘
               │ Internet (HTTPS sécurisé)
    ┌──────────┴──────────┐
    │                     │
┌───▼───────┐      ┌──────▼────┐
│  Ton PC   │      │ Autre PC  │
│ (.exe)    │      │  (.exe)   │
└───────────┘      └───────────┘
```

**Explication simple :**

- 🗄️ **La BD MySQL** : c'est là où toutes les données sont stockées (clients, billets, trajets...)
- ⚙️ **L'API FastAPI** : c'est un intermédiaire. Les PCs parlent à l'API, et l'API parle à la BD.
- 💻 **Les PCs** : ils ont juste l'adresse de l'API. Ils ne voient jamais le mot de passe de la BD.

> **Pourquoi cette architecture ?**
> Si quelqu'un vole le `.exe` installé sur un PC, il ne peut pas voler le mot de passe de ta BD.
> Le mot de passe reste uniquement sur le serveur DigitalOcean. C'est la bonne pratique professionnelle.

---

- [ ] 📋 Ce qu'il te faut avant de commencer
- [ ] Un compte **GitHub** — si tu n'en as pas : https://github.com/signup (gratuit)
- [ ] Un compte **DigitalOcean** — https://www.digitalocean.com (payant, ~$20/mois total)
- [ ] Une carte bancaire (Visa / Mastercard)
- [ ] Ton projet déjà sur GitHub (on verra comment faire)
- [ ] Environ **1h à 1h30** la première fois

---

---

# PHASE 1 — Mettre le code sur GitHub

> **Pourquoi GitHub ?**
> DigitalOcean va lire ton code directement depuis GitHub pour déployer l'API automatiquement.
> C'est comme donner à DigitalOcean l'accès à ton projet pour qu'il le lance tout seul.

## Étape 1.1 — Créer un dépôt GitHub privé

1. Va sur https://github.com et connecte-toi
2. Clique sur le **"+"** en haut à droite → **"New repository"**
3. Remplis :
   - **Repository name** : `ngokaf-trans`
   - **Private** ✅ (important — ton code est privé !)
   - **Ne coche rien d'autre**
4. Clique **"Create repository"**

## Étape 1.2 — Vérifier le .gitignore

Avant d'envoyer le code, vérifie que ton fichier `.gitignore` contient bien `.env`
(il ne faut **jamais** envoyer les mots de passe sur GitHub).

Ton `.gitignore` contient déjà `.env` — ✅ c'est bon.

## Étape 1.3 — Envoyer ton code sur GitHub

Ouvre **PowerShell** dans ton dossier de projet et tape ces commandes une par une :

```powershell
# Va dans ton dossier projet
cd "C:\Users\Marty\Documents\ngokaf TRANS"

# Initialise Git (si pas déjà fait)
git init

# Ajoute tous les fichiers (sauf ceux dans .gitignore)
git add .

# Crée un premier "snapshot" de ton code
git commit -m "Premier déploiement"

# Connecte ton dossier local à GitHub
# Remplace TON_USERNAME par ton nom d'utilisateur GitHub
git remote add origin https://github.com/TON_USERNAME/ngokaf-trans.git

# Envoie le code
git push -u origin main
```

> ✅ Quand c'est fini, actualise la page GitHub — tu dois voir tous tes fichiers.

---

---

# PHASE 2 — Créer la base de données MySQL sur DigitalOcean

## Étape 2.1 — Créer un compte DigitalOcean

1. Va sur https://www.digitalocean.com
2. Clique **"Sign Up"**
3. Crée un compte avec ton email
4. Vérifie ton email (ils envoient un lien)
5. Entre ta carte bancaire (nécessaire pour activer le compte)

> Tu arrives sur le **Dashboard** (tableau de bord principal)

## Étape 2.2 — Créer le cluster MySQL

1. Dans le menu gauche, clique **"Databases"**
2. Clique le bouton vert **"Create Database Cluster"**
3. Configure comme ceci :

| Champ                           | Valeur                                                    |
| ------------------------------- | --------------------------------------------------------- |
| **Database engine**       | MySQL 8                                                   |
| **Cluster configuration** | Basic                                                     |
| **Machine type**          | Regular SSD                                               |
| **Node plan**             | $15/mo (1 GB RAM)                                         |
| **Datacenter region**     | **Frankfurt (FRA1)** ← le plus proche de l'Afrique |
| **Cluster name**          | `ngokaf-trans-db`                                       |

4. Clique **"Create Database Cluster"**
5. ⏳ **Attends 3 à 5 minutes** — DigitalOcean prépare le serveur MySQL

> ✅ Quand tu vois le point vert **"Active"** → le serveur MySQL est prêt !

## Étape 2.3 — Créer la base de données `ngokaf_trans`

Par défaut, DigitalOcean crée une base vide appelée `defaultdb`.On va créer notre vraie base :

1. Clique sur ton cluster `ngokaf-trans-db`
2. Clique l'onglet **"Users & Databases"**
3. Dans la section **"Databases"** → clique **"Add new database"**
4. Nom : `ngokaf_trans`
5. Clique **"Save"**

## Étape 2.4 — Récupérer les informations de connexion

1. Clique l'onglet **"Overview"** de ton cluster
2. Tu vois un encadré **"Connection details"**
3. Dans le menu déroulant, sélectionne **"Connection parameters"**

Tu vas voir quelque chose comme :

```
host      : ngokaf-trans-db-do-user-12345678-0.b.db.ondigitalocean.com
port      : 25060
database  : ngokaf_trans
username  : doadmin
password  : ABCDEFGHIJKLM123456789
```

📝 **COPIE CES INFORMATIONS** dans un bloc-notes. Tu en auras besoin juste après.

## Étape 2.5 — Télécharger le certificat SSL

Sur la même page, cherche le lien **"Download the CA certificate"**.
Clique dessus — un fichier `ca-certificate.crt` se télécharge.

Enregistre-le ici sur ton PC :

```
C:\Users\Marty\Documents\ngokaf TRANS\config\ca-certificate.crt
```

## Étape 2.6 — Autoriser les connexions

Par défaut, DigitalOcean bloque tout. On doit autoriser l'accès :

1. Clique l'onglet **"Settings"** de ton cluster
2. Cherche **"Trusted sources"** → clique **"Edit"**
3. Pour l'instant, entre `0.0.0.0/0` (autorise tout — on sécurisera plus tard)
4. Clique **"Save"**

## Étape 2.7 — Importer tes données

Maintenant on envoie toutes tes données (clients, trajets, etc.) vers DigitalOcean.

Ouvre **PowerShell** et tape cette commande (remplace les valeurs par les tiennes) :

```powershell
& "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" `
  --host=COLLE_TON_HOST_ICI `
  --port=25060 `
  --user=doadmin `
  "--password=COLLE_TON_MOT_DE_PASSE_ICI" `
  "--ssl-ca=C:\Users\Marty\Documents\ngokaf TRANS\config\ca-certificate.crt" `
  ngokaf_trans `
  < "C:\Users\Marty\Documents\ngokaf TRANS\backups\ngokaf_trans_export_2026-09-17.sql"
```

> ⏳ Attends 1-2 minutes.
> ✅ Si aucune erreur rouge n'apparaît → **tes données sont en ligne !**

---

---

# PHASE 3 — Déployer l'API FastAPI sur DigitalOcean

> **C'est quoi l'API ?**
> C'est ton fichier `api/main.py`. C'est un programme Python qui tourne en permanence
> sur un serveur et répond aux demandes de tes PCs clients.

## Étape 3.1 — Créer une App sur DigitalOcean App Platform

1. Dans le menu gauche de DigitalOcean, clique **"Apps"**
2. Clique **"Create App"**
3. Sélectionne **"GitHub"** comme source
4. Connecte ton compte GitHub (autorise DigitalOcean à lire tes repos)
5. Choisis le repo `ngokaf-trans`
6. Branche : `main`
7. Coche **"Autodeploy"** ✅ (met à jour automatiquement quand tu pousses du code)
8. Clique **"Next"**

## Étape 3.2 — Configurer le service

DigitalOcean va détecter ton `Dockerfile` automatiquement. Vérifie :

| Champ                 | Valeur                                              |
| --------------------- | --------------------------------------------------- |
| **Type**        | Web Service                                         |
| **Port**        | 8080                                                |
| **Run command** | `uvicorn api.main:app --host 0.0.0.0 --port 8080` |
| **Plan**        | Basic — $5/mois                                    |

Clique **"Next"**

## Étape 3.3 — Ajouter les variables d'environnement (TRÈS IMPORTANT)

C'est ici qu'on donne à l'API les informations pour se connecter à la BD.
**Ces infos restent sur le serveur DigitalOcean — jamais dans l'exe installé sur les PCs.**

Clique **"Edit"** à côté de **"Environment Variables"** et ajoute :

```
DB_HOST          = COLLE_TON_HOST_DIGITALOCEAN
DB_PORT          = 25060
DB_USER          = doadmin
DB_PASSWORD      = COLLE_TON_MOT_DE_PASSE
DB_NAME          = ngokaf_trans
DB_SSL_MODE      = require
DB_CREATE_DATABASE = false
DB_CONNECT_TIMEOUT = 10
API_TOKEN_SECRET = GENERE_UNE_CLE_SECRETE_ICI
```

> **Pour `API_TOKEN_SECRET`** : génère une clé aléatoire en PowerShell :
>
> ```powershell
> -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 48 | % {[char]$_})
> ```
>
> Copie le résultat et colle-le comme valeur.

Clique **"Next"** puis **"Create Resources"**

## Étape 3.4 — Attendre le déploiement

⏳ **Attends 5 à 10 minutes** — DigitalOcean télécharge ton code, l'installe et le démarre.

Tu vois une barre de progression. Quand c'est vert → **l'API est en ligne !**

## Étape 3.5 — Récupérer l'URL de ton API

Une fois déployée :

1. Clique sur ton app
2. Tu vois une URL du style : `https://ngokaf-trans-abc123.ondigitalocean.app`

> **Note cette URL** — c'est l'adresse de ton API.

## Étape 3.6 — Tester que l'API fonctionne

Dans ton navigateur, va sur :

```
https://ngokaf-trans-abc123.ondigitalocean.app/health
```

Tu dois voir :

```json
{"status": "ok"}
```

✅ **L'API est en ligne et connectée à ta BD !**

---

---

# PHASE 4 — Construire l'installeur Windows (.exe)

C'est la dernière phase. On va créer le fichier `.exe` que les utilisateurs installent.
**L'exe contiendra déjà l'URL de l'API** — l'utilisateur n'aura rien à configurer.

## Étape 4.1 — Mettre à jour ton .env local

Ouvre `C:\Users\Marty\Documents\ngokaf TRANS\.env` et remplace le contenu par :

```env
DB_HOST=TON_HOST_DIGITALOCEAN
DB_PORT=25060
DB_USER=doadmin
DB_PASSWORD=TON_MOT_DE_PASSE
DB_NAME=ngokaf_trans
DB_SSL_MODE=require
DB_CREATE_DATABASE=false
DB_CONNECT_TIMEOUT=10
API_BASE_URL=https://TON_APP.ondigitalocean.app
API_TIMEOUT_SECONDS=20
AGENCY_NAME=NGOKAF TRANS
AGENCY_ADDRESS=Centre-ville - Lubumbashi, RDC
AGENCY_PHONE=(+243) 975079756
TERMINAL_NAME=TERMINAL PRINCIPAL
SESSION_TIMEOUT_MINUTES=30
LUGGAGE_BASE_FEE=2500
LUGGAGE_WEIGHT_RATE=200
```

## Étape 4.2 — Mettre à jour le setup.iss (installeur)

Dans le fichier `installer\setup.iss`, la ligne 9 définit l'URL qui sera inscrite
dans le `.env` généré sur les PCs des utilisateurs. Vérifie qu'elle est correcte :

```pascal
#define ApiBaseUrl "https://TON_APP.ondigitalocean.app"
```

> C'est cette URL qui sera automatiquement mise dans le `.env` de chaque PC lors de l'installation.
> **L'utilisateur n'a rien à toucher.**

## Étape 4.3 — Lancer le build

Ouvre **PowerShell** et tape :

```powershell
cd "C:\Users\Marty\Documents\ngokaf TRANS"
.\build.ps1
```

Le script va automatiquement :

1. Installer les dépendances Python
2. Créer l'icône
3. Nettoyer les anciens fichiers
4. Créer le `.exe` avec PyInstaller
5. Créer l'installeur avec Inno Setup

⏳ **Attends 5 à 10 minutes**

✅ À la fin tu vois : `installer\Output\Setup_Ngokaf_Trans.exe`

## Étape 4.4 — Tester l'installeur

1. Double-clique sur `Setup_Ngokaf_Trans.exe`
2. Suis l'assistant d'installation
3. Lance l'application
4. Elle doit se connecter directement à ta BD DigitalOcean **sans te demander quoi que ce soit**

---

---

# PHASE 5 — Distribuer l'application

## Mettre l'exe en ligne

Pour partager l'exe, tu peux utiliser :

| Option                        | Comment                                                               | Gratuit ? |
| ----------------------------- | --------------------------------------------------------------------- | --------- |
| **Google Drive**        | Mets`Setup_Ngokaf_Trans.exe` dans un dossier Drive, partage le lien | ✅        |
| **GitHub Releases**     | Dans ton repo GitHub → "Releases" → Upload l'exe                    | ✅        |
| **DigitalOcean Spaces** | Stockage de fichiers DigitalOcean                                     | ~$5/mois  |

**La méthode la plus simple : Google Drive**

1. Va sur https://drive.google.com
2. Crée un dossier `NGOKAF TRANS - Installeur`
3. Glisse-dépose `Setup_Ngokaf_Trans.exe` dedans
4. Fais clic droit → **"Partager"** → **"Toute personne avec le lien"**
5. Copie le lien et envoie-le à tes utilisateurs

---

## Ce que fait l'utilisateur (RIEN de compliqué)

1. Télécharge `Setup_Ngokaf_Trans.exe` depuis le lien que tu donnes
2. Double-clique pour installer
3. Lance l'application
4. **C'est tout !** L'app se connecte automatiquement à ta BD en ligne.

---

---

# 🔁 Résumé des étapes

```
PHASE 1 — GitHub
  ✅ Créer un repo privé GitHub
  ✅ Push ton code

PHASE 2 — Base de données (DigitalOcean Managed MySQL — $15/mois)
  ✅ Créer le cluster MySQL
  ✅ Créer la base ngokaf_trans
  ✅ Récupérer host/port/user/password
  ✅ Télécharger le certificat SSL
  ✅ Autoriser les connexions
  ✅ Importer tes données (le fichier .sql exporté)

PHASE 3 — API (DigitalOcean App Platform — $5/mois)
  ✅ Créer l'app depuis GitHub
  ✅ Configurer les variables d'environnement (credentials BD)
  ✅ Récupérer l'URL de l'API
  ✅ Tester /health

PHASE 4 — Installeur Windows
  ✅ Mettre à jour .env local avec les infos DigitalOcean
  ✅ Mettre à jour setup.iss avec l'URL de l'API
  ✅ Lancer build.ps1
  ✅ Tester Setup_Ngokaf_Trans.exe

PHASE 5 — Distribution
  ✅ Mettre l'exe sur Google Drive ou GitHub Releases
  ✅ Partager le lien aux utilisateurs
```

**Coût total :** ~$20/mois (BD $15 + API $5) ≈ 12 000 FCFA/mois

---

# 🆘 Problèmes fréquents

| Problème                          | Cause probable                 | Solution                        |
| ---------------------------------- | ------------------------------ | ------------------------------- |
| `Connection refused` à l'import | Trusted Sources pas configuré | Étape 2.6                      |
| `Access denied`                  | Mauvais username ou password   | Revérifie étape 2.4           |
| L'API retourne 500                 | Variables d'env manquantes     | Revérifie étape 3.3           |
| L'exe ne se connecte pas           | Mauvaise URL dans setup.iss    | Revérifie étape 4.2           |
| Build échoue (Inno Setup)         | Inno Setup pas installé       | Télécharge sur jrsoftware.org |

---

> 💡 **Conseil d'ingénieur :** À chaque fois que tu mets à jour l'application,
> tu fais juste `git push` et DigitalOcean redéploie l'API automatiquement.
> Pour les PCs clients, tu reconstruis l'exe avec `build.ps1` et tu redistribues l'installeur.
