#!/usr/bin/env python3
"""
Exemple d'utilisation du Email Finder Bot
"""

from email_finder import EmailFinder

# Exemple 1: Utilisation simple
print("=" * 60)
print("Exemple 1: Utilisation simple")
print("=" * 60)

finder = EmailFinder("https://hanae-restaurant.ch/", max_pages=50)
emails = finder.find_emails()

print(f"\nEmails trouvés: {emails}\n")

# Exemple 2: Utilisation avec résultats détaillés
print("=" * 60)
print("Exemple 2: Résultats détaillés")
print("=" * 60)

finder2 = EmailFinder("https://hanae-restaurant.ch/", max_pages=50)
results = finder2.crawl()

print(f"\nBase URL: {results['base_url']}")
print(f"Pages visitées: {results['pages_scraped']}")
print(f"Total emails: {results['total_emails']}")
print(f"\nPages importantes:")
for page in results['important_pages']:
    print(f"  - {page}")
print(f"\nEmails trouvés:")
for email in results['emails_found']:
    print(f"  ✓ {email}")

