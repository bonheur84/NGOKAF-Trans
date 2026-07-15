# Guide d'Utilisation GitHub - Ngokaf Trans

Ce guide explique comment configurer et utiliser GitHub pour distribuer l'application Ngokaf Trans de manière professionnelle.

---

## 📋 Table des matières

1. [Création du compte GitHub](#1-création-du-compte-github)
2. [Création du repository](#2-création-du-repository)
3. [Envoi du code sur GitHub](#3-envoi-du-code-sur-github)
4. [Création des versions (Releases)](#4-création-des-versions-releases)
5. [Ajout du fichier .exe](#5-ajout-du-fichier-exe)
6. [Téléchargement par les utilisateurs](#6-téléchargement-par-les-utilisateurs)
7. [Mise à jour vers une nouvelle version](#7-mise-à-jour-vers-une-nouvelle-version)
8. [Workflow automatique avec GitHub Actions](#8-workflow-automatique-avec-github-actions)

---

## 1. Création du compte GitHub

### Étape 1 : Inscription

1. Allez sur [https://github.com](https://github.com)
2. Cliquez sur **"Sign up"** (en haut à droite)
3. Remplissez le formulaire :
   - **Username** : `bonheur84` (ou votre nom d'utilisateur)
   - **Email** : Votre adresse email
   - **Password** : Un mot de passe sécurisé
4. Cliquez sur **"Create account"**
5. Vérifiez votre adresse email via le lien reçu

### Étape 2 : Configuration du profil

1. Connectez-vous à GitHub
2. Cliquez sur votre photo de profil (en haut à droite)
3. Allez dans **"Settings"**
4. Complétez votre profil :
   - Nom complet
   - Bio (description)
   - Photo de profil

---

## 2. Création du repository

### Étape 1 : Créer un nouveau repository

1. Connectez-vous à GitHub
2. Cliquez sur le **+** en haut à droite
3. Sélectionnez **"New repository"**
4. Remplissez les informations :
   - **Repository name** : `Ngokaf-Trans`
   - **Description** : `Application desktop Windows de gestion de billets et bagages pour l'agence NGOKAF TRANS`
   - **Public/Private** : Choisissez **Public** (gratuit et visible par tous)
   - **Initialize this repository** : NE PAS cocher (nous allons pousser le code existant)
5. Cliquez sur **"Create repository"**

### Étape 2 : Notez l'URL du repository

Une fois créé, vous verrez l'URL de votre repository :
```
https://github.com/bonheur84/Ngokaf-Trans.git
```
Notez cette URL, elle sera utilisée pour l'envoi du code.

---

## 3. Envoi du code sur GitHub

### Étape 1 : Initialiser Git localement

Ouvrez un terminal (PowerShell ou CMD) dans le dossier de votre projet :

```powershell
cd "C:\Users\nzaub\Pictures\ngokaf - Copy"
```

### Étape 2 : Initialiser Git

```powershell
git init
```

### Étape 3 : Créer un fichier .gitignore

Créez un fichier `.gitignore` à la racine du projet pour exclure les fichiers inutiles :

```powershell
# Créer le fichier .gitignore
notepad .gitignore
```

Ajoutez le contenu suivant :

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.spec
build/
dist/

# Environnement
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Base de données
*.db
*.sqlite
*.sqlite3

# Fichiers temporaires
temp/
tmp/
*.tmp

# Inno Setup output
installer/Output/

# Backup
backups/
*.bak
```

### Étape 4 : Ajouter les fichiers au staging

```powershell
git add .
```

### Étape 5 : Faire le premier commit

```powershell
git commit -m "Initial commit - Ngokaf Trans v1.0"
```

### Étape 6 : Connecter au repository GitHub

```powershell
git remote add origin https://github.com/bonheur84/Ngokaf-Trans.git
```

### Étape 7 : Pousser le code sur GitHub

```powershell
git branch -M main
git push -u origin main
```

Si on vous demande de vous authentifier :
- **Username** : votre nom d'utilisateur GitHub
- **Password** : utilisez un **Personal Access Token** (pas votre mot de passe)

#### Comment créer un Personal Access Token :

1. Allez dans GitHub → Settings (votre profil)
2. Cliquez sur **"Developer settings"** (en bas à gauche)
3. Cliquez sur **"Personal access tokens"** → **"Tokens (classic)"**
4. Cliquez sur **"Generate new token"** → **"Generate new token (classic)"**
5. Donnez un nom (ex: "Ngokaf Trans")
6. Cochez **"repo"** (accès complet aux repositories)
7. Cliquez sur **"Generate token"**
8. **COPIEZ LE TOKEN** (il ne sera plus affiché après)
9. Utilisez ce token comme mot de passe

---

## 4. Création des versions (Releases)

### Méthode 1 : Automatique avec GitHub Actions (Recommandé)

Cette méthode utilise le workflow que nous avons configuré.

#### Étape 1 : Créer un tag pour la version

```powershell
git tag v1.0.0
git push origin v1.0.0
```

#### Étape 2 : GitHub Actions crée automatiquement la Release

1. Allez sur votre repository GitHub
2. Cliquez sur **"Actions"** (onglet en haut)
3. Vous verrez le workflow "Build and Release" en cours d'exécution
4. Attendez la fin (quelques minutes)
5. Allez dans **"Releases"** pour voir la release créée automatiquement

### Méthode 2 : Manuelle (Alternative)

#### Étape 1 : Compiler l'application localement

```powershell
# Exécuter le script de build
.\build.bat
```

Cela créera le fichier `installer\Output\Setup_Ngokaf_Trans.exe`

#### Étape 2 : Créer une Release sur GitHub

1. Allez sur votre repository GitHub
2. Cliquez sur **"Releases"** (onglet à droite)
3. Cliquez sur **"Create a new release"**
4. Remplissez les informations :
   - **Choose a tag** : Cliquez sur **"Choose a tag"** → **"Create new tag"**
   - **Tag** : `v1.0.0`
   - **Release title** : `Ngokaf Trans v1.0`
   - **Description** :
     ```
     ## Ngokaf Trans v1.0
     
     ### Nouveautés
     - Première version stable
     - Gestion des utilisateurs avec rôles
     - Système de facturation
     - Rapports et statistiques
     - Sauvegarde automatique
     
     ### Installation
     1. Téléchargez Setup_Ngokaf_Trans_v1.0.exe
     2. Exécutez l'installateur
     3. Configurez MySQL dans le fichier .env
     4. Lancez l'application
     ```
5. Cliquez sur **"Publish release"**

#### Étape 3 : Ajouter le fichier .exe

1. Une fois la release créée, cliquez sur **"Edit release"**
2. Dans la section **"Assets"**, cliquez sur **"Attach binaries"**
3. Sélectionnez le fichier `Setup_Ngokaf_Trans.exe`
4. Cliquez sur **"Update release"**

---

## 5. Ajout du fichier .exe

### Avec GitHub Actions (Automatique)

Le workflow automatique renomme le fichier et l'ajoute automatiquement à la release avec le bon format :
```
Setup_Ngokaf_Trans_v1.0.0.exe
```

### Manuellement

Si vous préférez ajouter le fichier manuellement :

1. Renommez le fichier localement :
   ```powershell
   copy "installer\Output\Setup_Ngokaf_Trans.exe" "Setup_Ngokaf_Trans_v1.0.0.exe"
   ```

2. Allez sur la Release sur GitHub
3. Cliquez sur **"Edit release"**
4. Faites glisser le fichier `Setup_Ngokaf_Trans_v1.0.0.exe` dans la zone **"Attach binaries"**
5. Cliquez sur **"Update release"**

---

## 6. Téléchargement par les utilisateurs

### Processus pour les utilisateurs

1. **Accéder aux Releases** :
   - Allez sur : `https://github.com/bonheur84/Ngokaf-Trans/releases`
   - Ou cliquez sur **"Releases"** sur la page du repository

2. **Télécharger la dernière version** :
   - Cliquez sur la release **"Latest"** (en haut)
   - Téléchargez `Setup_Ngokaf_Trans_v1.0.0.exe`
   - Ou cliquez sur **"Assets"** pour voir tous les fichiers

3. **Installer l'application** :
   - Double-cliquez sur `Setup_Ngokaf_Trans_v1.0.0.exe`
   - Suivez les instructions de l'installateur
   - Configurez MySQL dans le fichier `.env`
   - Lancez l'application

### Lien direct de téléchargement

Chaque release a un lien direct :
```
https://github.com/bonheur84/Ngokaf-Trans/releases/latest
```

Ce lien redirige toujours vers la dernière version.

---

## 7. Mise à jour vers une nouvelle version

### Workflow de développement

```
Modification du code
↓
Commit GitHub
↓
Création du tag v1.x
↓
Compilation automatique
↓
Création automatique de la Release
↓
Ajout du fichier Setup_Ngokaf_Trans_v1.x.exe
```

### Étapes détaillées

#### Étape 1 : Faire les modifications

1. Modifiez le code de l'application
2. Testez les modifications localement

#### Étape 2 : Commiter les changements

```powershell
git add .
git commit -m "feat: Ajout de la fonctionnalité X"
```

#### Étape 3 : Pousser sur GitHub

```powershell
git push origin main
```

#### Étape 4 : Mettre à jour le CHANGELOG

Ouvrez `CHANGELOG.md` et ajoutez les modifications de la nouvelle version :

```markdown
## [1.1.0] - 2026-08-01

### Added
- Nouvelle fonctionnalité X
- Amélioration de l'interface

### Fixed
- Correction du bug Y
```

Committez le changement :

```powershell
git add CHANGELOG.md
git commit -m "docs: Mise à jour du CHANGELOG pour v1.1.0"
git push origin main
```

#### Étape 5 : Créer un nouveau tag

```powershell
git tag v1.1.0
git push origin v1.1.0
```

#### Étape 6 : GitHub Actions crée la release

Le workflow automatique :
- Compile l'application
- Crée l'installateur
- Crée une nouvelle release
- Ajoute le fichier `Setup_Ngokaf_Trans_v1.1.0.exe`

#### Étape 7 : Vérifier la release

1. Allez sur **"Releases"** sur GitHub
2. Vérifiez que la release v1.1.0 est créée
3. Vérifiez que le fichier .exe est présent
4. Testez le téléchargement

---

## 8. Workflow automatique avec GitHub Actions

### Fonctionnement du workflow

Le fichier `.github/workflows/release.yml` configure un workflow automatique qui :

1. **Se déclenche** quand vous poussez un tag (ex: `v1.0.0`)
2. **Installe** Python et les dépendances
3. **Compile** l'application avec PyInstaller
4. **Crée** l'installateur avec Inno Setup
5. **Renomme** le fichier avec le numéro de version
6. **Crée** automatiquement une Release GitHub
7. **Attache** le fichier .exe à la release

### Avantages

- ✅ **Automatique** : Plus besoin de compiler manuellement
- ✅ **Consistant** : Toujours le même processus de build
- ✅ **Versionné** : Chaque release est tracée
- ✅ **Gratuit** : Utilise les fonctionnalités gratuites de GitHub
- ✅ **Professionnel** : Workflow standard de l'industrie

### Personnalisation

Vous pouvez modifier le fichier `.github/workflows/release.yml` pour :
- Changer la version de Python
- Ajouter des étapes de tests
- Modifier le nom des fichiers
- Ajouter des notifications

---

## 📝 Résumé rapide

### Pour créer une nouvelle version

```powershell
# 1. Commiter les changements
git add .
git commit -m "Description des changements"
git push origin main

# 2. Créer le tag
git tag v1.2.0
git push origin v1.2.0

# 3. Attendre que GitHub Actions crée la release
# (Quelques minutes)

# 4. Vérifier sur GitHub → Releases
```

### Pour les utilisateurs

```
1. Aller sur : https://github.com/bonheur84/Ngokaf-Trans/releases
2. Télécharger : Setup_Ngokaf_Trans_v1.x.0.exe
3. Installer et utiliser
```

---

## 🔧 Résolution de problèmes

### Problème : "Authentication failed"

**Solution** : Utilisez un Personal Access Token au lieu de votre mot de passe.

### Problème : "Tag already exists"

**Solution** : Supprimez le tag localement et sur GitHub :
```powershell
git tag -d v1.0.0
git push origin :refs/tags/v1.0.0
```

### Problème : GitHub Actions échoue

**Solution** :
1. Allez sur l'onglet "Actions" sur GitHub
2. Cliquez sur le workflow échoué
3. Consultez les logs pour voir l'erreur
4. Corrigez le problème et poussez un nouveau tag

### Problème : Fichier .exe trop volumineux

**Solution** : GitHub limite les fichiers à 2 GB. Si votre fichier est plus grand :
- Optimisez PyInstaller (excluezles modules inutiles)
- Utilisez UPX pour compresser l'exécutable

---

## 📚 Ressources utiles

- [Documentation GitHub](https://docs.github.com)
- [GitHub Actions](https://github.com/features/actions)
- [Git Documentation](https://git-scm.com/doc)
- [Semantic Versioning](https://semver.org)

---

**Dernière mise à jour : 15 Juillet 2026**
