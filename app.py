#!/usr/bin/env python3
"""
API Flask pour Email Finder Bot
Déployable sur Render
"""

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import logging
import csv
import io
from urllib.parse import urlparse
from email_finder import EmailFinder

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Créer l'application Flask
app = Flask(__name__)
CORS(app)  # Permettre les requêtes CORS

# Route de santé pour vérifier que l'API fonctionne
@app.route('/health', methods=['GET'])
def health():
    """Endpoint de santé"""
    return jsonify({
        'status': 'healthy',
        'service': 'Email Finder API'
    }), 200

# Route principale pour trouver les emails
@app.route('/api/find-emails', methods=['GET', 'POST'])
def find_emails():
    """
    Endpoint principal pour trouver les emails sur un site web
    
    GET params ou POST body:
    - url: URL du site à scraper (requis)
    - max_pages: Nombre maximum de pages à visiter (optionnel, défaut: 50)
    - timeout: Timeout pour les requêtes HTTP en secondes (optionnel, défaut: 10)
    
    Returns:
    JSON avec les emails trouvés et les métadonnées
    """
    try:
        # Récupérer les paramètres
        if request.method == 'POST':
            data = request.get_json() or {}
            url = data.get('url') or request.args.get('url')
            max_pages = data.get('max_pages') or request.args.get('max_pages', 50, type=int)
            timeout = data.get('timeout') or request.args.get('timeout', 10, type=int)
        else:
            url = request.args.get('url')
            max_pages = request.args.get('max_pages', 50, type=int)
            timeout = request.args.get('timeout', 10, type=int)
        
        # Valider l'URL
        if not url:
            return jsonify({
                'error': 'URL manquante',
                'message': 'Veuillez fournir une URL via le paramètre "url"',
                'example': '/api/find-emails?url=https://example.com'
            }), 400
        
        # Valider le format de l'URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return jsonify({
                    'error': 'URL invalide',
                    'message': 'L\'URL doit contenir un schéma (http:// ou https://)',
                    'example': 'https://example.com'
                }), 400
        except Exception as e:
            return jsonify({
                'error': 'URL invalide',
                'message': str(e)
            }), 400
        
        # Valider max_pages
        if max_pages < 1 or max_pages > 500:
            return jsonify({
                'error': 'max_pages invalide',
                'message': 'max_pages doit être entre 1 et 500'
            }), 400
        
        logger.info(f"Requête pour scraper: {url} (max_pages: {max_pages})")
        
        # Créer l'instance du finder
        finder = EmailFinder(url, max_pages=max_pages, timeout=timeout)
        
        # Lancer le crawl
        results = finder.crawl()
        
        # Retourner les résultats
        return jsonify({
            'success': True,
            'url': url,
            'results': {
                'total_emails': results['total_emails'],
                'emails': results['emails_found'],
                'pages_scraped': results['pages_scraped'],
                'important_pages': results['important_pages']
            }
        }), 200
        
    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        return jsonify({
            'error': 'Erreur de validation',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue lors du scraping',
            'details': str(e) if app.debug else None
        }), 500

# Route alternative avec l'URL dans le path (pour Render)
@app.route('/api/find-emails/<path:url>', methods=['GET'])
def find_emails_from_path(url):
    """
    Endpoint alternatif avec l'URL dans le chemin
    
    Exemple: /api/find-emails/https://example.com
    """
    try:
        # Ajouter le schéma si manquant
        if not url.startswith('http://') and not url.startswith('https://'):
            url = 'https://' + url
        
        # Récupérer les autres paramètres
        max_pages = request.args.get('max_pages', 50, type=int)
        timeout = request.args.get('timeout', 10, type=int)
        
        # Valider l'URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return jsonify({
                    'error': 'URL invalide',
                    'message': 'L\'URL doit contenir un schéma (http:// ou https://)',
                    'example': 'https://example.com'
                }), 400
        except Exception as e:
            return jsonify({
                'error': 'URL invalide',
                'message': str(e)
            }), 400
        
        # Valider max_pages
        if max_pages < 1 or max_pages > 500:
            return jsonify({
                'error': 'max_pages invalide',
                'message': 'max_pages doit être entre 1 et 500'
            }), 400
        
        logger.info(f"Requête pour scraper: {url} (max_pages: {max_pages})")
        
        # Créer l'instance du finder
        finder = EmailFinder(url, max_pages=max_pages, timeout=timeout)
        
        # Lancer le crawl
        results = finder.crawl()
        
        # Retourner les résultats
        return jsonify({
            'success': True,
            'url': url,
            'results': {
                'total_emails': results['total_emails'],
                'emails': results['emails_found'],
                'pages_scraped': results['pages_scraped'],
                'important_pages': results['important_pages']
            }
        }), 200
        
    except ValueError as e:
        logger.error(f"Erreur de validation: {e}")
        return jsonify({
            'error': 'Erreur de validation',
            'message': str(e)
        }), 400
        
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue lors du scraping',
            'details': str(e) if app.debug else None
        }), 500

# Route pour traiter un CSV
@app.route('/api/process-csv', methods=['POST'])
def process_csv():
    """
    Endpoint pour traiter un fichier CSV
    
    Le CSV doit contenir une colonne 'url' (ou 'URL').
    Pour chaque ligne, le bot scrapera l'URL et ajoutera une colonne 'email'
    avec les emails trouvés (séparés par des virgules si plusieurs).
    
    Form data:
    - file: fichier CSV (requis)
    - max_pages: nombre max de pages par site (optionnel, défaut: 50)
    - timeout: timeout en secondes (optionnel, défaut: 10)
    - url_column: nom de la colonne URL (optionnel, défaut: 'url')
    
    Returns:
    CSV avec colonne 'email' ajoutée
    """
    try:
        # Vérifier qu'un fichier a été uploadé
        if 'file' not in request.files:
            return jsonify({
                'error': 'Fichier manquant',
                'message': 'Veuillez fournir un fichier CSV via le paramètre "file"'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'error': 'Fichier vide',
                'message': 'Aucun fichier sélectionné'
            }), 400
        
        if not file.filename.lower().endswith('.csv'):
            return jsonify({
                'error': 'Format invalide',
                'message': 'Le fichier doit être un CSV (.csv)'
            }), 400
        
        # Récupérer les paramètres optionnels
        max_pages = request.form.get('max_pages', 50, type=int)
        timeout = request.form.get('timeout', 10, type=int)
        url_column = request.form.get('url_column', 'url').strip().lower()
        
        # Valider max_pages
        if max_pages < 1 or max_pages > 500:
            return jsonify({
                'error': 'max_pages invalide',
                'message': 'max_pages doit être entre 1 et 500'
            }), 400
        
        # Lire le CSV
        try:
            # Décoder le fichier
            stream = io.StringIO(file.stream.read().decode('utf-8-sig'))  # utf-8-sig pour gérer BOM
            csv_reader = csv.DictReader(stream)
            
            # Vérifier que la colonne URL existe
            fieldnames = csv_reader.fieldnames
            if not fieldnames:
                return jsonify({
                    'error': 'CSV invalide',
                    'message': 'Le CSV est vide ou invalide'
                }), 400
            
            # Chercher la colonne URL (case insensitive)
            url_col = None
            for col in fieldnames:
                if col.strip().lower() == url_column:
                    url_col = col
                    break
            
            if not url_col:
                return jsonify({
                    'error': 'Colonne URL introuvable',
                    'message': f'La colonne "{url_column}" n\'existe pas dans le CSV',
                    'colonnes_disponibles': list(fieldnames)
                }), 400
            
            # Lire toutes les lignes
            rows = list(csv_reader)
            
            if not rows:
                return jsonify({
                    'error': 'CSV vide',
                    'message': 'Le CSV ne contient aucune ligne de données'
                }), 400
            
            logger.info(f"Traitement de {len(rows)} URLs depuis le CSV")
            
            # Traiter chaque ligne
            results = []
            for idx, row in enumerate(rows, 1):
                url = row.get(url_col, '').strip()
                
                if not url:
                    logger.warning(f"Ligne {idx}: URL vide, ignorée")
                    row['email'] = ''
                    results.append(row)
                    continue
                
                # Ajouter le schéma si manquant
                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'https://' + url
                
                logger.info(f"Traitement ligne {idx}/{len(rows)}: {url}")
                
                try:
                    # Scraper l'URL
                    finder = EmailFinder(url, max_pages=max_pages, timeout=timeout)
                    found_emails = finder.find_emails()
                    
                    # Joindre les emails avec des virgules
                    email_str = ', '.join(found_emails) if found_emails else ''
                    row['email'] = email_str
                    
                    logger.info(f"Ligne {idx}: {len(found_emails)} email(s) trouvé(s)")
                    
                except Exception as e:
                    logger.error(f"Erreur lors du scraping de {url}: {e}")
                    row['email'] = f'ERROR: {str(e)}'
                
                results.append(row)
            
            # Créer le CSV de sortie
            output = io.StringIO()
            
            # Ajouter la colonne 'email' aux fieldnames si elle n'existe pas
            output_fieldnames = list(fieldnames)
            if 'email' not in output_fieldnames:
                output_fieldnames.append('email')
            
            csv_writer = csv.DictWriter(output, fieldnames=output_fieldnames)
            csv_writer.writeheader()
            csv_writer.writerows(results)
            
            # Préparer la réponse
            output.seek(0)
            csv_output = output.getvalue()
            
            # Créer un fichier en mémoire pour le retour
            mem = io.BytesIO()
            mem.write(csv_output.encode('utf-8-sig'))  # BOM pour Excel
            mem.seek(0)
            
            logger.info(f"CSV traité avec succès: {len(results)} lignes")
            
            return send_file(
                mem,
                mimetype='text/csv',
                as_attachment=True,
                download_name='results_with_emails.csv'
            )
            
        except UnicodeDecodeError:
            return jsonify({
                'error': 'Encodage invalide',
                'message': 'Le fichier CSV doit être encodé en UTF-8'
            }), 400
        except Exception as e:
            logger.error(f"Erreur lors de la lecture du CSV: {e}", exc_info=True)
            return jsonify({
                'error': 'Erreur de traitement CSV',
                'message': 'Une erreur est survenue lors de la lecture du CSV',
                'details': str(e) if app.debug else None
            }), 500
            
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}", exc_info=True)
        return jsonify({
            'error': 'Erreur serveur',
            'message': 'Une erreur est survenue lors du traitement',
            'details': str(e) if app.debug else None
        }), 500

# Route pour l'interface web avec formulaire CSV
@app.route('/', methods=['GET'])
def index():
    """Interface web pour uploader un CSV"""
    html_template = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Finder - CSV Processor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 40px;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        .upload-section {
            border: 2px dashed #ddd;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            margin-bottom: 30px;
            transition: all 0.3s;
        }
        .upload-section:hover {
            border-color: #667eea;
            background: #f8f9ff;
        }
        .upload-section.dragover {
            border-color: #667eea;
            background: #f0f4ff;
        }
        input[type="file"] {
            display: none;
        }
        .file-label {
            display: inline-block;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border-radius: 6px;
            cursor: pointer;
            font-size: 16px;
            transition: background 0.3s;
        }
        .file-label:hover {
            background: #5568d3;
        }
        .file-name {
            margin-top: 15px;
            color: #666;
            font-size: 14px;
        }
        .options {
            margin: 20px 0;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
        }
        .option-group {
            display: flex;
            flex-direction: column;
        }
        .option-group label {
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        .option-group input {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
        }
        .submit-btn {
            width: 100%;
            padding: 15px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            margin-top: 20px;
        }
        .submit-btn:hover:not(:disabled) {
            background: #5568d3;
        }
        .submit-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        .loading {
            display: none;
            text-align: center;
            margin: 20px 0;
            color: #667eea;
        }
        .loading.active {
            display: block;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .error {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            display: none;
        }
        .error.active {
            display: block;
        }
        .success {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 6px;
            margin: 20px 0;
            display: none;
        }
        .success.active {
            display: block;
        }
        .download-link {
            display: inline-block;
            margin-top: 10px;
            padding: 10px 20px;
            background: #28a745;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        .download-link:hover {
            background: #218838;
        }
        .info-box {
            background: #e7f3ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .info-box h3 {
            margin-bottom: 10px;
            color: #333;
        }
        .info-box ul {
            margin-left: 20px;
            color: #666;
        }
        .info-box li {
            margin: 5px 0;
        }
        @media (max-width: 600px) {
            .options {
                grid-template-columns: 1fr;
            }
            .container {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📧 Email Finder</h1>
        <p class="subtitle">Trouvez les emails sur vos sites web depuis un fichier CSV</p>
        
        <div class="info-box">
            <h3>Comment utiliser :</h3>
            <ul>
                <li>Préparez un fichier CSV avec une colonne "url" (ou "URL")</li>
                <li>Chaque ligne contient une URL à scraper</li>
                <li>Le CSV retourné contiendra une colonne "email" avec les emails trouvés</li>
            </ul>
        </div>
        
        <form id="uploadForm" enctype="multipart/form-data">
            <div class="upload-section" id="uploadSection">
                <input type="file" id="csvFile" name="file" accept=".csv" required>
                <label for="csvFile" class="file-label">📁 Choisir un fichier CSV</label>
                <div class="file-name" id="fileName">Aucun fichier sélectionné</div>
            </div>
            
            <div class="options">
                <div class="option-group">
                    <label for="maxPages">Pages maximum par site :</label>
                    <input type="number" id="maxPages" name="max_pages" value="50" min="1" max="500">
                </div>
                <div class="option-group">
                    <label for="timeout">Timeout (secondes) :</label>
                    <input type="number" id="timeout" name="timeout" value="10" min="1" max="300">
                </div>
            </div>
            
            <div class="option-group">
                <label for="urlColumn">Nom de la colonne URL :</label>
                <input type="text" id="urlColumn" name="url_column" value="url" placeholder="url">
            </div>
            
            <button type="submit" class="submit-btn" id="submitBtn">
                🔍 Rechercher les emails
            </button>
        </form>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Traitement en cours... Cela peut prendre plusieurs minutes selon le nombre d'URLs.</p>
        </div>
        
        <div class="error" id="error"></div>
        <div class="success" id="success">
            <strong>✅ Succès !</strong> Votre fichier CSV a été traité.
            <a href="#" id="downloadLink" class="download-link" download>📥 Télécharger le CSV avec les emails</a>
        </div>
    </div>
    
    <script>
        const fileInput = document.getElementById('csvFile');
        const fileName = document.getElementById('fileName');
        const uploadSection = document.getElementById('uploadSection');
        const form = document.getElementById('uploadForm');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const success = document.getElementById('success');
        const submitBtn = document.getElementById('submitBtn');
        const downloadLink = document.getElementById('downloadLink');
        
        // Afficher le nom du fichier
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                fileName.textContent = e.target.files[0].name;
            } else {
                fileName.textContent = 'Aucun fichier sélectionné';
            }
        });
        
        // Drag and drop
        uploadSection.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadSection.classList.add('dragover');
        });
        
        uploadSection.addEventListener('dragleave', () => {
            uploadSection.classList.remove('dragover');
        });
        
        uploadSection.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadSection.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                fileName.textContent = e.dataTransfer.files[0].name;
            }
        });
        
        // Soumission du formulaire
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            
            // Masquer les messages précédents
            error.classList.remove('active');
            success.classList.remove('active');
            loading.classList.add('active');
            submitBtn.disabled = true;
            
            try {
                const response = await fetch('/api/process-csv', {
                    method: 'POST',
                    body: formData
                });
                
                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ message: 'Erreur inconnue' }));
                    throw new Error(errorData.message || `Erreur ${response.status}`);
                }
                
                // Récupérer le CSV
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                
                // Créer un nom de fichier avec timestamp
                const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, -5);
                const originalName = fileInput.files[0].name.replace('.csv', '');
                const downloadFileName = `${originalName}_with_emails_${timestamp}.csv`;
                
                downloadLink.href = url;
                downloadLink.download = downloadFileName;
                
                loading.classList.remove('active');
                success.classList.add('active');
                
            } catch (err) {
                loading.classList.remove('active');
                error.textContent = '❌ Erreur: ' + err.message;
                error.classList.add('active');
            } finally {
                submitBtn.disabled = false;
            }
        });
    </script>
</body>
</html>
    """
    return render_template_string(html_template)

# Route pour la documentation API
@app.route('/api', methods=['GET'])
def api_docs():
    """Documentation de l'API"""
    return jsonify({
        'service': 'Email Finder API',
        'version': '1.0.0',
        'endpoints': {
            'health': {
                'method': 'GET',
                'path': '/health',
                'description': 'Vérifier l\'état de l\'API'
            },
            'find_emails': {
                'method': 'GET',
                'path': '/api/find-emails?url=<URL>&max_pages=<NUMBER>',
                'description': 'Trouver les emails sur un site web',
                'parameters': {
                    'url': 'URL du site à scraper (requis)',
                    'max_pages': 'Nombre maximum de pages à visiter (optionnel, défaut: 50, max: 500)',
                    'timeout': 'Timeout en secondes (optionnel, défaut: 10)'
                },
                'examples': [
                    '/api/find-emails?url=https://example.com',
                    '/api/find-emails?url=https://example.com&max_pages=100'
                ]
            },
            'find_emails_post': {
                'method': 'POST',
                'path': '/api/find-emails',
                'description': 'Trouver les emails (POST avec JSON)',
                'body': {
                    'url': 'URL du site à scraper (requis)',
                    'max_pages': 'Nombre maximum de pages (optionnel)',
                    'timeout': 'Timeout en secondes (optionnel)'
                },
                'example': {
                    'url': 'https://example.com',
                    'max_pages': 50
                }
            },
            'process_csv': {
                'method': 'POST',
                'path': '/api/process-csv',
                'description': 'Traiter un fichier CSV avec des URLs et trouver les emails',
                'content_type': 'multipart/form-data',
                'parameters': {
                    'file': 'Fichier CSV avec colonne "url" (requis)',
                    'max_pages': 'Nombre maximum de pages par site (optionnel, défaut: 50)',
                    'timeout': 'Timeout en secondes (optionnel, défaut: 10)',
                    'url_column': 'Nom de la colonne URL (optionnel, défaut: "url")'
                },
                'returns': 'CSV avec colonne "email" ajoutée',
                'example_curl': 'curl -X POST -F "file=@urls.csv" https://votre-api.onrender.com/api/process-csv'
            }
        }
    }), 200

if __name__ == '__main__':
    # Configuration pour le développement
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

