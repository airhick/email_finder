#!/usr/bin/env python3
"""
OpenStreetMap Scraper using Overpass API
Scrapes businesses and companies from OpenStreetMap data
"""

import requests
import logging
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote

logger = logging.getLogger(__name__)

# API Overpass d'OpenStreetMap
OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

class OSMScraper:
    """
    Classe pour scraper les données OpenStreetMap via l'API Overpass
    """
    
    def __init__(self, city: str, bbox: Optional[Tuple[float, float, float, float]] = None, timeout: int = 30):
        """
        Initialise le scraper OSM
        
        Args:
            city: Nom de la ville
            bbox: Bounding box (min_lat, min_lon, max_lat, max_lon) - optionnel
            timeout: Timeout pour les requêtes en secondes
        """
        self.city = city
        self.bbox = bbox
        self.timeout = timeout
        self.companies = []
        
    def geocode_city(self) -> Optional[Tuple[float, float, float, float]]:
        """
        Geocode une ville pour obtenir ses coordonnées et bounding box
        Utilise Nominatim (OpenStreetMap geocoding service)
        """
        try:
            url = f"https://nominatim.openstreetmap.org/search"
            params = {
                'q': self.city,
                'format': 'json',
                'limit': 1,
                'addressdetails': 1
            }
            headers = {
                'User-Agent': 'PassivLeads/1.0'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            if data:
                location = data[0]
                # Extraire la bounding box depuis les données
                if 'boundingbox' in location:
                    bbox = location['boundingbox']
                    # bbox format: [min_lat, max_lat, min_lon, max_lon]
                    return (float(bbox[0]), float(bbox[2]), float(bbox[1]), float(bbox[3]))
                elif 'lat' in location and 'lon' in location:
                    # Si pas de bbox, créer une zone autour du point central
                    lat = float(location['lat'])
                    lon = float(location['lon'])
                    # Créer une zone de ~5km autour
                    offset = 0.045  # ~5km
                    return (lat - offset, lon - offset, lat + offset, lon + offset)
            
            return None
        except Exception as e:
            logger.error(f"Erreur lors du geocoding de {self.city}: {e}")
            return None
    
    def build_overpass_query(self, company_types: List[str]) -> str:
        """
        Construit une requête Overpass QL pour récupérer les entreprises
        
        Args:
            company_types: Liste des types d'entreprises (amenity, shop, office, etc.)
        
        Returns:
            Requête Overpass QL formatée
        """
        if not self.bbox:
            self.bbox = self.geocode_city()
            if not self.bbox:
                raise ValueError(f"Impossible de géocoder la ville: {self.city}")
        
        min_lat, min_lon, max_lat, max_lon = self.bbox
        
        # Construire les filtres pour les types d'entreprises
        filters = []
        
        # Types d'amenity courants
        amenity_types = ['restaurant', 'cafe', 'bar', 'hotel', 'bank', 'pharmacy', 
                        'hospital', 'school', 'university', 'library', 'cinema', 
                        'theatre', 'fuel', 'parking', 'post_office', 'police', 
                        'fire_station', 'townhall', 'courthouse']
        
        # Types de shop courants
        shop_types = ['supermarket', 'bakery', 'butcher', 'clothes', 'shoes', 
                     'electronics', 'furniture', 'bookshop', 'jewelry', 'hairdresser',
                     'florist', 'car', 'bicycle', 'hardware', 'department_store']
        
        # Types d'office
        office_types = ['lawyer', 'accountant', 'insurance', 'estate_agent', 
                       'architect', 'consulting', 'it', 'advertising']
        
        # Types de craft
        craft_types = ['carpenter', 'electrician', 'plumber', 'painter', 
                      'photographer', 'printmaker', 'tailor', 'blacksmith']
        
        # Construire les filtres selon les types demandés
        for comp_type in company_types:
            comp_type_lower = comp_type.lower().strip()
            
            # Vérifier si c'est un type d'amenity
            if comp_type_lower in amenity_types:
                filters.append(f'node["amenity"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'way["amenity"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
            
            # Vérifier si c'est un type de shop
            elif comp_type_lower in shop_types:
                filters.append(f'node["shop"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'way["shop"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
            
            # Vérifier si c'est un type d'office
            elif comp_type_lower in office_types:
                filters.append(f'node["office"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'way["office"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
            
            # Vérifier si c'est un type de craft
            elif comp_type_lower in craft_types:
                filters.append(f'node["craft"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'way["craft"="{comp_type_lower}"]({min_lat},{min_lon},{max_lat},{max_lon});')
            
            # Sinon, chercher dans tous les champs courants
            else:
                # Recherche générique dans amenity, shop, office, craft
                filters.append(f'node["amenity"~".*{comp_type_lower}.*"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'way["amenity"~".*{comp_type_lower}.*"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'node["shop"~".*{comp_type_lower}.*"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'way["shop"~".*{comp_type_lower}.*"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'node["office"~".*{comp_type_lower}.*"]({min_lat},{min_lon},{max_lat},{max_lon});')
                filters.append(f'way["office"~".*{comp_type_lower}.*"]({min_lat},{min_lon},{max_lat},{max_lon});')
        
        # Si aucun filtre spécifique, récupérer toutes les entreprises
        if not filters:
            filters.append(f'node["amenity"]({min_lat},{min_lon},{max_lat},{max_lon});')
            filters.append(f'way["amenity"]({min_lat},{min_lon},{max_lat},{max_lon});')
            filters.append(f'node["shop"]({min_lat},{min_lon},{max_lat},{max_lon});')
            filters.append(f'way["shop"]({min_lat},{min_lon},{max_lat},{max_lon});')
            filters.append(f'node["office"]({min_lat},{min_lon},{max_lat},{max_lon});')
            filters.append(f'way["office"]({min_lat},{min_lon},{max_lat},{max_lon});')
        
        # Construire la requête complète (format Overpass QL correct)
        query = f"""[out:json][timeout:{self.timeout}];
(
    {''.join(filters)}
);
out body;
>;
out skel qt;"""
        return query
    
    def scrape_companies(self, company_types: List[str]) -> List[Dict]:
        """
        Scrape les entreprises depuis OpenStreetMap
        
        Args:
            company_types: Liste des types d'entreprises à rechercher
        
        Returns:
            Liste des entreprises trouvées
        """
        try:
            # Obtenir le bbox si nécessaire
            if not self.bbox:
                self.bbox = self.geocode_city()
                if not self.bbox:
                    raise ValueError(f"Impossible de géocoder la ville: {self.city}")
            
            # Construire la requête Overpass
            query = self.build_overpass_query(company_types)
            
            logger.info(f"Scraping OSM pour {self.city} avec {len(company_types)} types d'entreprises")
            
            # Faire la requête à l'API Overpass
            response = requests.post(
                OVERPASS_API_URL,
                data=query,
                headers={'Content-Type': 'text/plain'},
                timeout=self.timeout + 10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Parser les résultats
            companies = []
            elements = data.get('elements', [])
            
            for element in elements:
                if element.get('type') in ['node', 'way']:
                    tags = element.get('tags', {})
                    
                    # Extraire les informations pertinentes
                    company = {
                        'name': tags.get('name', ''),
                        'type': tags.get('amenity') or tags.get('shop') or tags.get('office') or tags.get('craft') or '',
                        'category': tags.get('amenity') or tags.get('shop') or tags.get('office') or tags.get('craft') or '',
                        'address': tags.get('addr:street', ''),
                        'housenumber': tags.get('addr:housenumber', ''),
                        'postcode': tags.get('addr:postcode', ''),
                        'city': tags.get('addr:city', '') or self.city,
                        'phone': tags.get('phone', '') or tags.get('contact:phone', ''),
                        'website': tags.get('website', '') or tags.get('contact:website', ''),
                        'email': tags.get('email', '') or tags.get('contact:email', ''),
                        'opening_hours': tags.get('opening_hours', ''),
                        'lat': element.get('lat', ''),
                        'lon': element.get('lon', ''),
                        'osm_id': element.get('id', ''),
                        'osm_type': element.get('type', '')
                    }
                    
                    # Pour les ways, obtenir le centre depuis les coordonnées
                    if element.get('type') == 'way' and 'center' in element:
                        company['lat'] = element['center'].get('lat', '')
                        company['lon'] = element['center'].get('lon', '')
                    
                    # Construire l'adresse complète
                    address_parts = []
                    if company['housenumber']:
                        address_parts.append(company['housenumber'])
                    if company['address']:
                        address_parts.append(company['address'])
                    if company['postcode']:
                        address_parts.append(company['postcode'])
                    if company['city']:
                        address_parts.append(company['city'])
                    
                    company['full_address'] = ', '.join(address_parts) if address_parts else ''
                    
                    # Ajouter seulement si l'entreprise a un nom
                    if company['name']:
                        companies.append(company)
            
            logger.info(f"Trouvé {len(companies)} entreprises pour {self.city}")
            self.companies = companies
            
            return companies
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la requête Overpass: {e}")
            raise
        except Exception as e:
            logger.error(f"Erreur lors du scraping OSM: {e}", exc_info=True)
            raise
    
    def get_bbox(self) -> Optional[Tuple[float, float, float, float]]:
        """Retourne le bounding box de la ville"""
        if not self.bbox:
            self.bbox = self.geocode_city()
        return self.bbox

