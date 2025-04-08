import os
import logging
import time
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
        return render_template("index.html", deals=deals)
    except Exception as e:
        logger.error(f"Error retrieving deals: {str(e)}")
        flash(f"Error retrieving deals: {str(e)}", "danger")
        return render_template("index.html", deals=[])

@app.route("/scrape", methods=["POST"])
def scrape_deals():
    """Route to trigger scraping of deals"""
    try:
        rate_limit()
        location = request.form.get("location", "Austin")
        scraped_deals = YelpScraper.scrape(location)
        
        # Add each deal to the database
        for deal in scraped_deals:
            deal_db.add_deal(deal["name"], deal["deal"], deal["location"])
        
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
            
            if not business_name or not deal or not location:
                flash("All fields are required", "danger")
                return redirect(url_for("submit_deal"))
            
            deal_db.add_deal(business_name, deal, location)
            flash("Deal submitted successfully!", "success")
            return redirect(url_for("home"))
        
        except Exception as e:
            logger.error(f"Error submitting deal: {str(e)}")
            flash(f"Error submitting deal: {str(e)}", "danger")
            return redirect(url_for("submit_deal"))
    
    return render_template("submit.html")

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
