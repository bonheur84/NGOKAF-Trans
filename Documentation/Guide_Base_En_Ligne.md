# Mettre NGOKAF TRANS sur une base MySQL en ligne

Utilisez une base **MySQL managée** (par exemple DigitalOcean Managed MySQL). Ne rendez jamais MySQL accessible à tout Internet sans restriction.

## 1. Créer la base

Créez un cluster MySQL 8, puis créez :

- une base : `ngokaf_trans` ;
- un utilisateur applicatif dédié, sans privilèges d'administration globaux ;
- une liste d'adresses IP autorisées : uniquement les IP publiques fixes des agences ou du VPN.

Téléchargez le certificat CA de l'hébergeur et placez-le dans un dossier protégé, par exemple `C:\ProgramData\NGOKAF_TRANS\certs\provider-ca.pem`.

## 2. Configurer chaque poste

Dans `%LOCALAPPDATA%\NGOKAF_TRANS\.env`, renseignez les paramètres fournis par l'hébergeur :

```env
DB_HOST=votre-hote-mysql.exemple.com
DB_PORT=25060
DB_USER=ngokaf_app
DB_PASSWORD=un-mot-de-passe-long-et-unique
DB_NAME=ngokaf_trans
DB_SSL_MODE=verify_ca
DB_SSL_CA=C:\ProgramData\NGOKAF_TRANS\certs\provider-ca.pem
DB_CREATE_DATABASE=false
DB_CONNECT_TIMEOUT=10
```

Ne partagez jamais ce fichier, le certificat ou le mot de passe sur WhatsApp, e-mail non chiffré ou GitHub.

## 3. Vérifier avant de lancer l’application

Depuis le dossier de l’application :

```powershell
python scripts\cloud_db_preflight.py
```

Le résultat doit afficher `[OK]` et une ligne `TLS` avec un chiffrement actif. Lancez ensuite l’application : les tables et index nécessaires seront vérifiés automatiquement.

## 4. Sauvegardes et exploitation

- Conservez les sauvegardes automatiques de l’hébergeur et activez la restauration à un instant donné si proposée.
- Gardez également un export chiffré quotidien hors de l’hébergeur.
- Testez une restauration avant le premier déploiement réel.
- Chaque poste doit avoir une connexion Internet stable ; pour plusieurs agences, un VPN ou des IP fixes est préférable.
- Créez un compte MySQL distinct pour chaque environnement (test et production).
