"""
Google Maps data scraper for happy hour deals
"""
import os
import logging
import time
import random
import requests
from bs4 import BeautifulSoup
import trafilatura
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class GoogleMapsScraper:
    """Class for retrieving location data from Google Maps"""
    
    # Base headers for requests to simulate a real browser
    BASE_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.51 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }
    
    # Maximum number of attempts to retrieve data
    MAX_ATTEMPTS = 3
    
    # Delay between requests (in seconds) to avoid rate limiting
    MIN_DELAY = 2
    MAX_DELAY = 5
    
    @staticmethod
    def get_random_delay():
        """Get a random delay between requests"""
        return random.uniform(GoogleMapsScraper.MIN_DELAY, GoogleMapsScraper.MAX_DELAY)
    
    @staticmethod
    def get_place_data(business_name, location, district=None):
        """
        Retrieve data for a place from Google Maps
        
        Args:
            business_name (str): Name of the business
            location (str): Address or location
            district (str, optional): District/neighborhood to improve search
            
        Returns:
            dict: Place data including rating, formatted address, etc.
        """
        # Build a more specific search query using all available information
        search_query = f"{business_name}"
        if location and "Berlin" in location:
            search_query += f" {location}"
        elif district:
            search_query += f" {district} Berlin"
        else:
            search_query += " Berlin"  # Add Berlin as default location context
            
        # URL encode the search query
        encoded_query = quote_plus(search_query)
        
        # Google Maps search URL
        search_url = f"https://www.google.com/maps/search/{encoded_query}"
        
        logger.debug(f"Searching Google Maps for: {search_query}")
        
        place_data = {
            "business_name": business_name,
            "original_location": location,
            "district": district,
            "found": False,
            "google_maps_url": search_url,
            "formatted_address": None,
            "rating": None,
            "reviews_count": None,
            "place_type": None,
            "price_level": None,
            "has_website": False
        }
        
        for attempt in range(GoogleMapsScraper.MAX_ATTEMPTS):
            try:
                response = requests.get(search_url, headers=GoogleMapsScraper.BASE_HEADERS, timeout=15)
                
                if response.status_code == 200:
                    # We've got a response, but Google Maps loads data dynamically with JavaScript
                    # We'll extract what we can from the initial HTML
                    # For a production app, you'd likely use a headless browser like Selenium
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to extract data from the page
                    # This is simplified and might need adjustments based on current Google Maps structure
                    place_data["found"] = True
                    
                    # Use trafilatura to extract main content text
                    extracted_text = trafilatura.extract(response.text)
                    
                    if extracted_text:
                        # Look for address patterns in the extracted text
                        lines = extracted_text.split('\n')
                        for line in lines:
                            # Try to identify address lines
                            if ',' in line and any(char.isdigit() for char in line) and len(line) > 10 and len(line) < 100:
                                if not place_data["formatted_address"]:
                                    place_data["formatted_address"] = line.strip()
                                    
                            # Look for rating information
                            if "★" in line or "stars" in line.lower() or "rating" in line.lower():
                                rating_text = line.strip()
                                # Extract numeric rating (assuming format like "4.5 stars" or "Rating: 4.5")
                                import re
                                rating_match = re.search(r'(\d+\.\d+)', rating_text)
                                if rating_match:
                                    place_data["rating"] = float(rating_match.group(1))
                                
                                # Extract reviews count if available
                                reviews_match = re.search(r'(\d+)\s+reviews', rating_text, re.IGNORECASE)
                                if reviews_match:
                                    place_data["reviews_count"] = int(reviews_match.group(1))
                            
                            # Look for place type information
                            if "restaurant" in line.lower() or "bar" in line.lower() or "café" in line.lower() or "pub" in line.lower():
                                for place_type in ["restaurant", "bar", "café", "pub", "bistro", "tavern"]:
                                    if place_type in line.lower():
                                        place_data["place_type"] = place_type.capitalize()
                                        break
                            
                            # Look for price level
                            if "€€€" in line:
                                place_data["price_level"] = 3
                            elif "€€" in line:
                                place_data["price_level"] = 2
                            elif "€" in line:
                                place_data["price_level"] = 1
                            
                            # Check for website mention
                            if "website" in line.lower():
                                place_data["has_website"] = True
                    
                    break  # Successfully retrieved and processed data
                    
                elif response.status_code == 429:
                    # Too many requests, wait longer before retrying
                    logger.warning(f"Rate limited by Google Maps (attempt {attempt+1}/{GoogleMapsScraper.MAX_ATTEMPTS})")
                    time.sleep(GoogleMapsScraper.get_random_delay() * 2)
                    
                else:
                    logger.warning(f"Failed to retrieve data with status code {response.status_code} (attempt {attempt+1}/{GoogleMapsScraper.MAX_ATTEMPTS})")
                    time.sleep(GoogleMapsScraper.get_random_delay())
                    
            except Exception as e:
                logger.error(f"Error retrieving Google Maps data: {str(e)} (attempt {attempt+1}/{GoogleMapsScraper.MAX_ATTEMPTS})")
                time.sleep(GoogleMapsScraper.get_random_delay())
        
        return place_data
    
    @staticmethod
    def enrich_deal_data(deal):
        """
        Enrich a deal with Google Maps data
        
        Args:
            deal (dict): Deal data to enrich
            
        Returns:
            dict: Deal with enriched data
        """
        if 'business_name' not in deal or 'location' not in deal:
            logger.warning("Cannot enrich deal without business name and location")
            return deal
        
        try:
            # Add a random delay to avoid rate limiting
            time.sleep(GoogleMapsScraper.get_random_delay())
            
            # Get place data from Google Maps
            business_name = deal['business_name']
            location = deal['location']
            district = deal.get('district')
            
            place_data = GoogleMapsScraper.get_place_data(business_name, location, district)
            
            # Enrich the deal with Google Maps data
            if place_data["found"]:
                # Update location if we found a better formatted address
                if place_data["formatted_address"]:
                    deal["google_maps_address"] = place_data["formatted_address"]
                
                # Add other useful data
                deal["google_maps_url"] = place_data["google_maps_url"]
                deal["rating"] = place_data["rating"]
                deal["reviews_count"] = place_data["reviews_count"]
                deal["place_type"] = place_data["place_type"]
                deal["price_level"] = place_data["price_level"]
                deal["has_website"] = place_data["has_website"]
                
                # If this has an accurate Google Maps address, mark it as mappable
                if place_data["formatted_address"]:
                    deal["has_accurate_location"] = True
                
                # If the district wasn't present but we got it from Google, add it
                if not district and "Berlin" in (place_data["formatted_address"] or ""):
                    # Try to extract district from the address
                    berlin_districts = [
                        "Mitte", "Prenzlauer Berg", "Neukölln", "Wedding", "Kreuzberg", 
                        "Charlottenburg", "Schöneberg", "Friedrichshain", "Moabit", "Tiergarten",
                        "Lichtenberg", "Köpenick", "Spandau", "Steglitz", "Marzahn", "Wilmersdorf",
                        "Tempelhof", "Treptow", "Pankow", "Reinickendorf", "Zehlendorf"
                    ]
                    
                    for d in berlin_districts:
                        if d in (place_data["formatted_address"] or ""):
                            deal["district"] = d
                            break
            
            return deal
            
        except Exception as e:
            logger.error(f"Error enriching deal data: {str(e)}")
            return deal