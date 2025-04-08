import os
import logging
import time
import urllib.parse
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from db import DealDB
from scraper import YelpScraper
import facebook
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

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

def rate_limit():
    """Simple rate limiting function"""
    global last_request_time
    current_time = time.time()
    if current_time - last_request_time < MIN_REQUEST_INTERVAL:
        time.sleep(MIN_REQUEST_INTERVAL - (current_time - last_request_time))
    last_request_time = time.time()

@app.route("/")
def home():
    """Home page route - displays all deals"""
    try:
        deals = deal_db.get_all_deals()
        
        # Get district filter if specified
        district = request.args.get('district')
        if district:
            # Filter deals by district
            deals = [d for d in deals if d.get('district') and d.get('district').lower() == district.lower()]
        
        # Get all unique districts for the filter dropdown
        districts = sorted(list(set(d.get('district') for d in deal_db.get_all_deals() if d.get('district'))))
        
        return render_template("index.html", deals=deals, districts=districts, current_district=district)
    except Exception as e:
        logger.error(f"Error retrieving deals: {str(e)}")
        flash(f"Error retrieving deals: {str(e)}", "danger")
        return render_template("index.html", deals=[], districts=[], current_district=None)

@app.route("/scrape", methods=["POST"])
def scrape_deals():
    """Route to trigger scraping of deals"""
    try:
        rate_limit()
        location = request.form.get("location", "Berlin")  # Default to Berlin
        scraped_deals = YelpScraper.scrape(location)
        
        # Add each deal to the database
        for deal in scraped_deals:
            # Check if this is a Berlin deal with district info
            district = deal.get("district")
            has_accurate_location = deal.get("has_accurate_location", False)
            
            # Add to database with all available info
            deal_db.add_deal(
                deal["name"], 
                deal["deal"], 
                deal["location"],
                district=district, 
                has_accurate_location=has_accurate_location
            )
        
        flash(f"Successfully scraped {len(scraped_deals)} deals!", "success")
    except Exception as e:
        logger.error(f"Error scraping deals: {str(e)}")
        flash(f"Error scraping deals: {str(e)}", "danger")
    
    return redirect(url_for("home"))

@app.route("/post", methods=["POST"])
def post_to_facebook():
    """Route to post deals to Facebook"""
    try:
        rate_limit()
        business_name = request.form.get("business_name")
        
        if not business_name:
            return jsonify({"status": "error", "message": "Business name is required"}), 400
        
        deal_data = deal_db.get_deal(business_name)
        
        if not deal_data:
            return jsonify({"status": "error", "message": "Deal not found"}), 404
        
        # Get Facebook access token from environment
        fb_access_token = os.environ.get("FB_ACCESS_TOKEN")
        
        if not fb_access_token:
            return jsonify({"status": "error", "message": "Facebook access token not found"}), 500
        
        # Prepare the message
        message = f"Check out this happy hour deal at {business_name}!\n\n"
        message += f"Deal: {deal_data['deal']}\n"
        message += f"Location: {deal_data['location']}\n"
        message += f"\nPosted by Backyard Billboards"
        
        # Post to Facebook
        try:
            graph = facebook.GraphAPI(access_token=fb_access_token)
            graph.put_object(parent_object="me", connection_name="feed", message=message)
            return jsonify({"status": "success", "message": "Posted to Facebook successfully"})
        except facebook.GraphAPIError as e:
            logger.error(f"Facebook API error: {str(e)}")
            return jsonify({"status": "error", "message": f"Facebook API error: {str(e)}"}), 500
        
    except Exception as e:
        logger.error(f"Error posting to Facebook: {str(e)}")
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

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template("index.html", deals=[], error="Page not found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template("index.html", deals=[], error="Internal server error"), 500
