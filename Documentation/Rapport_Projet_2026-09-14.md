# Rapport complet du projet NGOKAF TRANS

**Date de l'analyse :** 14 septembre 2026  
**Périmètre :** code source, configuration, build, installateur, documentation et tests disponibles dans le dépôt.  
**Conclusion :** NGOKAF TRANS est une application de bureau Windows fonctionnellement riche pour les opérations d'une compagnie de transport. Son architecture est claire et le passage au multi-agence est bien engagé. Les priorités suivantes sont de consolider les garanties de données en concurrence, sécuriser l'exploitation MySQL et synchroniser la documentation avec l'implémentation actuelle.

## 1. Finalité et périmètre fonctionnel

NGOKAF TRANS gère la vente de billets et l'enregistrement des bagages, avec des espaces distincts pour les caissiers et les administrateurs. L'application cible Windows 10/11 et dépend d'un serveur MySQL accessible localement ou sur le réseau.

Les fonctions principales observées sont :

- authentification des utilisateurs et rôles `administrateur` / `caissier` ;
- gestion de deux agences, Lubumbashi et Kolwezi, avec isolation des données ;
- gestion des bus, sièges, trajets et conducteurs ;
- vente, annulation et recherche de billets avec QR code et impression thermique 80 mm ;
- enregistrement, tarification, suivi et étiquette 58 mm des bagages ;
- tableau de bord, statistiques, finances et dépenses ;
- exports CSV, Excel et PDF, dont le manifeste passagers ;
- audit, notifications et sauvegardes MySQL manuelles ou planifiées.

## 2. Architecture technique

L'application est écrite en Python et suit une séparation de type MVC étendue par une couche de services :

```text
PySide6 views -> controllers -> services -> SQLAlchemy models -> MySQL
                                      |-> reports / exports / audit / backup
```

| Couche | Responsabilité | Éléments principaux |
|---|---|---|
| Point d'entrée | Initialise Qt, les ressources, les logs, la base et les fenêtres | `main.py` |
| Configuration | Charge `.env` et `config.ini`, sépare données modifiables et ressources packagées | `config/settings.py` |
| Données | Déclare les entités SQLAlchemy et les relations | `models/` |
| Accès DB | Crée la base, les tables et applique les migrations légères | `database/` |
| Métier | Applique les règles de vente, bagages, finances, export, audit et sauvegarde | `services/` |
| Interface | Écrans PySide6 administrateur, caissier et composants réutilisables | `views/` |
| Sorties | Tickets et étiquettes PDF, exports tableurs/PDF | `reports/`, `services/export_service.py` |

Le démarrage est robuste dans son intention : une vérification des ressources est exécutée, la base est initialisée avant l'ouverture de l'écran de connexion et les erreurs de démarrage sont affichées à l'utilisateur.

## 3. Technologies et dépendances

| Domaine | Technologies |
|---|---|
| Interface | PySide6, qtawesome, matplotlib |
| Persistance | MySQL 8+, SQLAlchemy 2, PyMySQL |
| Sécurité applicative | bcrypt, cryptography, python-dotenv |
| Documents | ReportLab, openpyxl, qrcode, python-barcode, Pillow |
| Packaging | PyInstaller, Inno Setup 6 |
| Compatibilité déclarée | Python 3.10+, Windows x64 |

La dépendance `opencv-python-headless` est également présente. Son usage direct n'a pas été identifié dans les fichiers Python listés ; elle mérite d'être confirmée afin de réduire le poids du paquet si elle n'est plus nécessaire.

## 4. Données et règles métier

### Entités principales

| Entité | Rôle |
|---|---|
| `agencies` | Agence, ville, coordonnées et statut ; socle du cloisonnement fonctionnel |
| `users` | Administrateurs et caissiers, mot de passe haché, agence, statut et dernière connexion |
| `buses`, `seats` | Parc, capacité, disposition et sièges générés par bus |
| `routes`, `drivers` | Trajets, bus, conducteur, horaires, distance et prix indicatif |
| `tickets`, `ticket_cancellations` | Ventes, siège, date de voyage, QR code et traçabilité des annulations |
| `luggage` | Expéditeur/destinataire, poids, frais, code-barres, QR code et statut |
| `expenses` | Dépenses, catégories, fournisseur, moyen de paiement et pièce jointe |
| `notifications`, `audit_logs`, `login_logs` | Alertes et journalisation des actions/connexions |
| `sequences`, `app_settings` | Numérotation journalière et paramètres par agence |

### Multi-agence

La migration ajoute `agency_id` aux tables opérationnelles et adapte plusieurs contraintes uniques au périmètre de l'agence : bus, bagages, paramètres, séquences et tickets. Les services de vente vérifient explicitement que le trajet et le bus appartiennent à l'agence du caissier. Les requêtes de liste et de statistiques utilisent également le contexte d'agence.

Les comptes créés/attendus par la migration sont `admin_lubumbashi` et `admin_kolwezi`. Les mots de passe initiaux codés dans la migration doivent être changés à l'installation ; ils ne doivent pas être considérés comme des identifiants de production pérennes.

### Cycle de vente

1. Le caissier choisit un trajet et un siège.
2. Le service vérifie l'agence, le bus, la capacité et l'occupation du siège.
3. Une séquence verrouillée attribue un numéro de billet journalier par agence.
4. Le billet, son QR code et un événement d'audit sont créés.
5. Une alerte est produite lorsqu'il reste cinq sièges ou moins, ou lorsque le bus devient complet.
6. Une annulation crée un enregistrement dédié et libère le siège pour les recherches ultérieures.

## 5. Interface, reporting et exploitation

L'administrateur dispose de modules dédiés au tableau de bord, aux trajets, bus, conducteurs, utilisateurs, bagages, finances, rapports, paramètres, audit et notifications. Le caissier utilise l'interface de ventes et de bagages.

Les impressions sont conçues pour les usages de guichet : ticket 80 mm avec QR code et étiquette bagage 58 mm avec code-barres/QR code. Les exports couvrent les ventes, bagages, manifeste bus, dépenses, activité, recettes et rapports financiers complets.

Les logs sont écrits dans `logs/ngokaf.log` avec rotation (2 Mo, cinq archives). Les sauvegardes sont organisées par année/mois/jour et incluent les rapports générés. Un minuteur Qt déclenche la sauvegarde automatique au prochain minuit après le lancement de l'application.

## 6. Build, installation et livraison

Le pipeline de distribution est cohérent avec une application Windows native :

1. `build.bat` installe les dépendances, génère l'icône et lance PyInstaller avec `main.spec`.
2. Inno Setup compile ensuite `installer/setup.iss`.
3. Le résultat attendu est l'exécutable dans `dist/NGOKAF_TRANS/` et l'installateur `installer/Output/Setup_Ngokaf_Trans.exe`.
4. Le workflow GitHub Actions construit et publie l'installateur lors d'un tag `v*`.

L'installateur est déclaré en version **2.0.0**, alors que le README affiche encore **1.0.0**. La version devrait être définie à un seul endroit ou injectée depuis le tag de release.

## 7. Vérifications réalisées

| Vérification | Résultat |
|---|---|
| Inventaire du dépôt et lecture de l'architecture | Réalisé |
| Lecture des modèles, services critiques, scripts de build et installateur | Réalisé |
| Compilation syntaxique (`python -m compileall`) | Réussie |
| Test d'isolation multi-agence | Présent, mais non exécuté : requiert MySQL configuré |
| Tests unitaires/CI automatisés | Aucun framework ou suite de tests récurrente identifié |

La compilation réussie établit l'absence d'erreur de syntaxe dans le code analysé. Elle ne remplace pas des tests fonctionnels avec MySQL, une imprimante de test ou un exécutable packagé.

## 8. Points forts

- Découpage lisible entre interface, services, modèles et infrastructure.
- Modèles SQLAlchemy typés et relations explicites.
- Cloisonnement multi-agence déjà porté dans les modèles, migrations et services sensibles.
- Mots de passe traités avec bcrypt plutôt qu'en clair.
- Journal d'audit et journal des connexions utiles pour l'exploitation.
- Gestion complète du cycle vente/bagage, avec sorties adaptées au terrain.
- Packaging et publication automatisée déjà en place.
- Gestion des erreurs de démarrage et rotation des journaux prévues.

## 9. Risques et améliorations recommandées

| Priorité | Constat | Risque | Recommandation |
|---|---|---|---|
| Haute | L'occupation d'un siège est vérifiée en applicatif, sans contrainte unique `(route_id, travel_date, seat_number)` ni transaction sérialisable visible. | Deux ventes simultanées peuvent attribuer le même siège. | Ajouter une contrainte unique incluant le trajet, la date et le siège ; intercepter proprement l'erreur d'intégrité. |
| Haute | `mysqldump` et `mysql` reçoivent le mot de passe dans leurs arguments. | Le mot de passe peut apparaître dans la liste des processus ou des diagnostics système. | Utiliser un fichier de configuration MySQL protégé, `MYSQL_PWD` avec précautions, ou une méthode d'authentification adaptée à l'environnement. |
| Haute | Les identifiants administrateurs initiaux sont codés dans la migration. | Accès non autorisé si le mot de passe n'est pas modifié dès le déploiement. | Forcer le changement de mot de passe au premier accès ou fournir des secrets de démarrage uniques par installation. |
| Moyenne | Le test d'isolation contient `assert ... or True`. | Cette assertion ne peut jamais échouer et donne une fausse assurance. | Retirer `or True` et ajouter des cas de données appartenant explicitement aux deux agences. |
| Moyenne | Le test d'isolation est un script manuel dépendant de la base réelle. | Régressions possibles avant livraison. | Ajouter pytest avec une base MySQL de test éphémère, et l'exécuter dans GitHub Actions. |
| Moyenne | Le README et `Documentation_Technique.md` décrivent encore l'ancien schéma et l'ancien administrateur par défaut. | Erreurs de configuration et support plus coûteux. | Mettre à jour les guides à partir des modèles actuels et mentionner le multi-agence. |
| Moyenne | La session expose un paramètre de délai, mais la documentation technique indique que la déconnexion automatique est désactivée. | Comportement de sécurité ambigu. | Définir, implémenter et tester une politique explicite d'expiration de session. |
| Basse | `opencv-python-headless` semble ne pas être référencé directement. | Distribution plus lourde et surface de maintenance accrue. | Confirmer l'usage et retirer la dépendance si elle est inutile. |
| Basse | La sauvegarde automatique ne s'exécute qu'après que l'application est restée ouverte jusqu'à minuit. | Une journée peut ne pas être sauvegardée si le poste est éteint. | Ajouter une vérification au démarrage : si aucune sauvegarde du jour précédent n'existe, en créer une ou alerter. |

## 10. Feuille de route proposée

### Court terme

1. Ajouter la contrainte d'unicité de siège et un test de vente concurrente.
2. Supprimer les secrets de démarrage prévisibles et forcer leur renouvellement.
3. Corriger le test multi-agence et créer une suite de tests automatisés minimale.
4. Actualiser README, guide technique et guides utilisateurs avec la version 2.0.0 et les deux agences.

### Moyen terme

1. Introduire des migrations versionnées (par exemple Alembic) à la place des migrations best-effort dispersées.
2. Ajouter des tests d'intégration pour les exports, annulations, droits et sauvegarde/restauration.
3. Formaliser la supervision : état de la dernière sauvegarde, rétention, alerte et procédure de restauration testée.
4. Mettre en place un numéro de version unique réutilisé par l'application, le README, l'installateur et la release CI.

## 11. Conclusion

Le projet possède une base solide et déjà proche d'un produit opérationnel : la couverture métier est large, l'expérience de caisse est prise en compte et la séparation multi-agence est structurante. Avant un déploiement étendu, la meilleure valeur provient de la sécurisation des accès et des sauvegardes, de l'intégrité des réservations en concurrence et d'une stratégie de tests/migrations reproductible. La mise à jour documentaire est également nécessaire pour que l'exploitation reflète fidèlement la version réellement distribuée.
