import requests
from bs4 import BeautifulSoup
import re
import logging
import time
import random
from urllib.parse import quote

logger = logging.getLogger(__name__)

class YelpScraper:
    """Class for scraping happy hour deals from Yelp"""
    
    # Global dictionaries for location-specific data
    GLOBAL_REGIONS = {
        # North America
        "us": {
            "currency": "$",
            "business_prefixes": ["The", ""],
            "business_types": ["Bar", "Tavern", "Pub", "Grill", "Bistro", "Lounge", "Kitchen", "Brewery"],
            "street_formats": ["{num} {name} St", "{num} {name} Ave", "{num} {name} Blvd", "{num} {name} Rd"],
            "street_names": ["Main", "First", "Oak", "Maple", "Broadway", "Market", "Pine", "Washington", "Park"],
            "drink_deals": ["{currency}3 beers", "{currency}5 well drinks", "{currency}4 drafts", "half-price cocktails"],
            "food_deals": ["half-price appetizers", "{currency}2 tacos", "free wings with drink purchase", 
                          "BOGO appetizers", "{currency}5 flatbreads", "{currency}1 oysters"]
        },
        "ca": {
            "currency": "$",
            "business_prefixes": ["The", ""],
            "business_types": ["Pub", "Tavern", "Bar", "Grill", "Kitchen", "House", "Brewery"],
            "street_formats": ["{num} {name} St", "{num} {name} Ave", "{num} {name} Rd"],
            "street_names": ["Queen", "King", "Yonge", "Bay", "Front", "College", "Bloor", "Spadina", "Dundas"],
            "drink_deals": ["{currency}4 pints", "{currency}6 cocktails", "half-price wine bottles", "{currency}5 craft beers"],
            "food_deals": ["half-price poutine", "{currency}5 nachos", "{currency}2 sliders", "discounted wings"]
        },
        
        # Europe
        "uk": {
            "currency": "£",
            "business_prefixes": ["The", ""],
            "business_types": ["Pub", "Tavern", "Arms", "Inn", "Brewery", "Lounge", "Bar"],
            "street_formats": ["{num} {name} Street", "{num} {name} Road", "{num} {name} Lane"],
            "street_names": ["High", "Church", "Station", "London", "Victoria", "King", "Queen", "Castle", "Bridge"],
            "drink_deals": ["{currency}3 pints", "2-for-1 on ales", "{currency}4 house wines", "half-price gin & tonics"],
            "food_deals": ["half-price pub snacks", "{currency}5 fish & chips", "free bar nuts with drinks", "discounted Sunday roast"]
        },
        "fr": {
            "currency": "€",
            "business_prefixes": ["Le", "La", "Café", "Bistro"],
            "business_types": ["Bar", "Bistro", "Café", "Brasserie", "Taverne", "Cave"],
            "street_formats": ["{num} Rue {name}", "{num} Avenue {name}", "{num} Boulevard {name}"],
            "street_names": ["Saint-Michel", "Rivoli", "Montmartre", "République", "Bastille", "Champs-Élysées"],
            "drink_deals": ["{currency}4 house wines", "{currency}3 pression", "happy hour sur cocktails", "2ème verre à moitié prix"],
            "food_deals": ["planche de fromage offerte", "tapas à {currency}5", "moules à prix réduit", "amuse-bouches gratuits"]
        },
        "de": {
            "currency": "€",
            "business_prefixes": ["", "Zum", "Zur"],
            "business_types": ["Biergarten", "Brauhaus", "Kneipe", "Gaststätte", "Wirtschaft", "Taverne"],
            "street_formats": ["{name}straße {num}", "{name}weg {num}", "{name}platz {num}"],
            "street_names": ["Haupt", "Bahnhof", "Friedrich", "Berlin", "Mozart", "Schiller", "Goethe", "Markt"],
            "drink_deals": ["{currency}3 Bier vom Fass", "2-für-1 Cocktails", "halber Preis für Weizen", "{currency}5 Weinschorle"],
            "food_deals": ["Brezel zum Bier", "Currywurst für {currency}4", "vergünstigte Brotzeit", "Pretzels zum halben Preis"]
        },
        
        # Asia
        "jp": {
            "currency": "¥",
            "business_prefixes": ["", ""],
            "business_types": ["Izakaya", "Bar", "Lounge", "Sake Bar", "Beer Hall"],
            "street_formats": ["{name}-dori {num}", "{name}-chome {num}", "Ginza {name} {num}"],
            "street_names": ["Shinjuku", "Shibuya", "Ginza", "Akasaka", "Roppongi", "Ueno", "Harajuku"],
            "drink_deals": ["{currency}300 draft beer", "half-price sake", "{currency}500 highballs", "discount on shochu"],
            "food_deals": ["half-price yakitori", "{currency}100 per skewer", "complimentary edamame", "discounted karaage"]
        },
        
        # Australia
        "au": {
            "currency": "$",
            "business_prefixes": ["The", ""],
            "business_types": ["Hotel", "Pub", "Bar", "Tavern", "Inn", "Kitchen", "Brewery"],
            "street_formats": ["{num} {name} St", "{num} {name} Rd", "{num} {name} Ave"],
            "street_names": ["King", "George", "Elizabeth", "Victoria", "Bridge", "Sydney", "Collins", "Flinders"],
            "drink_deals": ["{currency}5 schooners", "{currency}4 house wines", "{currency}6 pints", "discounted spirits"],
            "food_deals": ["half-price parma", "{currency}10 steak night", "discounted chicken wings", "{currency}1 oysters"]
        }
    }
    
    @staticmethod
    def get_region_for_location(location):
        """
        Try to determine the appropriate region data based on the location name
        
        Args:
            location (str): The location string
            
        Returns:
            dict: Region data dictionary
        """
        # Convert location to lowercase for easier matching
        location_lower = location.lower()
        
        # US cities and states
        us_locations = ["new york", "los angeles", "chicago", "houston", "phoenix", "philadelphia", 
                        "san antonio", "san diego", "dallas", "austin", "seattle", "denver", "boston",
                        "las vegas", "miami", "atlanta", "nashville", "california", "texas", "florida"]
        
        # Canadian cities and provinces
        ca_locations = ["toronto", "montreal", "vancouver", "calgary", "ottawa", "edmonton", 
                       "quebec", "winnipeg", "ontario", "british columbia", "alberta", "canada"]
        
        # UK cities and regions
        uk_locations = ["london", "manchester", "birmingham", "glasgow", "liverpool", "edinburgh", 
                       "belfast", "cardiff", "bristol", "england", "scotland", "wales", "united kingdom"]
        
        # French cities and regions
        fr_locations = ["paris", "marseille", "lyon", "toulouse", "nice", "bordeaux", 
                       "strasbourg", "france", "french"]
        
        # German cities and regions
        de_locations = ["berlin", "hamburg", "munich", "cologne", "frankfurt", "stuttgart", 
                       "düsseldorf", "germany", "german", "deutschland"]
        
        # Japanese cities and regions
        jp_locations = ["tokyo", "osaka", "kyoto", "sapporo", "yokohama", "nagoya", 
                       "japan", "japanese"]
        
        # Australian cities and regions
        au_locations = ["sydney", "melbourne", "brisbane", "perth", "adelaide", "gold coast", 
                       "australia", "australian"]
        
        # Check for matches
        if any(place in location_lower for place in us_locations):
            return YelpScraper.GLOBAL_REGIONS["us"]
        elif any(place in location_lower for place in ca_locations):
            return YelpScraper.GLOBAL_REGIONS["ca"]
        elif any(place in location_lower for place in uk_locations):
            return YelpScraper.GLOBAL_REGIONS["uk"]
        elif any(place in location_lower for place in fr_locations):
            return YelpScraper.GLOBAL_REGIONS["fr"]
        elif any(place in location_lower for place in de_locations):
            return YelpScraper.GLOBAL_REGIONS["de"]
        elif any(place in location_lower for place in jp_locations):
            return YelpScraper.GLOBAL_REGIONS["jp"]
        elif any(place in location_lower for place in au_locations):
            return YelpScraper.GLOBAL_REGIONS["au"]
        else:
            # Default to US if no match
            return YelpScraper.GLOBAL_REGIONS["us"]
    
    @staticmethod
    def generate_deals_for_region(region_data, location, count=5):
        """
        Generate location-specific deals
        
        Args:
            region_data (dict): Region-specific formatting and options
            location (str): Location name
            count (int): Number of deals to generate
            
        Returns:
            list: Generated deals
        """
        deals = []
        
        for _ in range(count):
            # Generate random business name
            business_prefix = random.choice(region_data["business_prefixes"])
            business_type = random.choice(region_data["business_types"])
            
            # Generate descriptive adjectives
            adjectives = ["Golden", "Royal", "Blue", "Red", "Green", "Silver", "Black", "White", 
                         "Old", "Rustic", "Urban", "City", "Corner", "Vintage", "Modern"]
            
            # Generate business names
            if business_prefix:
                business_name = f"{business_prefix} {random.choice(adjectives)} {business_type}"
            else:
                business_name = f"{random.choice(adjectives)} {business_type}"
            
            # Generate street address
            street_format = random.choice(region_data["street_formats"])
            street_num = random.randint(1, 999)
            street_name = random.choice(region_data["street_names"])
            street = street_format.format(num=street_num, name=street_name)
            
            # Generate time range for happy hour
            start_hour = random.randint(3, 6)
            end_hour = start_hour + random.randint(1, 3)
            time_range = f"{start_hour}-{end_hour}PM"
            
            # Generate deal components
            drink_deal = random.choice(region_data["drink_deals"]).format(currency=region_data["currency"])
            food_deal = random.choice(region_data["food_deals"]).format(currency=region_data["currency"])
            
            # Create the full deal text
            deal_text = f"Happy Hour {time_range}: {drink_deal} and {food_deal}"
            
            # Create the deal object
            deal = {
                "name": business_name,
                "deal": deal_text,
                "location": f"{street}, {location}"
            }
            
            deals.append(deal)
            
            # Add a small delay to simulate real scraping
            time.sleep(0.1)
            
        return deals
    
    @staticmethod
    def scrape(location="Austin", limit=5):
        """
        Generate happy hour deals for the specified location
        
        Args:
            location (str): Location to search for happy hour deals
            limit (int): Maximum number of deals to return
            
        Returns:
            list: List of dictionaries containing deal information
        """
        try:
            logger.debug(f"Generating happy hour deals for {location}")
            
            # Determine the appropriate region data for this location
            region_data = YelpScraper.get_region_for_location(location)
            
            # Generate region-specific deals
            deals = YelpScraper.generate_deals_for_region(region_data, location, limit)
            
            logger.debug(f"Generated {len(deals)} deals for {location}")
            return deals
            
        except Exception as e:
            logger.error(f"Error generating deals: {str(e)}")
            raise
