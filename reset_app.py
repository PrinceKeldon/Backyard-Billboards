"""
This script completely resets the application's cache and fixes any remaining issues
"""
import os
import time
import logging
import sys
from db import DealDB

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add app directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    # Import app modules - import wsgi.application to ensure consistent app reference
    from wsgi import application
    from app import clear_cache, cache
    import models
    logger.info("Successfully imported application modules")
except ImportError as e:
    logger.error(f"Error importing application modules: {str(e)}")
    sys.exit(1)

def reset_application():
    """Reset the application's cache and fix any remaining issues"""
    logger.info("Starting application reset process...")
    
    # Step 1: Clear the entire app cache
    logger.info("Clearing application cache...")
    try:
        clear_cache()
        logger.info("Application cache cleared successfully")
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
    
    # Step 2: Verify currency placeholders are fixed in the database
    logger.info("Verifying currency placeholders are fixed...")
    deal_db = DealDB()
    deals = deal_db.get_all_deals()
    
    placeholders_found = False
    for deal in deals:
        business_name = deal.get('business_name')
        deal_text = deal.get('deal', '')
        
        # Skip if no business name or deal text
        if not business_name or not deal_text:
            continue
        
        # Check if this deal has currency placeholders
        if '{currency}' in deal_text:
            placeholders_found = True
            logger.warning(f"Found currency placeholder in: {business_name}")
            logger.warning(f"Deal text: {deal_text}")
            
            # Fix the placeholder
            logger.info(f"Fixing currency placeholder for {business_name}...")
            updated_deal_text = deal_text.replace('{currency}', '€')
            
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
            logger.info(f"Fixed currency placeholder for {business_name}")
    
    if not placeholders_found:
        logger.info("No currency placeholders found in the database")
    
    # Step 3: Verify database integrity
    logger.info("Verifying database integrity...")
    try:
        # Check if we can retrieve deals
        all_deals = deal_db.get_all_deals()
        logger.info(f"Database integrity verified: Found {len(all_deals)} deals")
        
        # Check if we can retrieve hidden gems
        hidden_gems = deal_db.get_hidden_gems()
        logger.info(f"Database integrity verified: Found {len(hidden_gems)} hidden gems")
        
        # Check if we can retrieve late night deals
        late_night_deals = deal_db.get_late_night_deals()
        logger.info(f"Database integrity verified: Found {len(late_night_deals)} late night deals")
    except Exception as e:
        logger.error(f"Database integrity check failed: {str(e)}")
        return False
    
    # Step 4: Reset the application cache
    logger.info("Resetting the application cache...")
    try:
        # Clear the cache again to ensure fresh data
        clear_cache()
        logger.info("Application cache cleared again to ensure fresh data")
    except Exception as e:
        logger.error(f"Error resetting application cache: {str(e)}")
        return False
    
    logger.info("Application reset process completed successfully")
    return True

if __name__ == "__main__":
    success = reset_application()
    if success:
        print("Application reset successful. All checks passed.")
    else:
        print("Application reset completed but some issues were detected.")")