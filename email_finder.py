#!/usr/bin/env python3
"""
Email Finder Bot - Scrape un site web pour trouver tous les emails
"""

import re
import logging
from urllib.parse import urljoin, urlparse
from typing import Set, List, Dict, Tuple, Optional, Any
import requests
from bs4 import BeautifulSoup
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EmailFinder:
    """Bot pour trouver tous les emails sur un site web"""
    
    def __init__(self, base_url: str, max_pages: int = 10, timeout: int = 10, max_workers: int = 20):
        """
        Initialise le bot
        
        Args:
            base_url: URL de base du site à scraper
            max_pages: Nombre maximum de pages à visiter
            timeout: Timeout pour les requêtes HTTP en secondes
        """
        self.base_url = base_url.rstrip('/')
        parsed_url = urlparse(base_url)
        self.domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        self.max_pages = max_pages
        self.timeout = timeout
        self.max_workers = max_workers  # Nombre de threads pour le scraping parallèle
        
        # Pages visitées et à visiter
        self.visited_urls: Set[str] = set()
        self.to_visit: deque = deque([base_url])
        
        # Emails trouvés
        self.emails: Set[str] = set()
        
        # Lock pour la synchronisation des threads
        self.lock = threading.Lock()
        
        # Pages importantes à parser en priorité
        self.important_keywords = [
            'contact', 'politique', 'privacy', 'confidentialite', 
            'mentions-legales', 'legal', 'cgv', 'cgu', 'about',
            'a-propos', 'equipe', 'team', 'footer', 'mentions'
        ]
        
        # Headers pour les requêtes
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Pattern regex pour les emails
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
    
    def is_valid_url(self, url: str) -> bool:
        """Vérifie si l'URL est valide et appartient au même domaine"""
        try:
            parsed = urlparse(url)
            base_parsed = urlparse(self.domain)
            
            # Vérifier que c'est le même domaine
            if parsed.netloc != base_parsed.netloc:
                return False
            
            # Ignorer les fichiers non-HTML
            if any(url.lower().endswith(ext) for ext in [
                '.pdf', '.jpg', '.jpeg', '.png', '.gif', '.svg',
                '.zip', '.rar', '.exe', '.mp4', '.mp3', '.avi',
                '.css', '.js', '.xml', '.json'
            ]):
                return False
            
            # Ignorer les liens mailto:, tel:, javascript:, etc.
            if parsed.scheme not in ['http', 'https', '']:
                return False
            
            return True
        except Exception as e:
            logger.debug(f"Erreur lors de la validation de l'URL {url}: {e}")
            return False
    
    def normalize_url(self, url: str) -> str:
        """Normalise l'URL (enlève les fragments, paramètres de tracking, etc.)"""
        try:
            parsed = urlparse(url)
            # Garder seulement le schéma, netloc et path
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            # Enlever le trailing slash pour éviter les doublons
            normalized = normalized.rstrip('/')
            return normalized
        except Exception as e:
            logger.debug(f"Erreur lors de la normalisation de l'URL {url}: {e}")
            return url
    
    def extract_emails_from_text(self, text: str) -> Set[str]:
        """Extrait les emails d'un texte"""
        emails = set()
        matches = self.email_pattern.findall(text)
        
        for email in matches:
            # Filtrer les emails invalides (ex: example@example dans les exemples)
            email_lower = email.lower()
            if not any(skip in email_lower for skip in [
                'example.com', 'example@', 'test@', 'noreply',
                'no-reply', 'donotreply', 'placeholder'
            ]):
                emails.add(email_lower)
        
        return emails
    
    def is_important_page(self, url: str) -> bool:
        """Détermine si une page est importante (contact, politique, etc.)"""
        url_lower = url.lower()
        return any(keyword in url_lower for keyword in self.important_keywords)
    
    def fetch_page(self, url: str) -> Tuple[Optional[str], Optional[BeautifulSoup]]:
        """
        Récupère le contenu d'une page
        
        Returns:
            Tuple (text_content, soup_object) ou (None, None) en cas d'erreur
        """
        try:
            logger.info(f"Récupération de: {url}")
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Vérifier que c'est du HTML
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type:
                logger.debug(f"Type de contenu non-HTML: {content_type}")
                return None, None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extraire le texte brut
            text_content = soup.get_text()
            
            return text_content, soup
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Erreur lors de la récupération de {url}: {e}")
            return None, None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la récupération de {url}: {e}")
            return None, None
    
    def extract_links(self, soup: BeautifulSoup, current_url: str) -> List[str]:
        """Extrait tous les liens d'une page"""
        links = []
        
        for tag in soup.find_all('a', href=True):
            href = tag['href']
            # Convertir en URL absolue
            absolute_url = urljoin(current_url, href)
            normalized_url = self.normalize_url(absolute_url)
            
            if self.is_valid_url(normalized_url):
                links.append(normalized_url)
        
        return links
    
    def scrape_page(self, url: str, soup: Optional[BeautifulSoup] = None) -> Tuple[Set[str], Optional[BeautifulSoup]]:
        """
        Scrape une page et retourne les emails trouvés et le soup
        
        Args:
            url: URL de la page à scraper
            soup: Soup object optionnel (si déjà récupéré)
        
        Returns:
            Tuple (emails_found, soup_object)
        """
        emails_found = set()
        
        # Si soup n'est pas fourni, le récupérer
        if soup is None:
            text_content, soup = self.fetch_page(url)
            if text_content is None or soup is None:
                return emails_found, None
        else:
            text_content = soup.get_text()
        
        # Extraire les emails du texte
        emails_from_text = self.extract_emails_from_text(text_content)
        emails_found.update(emails_from_text)
        
        # Extraire les emails des attributs href="mailto:..."
        for tag in soup.find_all(href=re.compile(r'^mailto:', re.I)):
            mailto = tag.get('href', '')
            email = mailto.replace('mailto:', '').split('?')[0].strip()
            if email and '@' in email:
                emails_found.add(email.lower())
        
        # Extraire les emails des attributs data-email, data-contact, etc.
        for tag in soup.find_all(attrs={'data-email': True}):
            email = tag.get('data-email', '').strip()
            if email and '@' in email:
                emails_found.add(email.lower())
        
        # Extraire les emails des scripts JavaScript
        for script in soup.find_all('script'):
            if script.string:
                script_emails = self.extract_emails_from_text(script.string)
                emails_found.update(script_emails)
        
        # Extraire les emails des commentaires HTML
        for comment in soup.find_all(string=lambda text: isinstance(text, str) and '@' in text):
            comment_emails = self.extract_emails_from_text(str(comment))
            emails_found.update(comment_emails)
        
        logger.info(f"Emails trouvés sur {url}: {emails_found}")
        
        return emails_found, soup
    
    def _scrape_page_thread_safe(self, url: str) -> Tuple[Set[str], Optional[BeautifulSoup], List[str]]:
        """
        Scrape une page de manière thread-safe et retourne les emails, soup et liens
        
        Returns:
            Tuple (emails, soup, links)
        """
        emails_found, soup = self.scrape_page(url)
        links = []
        
        if soup:
            links = self.extract_links(soup, url)
        
        return emails_found, soup, links
    
    def crawl(self) -> Dict[str, Any]:
        """
        Crawl le site web et trouve tous les emails en parallèle
        
        Returns:
            Dictionnaire avec les résultats
        """
        logger.info(f"Début du crawl parallèle de {self.base_url} (max {self.max_pages} pages, {self.max_workers} workers)")
        
        pages_scraped = 0
        important_pages_found = []
        
        # Prioriser les pages importantes
        important_urls = []
        
        # Première passe : scraper la page d'accueil pour découvrir les liens
        urls_to_scrape = []
        normalized_base = self.normalize_url(self.base_url)
        urls_to_scrape.append(normalized_base)
        self.visited_urls.add(normalized_base)
        
        # Scraper la première page pour découvrir les liens
        emails_found, soup = self.scrape_page(normalized_base)
        with self.lock:
            self.emails.update(emails_found)
            pages_scraped += 1
            if self.is_important_page(normalized_base):
                important_pages_found.append(normalized_base)
        
        # Extraire les liens de la première page
        if soup:
            links = self.extract_links(soup, normalized_base)
            for link in links:
                normalized_link = self.normalize_url(link)
                if normalized_link not in self.visited_urls:
                    if self.is_important_page(normalized_link):
                        if normalized_link not in important_urls:
                            important_urls.append(normalized_link)
                    else:
                        if normalized_link not in self.to_visit:
                            self.to_visit.append(normalized_link)
        
        # Collecter les URLs jusqu'à atteindre max_pages (déjà 1 page scrapée)
        while len(urls_to_scrape) < self.max_pages and (self.to_visit or important_urls):
            # Traiter d'abord les pages importantes
            if important_urls:
                current_url = important_urls.pop(0)
            elif self.to_visit:
                current_url = self.to_visit.popleft()
            else:
                break
            
            normalized_url = self.normalize_url(current_url)
            
            # Skip si déjà visité ou déjà dans la liste
            if normalized_url in self.visited_urls or normalized_url in urls_to_scrape:
                continue
            
            self.visited_urls.add(normalized_url)
            urls_to_scrape.append(normalized_url)
            
            # Si on a atteint la limite, arrêter
            if len(urls_to_scrape) >= self.max_pages:
                break
        
        # Limiter à max_pages (on a déjà scrapé la première page)
        urls_to_scrape = urls_to_scrape[1:]  # Retirer la première page déjà scrapée
        
        # Scraper toutes les pages restantes en parallèle
        if urls_to_scrape:
            logger.info(f"Scraping de {len(urls_to_scrape)} pages supplémentaires en parallèle (1 page déjà scrapée)...")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Soumettre toutes les tâches
                future_to_url = {
                    executor.submit(self._scrape_page_thread_safe, url): url 
                    for url in urls_to_scrape
                }
                
                # Traiter les résultats au fur et à mesure
                for future in as_completed(future_to_url):
                    url = future_to_url[future]
                    normalized_url = self.normalize_url(url)
                    
                    try:
                        emails_found, soup, links = future.result()
                        
                        # Mettre à jour les emails de manière thread-safe
                        with self.lock:
                            self.emails.update(emails_found)
                            pages_scraped += 1
                            
                            # Marquer les pages importantes
                            if self.is_important_page(normalized_url):
                                important_pages_found.append(normalized_url)
                            
                            # Collecter les nouveaux liens pour un potentiel second passage
                            for link in links:
                                normalized_link = self.normalize_url(link)
                                if normalized_link not in self.visited_urls:
                                    if self.is_important_page(normalized_link):
                                        if normalized_link not in important_urls:
                                            important_urls.append(normalized_link)
                                    else:
                                        if normalized_link not in self.to_visit:
                                            self.to_visit.append(normalized_link)
                        
                        logger.info(f"✓ Page {pages_scraped}/{len(urls_to_scrape)+1}: {normalized_url} - {len(emails_found)} email(s) trouvé(s)")
                        
                    except Exception as e:
                        logger.error(f"Erreur lors du scraping de {url}: {e}")
        else:
            logger.info("Aucune page supplémentaire à scraper")
        
        logger.info(f"Crawl terminé. {pages_scraped} pages visitées, {len(self.emails)} emails trouvés")
        
        return {
            'base_url': self.base_url,
            'pages_scraped': pages_scraped,
            'emails_found': sorted(list(self.emails)),
            'important_pages': important_pages_found,
            'total_emails': len(self.emails)
        }
    
    def find_emails(self) -> List[str]:
        """
        Méthode principale pour trouver les emails
        
        Returns:
            Liste des emails trouvés
        """
        results = self.crawl()
        return results['emails_found']


def main():
    """Fonction principale pour l'utilisation en ligne de commande"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python email_finder.py <URL> [--max-pages N]")
        print("Exemple: python email_finder.py https://hanae-restaurant.ch/")
        sys.exit(1)
    
    url = sys.argv[1]
    max_pages = 100
    
    # Parser les arguments optionnels
    if '--max-pages' in sys.argv:
        idx = sys.argv.index('--max-pages')
        if idx + 1 < len(sys.argv):
            try:
                max_pages = int(sys.argv[idx + 1])
            except ValueError:
                print("Erreur: --max-pages doit être un nombre")
                sys.exit(1)
    
    print(f"\n{'='*60}")
    print(f"Email Finder Bot")
    print(f"{'='*60}")
    print(f"URL: {url}")
    print(f"Pages maximum: {max_pages}")
    print(f"{'='*60}\n")
    
    finder = EmailFinder(url, max_pages=max_pages)
    results = finder.crawl()
    
    print(f"\n{'='*60}")
    print(f"RÉSULTATS")
    print(f"{'='*60}")
    print(f"Pages visitées: {results['pages_scraped']}")
    print(f"Emails trouvés: {results['total_emails']}")
    print(f"\nPages importantes visitées:")
    for page in results['important_pages']:
        print(f"  - {page}")
    
    if results['emails_found']:
        print(f"\n📧 EMAILS TROUVÉS:")
        print(f"{'-'*60}")
        for email in results['emails_found']:
            print(f"  ✓ {email}")
    else:
        print(f"\n⚠️  Aucun email trouvé sur le site")
    
    print(f"\n{'='*60}\n")


if __name__ == '__main__':
    main()

