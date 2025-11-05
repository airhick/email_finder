#!/bin/bash
# Script pour démarrer l'application en local

echo "🚀 Démarrage de l'Email Finder API..."
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Vérifier que pip est installé
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 n'est pas installé. Veuillez l'installer d'abord."
    exit 1
fi

# Installer les dépendances si nécessaire
echo "📦 Vérification des dépendances..."
pip3 install -q -r requirements.txt

# Démarrer le serveur
echo ""
echo "✅ Démarrage du serveur sur http://localhost:5000"
echo "📝 Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""
echo "🌐 Ouvrez votre navigateur sur : http://localhost:5000"
echo ""

python3 app.py

