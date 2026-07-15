# Guide d'Installation - NGOKAF TRANS

## Table des matières

1. [Prérequis système](#prérequis-système)
2. [Installation de MySQL](#installation-de-mysql)
3. [Installation de l'application](#installation-de-lapplication)
4. [Configuration initiale](#configuration-initiale)
5. [Premier lancement](#premier-lancement)
6. [Vérification de l'installation](#vérification-de-linstallation)

---

## Prérequis système

### Configuration minimale requise

- **Système d'exploitation** : Windows 10 ou 11 (64 bits)
- **Processeur** : Intel Core i3 ou équivalent
- **Mémoire RAM** : 4 Go minimum (8 Go recommandé)
- **Espace disque** : 500 Mo pour l'application + 5 Go pour les données
- **Écran** : Résolution 1280×720 minimum (1920×1080 recommandé)

### Logiciels requis

- **MySQL Server** 8.0 ou supérieur
- **Microsoft .NET Framework** (généralement inclus dans Windows)

---

## Installation de MySQL

### Téléchargement

1. Allez sur le site officiel : https://dev.mysql.com/downloads/mysql/
2. Téléchargez MySQL Community Server 8.0
3. Choisissez la version Windows 64-bit

### Installation

1. Lancez l'installateur MySQL
2. Choisissez "Developer Default" ou "Server only"
3. Acceptez les termes de licence
4. Cliquez sur "Execute" pour l'installation
5. Configurez le serveur :
   - **Type de configuration** : Standalone MySQL Server
   - **Port** : 3306 (par défaut)
   - **Mot de passe root** : Choisissez un mot de passe sécurisé
   - **Service Windows** : Cochez "Configure MySQL Server as a Windows Service"
6. Cliquez sur "Execute" pour appliquer la configuration
7. Terminez l'installation

### Vérification

1. Ouvrez MySQL Command Line Client
2. Entrez le mot de passe root
3. Tapez : `SHOW DATABASES;`
4. Vous devriez voir la liste des bases de données

---

## Installation de l'application

### Méthode recommandée : Installateur Windows

1. Localisez le fichier `Setup_Ngokaf_Trans.exe`
2. Double-cliquez sur l'installateur
3. Acceptez la licence
4. Choisissez le dossier d'installation (par défaut : `C:\Program Files\NGOKAF TRANS`)
5. Cliquez sur "Installer"
6. Attendez la fin de l'installation
7. Cochez "Lancer NGOKAF TRANS" si vous souhaitez démarrer immédiatement
8. Cliquez sur "Terminer"

### Raccourcis créés

L'installateur crée automatiquement :
- **Raccourci Bureau** : NGOKAF TRANS
- **Menu Démarrer** : NGOKAF TRANS
- **Désinstallateur** : Programmes et fonctionnalités

---

## Configuration initiale

### Localisation du fichier de configuration

Le fichier de configuration se trouve dans :

**Pour Windows 10/11 :**
```
C:\Users\[VotreNomUtilisateur]\AppData\Local\NGOKAF_TRANS\.env
```

### Éditer le fichier .env

1. Naviguez vers le dossier d'application
2. Ouvrez le fichier `.env` avec un éditeur de texte (Bloc-notes)
3. Modifiez les paramètres MySQL :

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=votre_mot_de_passe_mysql
DB_NAME=ngokaf_trans
```

4. Modifiez les informations de l'agence si nécessaire :

```env
AGENCY_NAME=NGOKAF TRANS
AGENCY_ADDRESS=Votre adresse
AGENCY_PHONE=Votre numéro
TERMINAL_NAME=TERMINAL PRINCIPAL
```

5. Enregistrez et fermez le fichier

### Configuration de config.ini (optionnel)

Le fichier `config.ini` permet des paramètres avancés. Il se trouve dans le même dossier que `.env`.

---

## Premier lancement

### Création de la base de données

Au premier lancement, l'application crée automatiquement :

- La base de données `ngokaf_trans`
- Toutes les tables nécessaires
- L'utilisateur administrateur par défaut

### Connexion administrateur

Utilisez les identifiants par défaut :

- **Identifiant** : `admin`
- **Mot de passe** : `admin123`

⚠️ **Important :** Changez immédiatement ce mot de passe après la première connexion.

### Étapes après la première connexion

1. Allez dans "Paramètres"
2. Section "Mot de passe administrateur"
3. Entrez l'ancien mot de passe (`admin123`)
4. Entrez un nouveau mot de passe sécurisé
5. Confirmez le nouveau mot de passe
6. Cliquez sur "Changer le mot de passe"

---

## Vérification de l'installation

### Vérifier MySQL

1. Ouvrez MySQL Command Line Client
2. Connectez-vous avec le mot de passe root
3. Tapez :

```sql
USE ngokaf_trans;
SHOW TABLES;
```

4. Vous devriez voir les tables : `users`, `tickets`, `buses`, `routes`, `drivers`, etc.

### Vérifier l'application

1. Lancez NGOKAF TRANS
2. Connectez-vous en tant qu'administrateur
3. Vérifiez que le tableau de bord s'affiche correctement
4. Vérifiez que toutes les sections du menu sont accessibles

### Vérifier les dossiers

L'application crée automatiquement les dossiers suivants dans `AppData\Local\NGOKAF_TRANS\` :

- `logs` : Fichiers journaux
- `backups` : Sauvegardes automatiques
- `reports` : Rapports générés
- `temp` : Fichiers temporaires
- `config` : Configuration

---

## Mise à jour de l'application

### Via l'installateur

1. Téléchargez la nouvelle version de `Setup_Ngokaf_Trans.exe`
2. Lancez l'installateur
3. Choisissez "Réparer" ou "Mettre à jour"
4. Suivez les instructions

⚠️ **Important :** Sauvegardez toujours la base de données avant une mise à jour.

### Sauvegarde avant mise à jour

1. Lancez l'application
2. Connectez-vous en tant qu'administrateur
3. Allez dans "Paramètres"
4. Cliquez sur "Créer une sauvegarde"
5. Attendez la confirmation

---

## Désinstallation

### Via le Panneau de configuration

1. Ouvrez le Panneau de configuration
2. Allez dans "Programmes et fonctionnalités"
3. Sélectionnez "NGOKAF TRANS"
4. Cliquez sur "Désinstaller"
5. Suivez les instructions
6. Choisissez de conserver ou supprimer le dossier `backups`

### Conservation des données

Lors de la désinstallation, vous pouvez choisir de conserver :

- Le dossier `backups` (sauvegardes)
- Le dossier `reports` (rapports)

Ces dossiers se trouvent dans `AppData\Local\NGOKAF_TRANS\`.

---

## Problèmes d'installation courants

### "MySQL introuvable"

**Solution :**
- Vérifiez que MySQL est installé
- Vérifiez que le service MySQL est démarré
- Vérifiez le fichier `.env`

### "Accès refusé à la base de données"

**Solution :**
- Vérifiez le mot de passe dans `.env`
- Vérifiez que l'utilisateur MySQL a les droits nécessaires
- Redémarrez le service MySQL

### "Erreur de connexion"

**Solution :**
- Vérifiez que MySQL tourne sur le port 3306
- Vérifiez le pare-feu Windows
- Désactivez temporairement l'antivirus

### "Application ne démarre pas"

**Solution :**
- Vérifiez que .NET Framework est installé
- Exécutez l'application en tant qu'administrateur
- Consultez le fichier journal dans `logs/ngokaf.log`

---

## Support technique

Si vous rencontrez des problèmes lors de l'installation :

1. Consultez le [Guide de dépannage](Guide_De_Pannage.md)
2. Vérifiez les journaux dans le dossier `logs`
3. Contactez le support avec :
   - Capture d'écran de l'erreur
   - Fichier journal (`logs/ngokaf.log`)
   - Configuration système

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
