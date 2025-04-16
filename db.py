import replit
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DealDB:
    """Database class for managing happy hour deals and users"""
    
    def _safe_key(self, key):
        """Make a key safe for storage by removing problematic characters"""
        return key.replace(':', '_').replace('/', '_').replace(' ', '_')
        
    def add_user(self, username, email, password_hash, is_admin=False):
        """Add a new user"""
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
            return True
        except Exception as e:
            logger.error(f"Error adding user: {str(e)}")
            raise
            
    def make_user_admin(self, username):
        """Make a user an admin"""
        try:
            if username in self.db:
                user_data = self.db[username]
                user_data['is_admin'] = True
                self.db[username] = user_data
                logger.info(f"Made user {username} an admin")
                return True
            return False
        except Exception as e:
            logger.error(f"Error making user admin: {str(e)}")
            return False

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
    
    def add_event(self, event_name, club_name, location, district=None, 
               image_url=None, start_time=None, end_time=None, description=None, 
               submitted_by=None):
        """
        Add a club event with 48-hour validity
        
        Args:
            event_name (str): Name of the event
            club_name (str): Name of the club
            location (str): Location of the club
            district (str, optional): District/neighborhood
            image_url (str, optional): URL to event image
            start_time (str, optional): Event start time
            end_time (str, optional): Event end time
            description (str, optional): Event description
            submitted_by (str, optional): Username of submitter
            
        Returns:
            dict: The added event data
        """
        try:
            # Generate a timestamp for when the event was added
            now = datetime.now()
            created_at = now.strftime("%Y-%m-%d %H:%M:%S.%f")
            
            # Calculate expiration time (48 hours from now)
            expiration_time = (now + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S.%f")
            
            # Create the event data
            event_data = {
                "event_name": event_name,
                "club_name": club_name,
                "location": location,
                "district": district,
                "image_url": image_url,
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
                "submitted_by": submitted_by,
                "created_at": created_at,
                "expires_at": expiration_time,
                "is_active": True
            }
            
            # Store in the database with the event name as the key
            safe_key = self._safe_key(f"event:{event_name}")
            self.db[safe_key] = event_data
            
            logger.info(f"Added event: {event_name} at {club_name}")
            return event_data
        
        except Exception as e:
            logger.error(f"Error adding event: {str(e)}")
            raise
            
    def get_active_events(self, limit=None):
        """
        Get all active events (not expired)
        
        Args:
            limit (int, optional): Maximum number of events to return
            
        Returns:
            list: List of active events
        """
        try:
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")
            
            events = []
            
            # Iterate through all keys
            for key in list(self.db.keys()):
                # Check if this is an event
                if key.startswith("event:"):
                    try:
                        event_data = self.db[key]
                        
                        # Include the event name in the data
                        event_name_from_key = key.replace("event:", "")
                        event_data["event_name"] = event_name_from_key
                        
                        # Check if the event has expired
                        if "expires_at" in event_data:
                            expires_at = event_data["expires_at"]
                            
                            # If not expired, add to the list
                            if expires_at > now_str:
                                events.append(event_data)
                            else:
                                # Mark as inactive if expired
                                event_data["is_active"] = False
                                self.db[key] = event_data
                                logger.info(f"Marked event as inactive (expired): {event_name_from_key}")
                    except Exception as e:
                        logger.error(f"Error processing event key {key}: {str(e)}")
            
            # Sort events by creation time (newest first)
            events = sorted(events, key=lambda x: x.get("created_at", ""), reverse=True)
            
            # Apply limit if provided
            if limit:
                events = events[:limit]
                
            logger.debug(f"Returning {len(events)} active events")
            return events
        
        except Exception as e:
            logger.error(f"Error getting active events: {str(e)}")
            raise
            
    def delete_expired_events(self):
        """
        Delete all expired events from the database
        
        Returns:
            int: Number of deleted events
        """
        try:
            now = datetime.now()
            now_str = now.strftime("%Y-%m-%d %H:%M:%S.%f")
            
            deleted_count = 0
            
            # Iterate through all keys
            for key in list(self.db.keys()):
                # Check if this is an event
                if key.startswith("event:"):
                    try:
                        event_data = self.db[key]
                        
                        # Check if the event has expired
                        if "expires_at" in event_data:
                            expires_at = event_data["expires_at"]
                            
                            # Delete if expired
                            if expires_at <= now_str:
                                del self.db[key]
                                deleted_count += 1
                                logger.info(f"Deleted expired event: {key}")
                    except Exception as e:
                        logger.error(f"Error processing event key {key}: {str(e)}")
    
            logger.info(f"Deleted {deleted_count} expired events")
            return deleted_count
        
        except Exception as e:
            logger.error(f"Error deleting expired events: {str(e)}")
            raise
    
    def delete_event(self, event_key):
        """
        Delete an event from the database
        
        Args:
            event_key (str): Key of the event to delete
            
        Returns:
            bool: Whether the deletion was successful
        """
        try:
            # Apply safe key function if not already applied
            safe_key = event_key
            if not safe_key.startswith("event:"):
                safe_key = self._safe_key(event_key)
            
            logger.debug(f"Attempting to delete event with key: {safe_key}, original key: {event_key}")
            logger.debug(f"Available keys: {list(self.db.keys())[:10]}")  # Only show first 10 keys to avoid overflow
                
            if safe_key in self.db:
                del self.db[safe_key]
                logger.info(f"Deleted event: {event_key}")
                return True
            else:
                logger.warning(f"Event not found with key: {safe_key}")
                return False
        except Exception as e:
            logger.error(f"Error deleting event: {str(e)}")
            return False
            
    def add_pending_event(self, event_name, club_name, location, district=None, 
                       image_url=None, start_time=None, end_time=None, description=None, 
                       submitted_by=None):
        """
        Add a club event pending admin approval
        
        Args:
            event_name (str): Name of the event
            club_name (str): Name of the club
            location (str): Location of the club
            district (str, optional): District/neighborhood
            image_url (str, optional): URL to event image
            start_time (str, optional): Event start time
            end_time (str, optional): Event end time
            description (str, optional): Event description
            submitted_by (str, optional): Username of submitter
            
        Returns:
            dict: The added pending event data
        """
        try:
            # Generate a timestamp for when the event was submitted
            now = datetime.now()
            submitted_at = now.strftime("%Y-%m-%d %H:%M:%S.%f")
            
            # Create the pending event data
            event_data = {
                "event_name": event_name,
                "club_name": club_name,
                "location": location,
                "district": district,
                "image_url": image_url,
                "start_time": start_time,
                "end_time": end_time,
                "description": description,
                "submitted_by": submitted_by,
                "submitted_at": submitted_at,
                "status": "pending"  # pending, approved, rejected
            }
            
            # Store in the database with a special prefix
            safe_key = self._safe_key(f"pending_event:{event_name}_{club_name}")
            self.db[safe_key] = event_data
            
            logger.info(f"Added pending event: {event_name} at {club_name} by {submitted_by}")
            return event_data
        
        except Exception as e:
            logger.error(f"Error adding pending event: {str(e)}")
            raise
            
    def get_pending_events(self):
        """
        Get all pending events awaiting admin approval
        
        Returns:
            list: List of pending events
        """
        try:
            pending_events = []
            
            # Iterate through all keys
            for key in list(self.db.keys()):
                # Check if this is a pending event
                if key.startswith("pending_event:"):
                    try:
                        event_data = self.db[key]
                        
                        # Add the key to the data for reference
                        event_data["db_key"] = key
                        
                        # Add to the list if status is pending
                        if event_data.get("status") == "pending":
                            pending_events.append(event_data)
                    except Exception as e:
                        logger.error(f"Error processing pending event key {key}: {str(e)}")
            
            # Sort events by submission time (newest first)
            pending_events = sorted(pending_events, key=lambda x: x.get("submitted_at", ""), reverse=True)
            
            logger.debug(f"Returning {len(pending_events)} pending events")
            return pending_events
        
        except Exception as e:
            logger.error(f"Error getting pending events: {str(e)}")
            raise
            
    def approve_pending_event(self, event_key):
        """
        Approve a pending event and make it active
        
        Args:
            event_key (str): Key of the pending event to approve
            
        Returns:
            bool: Whether the approval was successful
        """
        try:
            if event_key in self.db:
                # Get the pending event data
                event_data = self.db[event_key]
                
                # Generate a timestamp for when the event was approved
                now = datetime.now()
                approved_at = now.strftime("%Y-%m-%d %H:%M:%S.%f")
                
                # Calculate expiration time (48 hours from now)
                expiration_time = (now + timedelta(hours=48)).strftime("%Y-%m-%d %H:%M:%S.%f")
                
                # Prepare data for the approved event
                approved_event = {
                    "event_name": event_data.get("event_name"),
                    "club_name": event_data.get("club_name"),
                    "location": event_data.get("location"),
                    "district": event_data.get("district"),
                    "image_url": event_data.get("image_url"),
                    "start_time": event_data.get("start_time"),
                    "end_time": event_data.get("end_time"),
                    "description": event_data.get("description"),
                    "submitted_by": event_data.get("submitted_by"),
                    "created_at": approved_at,
                    "expires_at": expiration_time,
                    "is_active": True
                }
                
                # Create a new active event
                event_name = event_data.get("event_name")
                active_key = self._safe_key(f"event:{event_name}")
                self.db[active_key] = approved_event
                
                # Update the status of the pending event
                event_data["status"] = "approved"
                event_data["approved_at"] = approved_at
                self.db[event_key] = event_data
                
                logger.info(f"Approved pending event: {event_name}")
                return True
            else:
                logger.warning(f"Pending event not found with key: {event_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error approving pending event: {str(e)}")
            return False
            
    def reject_pending_event(self, event_key, rejection_reason=None):
        """
        Reject a pending event
        
        Args:
            event_key (str): Key of the pending event to reject
            rejection_reason (str, optional): Reason for rejection
            
        Returns:
            bool: Whether the rejection was successful
        """
        try:
            if event_key in self.db:
                # Get the pending event data
                event_data = self.db[event_key]
                
                # Update the status
                event_data["status"] = "rejected"
                event_data["rejected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                
                if rejection_reason:
                    event_data["rejection_reason"] = rejection_reason
                
                # Update the event in the database
                self.db[event_key] = event_data
                
                logger.info(f"Rejected pending event: {event_data.get('event_name')}")
                return True
            else:
                logger.warning(f"Pending event not found with key: {event_key}")
                return False
                
        except Exception as e:
            logger.error(f"Error rejecting pending event: {str(e)}")
            return False
            
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
