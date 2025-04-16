"""
This script checks the raw data in the database to verify if currency placeholders exist
"""
import logging
from db import DealDB

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_currency_placeholders():
    """Check for currency placeholders in the database"""
    deal_db = DealDB()
    deals = deal_db.get_all_deals()
    
    logger.info(f"Checking {len(deals)} deals for currency placeholders...")
    
    deals_with_placeholder = []
    for deal in deals:
        business_name = deal.get('business_name')
        deal_text = deal.get('deal', '')
        
        # Skip if no business name
        if not business_name:
            continue
        
        # Check if this deal has currency placeholders
        if '{currency}' in deal_text:
            logger.warning(f"Found currency placeholder in: {business_name}")
            logger.warning(f"Deal text: {deal_text}")
            deals_with_placeholder.append({
                'business_name': business_name,
                'deal_text': deal_text
            })
    
    if deals_with_placeholder:
        logger.warning(f"Found {len(deals_with_placeholder)} deals with currency placeholders")
        return deals_with_placeholder
    else:
        logger.info("No currency placeholders found in the database!")
        return []

if __name__ == "__main__":
    placeholders = check_currency_placeholders()
    if placeholders:
        print(f"Found {len(placeholders)} deals with currency placeholders:")
        for deal in placeholders:
            print(f"  - {deal['business_name']}: {deal['deal_text']}")
    else:
        print("No currency placeholders found in the database!")