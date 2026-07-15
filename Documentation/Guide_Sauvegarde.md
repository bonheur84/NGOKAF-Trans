# Guide de Sauvegarde - NGOKAF TRANS

## Table des matières

1. [Introduction](#introduction)
2. [Sauvegarde automatique](#sauvegarde-automatique)
3. [Sauvegarde manuelle](#sauvegarde-manuelle)
4. [Organisation des sauvegardes](#organisation-des-sauvegardes)
5. [Vérification des sauvegardes](#vérification-des-sauvegardes)
6. [Bonnes pratiques](#bonnes-pratiques)

---

## Introduction

Les sauvegardes sont essentielles pour protéger les données de NGOKAF TRANS. Ce guide explique comment fonctionnent les sauvegardes automatiques et comment effectuer des sauvegardes manuelles.

---

## Sauvegarde automatique

### Fonctionnement

Le système effectue automatiquement une sauvegarde complète tous les jours à **00h00 (minuit)**.

### Ce qui est sauvegardé

- **Base de données MySQL** complète (tables, données, procédures stockées)
- **Rapports générés** (PDF, Excel, CSV)
- **Historique** organisé par date

### Emplacement des sauvegardes

Les sauvegardes sont stockées dans :

```
C:\Users\[Utilisateur]\AppData\Local\NGOKAF_TRANS\backups\
```

### Structure des dossiers

Les sauvegardes sont organisées par année, mois et jour :

```
backups/
├── 2026/
│   ├── 07/
│   │   ├── 15/
│   │   │   ├── ngokaf_trans_20260715_000001.sql
│   │   │   └── reports/
│   │   │       ├── ventes_20260715.pdf
│   │   │       └── bagages_20260715.xlsx
│   │   ├── 16/
│   │   │   ├── ngokaf_trans_20260716_000001.sql
│   │   │   └── reports/
│   │   └── ...
│   ├── 08/
│   └── ...
```

### Notifications de sauvegarde

Le système envoie automatiquement des notifications :

- ✅ **Sauvegarde réussie** : Notification verte avec icône de succès
- ❌ **Sauvegarde échouée** : Notification rouge avec icône d'erreur

Ces notifications apparaissent dans la cloche de notification en haut à droite de l'écran.

---

## Sauvegarde manuelle

### Quand effectuer une sauvegarde manuelle

Il est recommandé d'effectuer une sauvegarde manuelle avant :

- Une mise à jour de l'application
- Une modification importante des données
- Un changement de configuration
- Une maintenance du serveur

### Effectuer une sauvegarde manuelle

1. Connectez-vous en tant qu'administrateur
2. Allez dans "Paramètres"
3. Section "Sauvegarde MySQL"
4. Cliquez sur "Créer une sauvegarde"
5. Attendez la confirmation
6. Une notification confirme le succès

### Vérifier la sauvegarde

Après une sauvegarde manuelle :

1. Vérifiez la notification de succès
2. Naviguez vers le dossier `backups`
3. Vérifiez que le fichier SQL a été créé
4. Vérifiez la taille du fichier (doit être > 0)

---

## Organisation des sauvegardes

### Nom des fichiers

Les fichiers de sauvegarde sont nommés automatiquement :

```
ngokaf_trans_YYYYMMDD_HHMMSS.sql
```

Exemple : `ngokaf_trans_20260715_143022.sql`

### Dossiers de rapports

Chaque sauvegarde inclut un sous-dossier `reports/` contenant :

- Tous les rapports PDF générés ce jour-là
- Tous les exports Excel
- Tous les exports CSV

### Historique

Le système conserve :

- **Sauvegardes quotidiennes** : Illimité (recommandé de nettoyer manuellement)
- **Rapports** : Inclus dans chaque sauvegarde quotidienne

---

## Vérification des sauvegardes

### Vérifier l'intégrité

Pour vérifier qu'une sauvegarde est valide :

1. Ouvrez MySQL Command Line Client
2. Connectez-vous avec le mot de passe root
3. Tapez :

```sql
SOURCE C:/Users/[Utilisateur]/AppData/Local/NGOKAF_TRANS/backups/2026/07/15/ngokaf_trans_20260715_000001.sql;
```

4. Si aucune erreur n'apparaît, la sauvegarde est valide

### Vérifier le contenu

Pour voir le contenu d'une sauvegarde sans la restaurer :

1. Ouvrez le fichier `.sql` avec un éditeur de texte
2. Vérifiez que les tables sont présentes
3. Vérifiez que les données sont complètes

### Taille des sauvegardes

Une sauvegarde typique pèse :

- **Base vide** : ~500 Ko
- **1000 billets** : ~2 Mo
- **10 000 billets** : ~15 Mo
- **Avec rapports** : +1 à 5 Mo

---

## Bonnes pratiques

### Fréquence des sauvegardes

- **Automatique** : Quotidienne à minuit (configurée par défaut)
- **Manuelle** : Avant toute opération critique

### Stockage externe

Pour une sécurité maximale :

1. Copiez régulièrement le dossier `backups` sur :
   - Un disque dur externe
   - Un service cloud (Google Drive, Dropbox, etc.)
   - Un serveur de sauvegarde réseau

### Rétention des sauvegardes

Recommandations :

- **Garder** : Les 30 derniers jours
- **Archiver** : Une sauvegarde par mois pour l'année
- **Supprimer** : Les sauvegardes plus anciennes (après archivage)

### Nettoyage des sauvegardes

Pour libérer de l'espace disque :

1. Naviguez vers le dossier `backups`
2. Supprimez les dossiers de dates anciennes
3. Conservez toujours au moins une sauvegarde récente

### Documentation

Documentez chaque sauvegarde manuelle :

- Date et heure
- Raison de la sauvegarde
- Personne ayant effectué la sauvegarde
- Emplacement de la copie externe (si applicable)

---

## Sauvegarde de la configuration

### Fichiers de configuration à sauvegarder

En plus de la base de données, sauvegardez régulièrement :

- `.env` : Configuration MySQL et agence
- `config.ini` : Paramètres avancés

### Emplacement

Ces fichiers se trouvent dans :

```
C:\Users\[Utilisateur]\AppData\Local\NGOKAF_TRANS\
```

### Méthode de sauvegarde

1. Copiez manuellement ces fichiers
2. Renommez-les avec la date : `.env.20260715.backup`
3. Stockez-les dans un endroit sécurisé

---

## Automatisation externe

### Script de sauvegarde externe

Pour des sauvegardes plus fréquentes, vous pouvez créer un script :

```batch
@echo off
set BACKUP_DIR=C:\Backups\NGOKAF
set DATE=%date:~6,4%%date:~3,2%%date:~0,2%
xcopy "C:\Users\[Utilisateur]\AppData\Local\NGOKAF_TRANS\backups" "%BACKUP_DIR%\%DATE%\" /E /I /Y
echo Sauvegarde externe terminee : %DATE%
```

### Planificateur de tâches Windows

Pour automatiser la copie externe :

1. Ouvrez le Planificateur de tâches Windows
2. Créez une nouvelle tâche
3. Déclencheur : Quotidien à une heure spécifique
4. Action : Exécuter le script de sauvegarde
5. Activez la tâche

---

## Dépannage

### Sauvegarde automatique ne fonctionne pas

**Causes possibles :**
- MySQL n'est pas démarré
- Permissions insuffisantes sur le dossier `backups`
- Espace disque insuffisant

**Solutions :**
- Vérifiez que MySQL tourne
- Vérifiez les permissions du dossier
- Libérez de l'espace disque
- Consultez le journal `logs/ngokaf.log`

### Erreur lors de la sauvegarde manuelle

**Causes possibles :**
- Mot de passe MySQL incorrect
- Base de données corrompue
- Disque plein

**Solutions :**
- Vérifiez le fichier `.env`
- Testez la connexion MySQL
- Libérez de l'espace disque

### Fichier de sauvegarde vide

**Causes possibles :**
- Erreur during mysqldump
- Permissions incorrectes

**Solutions :**
- Vérifiez les permissions
- Testez mysqldump manuellement
- Consultez le journal d'erreurs

---

## Support

En cas de problème avec les sauvegardes :

1. Consultez le [Guide de dépannage](Guide_De_Pannage.md)
2. Vérifiez le journal `logs/ngokaf.log`
3. Contactez le support avec :
   - Capture d'écran de l'erreur
   - Fichier journal
   - Configuration système

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
