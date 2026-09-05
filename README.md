# Bot Telegram — Alertes logements CROUS Nord-Pas-de-Calais

Surveille [trouverunlogement.lescrous.fr](https://trouverunlogement.lescrous.fr) et
envoie un message Telegram dès qu'un nouveau logement apparaît dans la zone
Nord + Pas-de-Calais (donc toutes les résidences CROUS de la MEL sont couvertes,
ainsi que Douai, Valenciennes, Arras, Béthune, Boulogne, Dunkerque, etc.).

## ⚠️ À savoir avant de commencer

- Le site des CROUS n'a **pas d'API publique documentée** pour les résultats de
  recherche : ce bot lit directement la page HTML de résultats et repère les
  logements via leurs liens `/tools/{id}/accommodations/{id}`, qui sont stables.
  Si le site change fortement de structure, il faudra ajuster
  `crous_bot/crous_client.py`.
- Actuellement, la phase active ("phase complémentaire") est consultable
  **sans connexion**. Si une phase nécessitant une authentification (DSE)
  devient active, ce bot ne pourra pas voir les résultats tant qu'une gestion
  de session/connexion n'est pas ajoutée — non couvert par cette version.
- Testez toujours avec `python run_once.py` en local avant de déployer, pour
  vérifier que des logements sont bien détectés dans votre zone.

## 1. Créer le bot Telegram

1. Ouvrez Telegram et parlez à **@BotFather**.
2. Envoyez `/newbot`, choisissez un nom et un identifiant (ex: `crous_mel_bot`).
3. BotFather vous donne un **token** du type `123456789:AA...` → à mettre dans
   `TELEGRAM_BOT_TOKEN`.
4. Démarrez une conversation avec votre nouveau bot (cliquez sur le lien
   fourni par BotFather et envoyez `/start`), sinon il ne pourra pas vous
   écrire.
5. Récupérez votre `chat_id` (deux méthodes) :
   - **Sans bot tiers (recommandé)** : après avoir envoyé `/start` à votre
     bot, ouvrez dans un navigateur
     `https://api.telegram.org/bot<VOTRE_TOKEN>/getUpdates` : la réponse JSON
     contient `"chat":{"id": ...}`, c'est votre `chat_id`.
   - **Avec un bot tiers** : parlez à **@userinfobot** sur Telegram, il
     renvoie votre identifiant numérique.
   (Pour un groupe : ajoutez votre bot au groupe, envoyez-y un message, puis
   utilisez `getUpdates` comme ci-dessus — l'ID du groupe commence par `-`.)

## 2. Configuration

```bash
cp .env.example .env
```

Éditez `.env` et renseignez `TELEGRAM_BOT_TOKEN` et `TELEGRAM_CHAT_ID`.

La zone géographique par défaut (`CROUS_BOUNDS`) couvre déjà tout le
Nord-Pas-de-Calais. Si vous voulez vous limiter strictement à la MEL, vous
pouvez soit :
- restreindre le rectangle `CROUS_BOUNDS` (allez sur
  `https://trouverunlogement.lescrous.fr/tools/47/search`, faites une
  recherche sur "Lille" puis "Rechercher dans la zone affichée" sur la carte :
  l'URL affichera un paramètre `bounds=...` que vous pouvez copier), soit
- renseigner `CROUS_VILLES_FILTRE` avec la liste des communes de la MEL
  (ex: `Lille,Villeneuve-d'Ascq,Roubaix,Tourcoing,Marcq-en-Barœul,Lambersart,
  Mons-en-Barœul,Loos,Wattignies,Faches-Thumesnil`).

## 3. Lancer en local (test rapide)

```bash
pip install -r requirements.txt
python run_once.py
```

Le premier lancement enregistre les logements déjà en ligne sans spammer votre
Telegram (un seul message récapitulatif est envoyé). Les lancements suivants
n'alertent que sur les **nouveautés**.

Pour une surveillance continue en local (boucle infinie, vérifie toutes les
`POLL_INTERVAL_SECONDS`) :

```bash
python -m crous_bot.main
```

## 4. Déploiement gratuit et automatique (recommandé) — GitHub Actions

Cette méthode ne nécessite aucun serveur : GitHub exécute le script pour vous.

1. Créez un dépôt GitHub (public de préférence, pour des minutes Actions
   illimitées) et poussez-y tout ce dossier.
2. Dans **Settings → Secrets and variables → Actions → New repository
   secret**, ajoutez :
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
   - (optionnel) `CROUS_BOUNDS` si vous voulez surcharger la zone par défaut
3. Le workflow `.github/workflows/surveillance.yml` tourne toutes les ~10
   minutes et committe `logements_vus.json` pour garder l'état entre deux
   exécutions.
4. Onglet **Actions** → sélectionnez le workflow → **Run workflow** pour
   lancer un premier cycle manuellement et vérifier que tout fonctionne.

**Points d'attention GitHub Actions :**
- Les crons GitHub sont exécutés "au mieux" : un cycle toutes les 10 minutes
  planifiées peut réellement se déclencher avec 5 à 15 minutes de retard.
- GitHub désactive les workflows planifiés après 60 jours sans activité sur
  le dépôt (un e-mail vous prévient ; il suffit de cliquer sur "Enable" pour
  réactiver). Les commits automatiques de `logements_vus.json` comptent comme
  de l'activité, donc en pratique cela ne devrait pas arriver tant que le
  workflow tourne.

## 5. Alternative — petit serveur / Raspberry Pi / VPS

Si vous préférez une machine à vous qui tourne en continu :

```bash
pip install -r requirements.txt
nohup python -m crous_bot.main &
```

ou avec un service systemd, ou simplement une tâche cron qui appelle
`python run_once.py` toutes les 5-10 minutes.

## Structure du projet

```
crous-lille-notifier/
├── crous_bot/
│   ├── config.py           # lecture de la configuration (.env)
│   ├── crous_client.py     # interrogation du site CROUS + extraction des annonces
│   ├── storage.py          # mémorisation des logements déjà notifiés
│   ├── telegram_notifier.py# envoi des messages Telegram
│   └── main.py             # logique d'un cycle + boucle continue
├── run_once.py             # point d'entrée pour cron / GitHub Actions (un seul cycle)
├── requirements.txt
├── .env.example
└── .github/workflows/surveillance.yml
```

## Personnalisation

- **Zone géographique** : modifiez `CROUS_BOUNDS` dans `.env`.
- **Filtre par ville** : renseignez `CROUS_VILLES_FILTRE`.
- **Fréquence** : `POLL_INTERVAL_SECONDS` (mode boucle locale) ou le `cron`
  dans le workflow GitHub Actions.
- **Format du message Telegram** : éditez le texte dans
  `crous_bot/main.py` (fonction `run_once`).
