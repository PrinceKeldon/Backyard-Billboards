"""
AI-powered recommendation engine for happy hour deals
Uses OpenAI GPT to provide personalized venue recommendations
"""
import os
import json
import logging
import httpx
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client in a way that doesn't crash the application
try:
    # Get API key from environment
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    
    # Initialize the client
    if OPENAI_API_KEY:
        openai = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully")
    else:
        # Use a dummy client that will be reinitialized later if the key becomes available
        openai = None
        logger.warning("OPENAI_API_KEY not found in environment variables")
        
except Exception as e:
    openai = None
    logger.error(f"Failed to initialize OpenAI client: {str(e)}")

# Function to get or recreate the OpenAI client
def get_openai_client():
    """Get the OpenAI client, recreating it if necessary"""
    global openai, OPENAI_API_KEY
    
    # If we already have a client, return it
    if openai is not None:
        return openai
        
    # Try to recreate the client
    try:
        # Check if the API key is in the environment
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if api_key:
            # Update the global variables
            OPENAI_API_KEY = api_key
            openai = OpenAI(api_key=api_key)
            logger.info("OpenAI client reinitialized successfully")
            return openai
    except Exception as e:
        logger.error(f"Failed to reinitialize OpenAI client: {str(e)}")
    
    # If we get here, we couldn't create a client
    return None

def get_ai_recommendation(user_preferences, deals):
    """
    Get AI-powered venue recommendations based on user preferences and available deals
    
    Args:
        user_preferences (dict): User preferences with keys like 'district', 'price_range', 'vibe', etc.
        deals (list): List of deal dictionaries with business details
        
    Returns:
        dict: Recommendation results with keys 'recommendations' (list), 'reasoning' (str)
    """
    try:
        # Validate input data first
        if not deals or len(deals) == 0:
            logger.error("No deals available for recommendations")
            return {
                "recommendations": _get_fallback_recommendations(deals, user_preferences),
                "reasoning": "No venues are currently available. Please try again later or add more venues."
            }

        # Pre-process preferences to normalize and clean data
        clean_preferences = _sanitize_preferences(user_preferences)
        
        # Apply smart filtering based on preferences
        filtered_deals = _pre_filter_deals(deals, clean_preferences)
        
        # If we don't have enough venues after filtering, include some popular ones
        if len(filtered_deals) < 3:
            # Add popular venues that weren't included in the filtered set
            popular_deals = sorted([d for d in deals if d not in filtered_deals], 
                                  key=lambda x: x.get("votes", 0), 
                                  reverse=True)[:5]
            filtered_deals.extend(popular_deals)
            
        # Limit to 8 venues maximum to reduce API call size but ensure enough variety
        filtered_deals = filtered_deals[:8]
        
        # Prepare simplified venue data for the AI
        venues_data = _prepare_venue_data(filtered_deals)
        
        # Create a more structured and concise prompt
        prompt = _create_recommendation_prompt(clean_preferences, venues_data)
        
        # Get or create the OpenAI client
        client = get_openai_client()
        if not client:
            logger.error("OpenAI client is not initialized or API key is missing")
            return {
                "recommendations": _get_fallback_recommendations(deals, clean_preferences),
                "reasoning": "AI recommendations are currently unavailable. We've selected some popular venues for you instead."
            }
        
        # Reduced timeout to 20 seconds to prevent long waits
        timeout = httpx.Timeout(20.0, connect=5.0)
        
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # Do not change this unless explicitly requested by the user
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an AI recommendation engine specializing in Berlin's bar and restaurant scene. Provide concise and accurate recommendations based on user preferences."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=400,  # Further reduced token count for faster response
            timeout=timeout
        )
        
        # Parse the response with error handling
        try:
            result = json.loads(response.choices[0].message.content)
        except (json.JSONDecodeError, IndexError, AttributeError) as e:
            logger.error(f"Error parsing AI response: {str(e)}")
            return {
                "recommendations": _get_fallback_recommendations(deals, clean_preferences),
                "reasoning": "We couldn't process the AI recommendations. Here are some popular venues instead."
            }
        
        # Match recommendations with full venue data
        matched_recommendations = _match_recommendations_with_deals(result, deals)
        
        # If no valid recommendations were found, use fallback
        if not matched_recommendations:
            logger.warning("No valid recommendations matched with available deals")
            return {
                "recommendations": _get_fallback_recommendations(deals, clean_preferences),
                "reasoning": "Our AI couldn't match your preferences with available venues. Here are some popular alternatives."
            }
        
        # Return the recommendations with reasoning
        return {
            "recommendations": matched_recommendations,
            "reasoning": result.get("reasoning", "Based on your preferences, we've selected these venues for you.")
        }
        
    except httpx.TimeoutException:
        logger.error("OpenAI API request timed out after 20 seconds")
        return {
            "recommendations": _get_fallback_recommendations(deals, user_preferences),
            "reasoning": "The recommendation request timed out. We've selected some popular venues for you instead."
        }
    except Exception as e:
        logger.error(f"Error getting AI recommendation: {str(e)}")
        return {
            "recommendations": _get_fallback_recommendations(deals, user_preferences),
            "reasoning": "We couldn't generate AI recommendations. Here are some popular options that might interest you."
        }

def _sanitize_preferences(preferences):
    """Clean and normalize user preferences"""
    clean_prefs = {}
    
    # Copy and sanitize each preference
    for key, value in preferences.items():
        if isinstance(value, str):
            clean_value = value.strip()
            if clean_value:  # Only include non-empty values
                clean_prefs[key] = clean_value
    
    return clean_prefs

def _pre_filter_deals(deals, preferences):
    """Apply smart filtering based on user preferences"""
    filtered_deals = deals.copy()
    
    # Filter by district if specified
    district_pref = preferences.get("district", "").lower()
    if district_pref:
        district_matches = [d for d in deals if d.get("district") and d.get("district").lower() == district_pref]
        if district_matches:
            filtered_deals = district_matches
    
    # Apply additional filters based on other preferences
    vibe_pref = preferences.get("vibe", "").lower()
    drink_pref = preferences.get("drink_preference", "").lower()
    
    # Score each deal based on preference match
    scored_deals = []
    for deal in filtered_deals:
        score = 0
        deal_text = deal.get("deal", "").lower()
        
        # Score based on votes (popular venues get a boost)
        score += min(deal.get("votes", 0), 10) / 2
        
        # Score based on drink preference match
        if drink_pref and drink_pref in deal_text:
            score += 3
            
        # Simple vibe matching based on keyword presence in deal text
        if vibe_pref:
            vibe_keywords = {
                "casual": ["casual", "relaxed", "chill", "cozy"],
                "trendy": ["trendy", "hip", "modern", "stylish"],
                "upscale": ["upscale", "elegant", "sophisticated", "luxurious"],
                "alternative": ["alternative", "unique", "creative", "indie"],
                "social": ["social", "lively", "buzzing", "vibrant"]
            }
            
            # Check if any keywords for the selected vibe appear in the deal text
            if vibe_pref in vibe_keywords:
                for keyword in vibe_keywords[vibe_pref]:
                    if keyword in deal_text:
                        score += 2
                        break
        
        scored_deals.append((deal, score))
    
    # Sort by score (highest first) and return the deals
    return [deal for deal, score in sorted(scored_deals, key=lambda x: x[1], reverse=True)]

def _prepare_venue_data(deals):
    """Prepare simplified venue data for the AI"""
    venues_data = []
    for deal in deals:
        venue_info = {
            "business_name": deal.get("business_name", "Unknown"),
            "district": deal.get("district", "Unknown"),
            "deal": deal.get("deal", ""),
            # Include only essential info to reduce prompt size
            "place_type": deal.get("place_type", ""),
        }
        venues_data.append(venue_info)
    return venues_data

def _create_recommendation_prompt(preferences, venues_data):
    """Create a structured and concise prompt for the AI"""
    # Create a simpler, more focused prompt
    prompt = f"""
    As Berlin's nightlife recommendation expert, find venues matching these preferences:
    {json.dumps(preferences, indent=2)}
    
    Available venues (limited selection):
    {json.dumps(venues_data, indent=2)}
    
    Respond with JSON only:
    {{
      "recommendations": [
        {{
          "business_name": "Venue Name",
          "explanation": "Brief reason why this venue matches preferences"
        }}
      ],
      "reasoning": "Short explanation of your recommendation logic"
    }}
    
    Include 1-3 best matching venues and keep explanations under 30 words each.
    """
    return prompt

def _match_recommendations_with_deals(ai_result, all_deals):
    """Match AI recommendations with full deal data"""
    matched_recommendations = []
    
    # Handle potential issues with AI response structure
    recommendations = ai_result.get("recommendations", [])
    if not isinstance(recommendations, list):
        logger.error("AI did not return a list of recommendations")
        return []
    
    # Process each recommendation
    for rec in recommendations:
        if not isinstance(rec, dict):
            continue
            
        rec_name = rec.get("business_name")
        if not rec_name:
            continue
            
        # Find the matching deal
        matched_deal = None
        for deal in all_deals:
            if deal.get("business_name") == rec_name:
                matched_deal = deal.copy()  # Create a copy to avoid modifying original
                break
        
        if matched_deal:
            # Add the explanation
            matched_deal["explanation"] = rec.get("explanation", "")
            matched_recommendations.append(matched_deal)
    
    return matched_recommendations

def _get_fallback_recommendations(deals, preferences=None):
    """Get fallback recommendations when AI fails"""
    if not deals:
        return []
        
    fallback_deals = []
    
    # Try to match district if specified
    if preferences and preferences.get("district"):
        district = preferences.get("district").lower()
        district_matches = [d for d in deals if d.get("district") and d.get("district").lower() == district]
        
        if district_matches:
            # Sort by votes within the district
            sorted_district = sorted(district_matches, key=lambda x: x.get("votes", 0), reverse=True)
            for deal in sorted_district[:3]:
                deal_copy = deal.copy()
                deal_copy["explanation"] = f"Popular venue in {deal.get('district', 'Berlin')}"
                fallback_deals.append(deal_copy)
    
    # If we don't have enough district matches, add top rated overall
    if len(fallback_deals) < 3:
        # Sort all deals by votes
        top_deals = sorted(deals, key=lambda x: x.get("votes", 0), reverse=True)
        
        # Add top voted deals not already included
        for deal in top_deals:
            if len(fallback_deals) >= 3:
                break
                
            # Check if already included
            if not any(d.get("business_name") == deal.get("business_name") for d in fallback_deals):
                deal_copy = deal.copy()
                deal_copy["explanation"] = f"Highly rated venue in {deal.get('district', 'Berlin')}"
                fallback_deals.append(deal_copy)
    
    return fallback_deals

def get_venue_description(business_name, deal_text, district, place_type):
    """
    Generate an AI-powered descriptive text for a venue
    
    Args:
        business_name (str): Name of the business
        deal_text (str): The deal description
        district (str): District/neighborhood
        place_type (str): Type of venue (Bar, Restaurant, etc.)
        
    Returns:
        str: AI-generated venue description
    """
    try:
        prompt = f"""
        Create an engaging, detailed description for this Berlin venue:
        
        Name: {business_name}
        Type: {place_type if place_type else 'Bar/Restaurant'}
        District: {district if district else 'Berlin'}
        Happy Hour Deal: {deal_text}
        
        Write about 2-3 sentences focusing on:
        - The venue's atmosphere and vibe
        - What makes it special in Berlin's nightlife scene
        - Why it's worth visiting during happy hour
        
        Do NOT include made-up specific details like opening hours, interior design specifics, or historical facts that are not provided.
        Make the description attractive but realistic, focusing on what can be reasonably inferred from the venue name, type, and deal.
        """
        
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # Do not change this unless explicitly requested by the user
        
        # Get or create the OpenAI client
        client = get_openai_client()
        if not client:
            logger.error("OpenAI client is not initialized or API key is missing")
            raise ValueError("OpenAI API key is missing. Cannot generate venue description.")
            
        # Use timeout for venue description generation as well
        timeout = httpx.Timeout(20.0, connect=5.0)
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a creative writer specializing in Berlin's nightlife scene."},
                     {"role": "user", "content": prompt}],
            max_tokens=300,
            timeout=timeout
        )
        
        return response.choices[0].message.content.strip()
        
    except httpx.TimeoutException:
        logger.error("OpenAI API request timed out while generating venue description")
        # Return a more specific timeout error message
        if district:
            return f"{business_name} is a popular spot in {district} offering happy hour deals. Visit for their special: {deal_text}"
        else:
            return f"{business_name} is a popular venue in Berlin offering happy hour deals. Their special: {deal_text}"
    except Exception as e:
        logger.error(f"Error generating venue description: {str(e)}")
        # Return a fallback description if AI fails
        if district and place_type:
            return f"A {place_type.lower()} in {district} offering happy hour deals. {business_name} is a popular spot for drinks with special pricing during happy hour."
        else:
            return f"A venue in Berlin offering happy hour deals. {business_name} is a great spot to enjoy discounted drinks."