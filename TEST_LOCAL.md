# Guide de test local

## Étapes pour tester l'interface en local

### 1. Installer les dépendances

Ouvrez un terminal dans le dossier du projet et installez les dépendances :

```bash
pip install -r requirements.txt
```

Ou si vous utilisez Python 3 spécifiquement :

```bash
pip3 install -r requirements.txt
```

### 2. Vérifier que tout est installé

Assurez-vous que tous les modules sont installés :

```bash
python -c "import flask, requests, bs4; print('✅ Toutes les dépendances sont installées')"
```

### 3. Démarrer le serveur

Lancez l'application Flask :

```bash
python app.py
```

Vous devriez voir un message comme :
```
 * Running on http://0.0.0.0:5000
```

**Note** : Si le port 5000 est déjà utilisé, vous pouvez modifier le port dans `app.py` ou utiliser une variable d'environnement :
```bash
PORT=8000 python app.py
```

### 4. Ouvrir l'interface dans le navigateur

Ouvrez votre navigateur et allez à :

```
http://localhost:5000
```

Ou :

```
http://127.0.0.1:5000
```

### 5. Tester avec un fichier CSV

#### Option A : Utiliser le fichier example.csv fourni

1. Sur l'interface web, cliquez sur "📁 Choisir un fichier CSV"
2. Sélectionnez le fichier `example.csv` dans le dossier du projet
3. Configurez les paramètres si besoin (par défaut : 50 pages, 10 secondes timeout)
4. Cliquez sur "🔍 Rechercher les emails"
5. Attendez le traitement (cela peut prendre quelques minutes)
6. Le CSV avec les emails sera téléchargé automatiquement

#### Option B : Créer votre propre CSV

Créez un fichier `test.csv` avec ce contenu :

```csv
url,name
https://hanae-restaurant.ch/,Hanae Restaurant
https://example.com,Example Site
```

Puis suivez les mêmes étapes que l'Option A.

### 6. Tester l'API directement

Vous pouvez aussi tester l'API directement via curl ou Python :

#### Avec curl :

```bash
curl -X POST -F "file=@example.csv" \
  -F "max_pages=50" \
  http://localhost:5000/api/process-csv \
  -o results.csv
```

#### Avec Python :

```bash
python example_csv_client.py http://localhost:5000 example.csv
```

### 7. Vérifier les logs

Pendant le traitement, vous verrez les logs dans le terminal où le serveur tourne :

```
2024-01-15 10:30:00 - INFO - Traitement de 3 URLs depuis le CSV
2024-01-15 10:30:01 - INFO - Traitement ligne 1/3: https://hanae-restaurant.ch/
2024-01-15 10:30:15 - INFO - Ligne 1: 2 email(s) trouvé(s)
...
```

### 8. Vérifier le résultat

Le CSV téléchargé devrait contenir une colonne "email" supplémentaire :

```csv
url,name,email
https://hanae-restaurant.ch/,Hanae Restaurant,info@hanae-restaurant.ch
https://example.com,Example Site,contact@example.com
```

## Dépannage

### Erreur "Module not found"

Installez les dépendances :
```bash
pip install -r requirements.txt
```

### Erreur "Port already in use"

Changez le port :
```bash
PORT=8000 python app.py
```

Puis accédez à `http://localhost:8000`

### Le serveur ne démarre pas

Vérifiez que vous êtes dans le bon dossier et que tous les fichiers sont présents :
- `app.py`
- `email_finder.py`
- `requirements.txt`

### L'interface ne charge pas

1. Vérifiez que le serveur tourne (vous devriez voir des logs dans le terminal)
2. Vérifiez l'URL : `http://localhost:5000` (pas `https://`)
3. Vérifiez les erreurs dans la console du navigateur (F12)

### Le traitement prend trop de temps

- Réduisez `max_pages` (par exemple à 10)
- Réduisez le nombre d'URLs dans votre CSV pour tester
- Augmentez le `timeout` si certains sites sont lents

## Astuce : Mode développement

Pour voir les erreurs détaillées, vous pouvez activer le mode debug dans `app.py` :

```python
app.run(host='0.0.0.0', port=port, debug=True)
```

**Attention** : Ne pas activer le debug en production !

## Test rapide

Pour un test rapide avec une seule URL :

1. Créez `test_simple.csv` :
```csv
url
https://hanae-restaurant.ch/
```

2. Upload sur l'interface
3. Résultat en quelques secondes !

