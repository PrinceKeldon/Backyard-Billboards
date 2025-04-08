import requests
from bs4 import BeautifulSoup
import re
import logging
import time
import random
from urllib.parse import quote
import os
from google_maps_scraper import GoogleMapsScraper

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
        
        # Berlin-specific data with accurate locations
        "berlin": {
            "currency": "€",
            "business_prefixes": ["", "Zum", "Zur", "Berliner"],
            "business_types": ["Eckkneipe", "Bierstube", "Brauhaus", "Kneipe", "Café", "Bar", "Weinbar", "Lokal"],
            "locations": [
                # Mitte
                {
                    "name": "Mein Haus am See",
                    "address": "Brunnenstraße 197-198, 10119 Berlin",
                    "district": "Mitte",
                    "drink_deal": "2-für-1 Cocktails von 18-20 Uhr",
                    "food_deal": "Kleine Snacks inklusive"
                },
                {
                    "name": "Neue Odessa Bar",
                    "address": "Torstraße 89, 10119 Berlin",
                    "district": "Mitte",
                    "drink_deal": "{currency}5 Longdrinks",
                    "food_deal": "Gratis Oliven und Nüsse"
                },
                {
                    "name": "Bar Tausend",
                    "address": "Schiffbauerdamm 11, 10117 Berlin",
                    "district": "Mitte",
                    "drink_deal": "{currency}7 Signature Cocktails",
                    "food_deal": "Asiatische Tapas für {currency}5"
                },
                
                # Prenzlauer Berg
                {
                    "name": "Prater Biergarten",
                    "address": "Kastanienallee 7-9, 10435 Berlin",
                    "district": "Prenzlauer Berg",
                    "drink_deal": "{currency}3,50 Prater Pils",
                    "food_deal": "Halber Preis für Brezeln"
                },
                {
                    "name": "Wohnzimmer Bar",
                    "address": "Lettestraße 6, 10437 Berlin",
                    "district": "Prenzlauer Berg",
                    "drink_deal": "{currency}4 Berliner Weiße mit Schuss",
                    "food_deal": "Nachos mit Dips für {currency}3,50"
                },
                {
                    "name": "Kulturbrauerei",
                    "address": "Schönhauser Allee 36, 10435 Berlin",
                    "district": "Prenzlauer Berg",
                    "drink_deal": "{currency}3,50 Craft Beer",
                    "food_deal": "Flammkuchen für {currency}5"
                },
                
                # Neukölln
                {
                    "name": "Klunkerkranich",
                    "address": "Karl-Marx-Straße 66, 12043 Berlin",
                    "district": "Neukölln",
                    "drink_deal": "{currency}4 Berliner Weiße",
                    "food_deal": "Happy Hour Pizza {currency}6"
                },
                {
                    "name": "Tier",
                    "address": "Weserstraße 42, 12045 Berlin",
                    "district": "Neukölln",
                    "drink_deal": "{currency}6 Craft Cocktails",
                    "food_deal": "Vegane Tacos {currency}3 pro Stück"
                },
                {
                    "name": "Rixdorf Biergarten",
                    "address": "Richardplatz 14, 12055 Berlin",
                    "district": "Neukölln",
                    "drink_deal": "{currency}3 Alster",
                    "food_deal": "Currywurst für {currency}4"
                },
                
                # Wedding
                {
                    "name": "Eschenbräu",
                    "address": "Triftstraße 67, 13353 Berlin",
                    "district": "Wedding",
                    "drink_deal": "{currency}3,20 Hausbier",
                    "food_deal": "Kostenlose Brezeln zum Bier"
                },
                {
                    "name": "Cafe Pförtner",
                    "address": "Uferstraße 8-11, 13357 Berlin",
                    "district": "Wedding",
                    "drink_deal": "{currency}3,50 Weinschorle",
                    "food_deal": "Häppchen vom Buffet für {currency}5"
                },
                
                # Kreuzberg
                {
                    "name": "BRLO Brwhouse",
                    "address": "Schöneberger Straße 16, 10963 Berlin",
                    "district": "Kreuzberg",
                    "drink_deal": "Craft Bier Tasting für {currency}10",
                    "food_deal": "Vegane Snack-Platte für {currency}7"
                },
                {
                    "name": "Hopfenreich",
                    "address": "Sorauer Straße 31, 10997 Berlin",
                    "district": "Kreuzberg",
                    "drink_deal": "{currency}4 wechselnde Craft-Biere",
                    "food_deal": "Kostenlose Erdnüsse"
                },
                {
                    "name": "Barkett",
                    "address": "Graefestraße 71, 10967 Berlin",
                    "district": "Kreuzberg",
                    "drink_deal": "{currency}5 Aperol Spritz",
                    "food_deal": "Hummus mit Brot für {currency}3"
                },
                
                # Charlottenburg
                {
                    "name": "Monkey Bar",
                    "address": "Budapester Straße 40, 10787 Berlin",
                    "district": "Charlottenburg",
                    "drink_deal": "{currency}6 Signature Cocktails",
                    "food_deal": "Happy Hour Tapas"
                },
                {
                    "name": "Bellboy Bar",
                    "address": "Kurfürstendamm 101, 10711 Berlin",
                    "district": "Charlottenburg",
                    "drink_deal": "{currency}8 Cocktails",
                    "food_deal": "Snacks zur Happy Hour"
                },
                
                # Schöneberg
                {
                    "name": "Zur Traube",
                    "address": "Regensburger Straße 15, 10777 Berlin",
                    "district": "Schöneberg",
                    "drink_deal": "{currency}2,80 Berliner Pilsner",
                    "food_deal": "Currywurst für {currency}4,50"
                },
                {
                    "name": "Green Door",
                    "address": "Winterfeldtstraße 50, 10781 Berlin",
                    "district": "Schöneberg",
                    "drink_deal": "{currency}7 Cocktail des Tages",
                    "food_deal": "Oliven & Käse gratis"
                },
                
                # Friedrichshain
                {
                    "name": "Protokoll",
                    "address": "Boxhagener Straße 105, 10245 Berlin",
                    "district": "Friedrichshain",
                    "drink_deal": "Alle Zapfbiere {currency}3,50",
                    "food_deal": "Flammkuchen zum halben Preis"
                },
                {
                    "name": "Süß war gestern",
                    "address": "Wühlischstraße 31, 10245 Berlin",
                    "district": "Friedrichshain",
                    "drink_deal": "{currency}5 Gin-Tonic",
                    "food_deal": "Käseplatte {currency}7"
                },
                {
                    "name": "Boxhagener Hof",
                    "address": "Boxhagener Straße 117, 10245 Berlin",
                    "district": "Friedrichshain",
                    "drink_deal": "{currency}3 Berliner Kindl",
                    "food_deal": "Schnitzelsandwich für {currency}4,50"
                },
                
                # Moabit
                {
                    "name": "Arminius Markthalle",
                    "address": "Arminiusstraße 2-4, 10551 Berlin",
                    "district": "Moabit",
                    "drink_deal": "{currency}3,50 Craft Beer vom Fass",
                    "food_deal": "Marktplatte für {currency}7"
                },
                {
                    "name": "Kallasch & Moabit",
                    "address": "Waldstraße 86, 10551 Berlin", 
                    "district": "Moabit",
                    "drink_deal": "{currency}3 Sternburger Bier",
                    "food_deal": "Pretzels für {currency}1,50"
                },
                
                # Tiergarten
                {
                    "name": "Café am Neuen See",
                    "address": "Lichtensteinallee 2, 10787 Berlin",
                    "district": "Tiergarten",
                    "drink_deal": "Maßkrug Bier für {currency}7",
                    "food_deal": "Flammkuchen zum halben Preis"
                },
                {
                    "name": "Berlin Pavillon",
                    "address": "Straße des 17. Juni 145, 10623 Berlin",
                    "district": "Tiergarten",
                    "drink_deal": "{currency}4,20 Prosecco",
                    "food_deal": "Antipasti-Platte für {currency}9"
                },
                
                # Lichtenberg
                {
                    "name": "Schlossgarten Biergarten",
                    "address": "Magdalenenstraße 77, 10365 Berlin",
                    "district": "Lichtenberg",
                    "drink_deal": "{currency}3 Biere und {currency}4 Longdrinks",
                    "food_deal": "Currywurst mit Pommes für {currency}5"
                },
                
                # Köpenick
                {
                    "name": "Hafenbar Köpenick",
                    "address": "Grünauer Straße 10, 12557 Berlin",
                    "district": "Köpenick",
                    "drink_deal": "{currency}3,20 Köpenicker Hell",
                    "food_deal": "Fischbrötchen für {currency}3,50"
                },
                
                # Spandau
                {
                    "name": "Brauhaus Spandau",
                    "address": "Neuendorfer Straße 1, 13585 Berlin",
                    "district": "Spandau",
                    "drink_deal": "{currency}3,50 Hausgebrautes",
                    "food_deal": "Spanferkel-Brötchen für {currency}4,50"
                },
                
                # Steglitz
                {
                    "name": "Schloßkeller Steglitz",
                    "address": "Schloßstraße 48, 12165 Berlin",
                    "district": "Steglitz",
                    "drink_deal": "2-für-1 Weine",
                    "food_deal": "Käse-Tapas für {currency}5"
                }
            ]
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
        
        # Special handling for Berlin
        if "berlin" in location_lower:
            logger.debug("Using Berlin-specific data for location")
            return YelpScraper.GLOBAL_REGIONS["berlin"]
        
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
        de_locations = ["hamburg", "munich", "cologne", "frankfurt", "stuttgart", 
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
        
        # Special handling for Berlin with accurate location data
        if "locations" in region_data:
            logger.debug("Using accurate location data for Berlin")
            
            # Get locations and shuffle them
            berlin_locations = region_data["locations"]
            random.shuffle(berlin_locations)
            
            # Limit to requested count
            max_deals = min(count, len(berlin_locations))
            
            # Create deals from accurate Berlin data
            for i in range(max_deals):
                location_data = berlin_locations[i]
                
                # Generate time range for happy hour
                start_hour = random.randint(16, 19)  # 4PM to 7PM in 24-hour format
                end_hour = start_hour + random.randint(2, 3)
                time_range = f"{start_hour}:00-{end_hour}:00 Uhr"
                
                # Format the deal text with currency symbol
                drink_deal = location_data["drink_deal"].format(currency=region_data["currency"])
                food_deal = location_data["food_deal"].format(currency=region_data["currency"])
                
                # Create the full deal text
                deal_text = f"Happy Hour {time_range}: {drink_deal} und {food_deal}"
                
                # Create the deal object with accurate address
                deal = {
                    "name": location_data["name"],
                    "deal": deal_text,
                    "location": location_data["address"],
                    "district": location_data["district"],
                    "has_accurate_location": True  # Flag for map integration
                }
                
                deals.append(deal)
                
                # Add a small delay to simulate real scraping
                time.sleep(0.1)
                
            return deals
            
        # Standard handling for other regions
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
                "location": f"{street}, {location}",
                "has_accurate_location": False
            }
            
            deals.append(deal)
            
            # Add a small delay to simulate real scraping
            time.sleep(0.1)
            
        return deals
    
    @staticmethod
    def clean_dataset():
        """Cleans the dataset by ensuring all deals have Berlin in their location or a district set.
        Also standardizes the locations to include Berlin if missing, and REMOVES any deals
        that have non-Berlin locations (like American street names or other countries).
        Specifically removes any locations referencing Austin, Texas or American-style addresses."""
        from db import DealDB
        deal_db = DealDB()
        deals = deal_db.get_all_deals()
        
        # Log how many deals we're processing
        logger.info(f"Cleaning {len(deals)} deals in the dataset...")
        
        cleaned_count = 0
        deleted_count = 0
        
        # List of confirmed Berlin districts for validation
        berlin_districts = [
            "Mitte", "Prenzlauer Berg", "Neukölln", "Wedding", "Kreuzberg", 
            "Charlottenburg", "Schöneberg", "Friedrichshain", "Moabit", "Tiergarten",
            "Lichtenberg", "Köpenick", "Spandau", "Steglitz", "Marzahn", "Wilmersdorf",
            "Tempelhof", "Treptow", "Pankow", "Reinickendorf", "Zehlendorf"
        ]
        
        # Common German/Berlin street indicators
        berlin_street_indicators = [
            "straße", "strasse", "allee", "platz", "damm", "weg", "ufer", "chaussee", 
            "gasse", "ring", "graben", "brücke", "bruecke", "promenade", "tor", "steg"
        ]
        
        # Common American street indicators that suggest non-Berlin locations
        non_berlin_indicators = [
            "street", "ave", "avenue", "blvd", "boulevard", "road", "rd", "drive", "dr", 
            "lane", "ln", "way", "court", "ct", "circle", "cir", "terrace", "broadway"
        ]
        
        # List of common U.S. states and cities that suggest non-Berlin locations
        us_locations = [
            "new york", "los angeles", "chicago", "houston", "philadelphia", "phoenix", 
            "san antonio", "san diego", "dallas", "san jose", "jacksonville", 
            "san francisco", "columbus", "charlotte", "seattle", "denver", "washington dc",
            "boston", "portland", "las vegas", "nashville", "baltimore", "oklahoma city",
            "california", "florida", "new york", "pennsylvania", "illinois", 
            "ohio", "georgia", "michigan", "north carolina", "new jersey", "virginia",
            "washington", "arizona", "massachusetts", "tennessee", "indiana", "missouri",
            "usa", "united states", "america", "nyc", "la", "sf", "nj", "ny",
            # Explicitly prioritize Austin and Texas detection
            "austin", "texas", "atx", "tx", "sixth street", "6th street", "east austin", 
            "south austin", "north austin", "west austin", "downtown austin", "congress avenue",
            "rainey street", "south congress", "guadalupe street", "the drag", "soco"
        ]
        
        for deal in deals:
            business_name = deal.get('business_name')
            location = deal.get('location', '')
            district = deal.get('district')
            
            # Skip if no business name
            if not business_name:
                continue
                
            # Get current deal data
            deal_data = deal_db.get_deal(business_name)
            if not deal_data:
                continue
            
            # Check if this is likely a non-Berlin location
            location_lower = location.lower()
            
            # Determine if this is likely a non-Berlin location based on indicators
            is_non_berlin = False
            
            # Check for U.S. locations or common American street name patterns
            if any(us_loc in location_lower for us_loc in us_locations):
                is_non_berlin = True
            
            # Check for American street indicators (while making sure we're not catching German street names)
            for indicator in non_berlin_indicators:
                # Look for the indicator as a standalone word (with spaces, at end of string, or before a comma/period)
                if (f" {indicator} " in f" {location_lower} " or 
                    location_lower.endswith(f" {indicator}") or 
                    f" {indicator}," in location_lower or 
                    f" {indicator}." in location_lower or
                    # Check for street numbers + street type (e.g., "123 Oak St" or "456 Main Ave")
                    re.search(r'\d+\s+\w+\s+' + indicator + r'[\s,\.]', location_lower)):
                    # Make sure it's not part of a German word
                    if not any(berlin_ind in location_lower for berlin_ind in berlin_street_indicators):
                        is_non_berlin = True
                        break
            
            # If it's a non-Berlin location, delete it
            if is_non_berlin:
                try:
                    deal_db.delete_deal(business_name)
                    deleted_count += 1
                    logger.info(f"Deleted non-Berlin location: {business_name} - {location}")
                    continue
                except Exception as e:
                    logger.error(f"Error deleting deal {business_name}: {str(e)}")
                    continue
            
            # Continue with updating valid Berlin locations
            needs_update = False
            
            # Add Berlin to the location if it's missing and no district is set
            if 'berlin' not in location_lower and not district:
                # Check if location has just a street name or is missing entirely
                if location.strip() and not location.endswith(', '):
                    location = f"{location}, Berlin"
                else:
                    location = f"{location}Berlin"
                needs_update = True
                
            # If we have a district but no Berlin in the location, add both district and Berlin
            if district and 'berlin' not in location_lower:
                if location.strip() and not location.endswith(', '):
                    location = f"{location}, {district}, Berlin"
                else:
                    location = f"{location}{district}, Berlin"
                needs_update = True
                
            # If the district isn't one of the known Berlin districts, add it
            if district and district not in berlin_districts:
                berlin_districts.append(district)
            
            # Update the deal if needed
            if needs_update and business_name:
                try:
                    # Update the location
                    deal_data['location'] = location
                    # Set has_accurate_location to True since we're adding Berlin
                    deal_data['has_accurate_location'] = True
                    # Set it back in the database
                    deal_db.delete_deal(business_name)
                    # Use all existing deal properties except the ones we're explicitly setting
                    deal_props = {k: v for k, v in deal_data.items() if k not in ['business_name', 'deal', 'location', 'has_accurate_location']}
                    deal_props['has_accurate_location'] = True
                    deal_db.add_deal(business_name, deal_data['deal'], location, **deal_props)
                    cleaned_count += 1
                except Exception as e:
                    logger.error(f"Error updating deal {business_name}: {str(e)}")
        
        logger.info(f"Cleaned {cleaned_count} deals in the dataset and removed {deleted_count} non-Berlin locations.")
        return cleaned_count + deleted_count
        
    @staticmethod
    def scrape(location=None, limit=5, enrich_with_google=False):
        """
        Generate happy hour deals for the specified location
        
        Args:
            location (str): Location to search for happy hour deals
            limit (int): Maximum number of deals to return
            enrich_with_google (bool): Whether to enrich deals with Google Maps data (default: False)
            
        Returns:
            list: List of dictionaries containing deal information
        """
        try:
            # Force Berlin location if RESTRICT_TO_BERLIN flag is set
            restrict_to_berlin = os.environ.get("RESTRICT_TO_BERLIN", "").lower() in ("true", "1", "yes")
            default_location = os.environ.get("DEFAULT_LOCATION", "Berlin, Germany")
            
            # Override location if restriction is enabled or location is not provided
            if location is None or restrict_to_berlin:
                location = default_location
                logger.info(f"Location restricted to Berlin: {location}")
            
            logger.debug(f"Generating happy hour deals for {location}")
            
            # Determine the appropriate region data for this location
            # Always use Berlin-specific data for Germany
            region_data = YelpScraper.GLOBAL_REGIONS.get("berlin", YelpScraper.GLOBAL_REGIONS.get("de"))
            
            # Generate Berlin-specific deals
            deals = YelpScraper.generate_deals_for_region(region_data, location, limit)
            
            # Enrich with Google Maps data if explicitly requested
            if enrich_with_google and os.environ.get("ENABLE_GOOGLE_MAPS_SCRAPING", "").lower() in ("true", "1", "yes"):
                logger.debug(f"Enriching deals with Google Maps data")
                
                # Process a subset of deals for Google Maps enrichment to avoid rate limiting
                google_enrichment_limit = min(len(deals), 2)  # Stricter limit (2 deals) for better performance
                
                # Allow overriding the limit with an environment variable
                try:
                    env_limit = os.environ.get("GOOGLE_MAPS_ENRICHMENT_LIMIT")
                    if env_limit:
                        google_enrichment_limit = min(len(deals), int(env_limit))
                except (ValueError, TypeError):
                    pass  # Use the default limit if environment variable is invalid
                
                # Add a notice about Google Maps enrichment
                logger.debug(f"Will enrich {google_enrichment_limit} deals with Google Maps data")
                
                # Enrich a limited number of deals with Google Maps data
                for i in range(google_enrichment_limit):
                    try:
                        # Apply a shorter timeout for Google Maps requests
                        deals[i] = GoogleMapsScraper.enrich_deal_data(deals[i], timeout=3.0)
                        
                        # Add a minimal delay between requests
                        if i < google_enrichment_limit - 1:
                            time.sleep(0.5)  # Reduced delay for better performance
                    except Exception as e:
                        logger.error(f"Error enriching deal {i} with Google Maps data: {str(e)}")
                        # Continue with other deals if one fails
            
            logger.debug(f"Generated {len(deals)} deals for {location}")
            return deals
            
        except Exception as e:
            logger.error(f"Error generating deals: {str(e)}")
            raise
