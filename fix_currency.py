"""
This script directly fixes all {currency} placeholders in the database 
and ensures the cache is properly cleared
"""
import logging
import os
import time
import sys
from db import DealDB

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app directory to path so we can import the app's cache
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Try to import the app's cache clearing function
try:
    from app import clear_cache, cache
    HAS_APP_CACHE = True
    logger.info("Successfully imported app's cache functions")
except ImportError:
    HAS_APP_CACHE = False
    logger.warning("Could not import app's cache functions. Using manual approach.")

def fix_all_currency_placeholders():
    """Fix all currency placeholders in the database by replacing {currency} with € symbol"""
    deal_db = DealDB()
    deals = deal_db.get_all_deals()
    fixed_count = 0
    
    logger.info(f"Checking {len(deals)} deals for currency placeholders...")
    
    for deal in deals:
        business_name = deal.get('business_name')
        deal_text = deal.get('deal', '')
        
        # Skip if no business name
        if not business_name:
            continue
        
        # Check if this deal has currency placeholders
        if '{currency}' in deal_text:
            try:
                logger.info(f"Fixing currency placeholder in: {business_name}")
                logger.info(f"Original deal text: {deal_text}")
                
                # Get all properties to preserve
                location = deal.get('location', '')
                district = deal.get('district')
                has_accurate_location = deal.get('has_accurate_location', False)
                rating = deal.get('rating')
                reviews_count = deal.get('reviews_count')
                place_type = deal.get('place_type')
                price_level = deal.get('price_level')
                google_maps_url = deal.get('google_maps_url')
                votes = deal.get('votes', 0)
                scraped_at = deal.get('scraped_at')
                is_hidden_gem = deal.get('is_hidden_gem', False)
                hidden_gem_description = deal.get('hidden_gem_description', '')
                late_night_deal = deal.get('late_night_deal', False)
                
                # Create the updated deal text
                updated_deal_text = deal_text.replace('{currency}', '€')
                logger.info(f"Updated deal text: {updated_deal_text}")
                
                # Delete and recreate the deal with the updated text
                deal_db.delete_deal(business_name)
                deal_db.add_deal(
                    business_name=business_name, 
                    deal=updated_deal_text,
                    location=location,
                    district=district,
                    has_accurate_location=has_accurate_location,
                    rating=rating,
                    reviews_count=reviews_count,
                    place_type=place_type,
                    price_level=price_level,
                    google_maps_url=google_maps_url,
                    votes=votes,
                    scraped_at=scraped_at,
                    is_hidden_gem=is_hidden_gem,
                    hidden_gem_description=hidden_gem_description,
                    late_night_deal=late_night_deal
                )
                
                fixed_count += 1
                
            except Exception as e:
                logger.error(f"Error fixing currency for {business_name}: {str(e)}")
    
    logger.info(f"Successfully fixed {fixed_count} deals with currency placeholders!")
    return fixed_count

def clear_app_cache():
    """Clear the application cache to ensure fresh data is used"""
    if HAS_APP_CACHE:
        # Use the app's built-in cache clearing function
        logger.info("Clearing application cache using app.clear_cache()...")
        clear_cache()
    else:
        # Manual method to restart the application (force cache refresh)
        logger.info("Using manual approach to clear cache (stopping/starting app)...")
        try:
            os.system("pkill -f gunicorn")
            time.sleep(2)
            os.system("gunicorn --bind 0.0.0.0:5000 --reuse-port wsgi:application &")
            logger.info("Application restarted to clear cache")
        except Exception as e:
            logger.error(f"Error restarting app: {str(e)}")

if __name__ == "__main__":
    fixed_count = fix_all_currency_placeholders()
    print(f"Fixed {fixed_count} deals with currency placeholders.")
    
    # Clear the cache to ensure the changes are reflected in the app
    clear_app_cache()
    print("Application cache cleared.")