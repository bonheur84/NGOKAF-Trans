# Guide de Restauration - NGOKAF TRANS

## Table des matières

1. [Introduction](#introduction)
2. [Quand restaurer](#quand-restaurer)
3. [Préparation à la restauration](#préparation-à-la-restauration)
4. [Restauration via l'interface](#restauration-via-linterface)
5. [Restauration manuelle via MySQL](#restauration-manuelle-via-mysql)
6. [Vérification après restauration](#vérification-apès-restauration)
7. [Problèmes courants](#problèmes-courants)

---

## Introduction

La restauration permet de récupérer les données de NGOKAF TRANS à partir d'une sauvegarde. Ce guide explique comment restaurer la base de données en cas de problème.

⚠️ **Important :** La restauration écrase complètement la base de données actuelle. Effectuez toujours une sauvegarde avant de restaurer.

---

## Quand restaurer

Restaurez une sauvegarde dans les cas suivants :

- **Corruption de la base de données** : Erreurs SQL fréquentes
- **Perte de données** : Suppression accidentelle de données
- **Migration vers un nouveau serveur** : Transfert des données
- **Test de sauvegarde** : Vérification de l'intégrité
- **Rollback** : Retour à un état antérieur après une erreur

---

## Préparation à la restauration

### 1. Sauvegarder l'état actuel

Avant toute restauration, créez une sauvegarde de l'état actuel :

1. Connectez-vous en tant qu'administrateur
2. Allez dans "Paramètres"
3. Cliquez sur "Créer une sauvegarde"
4. Notez le nom du fichier de sauvegarde

### 2. Choisir la sauvegarde à restaurer

Naviguez vers le dossier `backups` :

```
C:\Users\[Utilisateur]\AppData\Local\NGOKAF_TRANS\backups\
```

Sélectionnez la sauvegarde appropriée en fonction de :

- **Date** : Choisissez la date souhaitée
- **Heure** : Si plusieurs sauvegardes ce jour-là
- **Taille** : Vérifiez que le fichier n'est pas vide

### 3. Vérifier l'intégrité

Vérifiez que le fichier SQL :

- Existe et n'est pas vide
- A une taille raisonnable (> 500 Ko)
- Peut être ouvert avec un éditeur de texte

### 4. Arrêter l'application

1. Fermez NGOKAF TRANS
2. Vérifiez qu'aucun processus ne tourne
3. Assurez-vous que MySQL est démarré

---

## Restauration via l'interface

### Méthode recommandée

1. Lancez NGOKAF TRANS
2. Connectez-vous en tant qu'administrateur
3. Allez dans "Paramètres"
4. Section "Sauvegarde MySQL"
5. Cliquez sur "Restaurer…"
6. Naviguez vers le dossier `backups`
7. Sélectionnez le fichier `.sql` à restaurer
8. Lisez l'avertissement attentivement
9. Cliquez sur "Oui" pour confirmer
10. Attendez la fin de la restauration
11. Cliquez sur "OK" à la confirmation
12. **Redémarrez l'application**

### Messages de confirmation

- **Succès** : "Restauration terminée. Redémarrez l'application."
- **Erreur** : Message d'erreur détaillé

---

## Restauration manuelle via MySQL

### Si l'interface ne fonctionne pas

#### 1. Ouvrir MySQL Command Line Client

1. Appuyez sur `Windows + R`
2. Tapez `cmd`
3. Tapez : `mysql -u root -p`
4. Entrez le mot de passe root

#### 2. Sélectionner la base de données

```sql
USE ngokaf_trans;
```

#### 3. Restaurer le fichier

```sql
SOURCE C:/Users/[Utilisateur]/AppData/Local/NGOKAF_TRANS/backups/2026/07/15/ngokaf_trans_20260715_000001.sql;
```

#### 4. Vérifier

```sql
SHOW TABLES;
SELECT COUNT(*) FROM tickets;
```

#### 5. Quitter

```sql
EXIT;
```

---

## Vérification après restauration

### 1. Redémarrer l'application

1. Fermez complètement NGOKAF TRANS
2. Relancez l'application
3. Connectez-vous en tant qu'administrateur

### 2. Vérifier les données

Vérifiez dans le tableau de bord :

- **Nombre de billets** : Doit correspondre à la sauvegarde
- **Nombre de bus** : Doit correspondre à la sauvegarde
- **Nombre de conducteurs** : Doit correspondre à la sauvegarde

### 3. Vérifier les rapports

1. Allez dans "Rapports"
2. Générez un rapport de ventes
3. Vérifiez que les données sont cohérentes

### 4. Vérifier les utilisateurs

1. Allez dans "Utilisateurs"
2. Vérifiez que tous les utilisateurs sont présents
3. Testez la connexion avec un compte utilisateur

### 5. Vérifier les trajets

1. Allez dans "Trajets"
2. Vérifiez que les trajets sont corrects
3. Vérifiez les prix et les horaires

---

## Problèmes courants

### "Fichier introuvable"

**Cause :** Chemin incorrect ou fichier déplacé

**Solution :**
- Vérifiez le chemin complet
- Naviguez manuellement vers le dossier
- Utilisez le bouton "Parcourir"

### "Accès refusé"

**Cause :** Permissions insuffisantes

**Solution :**
- Exécutez l'application en tant qu'administrateur
- Vérifiez les permissions du fichier
- Déplacez le fichier dans un dossier accessible

### "Erreur MySQL"

**Cause :** Connexion MySQL échouée

**Solution :**
- Vérifiez que MySQL est démarré
- Vérifiez le fichier `.env`
- Testez la connexion MySQL

### "Restauration incomplète"

**Cause :** Fichier corrompu

**Solution :**
- Vérifiez la taille du fichier
- Essayez une autre sauvegarde
- Restaurez manuellement via MySQL

### "Erreur de syntaxe SQL"

**Cause :** Fichier SQL corrompu ou incompatible

**Solution :**
- Vérifiez le contenu du fichier
- Essayez une sauvegarde plus récente
- Contactez le support technique

---

## Restauration sur un nouveau serveur

### Scénario : Migration vers un nouveau serveur

#### 1. Installer MySQL sur le nouveau serveur

Suivez le [Guide d'Installation](Guide_Installation.md)

#### 2. Créer la base de données vide

```sql
CREATE DATABASE ngokaf_trans;
```

#### 3. Copier les fichiers de sauvegarde

1. Copiez le dossier `backups` de l'ancien serveur
2. Collez-le sur le nouveau serveur
3. Notez le nouveau chemin

#### 4. Restaurer via MySQL

```sql
USE ngokaf_trans;
SOURCE C:/chemin/vers/sauvegarde.sql;
```

#### 5. Configurer l'application

1. Installez NGOKAF TRANS sur le nouveau serveur
2. Modifiez le fichier `.env` avec les nouveaux paramètres MySQL
3. Lancez l'application
4. Vérifiez que tout fonctionne

---

## Restauration partielle

### Scénario : Restaurer uniquement certaines tables

⚠️ **Avancé :** Cette opération nécessite des connaissances SQL.

#### 1. Extraire les tables souhaitées

1. Ouvrez le fichier `.sql` avec un éditeur de texte
2. Recherchez les instructions `CREATE TABLE` et `INSERT`
3. Copiez uniquement les sections nécessaires

#### 2. Restaurer manuellement

```sql
USE ngokaf_trans;

-- Supprimer l'ancienne table
DROP TABLE IF EXISTS tickets;

-- Créer la table (copiée du fichier)
CREATE TABLE tickets (...);

-- Insérer les données (copiées du fichier)
INSERT INTO tickets VALUES (...);
```

---

## Automatisation de la restauration

### Script de restauration

Pour automatiser les restaurations fréquentes :

```batch
@echo off
set BACKUP_FILE=%1
mysql -u root -p[votre_mot_de_passe] ngokaf_trans < %BACKUP_FILE%
echo Restauration terminee : %BACKUP_FILE%
```

Utilisation :

```batch
restore.bat C:\backups\ngokaf_trans_20260715.sql
```

---

## Journal des restaurations

Chaque restauration est enregistrée dans le journal d'audit :

- Date et heure de la restauration
- Fichier restauré
- Utilisateur ayant effectué la restauration
- Résultat (succès/échec)

Pour consulter le journal :

1. Allez dans "Paramètres"
2. Section "Journal d'audit"
3. Filtrez par "restore"

---

## Support

En cas de problème lors de la restauration :

1. Consultez le [Guide de dépannage](Guide_De_Pannage.md)
2. Vérifiez le journal `logs/ngokaf.log`
3. Contactez le support avec :
   - Capture d'écran de l'erreur
   - Fichier journal
   - Fichier de sauvegarde concerné
   - Configuration système

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
