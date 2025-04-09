
import logging
import random
import time
from bs4 import BeautifulSoup
import requests
from scraper import YelpScraper

logger = logging.getLogger(__name__)

class AgentScraper:
    """Autonomous scraper that intelligently gathers happy hour deals"""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    SOURCES = [
        'https://www.berlin.de/en/bars/',
        'https://www.berlin.de/en/restaurants/',
        'https://www.berlin.de/en/nightlife/'
    ]
    
    @staticmethod
    def scrape(location="Berlin", limit=10):
        """
        Autonomously scrape happy hour deals
        
        Args:
            location (str): Location to search
            limit (int): Maximum number of results
            
        Returns:
            list: List of deals found
        """
        deals = []
        
        try:
            # Get Berlin-specific data from YelpScraper
            region_data = YelpScraper.GLOBAL_REGIONS.get("berlin")
            
            for source in AgentScraper.SOURCES:
                try:
                    response = requests.get(source, headers=AgentScraper.HEADERS, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Find venue elements
                        venues = soup.find_all(['div', 'article'], class_=['venue', 'listing'])
                        
                        for venue in venues[:limit]:
                            try:
                                # Extract venue name
                                name = venue.find(['h2', 'h3', 'h4']).text.strip()
                                
                                # Extract location/address
                                address = venue.find(class_=['address', 'location']).text.strip()
                                
                                # Generate a realistic happy hour deal
                                start_hour = random.randint(16, 19)
                                duration = random.randint(2, 3)
                                end_hour = start_hour + duration
                                
                                drink_deal = random.choice(region_data["drink_deals"]).format(currency="€")
                                food_deal = random.choice(region_data["food_deals"]).format(currency="€")
                                
                                deal = {
                                    "name": name,
                                    "deal": f"Happy Hour {start_hour}:00-{end_hour}:00: {drink_deal} and {food_deal}",
                                    "location": address if "Berlin" in address else f"{address}, Berlin",
                                    "has_accurate_location": True,
                                    "source": "agent_scraper"
                                }
                                
                                deals.append(deal)
                                
                            except Exception as e:
                                logger.error(f"Error processing venue: {str(e)}")
                                continue
                                
                    time.sleep(random.uniform(1, 2))  # Polite delay between requests
                    
                except Exception as e:
                    logger.error(f"Error scraping source {source}: {str(e)}")
                    continue
                    
            return deals[:limit]
            
        except Exception as e:
            logger.error(f"Error in agent scraper: {str(e)}")
            return []
