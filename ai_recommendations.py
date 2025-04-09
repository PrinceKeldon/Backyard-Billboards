"""
AI-powered recommendation engine for happy hour deals
Uses OpenAI GPT to provide personalized venue recommendations
"""
import os
import json
import logging
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = None
if OPENAI_API_KEY:
    try:
        openai = OpenAI(api_key=OPENAI_API_KEY)
        logger.info("OpenAI client initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {str(e)}")
else:
    logger.warning("OPENAI_API_KEY not found in environment variables")

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
        # Prepare the list of venues for the AI to consider
        venues_data = []
        for deal in deals:
            venue_info = {
                "business_name": deal.get("business_name", "Unknown"),
                "district": deal.get("district", "Unknown"),
                "deal": deal.get("deal", ""),
                "location": deal.get("location", ""),
                "place_type": deal.get("place_type", ""),
                "votes": deal.get("votes", 0),
                "rating": deal.get("rating", None),
                "price_level": deal.get("price_level", None)
            }
            venues_data.append(venue_info)
        
        # Create prompt for AI
        prompt = f"""
        As an AI recommendation engine for happy hour deals in Berlin, your task is to analyze venues and recommend the best ones that match the user's preferences.
        
        USER PREFERENCES:
        {json.dumps(user_preferences, indent=2)}
        
        AVAILABLE VENUES (up to 30 venues):
        {json.dumps(venues_data[:30], indent=2)}
        
        Based on the user's preferences, provide:
        1. A ranked list of up to 3 top recommendations
        2. A brief explanation for each recommendation
        3. A short summary of your reasoning
        
        Respond with JSON in this format:
        {{
            "recommendations": [
                {{
                    "business_name": "Venue Name",
                    "explanation": "Brief explanation why this venue matches preferences"
                }},
                ...
            ],
            "reasoning": "Overall explanation of your recommendation strategy"
        }}
        """
        
        # Get recommendation from OpenAI
        # The newest OpenAI model is "gpt-4o" which was released May 13, 2024.
        # Do not change this unless explicitly requested by the user
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an AI recommendation engine specializing in Berlin's bar and restaurant scene."},
                     {"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        # Parse the response
        result = json.loads(response.choices[0].message.content)
        
        # Match the recommendations with full deal data to include all details
        matched_recommendations = []
        for rec in result.get("recommendations", []):
            rec_name = rec.get("business_name")
            if not rec_name:
                continue
                
            # Find the full deal data for this recommendation
            matched_deal = None
            for deal in deals:
                if deal.get("business_name") == rec_name:
                    matched_deal = deal
                    break
            
            if matched_deal:
                # Include the AI explanation in the deal object
                matched_deal["explanation"] = rec.get("explanation", "")
                matched_recommendations.append(matched_deal)
        
        # Return the updated result with full deal objects
        return {
            "recommendations": matched_recommendations,
            "reasoning": result.get("reasoning", "")
        }
        
    except Exception as e:
        logger.error(f"Error getting AI recommendation: {str(e)}")
        # Return a fallback recommendation if AI fails
        return {
            "recommendations": [],
            "reasoning": f"Could not generate recommendations due to an error: {str(e)}"
        }

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
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are a creative writer specializing in Berlin's nightlife scene."},
                     {"role": "user", "content": prompt}],
            max_tokens=300
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        logger.error(f"Error generating venue description: {str(e)}")
        # Return a fallback description if AI fails
        if district and place_type:
            return f"A {place_type.lower()} in {district} offering happy hour deals. {business_name} is a popular spot for drinks with special pricing during happy hour."
        else:
            return f"A venue in Berlin offering happy hour deals. {business_name} is a great spot to enjoy discounted drinks."