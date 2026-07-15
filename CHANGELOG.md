# Changelog

All notable changes to Ngokaf Trans will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release preparation

## [1.0.0] - 2026-07-15

### Added
- Système de gestion des billets et bagages
- Gestion des utilisateurs avec rôles (administrateur, caissier)
- Gestion des trajets et bus
- Gestion des conducteurs
- Système de facturation
- Rapports et statistiques
- Sauvegarde automatique de la base de données
- Interface utilisateur moderne avec PyQt5
- Configuration flexible via fichiers .env et config.ini
- Installateur Windows professionnel avec Inno Setup
- Support multi-terminal

### Security
- Mot de passe administrateur par défaut (admin/admin123) à changer au premier lancement
- Connexion sécurisée à la base de données MySQL

### Fixed
- Correction des bugs de connexion MySQL
- Optimisation des performances de l'interface

---

## Notes de version

### Version 1.0.0
- Première version stable de Ngokaf Trans
- Système complet de gestion de transport
- Installation facile via setup Windows
- Documentation complète incluse

---

## Procédure de mise à jour

Pour les utilisateurs finaux :
1. Télécharger la nouvelle version depuis GitHub Releases
2. Exécuter le nouveau setup
3. Suivre les instructions de mise à jour
4. Sauvegarder la base de données avant la mise à jour

Pour les développeurs :
1. Créer une nouvelle branche pour les modifications
2. Faire les commits avec des messages clairs
3. Créer un Pull Request
4. Après fusion, créer un tag git (ex: v1.1.0)
5. La release sera créée automatiquement par GitHub Actions
