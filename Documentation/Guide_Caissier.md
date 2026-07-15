# Guide Caissier - NGOKAF TRANS

## Table des matières

1. [Introduction](#introduction)
2. [Connexion](#connexion)
3. [Interface principale](#interface-principale)
4. [Vente de billets](#vente-de-billets)
5. [Enregistrement des bagages](#enregistrement-des-bagages)
6. [Gestion des billets](#gestion-des-billets)
7. [Impression](#impression)
8. [Déconnexion](#déconnexion)

---

## Introduction

Le module Caissier de NGOKAF TRANS permet de gérer les ventes de billets et l'enregistrement des bagages. Ce guide détaille toutes les fonctionnalités disponibles pour les caissiers.

**Accès :** Les caissiers ont accès uniquement aux modules de vente et de bagages.

---

## Connexion

1. Lancez l'application NGOKAF TRANS
2. Entrez votre identifiant et mot de passe
3. Cliquez sur "Connexion"
4. L'interface caissier s'affiche

---

## Interface principale

L'interface caissier se compose de deux sections principales :

- **VENTES** : Gestion des ventes de billets
- **BAGAGES** : Enregistrement des bagages

Navigation entre les sections via le menu en haut de l'écran.

---

## Vente de billets

### Étape 1 : Sélectionner le trajet

1. Cliquez sur l'onglet "VENTES"
2. Dans la liste des trajets, sélectionnez :
   - **Origine** : Ville de départ
   - **Destination** : Ville d'arrivée
   - **Date** : Date du voyage
3. Cliquez sur "Rechercher"

### Étape 2 : Choisir le bus

1. Les bus disponibles pour le trajet s'affichent
2. Sélectionnez le bus souhaité
3. Les informations s'affichent :
   - Heure de départ
   - Prix du billet
   - Sièges disponibles

### Étape 3 : Sélectionner le siège

1. Le plan du bus s'affiche
2. Les sièges disponibles sont en vert
3. Les sièges occupés sont en rouge
4. Cliquez sur un siège disponible pour le sélectionner
5. Le siège passe en bleu (sélectionné)

### Étape 4 : Saisir les informations du passager

1. Remplissez le formulaire :
   - **Nom** : Nom du passager
   - **Prénom** : Prénom du passager
   - **Téléphone** : Numéro de contact (optionnel)
   - **Nombre de bagages** : Quantité de bagages (0 par défaut)

2. Le montant total s'affiche automatiquement

### Étape 5 : Confirmer la vente

1. Vérifiez les informations
2. Cliquez sur "Confirmer la vente"
3. Le billet est généré
4. Le ticket s'imprime automatiquement

### Annulation d'une vente

1. Allez dans "Historique des ventes"
2. Sélectionnez le billet à annuler
3. Cliquez sur "Annuler"
4. Confirmez l'annulation
5. Le siège est libéré
6. Une notification est envoyée

---

## Enregistrement des bagages

### Étape 1 : Sélectionner le billet

1. Cliquez sur l'onglet "BAGAGES"
2. Entrez le numéro de billet
3. Ou scannez le code QR du billet
4. Les informations du passager s'affichent

### Étape 2 : Peser le bagage

1. Placez le bagage sur la balance
2. Entrez le poids en kg
3. Le tarif est calculé automatiquement :
   - **Frais de base** : Tarif fixe
   - **Tarif au kg** : Poids × tarif/kg
   - **Total** : Frais de base + (poids × tarif/kg)

### Étape 3 : Générer l'étiquette

1. Vérifiez les informations
2. Cliquez sur "Générer l'étiquette"
3. L'étiquette s'imprime automatiquement
4. Collez l'étiquette sur le bagage

### Étape 4 : Confirmer l'enregistrement

1. Cliquez sur "Confirmer"
2. Le bagage est enregistré
3. Une notification confirme l'opération

### Historique des bagages

1. Cliquez sur "Historique"
2. Tous les bagages enregistrés s'affichent
3. Filtres disponibles :
   - Par date
   - Par trajet
   - Par numéro de billet

---

## Gestion des billets

### Consulter un billet

1. Allez dans "Historique des ventes"
2. Recherchez par :
   - Numéro de billet
   - Nom du passager
   - Date
3. Sélectionnez le billet
4. Les détails s'affichent

### Réimprimer un billet

1. Sélectionnez le billet dans l'historique
2. Cliquez sur "Réimprimer"
3. Le ticket est réimprimé

### Modifier un billet

⚠️ **Restriction :** Seuls certains champs peuvent être modifiés (téléphone, nombre de bagages).

1. Sélectionnez le billet
2. Cliquez sur "Modifier"
3. Modifiez les champs autorisés
4. Cliquez sur "Enregistrer"

---

## Impression

### Configuration de l'imprimante

1. Allez dans "Paramètres" (si accessible)
2. Section "Impression"
3. Configurez :
   - **Largeur ticket** : 80mm ou 58mm
   - **Largeur étiquette bagage** : 58mm ou 80mm
4. Cliquez sur "Enregistrer"

### Imprimer un ticket

L'impression est automatique après confirmation de vente.

### Imprimer une étiquette bagage

L'impression est automatique après génération de l'étiquette.

### Problèmes d'impression

Si l'impression échoue :

1. Vérifiez que l'imprimante est allumée
2. Vérifiez le papier
3. Vérifiez la connexion USB
4. Réessayez l'impression
5. Si le problème persiste, contactez l'administrateur

---

## Déconnexion

Pour quitter l'application :

1. Cliquez sur "Déconnexion" en haut à droite
2. La session se termine
3. L'écran de connexion réapparaît

⚠️ **Important :** Déconnectez-vous toujours après votre service.

---

## Bonnes pratiques

### Ventes

- Vérifiez toujours l'identité du passager
- Confirmez la destination avant la vente
- Vérifiez la disponibilité des sièges
- Imprimez toujours le ticket

### Bagages

- Vérifiez le poids réel
- Collez correctement l'étiquette
- Informez le passager des tarifs
- Enregistrez tous les bagages

### Sécurité

- Ne partagez pas votre mot de passe
- Déconnectez-vous après utilisation
- Signalez toute anomalie à l'administrateur
- Ne modifiez pas les paramètres système

---

## Erreurs fréquentes

### "Siège déjà occupé"

- Le siège a été vendu entre-temps
- Sélectionnez un autre siège
- Actualisez la liste des sièges

### "Billet introuvable"

- Vérifiez le numéro de billet
- Vérifiez la date
- Contactez l'administrateur si nécessaire

### "Erreur d'impression"

- Vérifiez l'imprimante
- Réessayez
- Contactez le support technique

### "Poids invalide"

- Vérifiez la balance
- Entrez un poids positif
- Le poids doit être en kg

---

## Support

En cas de problème :

1. Consultez le [Guide de dépannage](Guide_De_Pannage.md)
2. Contactez votre administrateur
3. Signalez l'erreur avec :
   - Heure de survenue
   - Action en cours
   - Message d'erreur

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
