import os
import logging
import time
import urllib.parse
import asyncio
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from db import DealDB
from scraper import YelpScraper
from telegram import Bot
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set application environment variables
os.environ["ENABLE_GOOGLE_MAPS_SCRAPING"] = "true"  # Google Maps scraping enabled but needs to be opted into
os.environ["GOOGLE_MAPS_ENRICHMENT_LIMIT"] = "2"    # Limit to 2 deals per request for better performance

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Add custom Jinja2 filters
@app.template_filter('urlencode')
def urlencode_filter(s):
    """Filter for URL-encoding strings"""
    if isinstance(s, str):
        return urllib.parse.quote_plus(s)
    return ''

# Initialize database
deal_db = DealDB()

# Rate limiting variables
last_request_time = 0
MIN_REQUEST_INTERVAL = 2  # seconds

# We'll handle data cleaning at query time instead of at startup

def rate_limit():
    """Simple rate limiting function"""
    global last_request_time
    current_time = time.time()
    if current_time - last_request_time < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - (current_time - last_request_time))
    last_request_time = time.time()

@app.route("/")
def home():
    """Home page route - displays all deals with filtering options"""
    try:
        deals = deal_db.get_all_deals()
        
        # Clean the dataset - filter out non-Berlin locations first
        berlin_deals = []
        for deal in deals:
            location = deal.get('location', '').lower()
            # Keep only deals with Berlin in the location or that have a district set
            if 'berlin' in location or deal.get('district'):
                berlin_deals.append(deal)
        
        # Get filter parameters
        district = request.args.get('district', '')
        search_query = request.args.get('search', '')
        deal_type = request.args.get('deal_type', '')
        
        # Start with Berlin-only deals
        filtered_deals = berlin_deals
        
        # Filter by district if specified
        if district:
            filtered_deals = [d for d in filtered_deals if d.get('district') and d.get('district').lower() == district.lower()]
        
        # Filter by search term if specified
        if search_query:
            search_query = search_query.lower()
            filtered_deals = [d for d in filtered_deals if 
                search_query in d.get('business_name', '').lower() or 
                search_query in d.get('deal', '').lower() or 
                search_query in d.get('location', '').lower() or
                (d.get('district') and search_query in d.get('district', '').lower())]
        
        # Filter by deal type if specified
        if deal_type:
            if deal_type == 'drink':
                # Filter for drink deals - expanded keywords for better matching
                keywords = ['beer', 'cocktail', 'drink', 'wine', 'bier', 'wein', 'getränk', 'pilsner', 
                           'draft', 'weiße', 'weinschorle', 'pint', 'brew', 'alcohol', 'booze', 'spirits',
                           'shot', 'für-1', '2-für-1', 'happy hour']
                filtered_deals = [d for d in filtered_deals if any(keyword in d.get('deal', '').lower() for keyword in keywords)]
            elif deal_type == 'happy hour':
                # Filter for explicit happy hour mentions or time-specific deals
                filtered_deals = [d for d in filtered_deals if 
                                 'happy hour' in d.get('deal', '').lower() or 
                                 'uhr:' in d.get('deal', '').lower() or
                                 'pm:' in d.get('deal', '').lower() or
                                 'am:' in d.get('deal', '').lower()]
        
        # Get all unique districts for the filter dropdown
        districts = sorted(list(set(d.get('district') for d in deals if d.get('district'))))
        
        # Return the filtered deals with all filter parameters
        return render_template(
            "index.html", 
            deals=filtered_deals, 
            districts=districts, 
            current_district=district,
            search_query=search_query,
            deal_type=deal_type
        )
    except Exception as e:
        logger.error(f"Error retrieving deals: {str(e)}")
        flash(f"Error retrieving deals: {str(e)}", "danger")
        return render_template(
            "index.html", 
            deals=[], 
            districts=[], 
            current_district=None,
            search_query='',
            deal_type=''
        )

@app.route("/scrape", methods=["POST"])
def scrape_deals():
    """Route to trigger scraping of deals"""
    try:
        rate_limit()
        location = request.form.get("location", "Berlin")  # Default to Berlin
        use_google_maps = request.form.get("use_google_maps", "on") == "on"
        
        # Scrape deals (with Google Maps data if enabled)
        scraped_deals = YelpScraper.scrape(location, enrich_with_google=use_google_maps)
        
        # Add each deal to the database
        for deal in scraped_deals:
            # Get deal attributes with proper defaults
            district = deal.get("district")
            has_accurate_location = deal.get("has_accurate_location", False)
            
            # Get Google Maps data if available
            rating = deal.get("rating")
            reviews_count = deal.get("reviews_count") 
            place_type = deal.get("place_type")
            price_level = deal.get("price_level")
            google_maps_url = deal.get("google_maps_url")
            google_maps_address = deal.get("google_maps_address")
            
            # Use the Google Maps address if it's available
            location = google_maps_address or deal["location"]
            
            # Additional deal properties
            deal_props = {
                "district": district,
                "has_accurate_location": has_accurate_location,
                "rating": rating,
                "reviews_count": reviews_count,
                "place_type": place_type,
                "price_level": price_level,
                "google_maps_url": google_maps_url
            }
            
            # Only add properties that are not None
            deal_props = {k: v for k, v in deal_props.items() if v is not None}
            
            # Add to database with all available info
            deal_db.add_deal(
                deal["name"], 
                deal["deal"], 
                location,
                **deal_props
            )
        
        flash(f"Successfully scraped {len(scraped_deals)} deals{' with Google Maps data' if use_google_maps else ''}!", "success")
    except Exception as e:
        logger.error(f"Error scraping deals: {str(e)}")
        flash(f"Error scraping deals: {str(e)}", "danger")
    
    return redirect(url_for("home"))

# Function to send message to Telegram
async def send_telegram_message(message):
    """Send a message via Telegram bot
    
    Args:
        message (str): The message to send
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get Telegram credentials from environment
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            logger.error("Telegram credentials not found")
            return False
        
        # Initialize bot with token
        bot = Bot(token=token)
        
        # Send message
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
        logger.info(f"Message sent to Telegram: {message}")
        return True
    except Exception as e:
        logger.error(f"Error sending message to Telegram: {str(e)}")
        return False

def run_async(coroutine):
    """Helper function to run async code in sync context"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(coroutine)
    loop.close()
    return result

@app.route("/post", methods=["POST"])
def post_to_telegram():
    """Route to post deals to Telegram"""
    try:
        rate_limit()
        business_name = request.form.get("business_name")
        
        if not business_name:
            return jsonify({"status": "error", "message": "Business name is required"}), 400
        
        deal_data = deal_db.get_deal(business_name)
        
        if not deal_data:
            return jsonify({"status": "error", "message": "Deal not found"}), 404
        
        # Check if Telegram credentials exist
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if not token or not chat_id:
            return jsonify({"status": "error", "message": "Telegram credentials not found"}), 500
        
        # Prepare the message (with HTML formatting for Telegram)
        message = f"<b>🍻 Happy Hour Deal at {business_name}!</b>\n\n"
        message += f"<b>Deal:</b> {deal_data['deal']}\n"
        message += f"<b>Location:</b> {deal_data['location']}\n"
        
        # Add district if available
        if deal_data.get('district'):
            message += f"<b>District:</b> {deal_data['district']}\n"
        
        # Add rating if available
        if deal_data.get('rating'):
            stars = "⭐" * int(deal_data['rating'])
            message += f"<b>Rating:</b> {deal_data['rating']} {stars}\n"
        
        # Add Google Maps URL if available
        if deal_data.get('google_maps_url'):
            message += f"<a href='{deal_data['google_maps_url']}'>View on Google Maps</a>\n"
            
        message += f"\n<i>Posted by Backyard Billboards</i>"
        
        # Post to Telegram (run async function in sync context)
        success = run_async(send_telegram_message(message))
        
        if success:
            return jsonify({"status": "success", "message": "Posted to Telegram successfully"})
        else:
            return jsonify({"status": "error", "message": "Failed to post to Telegram"}), 500
        
    except Exception as e:
        logger.error(f"Error posting to Telegram: {str(e)}")
        return jsonify({"status": "error", "message": f"Error: {str(e)}"}), 500

@app.route("/submit", methods=["GET", "POST"])
def submit_deal():
    """Route for manual deal submission"""
    if request.method == "POST":
        try:
            business_name = request.form.get("business_name")
            deal = request.form.get("deal")
            location = request.form.get("location")
            district = request.form.get("district")
            has_accurate_location = True if request.form.get("accurate_location") == "on" else False
            
            if not business_name or not deal or not location:
                flash("All fields are required", "danger")
                return redirect(url_for("submit_deal"))
            
            deal_db.add_deal(
                business_name, 
                deal, 
                location, 
                district=district,
                has_accurate_location=has_accurate_location
            )
            flash("Deal submitted successfully!", "success")
            return redirect(url_for("home"))
        
        except Exception as e:
            logger.error(f"Error submitting deal: {str(e)}")
            flash(f"Error submitting deal: {str(e)}", "danger")
            return redirect(url_for("submit_deal"))
    
    # Get all Berlin districts for the dropdown
    berlin_districts = [
        "Mitte", "Prenzlauer Berg", "Neukölln", "Wedding", "Kreuzberg", 
        "Charlottenburg", "Schöneberg", "Friedrichshain", "Moabit", "Tiergarten",
        "Lichtenberg", "Köpenick", "Spandau", "Steglitz", "Marzahn", "Wilmersdorf",
        "Tempelhof", "Treptow", "Pankow", "Reinickendorf", "Zehlendorf"
    ]
    berlin_districts.sort()
    
    # Get existing districts from database to append to the list
    existing_districts = []
    try:
        deals = deal_db.get_all_deals()
        existing_districts = set(d.get('district') for d in deals if d.get('district'))
        # Add any missing districts to the list
        for district in existing_districts:
            if district and district not in berlin_districts:
                berlin_districts.append(district)
        berlin_districts.sort()
    except Exception as e:
        logger.error(f"Error retrieving districts: {str(e)}")
    
    return render_template("submit.html", districts=berlin_districts)

@app.route("/delete", methods=["POST"])
def delete_deal():
    """Route to delete a deal"""
    try:
        business_name = request.form.get("business_name")
        
        if not business_name:
            return jsonify({"status": "error", "message": "Business name is required"}), 400
        
        deal_db.delete_deal(business_name)
        flash(f"Deal for {business_name} deleted successfully", "success")
        return redirect(url_for("home"))
    
    except Exception as e:
        logger.error(f"Error deleting deal: {str(e)}")
        flash(f"Error deleting deal: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route("/clean-dataset", methods=["GET"])
def clean_dataset():
    """Route to clean the dataset - ensures all locations include Berlin"""
    try:
        from scraper import YelpScraper
        cleaned_count = YelpScraper.clean_dataset()
        flash(f"Successfully cleaned dataset! Updated {cleaned_count} deals to include Berlin in their location.", "success")
    except Exception as e:
        logger.error(f"Error cleaning dataset: {str(e)}")
        flash(f"Error cleaning dataset: {str(e)}", "danger")
    
    return redirect(url_for("home"))

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template("index.html", deals=[], error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template("index.html", deals=[], error="Internal server error"), 500
