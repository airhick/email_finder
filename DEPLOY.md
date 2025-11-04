# Guide de déploiement sur Render

## Étapes rapides

### 1. Préparer le repository

Assurez-vous que tous les fichiers sont commités et poussés sur GitHub/GitLab/Bitbucket :
- `app.py`
- `email_finder.py`
- `requirements.txt`
- `Procfile` ou `render.yaml`
- `.gitignore`

### 2. Créer un compte Render

1. Allez sur [render.com](https://render.com)
2. Créez un compte (gratuit)
3. Connectez votre compte GitHub/GitLab/Bitbucket

### 3. Déployer le service

#### Option A : Via Dashboard (Simple)

1. Cliquez sur **"New"** → **"Web Service"**
2. Connectez votre repository
3. Configurez :
   - **Name**: `email-finder-api`
   - **Region**: Choisissez la région la plus proche
   - **Branch**: `main` ou `master`
   - **Root Directory**: (laissez vide)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: `Free` (ou Starter pour éviter l'endormissement)
4. Cliquez sur **"Create Web Service"**

#### Option B : Via Blueprint (Automatique)

1. Cliquez sur **"New"** → **"Blueprint"**
2. Sélectionnez votre repository
3. Render détectera automatiquement `render.yaml`
4. Cliquez sur **"Apply"**

### 4. Variables d'environnement (optionnel)

Dans les paramètres du service, ajoutez :
- `PYTHON_VERSION`: `3.11.0`
- `FLASK_ENV`: `production`

### 5. Attendre le déploiement

Render va automatiquement :
1. Builder votre application
2. Installer les dépendances
3. Démarrer le service

Le premier déploiement peut prendre 5-10 minutes.

### 6. Vérifier le déploiement

Une fois déployé, votre API sera accessible sur :
```
https://votre-service.onrender.com
```

Testez avec :
```bash
# Health check
curl https://votre-service.onrender.com/health

# Documentation
curl https://votre-service.onrender.com/api

# Test de recherche d'emails
curl "https://votre-service.onrender.com/api/find-emails?url=https://hanae-restaurant.ch/"
```

## Notes importantes

### Plan Free

- ✅ Gratuit
- ⚠️ Le service s'endort après 15 minutes d'inactivité
- ⚠️ La première requête après l'endormissement peut prendre 30-60 secondes
- ✅ Parfait pour les tests et projets personnels

### Plan Starter ($7/mois)

- ✅ Service toujours actif (pas d'endormissement)
- ✅ Meilleures performances
- ✅ Support SSL automatique
- ✅ Recommandé pour la production

### Monitoring (optionnel)

Pour éviter l'endormissement sur le plan Free, vous pouvez :
- Utiliser un service de monitoring comme [UptimeRobot](https://uptimerobot.com)
- Configurer un ping toutes les 5 minutes sur `/health`

## Troubleshooting

### Le service ne démarre pas

1. Vérifiez les logs dans Render Dashboard
2. Assurez-vous que `gunicorn` est dans `requirements.txt`
3. Vérifiez que la commande de démarrage est correcte : `gunicorn app:app`

### Erreur "Module not found"

1. Vérifiez que toutes les dépendances sont dans `requirements.txt`
2. Rebuild le service depuis Render Dashboard

### Timeout des requêtes

1. Augmentez le timeout dans votre code
2. Vérifiez que le site web cible est accessible
3. Considérez réduire `max_pages` pour les gros sites

### Service endormi (Free plan)

1. La première requête après l'endormissement peut être lente
2. Considérez upgrade au plan Starter pour la production

## Support

Pour plus d'aide :
- [Documentation Render](https://render.com/docs)
- [Support Render](https://render.com/support)

