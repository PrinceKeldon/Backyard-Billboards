"""
Berlin Event Scraper for Backyard Billboards
Scrapes current club events in Berlin for the digital billboard feature
"""
import logging
import re
import datetime
import time
import random
import trafilatura
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EventScraper:
    """Scrapes current Berlin club events from various sources"""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/',
        'Connection': 'keep-alive',
    }
    
    BERLIN_DISTRICTS = [
        "Mitte", "Prenzlauer Berg", "Neukölln", "Wedding", "Kreuzberg", 
        "Charlottenburg", "Schöneberg", "Friedrichshain", "Moabit", "Tiergarten",
        "Lichtenberg", "Köpenick", "Spandau", "Steglitz", "Marzahn", "Wilmersdorf",
        "Tempelhof", "Treptow", "Pankow", "Reinickendorf", "Zehlendorf"
    ]
    
    SOURCES = [
        'https://www.berlin.de/en/events/today/',
        'https://www.visitberlin.de/en/events-berlin',
        'https://www.residentadvisor.net/events/de/berlin',
    ]
    
    def __init__(self):
        """Initialize the scraper"""
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)
    
    def get_random_delay(self, min_delay=1.0, max_delay=3.0):
        """Get a random delay between requests to avoid rate limiting"""
        return random.uniform(min_delay, max_delay)
    
    def extract_date(self, text):
        """Extract date from text in various formats"""
        # Try to extract YYYY-MM-DD
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', text)
        if date_match:
            return date_match.group(1)
        
        # Try to extract DD.MM.YYYY
        date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', text)
        if date_match:
            day, month, year = date_match.groups()
            return f"{year}-{month}-{day}"
        
        # Try to extract "X April 2025" format
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12',
            'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'jun': '06',
            'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
        }
        
        for month_name, month_num in months.items():
            pattern = rf'(\d{{1,2}})\s+{month_name}\s+(\d{{4}})'
            date_match = re.search(pattern, text.lower())
            if date_match:
                day, year = date_match.groups()
                day = day.zfill(2)  # Pad with leading zero if needed
                return f"{year}-{month_num}-{day}"
        
        # Could not extract date, default to today's date
        return datetime.datetime.now().strftime("%Y-%m-%d")
    
    def extract_time(self, text):
        """Extract time from text in various formats"""
        # Try to extract HH:MM format
        time_match = re.search(r'(\d{1,2}):(\d{2})', text)
        if time_match:
            hour, minute = time_match.groups()
            hour = hour.zfill(2)  # Pad with leading zero if needed
            return f"{hour}:{minute}"
        
        # Try to extract "X PM/AM" format
        time_match = re.search(r'(\d{1,2})\s*(am|pm)', text.lower())
        if time_match:
            hour, period = time_match.groups()
            hour = int(hour)
            if period == 'pm' and hour < 12:
                hour += 12
            elif period == 'am' and hour == 12:
                hour = 0
            return f"{hour:02d}:00"
        
        # Could not extract time, default to evening (20:00)
        return "20:00"
    
    def detect_district(self, text):
        """Detect Berlin district from text"""
        for district in self.BERLIN_DISTRICTS:
            if district.lower() in text.lower():
                return district
        
        # Some common district mapping for phrases
        district_mapping = {
            "mitte berlin": "Mitte",
            "alexanderplatz": "Mitte",
            "hackescher markt": "Mitte",
            "friedrichshain-kreuzberg": "Friedrichshain",
            "fhain": "Friedrichshain",
            "xberg": "Kreuzberg",
            "chamissoplatz": "Kreuzberg",
            "bergmannkiez": "Kreuzberg",
            "nk": "Neukölln",
            "rixdorf": "Neukölln",
            "p'berg": "Prenzlauer Berg",
            "kollwitzplatz": "Prenzlauer Berg",
            "scheunenviertel": "Mitte",
            "potsdamer platz": "Tiergarten",
            "city west": "Charlottenburg",
            "karl-marx-allee": "Friedrichshain",
            "wasserturm": "Prenzlauer Berg",
            "paul-lincke-ufer": "Kreuzberg",
            "maybachufer": "Neukölln",
            "treptower park": "Treptow",
            "weserstraße": "Neukölln",
            "schillerkiez": "Neukölln",
            "graefekiez": "Kreuzberg"
        }
        
        for phrase, district in district_mapping.items():
            if phrase.lower() in text.lower():
                return district
        
        # Default to Mitte if no district is found
        return "Mitte"
    
    def clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Strip whitespace
        text = text.strip()
        
        return text
    
    def scrape_berlin_events(self, limit=15):
        """
        Scrape current Berlin club events from multiple sources
        
        Args:
            limit (int): Maximum number of events to return
            
        Returns:
            list: List of event dictionaries
        """
        events = []
        scraped_count = 0
        
        try:
            # Scrape Berlin.de events
            berlin_de_events = self._scrape_berlin_de()
            events.extend(berlin_de_events)
            scraped_count += len(berlin_de_events)
            
            # Reasonable delay between requests
            time.sleep(self.get_random_delay())
            
            # Scrape VisitBerlin events
            visitberlin_events = self._scrape_visitberlin()
            events.extend(visitberlin_events)
            scraped_count += len(visitberlin_events)
            
            # Reasonable delay between requests
            time.sleep(self.get_random_delay())
            
            # Scrape Resident Advisor events
            ra_events = self._scrape_resident_advisor()
            events.extend(ra_events)
            scraped_count += len(ra_events)
            
            # Remove duplicates based on event name and venue
            unique_events = []
            seen_events = set()
            
            for event in events:
                event_key = f"{event['event_name']}_{event['venue']}"
                if event_key not in seen_events:
                    seen_events.add(event_key)
                    unique_events.append(event)
            
            # Limit the number of events if needed
            if limit and len(unique_events) > limit:
                unique_events = unique_events[:limit]
            
            logger.info(f"Scraped {scraped_count} events, {len(unique_events)} unique events")
            return unique_events
            
        except Exception as e:
            logger.error(f"Error scraping Berlin events: {str(e)}")
            return events
    
    def _scrape_berlin_de(self):
        """Scrape events from Berlin.de"""
        events = []
        try:
            url = 'https://www.berlin.de/en/events/today/'
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch Berlin.de events: {response.status_code}")
                return events
            
            soup = BeautifulSoup(response.text, 'html.parser')
            event_elements = soup.select('.teaser-item')
            
            for element in event_elements:
                try:
                    # Skip if not a club/party event
                    category_element = element.select_one('.category')
                    if not category_element:
                        continue
                    
                    category = category_element.get_text().strip().lower()
                    is_club_event = any(term in category for term in ['club', 'party', 'music', 'concert', 'dj'])
                    
                    if not is_club_event:
                        continue
                    
                    # Extract event details
                    title_element = element.select_one('.teaser-title')
                    if not title_element:
                        continue
                    
                    event_name = title_element.get_text().strip()
                    
                    # Extract link and image
                    link_element = title_element.find('a')
                    event_url = urljoin(url, link_element['href']) if link_element and 'href' in link_element.attrs else None
                    
                    image_element = element.select_one('.teaser-image img')
                    image_url = image_element['src'] if image_element and 'src' in image_element.attrs else None
                    if image_url and not image_url.startswith(('http:', 'https:')):
                        image_url = urljoin(url, image_url)
                    
                    # Extract date, time, and location
                    date_element = element.select_one('.teaser-date')
                    date_text = date_element.get_text().strip() if date_element else ""
                    event_date = self.extract_date(date_text)
                    event_time = self.extract_time(date_text)
                    
                    location_element = element.select_one('.teaser-location')
                    venue = location_element.get_text().strip() if location_element else "Unknown Venue"
                    
                    # Extract description
                    description_element = element.select_one('.teaser-text')
                    description = description_element.get_text().strip() if description_element else ""
                    
                    # Detect district
                    full_text = f"{event_name} {venue} {description} {date_text}"
                    district = self.detect_district(full_text)
                    
                    # Create event data
                    event_data = {
                        'event_name': event_name,
                        'venue': venue,
                        'district': district,
                        'event_date': event_date,
                        'event_time': event_time,
                        'description': description,
                        'image_url': image_url,
                        'event_url': event_url,
                        'source': 'berlin.de'
                    }
                    
                    events.append(event_data)
                except Exception as e:
                    logger.warning(f"Error processing Berlin.de event: {str(e)}")
            
            logger.info(f"Scraped {len(events)} events from Berlin.de")
            return events
            
        except Exception as e:
            logger.error(f"Error scraping Berlin.de: {str(e)}")
            return events
    
    def _scrape_visitberlin(self):
        """Scrape events from VisitBerlin"""
        events = []
        try:
            url = 'https://www.visitberlin.de/en/events-berlin'
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch VisitBerlin events: {response.status_code}")
                return events
            
            soup = BeautifulSoup(response.text, 'html.parser')
            event_elements = soup.select('.teaser-event')
            
            for element in event_elements:
                try:
                    # Skip if not a club/party event
                    tags_element = element.select('.teaser-event__tag-list')
                    if tags_element:
                        tags_text = ' '.join([tag.get_text().strip().lower() for tag in tags_element])
                        is_club_event = any(term in tags_text for term in ['club', 'party', 'music', 'concert', 'dj', 'nightlife'])
                        
                        if not is_club_event:
                            continue
                    
                    # Extract event details
                    title_element = element.select_one('h4')
                    if not title_element:
                        continue
                    
                    event_name = title_element.get_text().strip()
                    
                    # Extract link and image
                    link_element = element.select_one('a.teaser-event__link')
                    event_url = urljoin(url, link_element['href']) if link_element and 'href' in link_element.attrs else None
                    
                    image_element = element.select_one('.teaser-event__image img')
                    image_url = image_element['src'] if image_element and 'src' in image_element.attrs else None
                    if image_url and not image_url.startswith(('http:', 'https:')):
                        image_url = urljoin(url, image_url)
                    
                    # Extract date, time, and location
                    date_element = element.select_one('.teaser-event__date')
                    date_text = date_element.get_text().strip() if date_element else ""
                    event_date = self.extract_date(date_text)
                    event_time = self.extract_time(date_text)
                    
                    location_element = element.select_one('.teaser-event__location')
                    venue = location_element.get_text().strip() if location_element else "Unknown Venue"
                    
                    # Extract description
                    description_element = element.select_one('.teaser-event__text')
                    description = description_element.get_text().strip() if description_element else ""
                    
                    # Detect district
                    full_text = f"{event_name} {venue} {description} {date_text}"
                    district = self.detect_district(full_text)
                    
                    # Create event data
                    event_data = {
                        'event_name': event_name,
                        'venue': venue,
                        'district': district,
                        'event_date': event_date,
                        'event_time': event_time,
                        'description': description,
                        'image_url': image_url,
                        'event_url': event_url,
                        'source': 'visitberlin.de'
                    }
                    
                    events.append(event_data)
                except Exception as e:
                    logger.warning(f"Error processing VisitBerlin event: {str(e)}")
            
            logger.info(f"Scraped {len(events)} events from VisitBerlin")
            return events
            
        except Exception as e:
            logger.error(f"Error scraping VisitBerlin: {str(e)}")
            return events
    
    def _scrape_resident_advisor(self):
        """Scrape events from Resident Advisor"""
        events = []
        try:
            url = 'https://www.residentadvisor.net/events/de/berlin'
            response = self.session.get(url, timeout=10)
            
            if response.status_code != 200:
                logger.warning(f"Failed to fetch Resident Advisor events: {response.status_code}")
                return events
            
            soup = BeautifulSoup(response.text, 'html.parser')
            event_elements = soup.select('.Box-sc-1sw3m7q-0')
            
            for element in event_elements:
                try:
                    # Skip if not an event listing
                    title_element = element.select_one('h2')
                    if not title_element:
                        continue
                    
                    event_name = title_element.get_text().strip()
                    
                    # Extract link
                    link_element = element.select_one('a')
                    event_url = urljoin(url, link_element['href']) if link_element and 'href' in link_element.attrs else None
                    
                    # Extract image if available
                    image_element = element.select_one('img')
                    image_url = image_element['src'] if image_element and 'src' in image_element.attrs else None
                    if image_url and not image_url.startswith(('http:', 'https:')):
                        image_url = urljoin(url, image_url)
                    
                    # Extract date, time, and venue
                    date_element = element.select_one('time')
                    date_text = date_element.get_text().strip() if date_element else ""
                    event_date = self.extract_date(date_text) 
                    event_time = self.extract_time(date_text)
                    
                    venue_element = element.select_one('h3')
                    venue = venue_element.get_text().strip() if venue_element else "Unknown Venue"
                    
                    # Extract venue's district (sometimes listed next to venue name)
                    district_text = ''
                    location_element = element.select_one('.Text-sc-1t0gn2o-0')
                    if location_element:
                        location_text = location_element.get_text().strip()
                        district_text = location_text
                    
                    # Get a description from the event page if possible
                    description = f"Club event at {venue} in Berlin"
                    if event_url:
                        try:
                            # Use trafilatura for cleaner content extraction if we have a URL
                            event_page_html = trafilatura.fetch_url(event_url)
                            if event_page_html:
                                extracted_text = trafilatura.extract(event_page_html)
                                if extracted_text:
                                    # Use the first 250 characters as a description
                                    description = self.clean_text(extracted_text[:250])
                        except Exception as inner_e:
                            logger.warning(f"Error fetching event page: {str(inner_e)}")
                    
                    # Detect district
                    district = self.detect_district(f"{venue} {district_text} {description}")
                    
                    # Create event data
                    event_data = {
                        'event_name': event_name,
                        'venue': venue,
                        'district': district,
                        'event_date': event_date,
                        'event_time': event_time,
                        'description': description,
                        'image_url': image_url,
                        'event_url': event_url,
                        'source': 'residentadvisor.net'
                    }
                    
                    events.append(event_data)
                except Exception as e:
                    logger.warning(f"Error processing Resident Advisor event: {str(e)}")
            
            logger.info(f"Scraped {len(events)} events from Resident Advisor")
            return events
            
        except Exception as e:
            logger.error(f"Error scraping Resident Advisor: {str(e)}")
            return events

# Standalone testing
if __name__ == "__main__":
    scraper = EventScraper()
    events = scraper.scrape_berlin_events(limit=10)
    
    print(f"Found {len(events)} club events in Berlin:")
    for i, event in enumerate(events, 1):
        print(f"\n{i}. {event['event_name']} at {event['venue']} ({event['district']})")
        print(f"   Date: {event['event_date']} at {event['event_time']}")
        print(f"   {event['description'][:100]}...")
        if event['image_url']:
            print(f"   Image: {event['image_url']}")
        if event['event_url']:
            print(f"   URL: {event['event_url']}")