# Déploiement centralisé : application sans configuration sur les PC

Cette architecture sépare les postes de caisse de MySQL : seule l’API hébergée connaît les identifiants de la base.

```text
Application Windows → HTTPS → API NGOKAF TRANS → MySQL managé DigitalOcean
```

## DigitalOcean App Platform

1. Créez la base **Managed MySQL** et la base `ngokaf_trans`.
2. Dans **App Platform**, créez une application depuis ce dépôt Git.
3. Choisissez le `Dockerfile` : `api/Dockerfile`.
4. Configurez les variables serveur dans App Platform :

```text
DB_HOST=...
DB_PORT=...
DB_USER=...
DB_PASSWORD=...
DB_NAME=ngokaf_trans
DB_SSL_MODE=verify_ca
DB_SSL_CA=/app/certs/provider-ca.pem
DB_CREATE_DATABASE=false
API_TOKEN_SECRET=<valeur aléatoire de 32 caractères minimum>
```

5. Déposez le certificat CA dans le stockage de secrets/fichiers prévu par votre déploiement, ou construisez l’image avec le certificat hors dépôt Git.
6. Associez un domaine, par exemple `api.ngokaftrans.com`, et forcez HTTPS.
7. Vérifiez `https://api.ngokaftrans.com/health` : la réponse doit être `{"status":"ok"}`.

## Générer l'installateur pour les postes

Après le déploiement, compilez l'installateur avec l'URL réelle de l'API :

```powershell
iscc installer\setup.iss /DApiBaseUrl="https://api.votre-domaine.com"
```

L'installation crée automatiquement `%LOCALAPPDATA%\NGOKAF_TRANS\.env` contenant seulement `API_BASE_URL`. Aucun mot de passe MySQL, certificat de base de données ou secret d'API n'est copié sur les PC.

## Règle de sécurité

- `DB_PASSWORD`, `DB_SSL_CA` et `API_TOKEN_SECRET` restent exclusivement sur DigitalOcean.
- Les PC reçoivent seulement l’URL HTTPS de l’API, intégrée dans l’installateur final.
- Ne rendez jamais le port MySQL public pour les postes de caisse.

## Endpoints actuellement disponibles

Toutes les routes `/v1/*` requièrent l’en-tête `Authorization: Bearer <access_token>` reçu avec `POST /v1/auth/login`.

- `GET /health` : contrôle de disponibilité ;
- `POST /v1/auth/login` et `GET /v1/session` : connexion et session ;
- `GET /v1/routes` et `GET /v1/routes/{id}/occupied-seats?travel_date=YYYY-MM-DD` : trajets et sièges occupés ;
- `POST /v1/tickets`, `GET /v1/tickets`, `POST /v1/tickets/{id}/cancel` : ventes et annulations ;
- `GET /v1/luggage/ticket/{luggage_code}`, `POST /v1/luggage`, `GET /v1/luggage`, `PATCH /v1/luggage/{id}/status` : bagages.

En mode `API_BASE_URL`, l'application desktop lance la caisse connectée : authentification, consultation des trajets et sièges, vente/impression de billets, puis enregistrement/impression de bagages passent par HTTPS. Les écrans d'administration (bus, trajets, utilisateurs et finances) restent à basculer après l'ajout de leurs endpoints API correspondants.
