# Guide de Dépannage - NGOKAF TRANS

## Table des matières

1. [Introduction](#introduction)
2. [Problèmes de démarrage](#problèmes-de-démarrage)
3. [Problèmes de connexion](#problèmes-de-connexion)
4. [Problèmes de base de données](#problèmes-de-base-de-données)
5. [Problèmes d'impression](#problèmes-dimpression)
6. [Problèmes de sauvegarde](#problèmes-de-sauvegarde)
7. [Problèmes de performance](#problèmes-de-performance)
8. [Obtenir de l'aide](#obtenir-de-laide)

---

## Introduction

Ce guide aide à résoudre les problèmes courants rencontrés avec NGOKAF TRANS. Pour chaque problème, vous trouverez les causes possibles et les solutions recommandées.

---

## Problèmes de démarrage

### L'application ne démarre pas

**Symptômes :**
- Rien ne se passe au lancement
- Message d'erreur au démarrage
- L'application se ferme immédiatement

**Causes possibles :**
- MySQL n'est pas démarré
- Fichier de configuration corrompu
- Permissions insuffisantes
- .NET Framework manquant

**Solutions :**

1. **Vérifier MySQL**
   - Ouvrez Services Windows (`services.msc`)
   - Vérifiez que "MySQL" est en cours d'exécution
   - Si non, démarrez le service

2. **Vérifier la configuration**
   - Naviguez vers `AppData\Local\NGOKAF_TRANS\.env`
   - Vérifiez que le fichier existe et n'est pas vide
   - Vérifiez les paramètres MySQL

3. **Exécuter en tant qu'administrateur**
   - Clic droit sur l'application
   - "Exécuter en tant qu'administrateur"

4. **Vérifier le journal**
   - Consultez `logs/ngokaf.log`
   - Recherchez les messages d'erreur

### Erreur "Impossible de trouver Python"

**Cause :** Tentative d'exécution depuis les sources sans Python installé

**Solution :**
- Utilisez l'installateur `Setup_Ngokaf_Trans.exe`
- Python n'est pas requis sur les postes clients

---

## Problèmes de connexion

### "Mot de passe incorrect"

**Causes possibles :**
- Mot de passe erroné
- Touche Maj activée
- Compte verrouillé

**Solutions :**

1. **Vérifier le mot de passe**
   - Réessayez en faisant attention à la casse
   - Vérifiez que la touche Maj n'est pas activée

2. **Réinitialiser le mot de passe**
   - Contactez l'administrateur
   - L'administrateur peut réinitialiser via "Utilisateurs"

### "Utilisateur introuvable"

**Cause :** Identifiant incorrect ou compte supprimé

**Solution :**
- Vérifiez l'identifiant
- Contactez l'administrateur pour vérifier l'existence du compte

### "Compte verrouillé"

**Cause :** Trop de tentatives de connexion échouées

**Solution :**
- Contactez l'administrateur
- L'administrateur peut déverrouiller le compte

---

## Problèmes de base de données

### "Impossible de se connecter à MySQL"

**Symptômes :**
- Erreur de connexion au démarrage
- Message "Access denied"

**Causes possibles :**
- MySQL n'est pas démarré
- Mot de passe MySQL incorrect dans `.env`
- Port MySQL incorrect
- Pare-feu bloque la connexion

**Solutions :**

1. **Vérifier MySQL**
   ```bash
   # Ouvrir MySQL Command Line Client
   mysql -u root -p
   # Entrez le mot de passe
   ```

2. **Vérifier le fichier .env**
   ```
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=votre_mot_de_passe
   DB_NAME=ngokaf_trans
   ```

3. **Vérifier le port**
   - MySQL utilise par défaut le port 3306
   - Vérifiez qu'aucun autre service n'utilise ce port

4. **Vérifier le pare-feu**
   - Ajoutez une exception pour MySQL
   - Désactivez temporairement le pare-feu pour tester

### "Base de données introuvable"

**Cause :** La base `ngokaf_trans` n'existe pas

**Solution :**
```sql
CREATE DATABASE ngokaf_trans;
```

L'application créera automatiquement les tables au prochain démarrage.

### "Erreur SQL lors de l'opération"

**Symptômes :**
- Erreur lors de la création/modification de données
- Message d'erreur SQL spécifique

**Solutions :**

1. **Vérifier le journal**
   - Consultez `logs/ngokaf.log`
   - Recherchez l'erreur SQL exacte

2. **Vérifier l'intégrité de la base**
   ```sql
   USE ngokaf_trans;
   CHECK TABLE tickets;
   CHECK TABLE buses;
   CHECK TABLE routes;
   ```

3. **Restaurer une sauvegarde**
   - Si la base est corrompue, restaurez une sauvegarde
   - Consultez le [Guide de restauration](Guide_Restauration.md)

---

## Problèmes d'impression

### L'imprimante ne répond pas

**Causes possibles :**
- Imprimante éteinte
- Papier manquant
- Connexion USB déconnectée
- Pilote incorrect

**Solutions :**

1. **Vérifier l'imprimante**
   - Allumez l'imprimante
   - Vérifiez le papier
   - Vérifiez la connexion USB

2. **Vérifier les pilotes**
   - Ouvrir Gestionnaire de périphériques
   - Vérifiez que l'imprimante est reconnue
   - Réinstallez les pilotes si nécessaire

3. **Tester l'imprimante**
   - Imprimez une page de test Windows
   - Si ça échoue, le problème est l'imprimante

### "Erreur d'impression"

**Symptômes :**
- Message d'erreur lors de l'impression
- Ticket non imprimé

**Solutions :**

1. **Vérifier les paramètres d'impression**
   - Allez dans "Paramètres"
   - Section "Impression"
   - Vérifiez la largeur du ticket (80mm ou 58mm)

2. **Réimprimer**
   - Allez dans "Historique des ventes"
   - Sélectionnez le billet
   - Cliquez sur "Réimprimer"

### Impression de mauvaise qualité

**Causes possibles :**
- Tête d'impression encrassée
- Papier de mauvaise qualité
- Paramètres incorrects

**Solutions :**

1. **Nettoyer la tête d'impression**
   - Suivez les instructions du fabricant
   - Utilisez du papier de qualité

2. **Ajuster les paramètres**
   - Vérifiez la densité d'encre
   - Vérifiez la vitesse d'impression

---

## Problèmes de sauvegarde

### "Sauvegarde automatique échouée"

**Symptômes :**
- Notification d'échec de sauvegarde
- Aucun fichier dans `backups`

**Causes possibles :**
- MySQL n'est pas démarré
- Permissions insuffisantes sur le dossier
- Espace disque insuffisant

**Solutions :**

1. **Vérifier MySQL**
   - Assurez-vous que MySQL est démarré

2. **Vérifier les permissions**
   - Clic droit sur dossier `backups`
   - Propriétés > Sécurité
   - Vérifiez que vous avez les droits d'écriture

3. **Vérifier l'espace disque**
   - Ouvrir "Ce PC"
   - Vérifiez l'espace disponible sur le disque
   - Libérez de l'espace si nécessaire

### "Restauration échouée"

**Symptômes :**
- Erreur lors de la restauration
- Base de données inchangée

**Causes possibles :**
- Fichier de sauvegarde corrompu
- Permissions insuffisantes
- MySQL incompatible

**Solutions :**

1. **Vérifier le fichier**
   - Ouvrez le fichier `.sql` avec un éditeur de texte
   - Vérifiez qu'il n'est pas vide
   - Vérifiez qu'il contient des instructions SQL

2. **Restaurer manuellement**
   - Utilisez MySQL Command Line Client
   - Consultez le [Guide de restauration](Guide_Restauration.md)

---

## Problèmes de performance

### L'application est lente

**Symptômes :**
- Temps de réponse long
- Interface qui fige
- Chargement lent des données

**Causes possibles :**
- Base de données volumineuse
- Index manquants
- Mémoire insuffisante
- Trop de données en mémoire

**Solutions :**

1. **Optimiser la base de données**
   ```sql
   USE ngokaf_trans;
   OPTIMIZE TABLE tickets;
   OPTIMIZE TABLE buses;
   OPTIMIZE TABLE routes;
   ```

2. **Vérifier la mémoire**
   - Ouvrir Gestionnaire des tâches
   - Vérifiez l'utilisation de la mémoire
   - Fermez d'autres applications si nécessaire

3. **Nettoyer les données anciennes**
   - Archivez les anciennes ventes
   - Supprimez les données inutiles
   - Effectuez une sauvegarde avant suppression

### "Mémoire insuffisante"

**Symptômes :**
- Message d'erreur mémoire
- Application se ferme

**Solutions :**

1. **Augmenter la mémoire virtuelle**
   - Panneau de configuration > Système
   - Paramètres avancés > Performances
   - Augmentez la mémoire virtuelle

2. **Fermer les autres applications**
   - Fermez les applications inutiles
   - Libérez de la mémoire

---

## Problèmes de notification

### Les notifications ne s'affichent pas

**Causes possibles :**
- Service de notification désactivé
- Paramètres incorrects

**Solutions :**

1. **Vérifier les paramètres**
   - Allez dans "Paramètres"
   - Vérifiez que les notifications sont activées

2. **Redémarrer l'application**
   - Fermez et relancez NGOKAF TRANS

### Notifications en double

**Cause :** Timer de notification mal configuré

**Solution :**
- Redémarrez l'application
- Le problème devrait se résoudre

---

## Obtenir de l'aide

### Avant de contacter le support

1. **Notez les informations suivantes :**
   - Version de l'application
   - Système d'exploitation
   - Message d'erreur exact
   - Heure de survenue du problème
   - Actions effectuées avant le problème

2. **Consultez les journaux :**
   - `logs/ngokaf.log`
   - Copiez les messages d'erreur pertinents

3. **Effectuez une sauvegarde :**
   - Créez une sauvegarde avant toute intervention
   - Cela protège vos données

### Contactez le support

Fournissez les informations suivantes :

- **Description du problème** : Décrivez ce qui ne fonctionne pas
- **Capture d'écran** : Si possible, incluez une capture
- **Fichier journal** : Joignez `logs/ngokaf.log`
- **Configuration** : Version Windows, version MySQL
- **Reproduction** : Étapes pour reproduire le problème

### Ressources

- [Guide Administrateur](Guide_Administrateur.md)
- [Guide Installation](Guide_Installation.md)
- [Guide Sauvegarde](Guide_Sauvegarde.md)
- [Guide Restauration](Guide_Restauration.md)

---

## Diagnostic rapide

### Checklist de diagnostic

Avant de contacter le support, vérifiez :

- [ ] MySQL est-il démarré ?
- [ ] Le fichier `.env` est-il correct ?
- [ ] L'espace disque est-il suffisant ?
- [ ] L'imprimante fonctionne-t-elle ?
- [ ] Les journaux contiennent-ils des erreurs ?
- [ ] Une sauvegarde récente existe-t-elle ?

### Commandes de diagnostic utiles

```bash
# Vérifier MySQL
mysql -u root -p -e "SHOW DATABASES;"

# Vérifier les tables
mysql -u root -p ngokaf_trans -e "SHOW TABLES;"

# Vérifier l'espace disque
dir C:\Users\[Utilisateur]\AppData\Local\NGOKAF_TRANS\backups
```

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
