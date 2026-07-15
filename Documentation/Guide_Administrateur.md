# Guide Administrateur - NGOKAF TRANS

## Table des matières

1. [Introduction](#introduction)
2. [Connexion](#connexion)
3. [Tableau de bord](#tableau-de-bord)
4. [Gestion des Trajets](#gestion-des-trajets)
5. [Gestion des Bus](#gestion-des-bus)
6. [Gestion des Conducteurs](#gestion-des-conducteurs)
7. [Gestion des Utilisateurs](#gestion-des-utilisateurs)
8. [Rapports](#rapports)
9. [Paramètres](#paramètres)
10. [Sauvegardes et Restaurations](#sauvegardes-et-restaurations)
11. [Notifications](#notifications)

---

## Introduction

Le module Administrateur de NGOKAF TRANS permet de gérer l'ensemble des opérations de l'agence de transport. Ce guide détaille toutes les fonctionnalités disponibles pour les administrateurs.

**Compte par défaut :**

- Utilisateur : `admin`
- Mot de passe : `admin123`

⚠️ **Important :** Changez le mot de passe par défaut après la première connexion.

---

## Connexion

1. Lancez l'application NGOKAF TRANS
2. Entrez votre identifiant et mot de passe
3. Cliquez sur "Connexion"
4. Le tableau de bord administrateur s'affiche

---

## Tableau de bord

Le tableau de bord présente une vue d'ensemble de l'activité de l'agence :

### Indicateurs clés

- **Ventes du jour** : Montant total des ventes de billets
- **Billets vendus** : Nombre de billets émis aujourd'hui
- **Bagages enregistrés** : Nombre total de bagages
- **Bus actifs** : Nombre de bus en service
- **Conducteurs disponibles** : Nombre de conducteurs actifs

### Graphiques

- **Ventes mensuelles** : Évolution des ventes sur les 12 derniers mois
- **Répartition par trajet** : Parts de marché par destination

---

## Gestion des Trajets

### Créer un trajet

1. Allez dans "Trajets" dans le menu latéral
2. Cliquez sur "Nouveau trajet"
3. Remplissez les informations :
   - **Origine** : Ville de départ
   - **Destination** : Ville d'arrivée
   - **Heure de départ** : Heure prévue
   - **Heure d'arrivée** : Heure estimée (optionnel)
   - **Distance** : Distance en km (optionnel)
   - **Prix** : Prix du billet en FC
   - **Statut** : Actif/Inactif
4. Cliquez sur "Enregistrer"

### Modifier un trajet

1. Sélectionnez le trajet dans la liste
2. Cliquez sur "Modifier"
3. Apportez les modifications nécessaires
4. Cliquez sur "Enregistrer"

### Supprimer un trajet

1. Sélectionnez le trajet
2. Cliquez sur "Supprimer"
3. Confirmez la suppression

⚠️ **Attention :** La suppression d'un trajet affecte les billets associés.

---

## Gestion des Bus

### Ajouter un bus

1. Allez dans "Bus" dans le menu
2. Cliquez sur "Nouveau bus"
3. Remplissez les informations :
   - **Immatriculation** : Plaque d'immatriculation
   - **Marque** : Fabricant (ex: Toyota, Mercedes)
   - **Modèle** : Modèle du véhicule
   - **Année** : Année de fabrication
   - **Capacité** : Nombre de sièges
   - **Couleur** : Couleur du bus
   - **Statut** : Actif/En maintenance/Hors service
4. Cliquez sur "Enregistrer"

### Gérer l'affectation

1. Sélectionnez un bus
2. Cliquez sur "Affecter à un trajet"
3. Choisissez le trajet et le conducteur
4. Cliquez sur "Confirmer"

---

## Gestion des Conducteurs

### Ajouter un conducteur

1. Allez dans "Conducteurs"
2. Cliquez sur "Nouveau conducteur"
3. Remplissez les informations :
   - **Nom complet** : Nom et prénom
   - **Téléphone** : Numéro de contact
   - **Permis** : Numéro de permis
   - **Date d'expiration** : Validité du permis
   - **Statut** : Actif/Indisponible
4. Cliquez sur "Enregistrer"

### Modifier le statut

1. Sélectionnez le conducteur
2. Cliquez sur "Modifier le statut"
3. Choisissez le nouveau statut
4. Cliquez sur "Enregistrer"

Une notification est envoyée automatiquement lorsqu'un conducteur devient indisponible.

---

## Gestion des Utilisateurs

### Créer un utilisateur

1. Allez dans "Utilisateurs"
2. Cliquez sur "Nouvel utilisateur"
3. Remplissez les informations :
   - **Nom complet** : Nom et prénom
   - **Identifiant** : Login unique
   - **Mot de passe** : Mot de passe (min. 6 caractères)
   - **Rôle** : Administrateur ou Caissier
   - **Email** : Adresse email (optionnel)
4. Cliquez sur "Enregistrer"

### Rôles disponibles

- **Administrateur** : Accès complet à toutes les fonctionnalités
- **Caissier** : Accès uniquement aux ventes et bagages

### Modifier un utilisateur

1. Sélectionnez l'utilisateur
2. Cliquez sur "Modifier"
3. Modifiez les informations nécessaires
4. Cliquez sur "Enregistrer"

### Réinitialiser le mot de passe

1. Sélectionnez l'utilisateur
2. Cliquez sur "Réinitialiser mot de passe"
3. Entrez le nouveau mot de passe
4. Cliquez sur "Confirmer"

---

## Rapports

### Types de rapports disponibles

1. **Rapport des ventes** : Détail des ventes par période
2. **Rapport des bagages** : Statistiques sur les bagages
3. **Rapport des trajets** : Performance par trajet
4. **Rapport financier** : Synthèse des revenus

### Générer un rapport

1. Allez dans "Rapports"
2. Sélectionnez le type de rapport
3. Choisissez la période (date début / date fin)
4. Cliquez sur "Générer"
5. Le rapport s'affiche à l'écran

### Exporter un rapport

1. Après génération, cliquez sur "Exporter"
2. Choisissez le format :
   - **PDF** : Pour impression
   - **Excel** : Pour analyse
   - **CSV** : Pour import dans autre logiciel
3. Sélectionnez le dossier de destination
4. Cliquez sur "Enregistrer"

---

## Paramètres

### Profil de l'agence

1. Allez dans "Paramètres"
2. Section "Profil agence"
3. Modifiez les informations :
   - **Nom de l'agence** : Nom affiché sur les tickets
   - **Adresse** : Adresse postale
   - **Téléphone** : Numéro de contact
   - **Terminal** : Nom du terminal
   - **Devise** : FC (fixe)
   - **TVA** : Taux de TVA en %
   - **Préfixe tickets** : Préfixe des numéros de billets (ex: TK-)
4. Cliquez sur "Enregistrer les paramètres"

### Paramètres d'impression

- **Largeur ticket** : 80mm ou 58mm selon l'imprimante
- **Largeur étiquette bagage** : 58mm ou 80mm

### Paramètres de session

⚠️ **Note :** La déconnexion automatique a été désactivée. La session reste active jusqu'à déconnexion manuelle.

### Paramètres de bagages

- **Frais base** : Tarif de base en FC
- **Tarif / kg** : Tarif par kilogramme en FC

### Changer le mot de passe administrateur

1. Section "Mot de passe administrateur"
2. Entrez le mot de passe actuel
3. Entrez le nouveau mot de passe (min. 6 caractères)
4. Confirmez le nouveau mot de passe
5. Cliquez sur "Changer le mot de passe"

---

## Sauvegardes et Restaurations

### Sauvegarde automatique

Le système effectue automatiquement une sauvegarde quotidienne à **00h00 (minuit)**.

**Ce qui est sauvegardé :**

- Base de données MySQL complète
- Tous les rapports générés (PDF, Excel, CSV)
- Historique organisé par année/mois/jour

**Emplacement :** `backups/YYYY/MM/DD/`

### Sauvegarde manuelle

1. Allez dans "Paramètres"
2. Section "Sauvegarde MySQL"
3. Cliquez sur "Créer une sauvegarde"
4. La sauvegarde est créée instantanément
5. Une notification confirme le succès

### Restaurer une sauvegarde

⚠️ **Attention :** La restauration écrase la base de données actuelle.

1. Allez dans "Paramètres"
2. Section "Sauvegarde MySQL"
3. Cliquez sur "Restaurer…"
4. Sélectionnez le fichier SQL dans le dossier backups
5. Confirmez l'avertissement
6. La restauration s'effectue
7. Redémarrez l'application

### Historique des sauvegardes

Les sauvegardes sont organisées ainsi :
```
backups/
├── 2026/
│   ├── 07/
│   │   ├── 15/
│   │   │   ├── ngokaf_trans_20260715_000001.sql
│   │   │   └── reports/
│   │   ├── 16/
│   │   └── ...
```

---

## Notifications

### Système de notifications

Le système envoie des notifications automatiques pour :

- ✅ Sauvegarde automatique réussie
- ❌ Échec de sauvegarde automatique
- 🚌 Bus complet (100% occupé)
- ⚠️ Sièges limités (5 ou moins)
- 🎫 Billet annulé
- 📦 Bagage enregistré
- 🗺️ Trajet annulé
- 👤 Conducteur indisponible
- 🚨 Erreur critique

### Accéder aux notifications

1. Cliquez sur l'icône 🔔 en haut à droite de l'écran
2. Le dialogue des notifications s'ouvre
3. Les notifications non lues apparaissent en gras

### Gérer les notifications

- **Marquer comme lu** : Cliquez sur l'icône ✓
- **Supprimer** : Cliquez sur l'icône 🗑️
- **Tout marquer lu** : Bouton en bas du dialogue
- **Supprimer les lues** : Bouton en haut du dialogue

### Badge de notification

Un point rouge sur la cloche 🔔 indique des notifications non lues.

---

## Journal d'audit

Toutes les actions administratives sont enregistrées dans le journal d'audit visible dans les Paramètres :

- Date et heure de l'action
- Type d'action (création, modification, suppression)
- Entité concernée (trajet, bus, utilisateur, etc.)
- ID de l'entité
- Détails de l'action
- Auteur de l'action

---

## Déconnexion

Pour quitter l'application :

1. Cliquez sur "DÉCONNEXION" dans le menu latéral
2. La session se termine
3. L'écran de connexion réapparaît

---

## Support technique

En cas de problème :

1. Consultez le [Guide de dépannage](Guide_De_Pannage.md)
2. Vérifiez le journal d'audit
3. Contactez le support technique avec :
   - Capture d'écran de l'erreur
   - Description détaillée du problème
   - Heure de survenue de l'erreur

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
