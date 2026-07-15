# Guide de Configuration - NGOKAF TRANS

## Table des matières

1. [Introduction](#introduction)
2. [Fichiers de configuration](#fichiers-de-configuration)
3. [Configuration MySQL](#configuration-mysql)
4. [Configuration de l'agence](#configuration-de-lagence)
5. [Configuration de l'impression](#configuration-de-limpression)
6. [Configuration des bagages](#configuration-des-bagages)
7. [Configuration avancée](#configuration-avancée)

---

## Introduction

Ce guide explique comment configurer NGOKAF TRANS selon vos besoins. La configuration se fait principalement via le fichier `.env` et l'interface administrateur.

---

## Fichiers de configuration

### Emplacement

Les fichiers de configuration se trouvent dans :

```
C:\Users\[Utilisateur]\AppData\Local\NGOKAF_TRANS\
```

### Fichiers disponibles

- **`.env`** : Configuration principale (MySQL, agence)
- **`config.ini`** : Paramètres avancés
- **`.env.example`** : Modèle de configuration
- **`config.ini.example`** : Modèle de configuration avancée

---

## Configuration MySQL

### Paramètres dans .env

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=votre_mot_de_passe
DB_NAME=ngokaf_trans
```

### DB_HOST

Adresse du serveur MySQL.

- **localhost** : MySQL installé sur la même machine
- **IP adresse** : MySQL sur un serveur distant (ex: 192.168.1.100)
- **nom de domaine** : MySQL accessible par nom de domaine

### DB_PORT

Port de connexion MySQL.

- **3306** : Port par défaut de MySQL
- **Autre port** : Si MySQL est configuré sur un port personnalisé

### DB_USER

Nom d'utilisateur MySQL.

- **root** : Utilisateur administrateur MySQL
- **Autre utilisateur** : Utilisateur avec droits sur la base ngokaf_trans

### DB_PASSWORD

Mot de passe de l'utilisateur MySQL.

⚠️ **Sécurité :** Utilisez un mot de passe fort et ne le partagez pas.

### DB_NAME

Nom de la base de données.

- **ngokaf_trans** : Nom par défaut (recommandé)
- **Autre nom** : Si vous utilisez un nom personnalisé

---

## Configuration de l'agence

### Paramètres dans .env

```env
AGENCY_NAME=NGOKAF TRANS
AGENCY_ADDRESS=BP 1245 - Douala, Cameroun
AGENCY_PHONE=(+237) 6XX XX XX XX
TERMINAL_NAME=TERMINAL PRINCIPAL
```

### AGENCY_NAME

Nom de l'agence affiché sur :

- Tickets
- Rapports
- Interface

### AGENCY_ADDRESS

Adresse postale de l'agence.

### AGENCY_PHONE

Numéro de téléphone de contact.

### TERMINAL_NAME

Nom du terminal ou de la gare.

### Modification via l'interface

1. Connectez-vous en tant qu'administrateur
2. Allez dans "Paramètres"
3. Section "Profil agence"
4. Modifiez les champs
5. Cliquez sur "Enregistrer les paramètres"

---

## Configuration de l'impression

### Paramètres dans .env

```env
TICKET_PREFIX=TK-
TICKET_WIDTH_MM=80
LUGGAGE_WIDTH_MM=58
```

### TICKET_PREFIX

Préfixe des numéros de billets.

- **TK-** : Par défaut
- **Autre** : Personnalisé selon vos besoins

Exemple : `BILLET-` générera des numéros comme `BILLET-000001`

### TICKET_WIDTH_MM

Largeur du ticket en millimètres.

- **80** : Imprimantes thermiques standard
- **58** : Imprimantes thermiques compactes

### LUGGAGE_WIDTH_MM

Largeur de l'étiquette bagage en millimètres.

- **58** : Étiquettes standard
- **80** : Étiquettes larges

### Modification via l'interface

1. Allez dans "Paramètres"
2. Section "Impression"
3. Sélectionnez les largeurs
4. Cliquez sur "Enregistrer les paramètres"

---

## Configuration des bagages

### Paramètres dans .env

```env
LUGGAGE_BASE_FEE=2500
LUGGAGE_WEIGHT_RATE=200
```

### LUGGAGE_BASE_FEE

Frais de base pour l'enregistrement d'un bagage (en FC).

- **2500** : Tarif par défaut
- **Autre** : Selon votre politique tarifaire

### LUGGAGE_WEIGHT_RATE

Tarif par kilogramme supplémentaire (en FC).

- **200** : Tarif par défaut
- **Autre** : Selon votre politique tarifaire

### Calcul du tarif

```
Total = Frais de base + (Poids en kg × Tarif/kg)
```

Exemple :

- Frais de base : 2500 FC
- Poids : 15 kg
- Tarif/kg : 200 FC
- Total = 2500 + (15 × 200) = 5500 FC

### Modification via l'interface

1. Allez dans "Paramètres"
2. Section "Session & bagages"
3. Modifiez les tarifs
4. Cliquez sur "Enregistrer les paramètres"

---

## Configuration avancée

### Fichier config.ini

Le fichier `config.ini` permet des paramètres avancés.

### Exemple de config.ini

```ini
[database]
pool_size=5
max_overflow=10
pool_timeout=30

[session]
timeout_minutes=30

[logging]
level=INFO
max_bytes=2000000
backup_count=5

[ui]
theme=default
language=fr
```

### Paramètres de base de données

- **pool_size** : Nombre de connexions dans le pool
- **max_overflow** : Nombre maximal de connexions supplémentaires
- **pool_timeout** : Délai d'attente pour une connexion (secondes)

### Paramètres de session

⚠️ **Note :** La déconnexion automatique a été désactivée. Ce paramètre n'est plus utilisé.

### Paramètres de journalisation

- **level** : Niveau de log (DEBUG, INFO, WARNING, ERROR)
- **max_bytes** : Taille maximale du fichier journal (octets)
- **backup_count** : Nombre de fichiers journal à conserver

### Paramètres d'interface

- **theme** : Thème de l'interface (default, dark, light)
- **language** : Langue de l'interface (fr, en)

---

 Configuration de la TVA

### Paramètre dans config.ini

```ini
[agency]
tva_percent=0
```

### TVA_PERCENT

Taux de TVA en pourcentage.

- **0** : Pas de TVA (par défaut)
- **19.25** : TVA Cameroun (exemple)
- **Autre** : Selon votre pays

### Application de la TVA

La TVA est appliquée automatiquement sur :

- Ventes de billets
- Frais de bagages

---

## Configuration des notifications

### Types de notifications

Le système envoie automatiquement des notifications pour :

- Sauvegardes automatiques (succès/échec)
- Bus complet
- Sièges limités
- Billets annulés
- Bagages enregistrés
- Trajets annulés
- Conducteurs indisponibles
- Erreurs critiques

### Activation/Désactivation

Les notifications sont activées par défaut. Pour les désactiver, modifiez le code source.

---

## Configuration des sauvegardes

### Sauvegarde automatique

La sauvegarde automatique est configurée pour s'exécuter tous les jours à 00h00.

Pour modifier l'heure, éditez `services/auto_backup_service.py`.

### Emplacement des sauvegardes

Par défaut : `AppData\Local\NGOKAF_TRANS\backups\`

Pour modifier, éditez `config/settings.py`.

---

## Configuration de sécurité

### Mot de passe administrateur

Changez le mot de passe par défaut après la première installation :

1. Connectez-vous en tant qu'admin
2. Allez dans "Paramètres"
3. Section "Mot de passe administrateur"
4. Entrez l'ancien mot de passe
5. Entrez le nouveau mot de passe (min. 6 caractères)
6. Confirmez
7. Cliquez sur "Changer le mot de passe"

### Création d'utilisateurs

Créez des comptes séparés pour chaque employé :

1. Allez dans "Utilisateurs"
2. Cliquez sur "Nouvel utilisateur"
3. Attribuez un rôle (Administrateur ou Caissier)
4. Définissez un mot de passe
5. Enregistrez

### Permissions

- **Administrateur** : Accès complet
- **Caissier** : Ventes et bagages uniquement

---

## Configuration réseau

### MySQL distant

Pour utiliser un serveur MySQL distant :

1. Modifiez `.env` :

   ```env
   DB_HOST=192.168.1.100
   DB_PORT=3306
   ```

2. Configurez le pare-feu du serveur MySQL pour autoriser les connexions

3. Assurez-vous que l'utilisateur MySQL a accès depuis votre IP

### Plusieurs postes

Pour plusieurs postes connectés à la même base :

1. Installez NGOKAF TRANS sur chaque poste
2. Configurez le même `.env` sur chaque poste (même DB_HOST)
3. Chaque poste doit avoir accès au serveur MySQL

---

## Configuration de l'interface

### Thème

Pour changer le thème :

1. Éditez `config.ini`
2. Modifiez `[ui] theme=`
3. Redémarrez l'application

Thèmes disponibles :

- **default** : Thème par défaut
- **dark** : Thème sombre
- **light** : Thème clair

### Langue

Pour changer la langue :

1. Éditez `config.ini`
2. Modifiez `[ui] language=`
3. Redémarrez l'application

Langues disponibles :

- **fr** : Français
- **en** : Anglais

---

## Vérification de la configuration

### Test de connexion MySQL

```bash
mysql -h localhost -P 3306 -u root -p
```

Si la connexion réussit, la configuration MySQL est correcte.

### Test de l'application

1. Lancez NGOKAF TRANS
2. Connectez-vous
3. Vérifiez que le tableau de bord s'affiche
4. Vérifiez que les données sont correctes

### Vérification des journaux

Consultez `logs/ngokaf.log` pour vérifier :

- Connexion MySQL réussie
- Chargement de la configuration
- Erreurs éventuelles

---

## Réinitialisation de la configuration

### Réinitialiser .env

1. Supprimez `.env`
2. Copiez `.env.example` vers `.env`
3. Modifiez les paramètres nécessaires
4. Redémarrez l'application

### Réinitialiser config.ini

1. Supprimez `config.ini`
2. Copiez `config.ini.example` vers `config.ini`
3. Modifiez les paramètres nécessaires
4. Redémarrez l'application

---

## Support

En cas de problème de configuration :

1. Consultez le [Guide de dépannage](Guide_De_Pannage.md)
2. Vérifiez les journaux dans `logs/ngokaf.log`
3. Contactez le support avec :
   - Fichiers de configuration
   - Messages d'erreur
   - Configuration système

---

**Version du logiciel :** 1.0  
**Date de mise à jour :** 15 Juillet 2026
