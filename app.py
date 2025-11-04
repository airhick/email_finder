#!/usr/bin/env python3
"""
API Flask pour Email Finder Bot
Déployable sur Render
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
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

# Route pour la documentation
@app.route('/', methods=['GET'])
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
            }
        }
    }), 200

if __name__ == '__main__':
    # Configuration pour le développement
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

