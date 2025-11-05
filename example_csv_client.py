#!/usr/bin/env python3
"""
Exemple de client pour utiliser l'API de traitement CSV
"""

import requests
import sys
import os

def process_csv_file(api_url, csv_file_path, max_pages=50, timeout=10, url_column='url'):
    """
    Envoie un fichier CSV à l'API et récupère le résultat avec les emails
    
    Args:
        api_url: URL de l'API (ex: http://localhost:5000 ou https://votre-api.onrender.com)
        csv_file_path: Chemin vers le fichier CSV à traiter
        max_pages: Nombre maximum de pages à scraper par site
        timeout: Timeout en secondes
        url_column: Nom de la colonne contenant les URLs
    
    Returns:
        Le contenu du CSV avec les emails
    """
    
    # Vérifier que le fichier existe
    if not os.path.exists(csv_file_path):
        print(f"Erreur: Le fichier {csv_file_path} n'existe pas")
        return None
    
    # Préparer la requête
    url = f"{api_url.rstrip('/')}/api/process-csv"
    
    with open(csv_file_path, 'rb') as f:
        files = {'file': (os.path.basename(csv_file_path), f, 'text/csv')}
        data = {
            'max_pages': max_pages,
            'timeout': timeout,
            'url_column': url_column
        }
        
        print(f"Envoi du fichier {csv_file_path} à l'API...")
        print(f"URL: {url}")
        print(f"Paramètres: max_pages={max_pages}, timeout={timeout}, url_column={url_column}")
        print()
        
        try:
            response = requests.post(url, files=files, data=data, timeout=None)
            response.raise_for_status()
            
            # Sauvegarder le résultat
            output_file = csv_file_path.replace('.csv', '_with_emails.csv')
            if output_file == csv_file_path:
                output_file = csv_file_path + '_with_emails.csv'
            
            with open(output_file, 'wb') as out:
                out.write(response.content)
            
            print(f"✅ Succès! Résultats sauvegardés dans: {output_file}")
            return response.content
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erreur lors de la requête: {e}")
            if hasattr(e.response, 'text'):
                print(f"Détails: {e.response.text}")
            return None


def main():
    """Fonction principale"""
    if len(sys.argv) < 3:
        print("Usage: python example_csv_client.py <API_URL> <CSV_FILE> [max_pages] [timeout] [url_column]")
        print()
        print("Exemples:")
        print("  python example_csv_client.py http://localhost:5000 example.csv")
        print("  python example_csv_client.py https://votre-api.onrender.com urls.csv 100 15")
        print("  python example_csv_client.py http://localhost:5000 example.csv 50 10 url")
        sys.exit(1)
    
    api_url = sys.argv[1]
    csv_file = sys.argv[2]
    max_pages = int(sys.argv[3]) if len(sys.argv) > 3 else 50
    timeout = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    url_column = sys.argv[5] if len(sys.argv) > 5 else 'url'
    
    result = process_csv_file(api_url, csv_file, max_pages, timeout, url_column)
    
    if result:
        print("\n✅ Traitement terminé avec succès!")
    else:
        print("\n❌ Échec du traitement")
        sys.exit(1)


if __name__ == '__main__':
    main()

