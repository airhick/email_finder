@echo off
REM Script pour démarrer l'application en local (Windows)

echo 🚀 Démarrage de l'Email Finder API...
echo.

REM Vérifier que Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python n'est pas installé. Veuillez l'installer d'abord.
    pause
    exit /b 1
)

REM Installer les dépendances si nécessaire
echo 📦 Vérification des dépendances...
pip install -q -r requirements.txt

REM Démarrer le serveur
echo.
echo ✅ Démarrage du serveur sur http://localhost:5000
echo 📝 Appuyez sur Ctrl+C pour arrêter le serveur
echo.
echo 🌐 Ouvrez votre navigateur sur : http://localhost:5000
echo.

python app.py

pause

