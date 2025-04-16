"""
Sample event generator for the Hot Now billboard 
Adds a few club events to demonstrate the feature
"""
import sys
import os
import datetime
import random
from db import DealDB

def add_sample_events():
    """Add sample events to the database"""
    # Initialize the database
    db = DealDB()
    
    # Create a few events for the next 48 hours
    now = datetime.datetime.now()
    
    # List of Berlin clubs with districts
    clubs = [
        {"name": "Berghain", "district": "Friedrichshain", 
         "address": "Am Wriezener Bahnhof, 10243 Berlin"},
        {"name": "Watergate", "district": "Kreuzberg",
         "address": "Falckensteinstraße 49, 10997 Berlin"},
        {"name": "Tresor", "district": "Mitte",
         "address": "Köpenicker Str. 70, 10179 Berlin"},
        {"name": "://about blank", "district": "Friedrichshain",
         "address": "Markgrafendamm, 10245 Berlin"},
        {"name": "Sisyphos", "district": "Lichtenberg",
         "address": "Hauptstraße 15, 10317 Berlin"},
        {"name": "Ritter Butzke", "district": "Kreuzberg",
         "address": "Ritterstraße 26, 10969 Berlin"},
        {"name": "KitKatClub", "district": "Mitte",
         "address": "Köpenicker Straße 76, 10179 Berlin"},
        {"name": "YAAM", "district": "Friedrichshain",
         "address": "Schillingbrücke 3, 10243 Berlin"},
        {"name": "Wilde Renate", "district": "Friedrichshain",
         "address": "Alt-Stralau 70, 10245 Berlin"},
        {"name": "RSO.Berlin", "district": "Neukölln",
         "address": "Schönstedtstraße, 12043 Berlin"}
    ]
    
    # List of DJs
    djs = [
        "Dixon", "Âme", "Marcel Dettmann", "Ben Klock", "Rødhåd", 
        "Ellen Allien", "Cassy", "Helena Hauff", "Job Jobse", "FJAAK", 
        "DJ Koze", "Honey Dijon", "Objekt", "Call Super", "Peggy Gou"
    ]
    
    # Event descriptions
    descriptions = [
        "Join us for a night of techno with Berlin's finest DJs in one of the city's most renowned clubs.",
        "Experience the underground techno scene with top selectors providing the soundtrack for an unforgettable night.",
        "Deep house and melodic techno on the main floor, with ambient sounds in the garden area.",
        "The legendary party returns with a carefully curated lineup of international and local talents.",
        "Immerse yourself in Berlin's vibrant club culture with pulsating beats and hypnotic rhythms.",
        "A celebration of electronic music spanning various genres, from ambient to hard techno."
    ]
    
    # Event image URLs (fictional, but realistic)
    image_urls = [
        "https://images.unsplash.com/photo-1544616566-4b54d1bdc74e",
        "https://images.unsplash.com/photo-1571370672064-7a74e40e8ce0",
        "https://images.unsplash.com/photo-1504704911898-68304a7d2807",
        "https://images.unsplash.com/photo-1563841930606-67e2bce48b78",
        "https://images.unsplash.com/photo-1547479117-da9abbff3fa0",
        "https://images.unsplash.com/photo-1525362081669-2b476bb628c3"
    ]
    
    # Generate events for the next 48 hours
    events_added = 0
    for i in range(8):  # Add 8 sample events
        # Select random club
        club = random.choice(clubs)
        
        # Create random datetime in the next 48 hours
        hours_ahead = random.randint(4, 47)
        event_datetime = now + datetime.timedelta(hours=hours_ahead)
        event_date = event_datetime.strftime("%Y-%m-%d")
        
        # Most club events start in the evening
        hour = random.randint(21, 23)
        minute = random.choice([0, 30])
        event_time = f"{hour:02d}:{minute:02d}"
        
        # Generate event name
        event_types = ["Night", "Session", "Experience", "Showcase", "Party"]
        dj_selection = random.sample(djs, min(3, random.randint(1, 3)))
        event_name = f"{random.choice(event_types)}: {' B2B '.join(dj_selection)}"
        
        # Select random description and image
        description = random.choice(descriptions)
        image_url = random.choice(image_urls)
        
        # Create event URL (fictional)
        event_url = f"https://ra.co/events/berlin/{club['name'].lower().replace(' ', '-')}-{event_date}"
        
        # Add to database
        try:
            db.add_event(
                event_name=event_name,
                venue=club["name"],
                district=club["district"],
                event_date=event_date,
                event_time=event_time,
                description=description,
                image_url=image_url,
                event_url=event_url,
                address=club["address"],
                source="sample_script",
                is_manually_added=True
            )
            events_added += 1
            print(f"Added event: {event_name} at {club['name']} on {event_date} at {event_time}")
        except Exception as e:
            print(f"Error adding event: {e}")
    
    print(f"\nAdded {events_added} sample events to the database")
    print("Use http://localhost:5000/hot-now to view the events")

if __name__ == "__main__":
    add_sample_events()