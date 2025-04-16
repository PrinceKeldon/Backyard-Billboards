import replit
from datetime import datetime
import datetime as dt
import logging

logger = logging.getLogger(__name__)

class DealDB:
    """Database class for managing happy hour deals and users"""
    
    def add_user(self, username, email, password_hash, is_admin=False):
        """
        Add a new user
        
        Args:
            username (str): Username
            email (str): Email address
            password_hash (str): Hashed password
            is_admin (bool, optional): Whether the user is an admin (default: False)
            
        Returns:
            bool: True if user created successfully, False otherwise
        """
        try:
            # Check if username or email already exists
            for user_data in self.db.values():
                if isinstance(user_data, dict):
                    if user_data.get('username') == username or user_data.get('email') == email:
                        return False
                        
            self.db[username] = {
                "password_hash": password_hash,
                "username": username,
                "email": email,
                "is_admin": is_admin
            }
            logger.info(f"Added user: {username} (admin: {is_admin})")
            return True
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            raise

    def get_user(self, username):
        """Get user data"""
        try:
            if username in self.db:
                return self.db[username]
            return None
        except Exception as e:
            logger.error(f"Error getting user: {str(e)}")
            raise
    
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
    
    def get_late_night_deals(self, limit=None):
        """
        Get deals that are available after 10 PM (afterparty deals)
        
        Args:
            limit (int, optional): Maximum number of deals to return
            
        Returns:
            list: List of late night deals
        """
        try:
            deals = self.get_all_deals()
            late_night_deals = []
            
            for deal in deals:
                deal_text = deal.get('deal', '').lower()
                
                # Check for time indicators after 10 PM
                has_late_time = False
                if any(time_str in deal_text for time_str in [
                    '22:00', '23:00', '00:00', '01:00', '02:00', '03:00', '04:00', '05:00',
                    '10pm', '11pm', '12am', '1am', '2am', '3am', '4am', '5am', 
                    '22 uhr', '23 uhr', '00 uhr', '01 uhr', '02 uhr', '03 uhr', '04 uhr', '05 uhr',
                    'midnight', 'mitternacht', 'late night', 'after 10'
                ]):
                    has_late_time = True
                
                # Check for after-hours indicators
                is_afterparty = any(indicator in deal_text for indicator in [
                    'afterparty', 'after party', 'after-party', 'after hours', 
                    'late night', 'nachts', 'night owl', 'spätabends'
                ])
                
                # Check for shot specials
                has_shots = any(shot_term in deal_text for shot_term in [
                    'shot', 'shots', 'schnapps', 'schnaps', 'jägermeister', 'tequila', 'vodka'
                ])
                
                # Add to late night deals if it meets the criteria
                if has_late_time or is_afterparty:
                    # Create a copy of the deal
                    late_night_deal = deal.copy()
                    
                    # Add premium flag for deals with shots (for 2x revenue share)
                    if has_shots:
                        late_night_deal['is_premium'] = True
                        late_night_deal['revenue_multiplier'] = 2
                    
                    late_night_deals.append(late_night_deal)
            
            # Sort late night deals by whether they're premium (shots) first, then by votes
            late_night_deals = sorted(
                late_night_deals, 
                key=lambda x: (x.get('is_premium', False), x.get('votes', 0)), 
                reverse=True
            )
            
            # Apply limit if provided
            if limit:
                late_night_deals = late_night_deals[:limit]
            
            logger.debug(f"Returning {len(late_night_deals)} late night deals")
            return late_night_deals
        except Exception as e:
            logger.error(f"Error getting late night deals: {str(e)}")
            raise
    
    # -------------------- Event Billboard Functions --------------------
    
    def add_event(self, event_name, venue, district, event_date, event_time, description, image_url=None, event_url=None, **kwargs):
        """
        Add a club event to the billboard
        
        Args:
            event_name (str): Name of the event
            venue (str): Name of the venue/club
            district (str): Berlin district
            event_date (str): Date of the event (YYYY-MM-DD)
            event_time (str): Time of the event (HH:MM)
            description (str): Description of the event
            image_url (str, optional): URL to event image
            event_url (str, optional): URL to event page
            **kwargs: Additional event properties
        
        Returns:
            dict: The added event data
        """
        try:
            # Create a unique key for the event
            sanitized_name = event_name.replace(' ', '_').replace('/', '_').replace('\\', '_')
            event_id = f"{sanitized_name}_{event_date}_{venue}"
            
            # Set event data with all properties
            event_data = {
                'event_name': event_name,
                'venue': venue,
                'district': district,
                'event_date': event_date,
                'event_time': event_time,
                'description': description,
                'image_url': image_url,
                'event_url': event_url,
                'added_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f"),
                **kwargs
            }
            
            # Store the event
            self.db[event_id] = event_data
            logger.info(f"Added event: {event_name} at {venue} on {event_date}")
            
            # Add the event_id to the event data for reference
            event_data['event_id'] = event_id
            return event_data
        
        except Exception as e:
            logger.error(f"Error adding event: {str(e)}")
            raise
    
    def get_event(self, event_id):
        """
        Get a specific event by ID
        
        Args:
            event_id (str): ID of the event
            
        Returns:
            dict: Event data or None if not found
        """
        try:
            event_data = self.db.get(event_id)
            if event_data:
                # Add the event_id to the event data for reference
                event_data['event_id'] = event_id
            return event_data
        except Exception as e:
            logger.error(f"Error getting event {event_id}: {str(e)}")
            return None
    
    def get_current_events(self, hours_window=48):
        """
        Get events happening within the specified time window
        
        Args:
            hours_window (int): Time window in hours from now (default: 48 hours)
            
        Returns:
            list: List of current events sorted by date/time
        """
        try:
            all_events = []
            current_time = datetime.datetime.now()
            end_time = current_time + datetime.timedelta(hours=hours_window)
            
            # Get all keys that start with event prefix
            for key in self.db.prefix(""):
                if "_" in key:  # Check if it's potentially an event key
                    event_data = self.db.get(key)
                    
                    # Skip if not an event or missing required fields
                    if not event_data or 'event_date' not in event_data or 'event_time' not in event_data:
                        continue
                    
                    try:
                        # Parse event datetime
                        event_datetime_str = f"{event_data['event_date']} {event_data['event_time']}"
                        event_datetime = datetime.datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M")
                        
                        # Check if event is within the window
                        if current_time <= event_datetime <= end_time:
                            # Add the event_id to the event data for reference
                            event_data['event_id'] = key
                            all_events.append(event_data)
                    except ValueError:
                        logger.warning(f"Invalid date/time format for event {key}: {event_datetime_str}")
            
            # Sort events by date and time
            sorted_events = sorted(all_events, key=lambda x: f"{x['event_date']} {x['event_time']}")
            
            logger.debug(f"Returning {len(sorted_events)} current events")
            return sorted_events
        
        except Exception as e:
            logger.error(f"Error getting current events: {str(e)}")
            return []
    
    def delete_event(self, event_id):
        """
        Delete an event from the billboard
        
        Args:
            event_id (str): ID of the event to delete
        """
        try:
            if self.db.get(event_id):
                del self.db[event_id]
                logger.info(f"Deleted event: {event_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting event {event_id}: {str(e)}")
            return False
    
    def clean_expired_events(self):
        """
        Clean up expired events from the database
        
        Returns:
            int: Number of events cleaned up
        """
        try:
            current_time = datetime.datetime.now()
            cleaned_count = 0
            
            # Get all keys that start with event prefix
            for key in self.db.prefix(""):
                if "_" in key:  # Check if it's potentially an event key
                    event_data = self.db.get(key)
                    
                    # Skip if not an event or missing required fields
                    if not event_data or 'event_date' not in event_data or 'event_time' not in event_data:
                        continue
                    
                    try:
                        # Parse event datetime
                        event_datetime_str = f"{event_data['event_date']} {event_data['event_time']}"
                        event_datetime = datetime.datetime.strptime(event_datetime_str, "%Y-%m-%d %H:%M")
                        
                        # Check if event is in the past
                        if event_datetime < current_time:
                            # Delete the event
                            del self.db[key]
                            cleaned_count += 1
                            logger.info(f"Cleaned up expired event: {key}")
                    except ValueError:
                        logger.warning(f"Invalid date/time format for event {key}: {event_datetime_str}")
            
            logger.info(f"Cleaned up {cleaned_count} expired events")
            return cleaned_count
        
        except Exception as e:
            logger.error(f"Error cleaning expired events: {str(e)}")
            return 0
