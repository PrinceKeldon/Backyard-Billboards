import replit
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DealDB:
    """Database class for managing happy hour deals"""
    
    def __init__(self):
        """Initialize database connection"""
        try:
            self.db = replit.db
            logger.debug("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def add_deal(self, business_name, deal, location, **kwargs):
        """
        Add a deal to the database
        
        Args:
            business_name (str): Name of the business
            deal (str): Description of the deal
            location (str): Location of the business
            **kwargs: Additional properties including:
                district (str): District/neighborhood (for Berlin)
                has_accurate_location (bool): Whether location is accurate for mapping
                rating (float): Google Maps rating (1-5)
                reviews_count (int): Number of reviews
                place_type (str): Type of establishment (Bar, Restaurant, etc.)
                price_level (int): Price level (1-4)
                google_maps_url (str): URL to Google Maps page
                votes (int): Number of upvotes for this deal
        """
        try:
            if not business_name or not deal or not location:
                raise ValueError("All fields are required")
            
            deal_data = {
                "deal": deal,
                "location": location,
                "scraped_at": str(datetime.now()),
                "has_accurate_location": kwargs.get("has_accurate_location", False),
                "votes": kwargs.get("votes", 0)  # Initialize votes to 0 by default
            }
            
            # Add optional fields from kwargs
            optional_fields = [
                "district", "rating", "reviews_count", "place_type", 
                "price_level", "google_maps_url", "is_hidden_gem",
                "hidden_gem_description", "hidden_gem_tips", "hidden_gem_photo_url",
                "submitted_by", "submission_type"
            ]
            
            for field in optional_fields:
                if field in kwargs and kwargs[field] is not None:
                    deal_data[field] = kwargs[field]
                
            self.db[business_name] = deal_data
            logger.debug(f"Added deal for {business_name}")
            return True
        except Exception as e:
            logger.error(f"Error adding deal: {str(e)}")
            raise
    
    def get_deal(self, business_name):
        """
        Get a specific deal by business name
        
        Args:
            business_name (str): Name of the business
            
        Returns:
            dict: Deal data or None if not found
        """
        try:
            if business_name in self.db:
                return self.db[business_name]
            return None
        except Exception as e:
            logger.error(f"Error getting deal: {str(e)}")
            raise
    
    def get_all_deals(self):
        """
        Get all deals from the database
        
        Returns:
            list: List of deals with business name included
        """
        try:
            deals = []
            logger.debug(f"DB keys: {list(self.db.keys())}")
            
            for business_name in self.db.keys():
                try:
                    deal_data = self.db[business_name]
                    logger.debug(f"Deal data for {business_name}: {deal_data}")
                    
                    # Replit DB returns ObservedDict objects
                    # Convert to a regular dictionary if needed
                    if hasattr(deal_data, "value"):
                        deal_data = deal_data.value
                        
                    # Skip if not a deal (in case other data is stored in the DB)
                    if not isinstance(deal_data, dict):
                        logger.debug(f"Skipping {business_name} as it's not a dictionary")
                        continue
                        
                    # Check if it has the required fields
                    if "deal" not in deal_data:
                        logger.debug(f"Skipping {business_name} as it doesn't have a 'deal' field")
                        continue
                    
                    # Add business name to the deal data
                    deal_info = deal_data.copy()  # Create a copy to avoid modifying the original
                    deal_info["business_name"] = business_name
                    deals.append(deal_info)
                except Exception as inner_e:
                    logger.error(f"Error processing deal {business_name}: {str(inner_e)}")
            
            # Sort deals by scraped_at date (newest first)
            deals.sort(key=lambda x: x.get("scraped_at", ""), reverse=True)
            logger.debug(f"Returning {len(deals)} deals")
            return deals
        except Exception as e:
            logger.error(f"Error getting all deals: {str(e)}")
            raise
    
    def delete_deal(self, business_name):
        """
        Delete a deal from the database
        
        Args:
            business_name (str): Name of the business
        """
        try:
            if business_name in self.db:
                del self.db[business_name]
                logger.debug(f"Deleted deal for {business_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting deal: {str(e)}")
            raise
    
    def clear_all_deals(self):
        """Clear all deals from the database (use with caution)"""
        try:
            for key in self.db.keys():
                del self.db[key]
            logger.debug("Cleared all deals")
            return True
        except Exception as e:
            logger.error(f"Error clearing deals: {str(e)}")
            raise
    
    def upvote_deal(self, business_name):
        """
        Increment the vote count for a deal
        
        Args:
            business_name (str): Name of the business
            
        Returns:
            dict: Updated deal data with new vote count or None if not found
        """
        try:
            if business_name not in self.db:
                logger.warning(f"Cannot upvote non-existent deal: {business_name}")
                return None
                
            deal_data = self.db[business_name]
            
            # Convert to a regular dictionary if needed
            if hasattr(deal_data, "value"):
                deal_data = deal_data.value
                
            # Ensure votes field exists
            if "votes" not in deal_data:
                deal_data["votes"] = 0
                
            # Increment vote count
            deal_data["votes"] += 1
            
            # Update the deal in the database
            self.db[business_name] = deal_data
            logger.debug(f"Upvoted deal for {business_name}, new count: {deal_data['votes']}")
            
            # Return the updated deal data with the business name included
            result = deal_data.copy()
            result["business_name"] = business_name
            return result
        except Exception as e:
            logger.error(f"Error upvoting deal: {str(e)}")
            raise
            
    def get_top_voted_deals(self, limit=10):
        """
        Get deals sorted by vote count (highest first)
        
        Args:
            limit (int): Maximum number of deals to return
            
        Returns:
            list: List of deals sorted by votes
        """
        try:
            deals = self.get_all_deals()
            
            # Ensure each deal has a votes field (default to 0 if missing)
            for deal in deals:
                if "votes" not in deal:
                    deal["votes"] = 0
                    
            # Sort by votes (highest first)
            sorted_deals = sorted(deals, key=lambda x: x.get("votes", 0), reverse=True)
            
            # Return at most 'limit' deals
            return sorted_deals[:limit]
        except Exception as e:
            logger.error(f"Error getting top voted deals: {str(e)}")
            raise
            
    def get_hidden_gems(self, district=None, limit=None):
        """
        Get deals marked as hidden gems
        
        Args:
            district (str, optional): Filter by district
            limit (int, optional): Maximum number of deals to return
            
        Returns:
            list: List of hidden gem deals
        """
        try:
            deals = self.get_all_deals()
            
            # Filter deals that are marked as hidden gems
            hidden_gems = [deal for deal in deals if deal.get("is_hidden_gem") == True]
            
            # Apply district filter if provided
            if district:
                hidden_gems = [deal for deal in hidden_gems if deal.get("district") == district]
                
            # Sort hidden gems by votes (highest first)
            hidden_gems = sorted(hidden_gems, key=lambda x: x.get("votes", 0), reverse=True)
            
            # Apply limit if provided
            if limit:
                hidden_gems = hidden_gems[:limit]
                
            logger.debug(f"Returning {len(hidden_gems)} hidden gems")
            return hidden_gems
        except Exception as e:
            logger.error(f"Error getting hidden gems: {str(e)}")
            raise
