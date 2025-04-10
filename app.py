import os
import logging
import time
import urllib.parse
import io
import random
import base64
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User
from db import DealDB
from scraper import YelpScraper
from google_maps_scraper import GoogleMapsScraper
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import trafilatura
from ai_recommendations import get_ai_recommendation, get_venue_description

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Set application environment variables
os.environ["ENABLE_GOOGLE_MAPS_SCRAPING"] = "true"  # Google Maps scraping enabled but needs to be opted into
os.environ["GOOGLE_MAPS_ENRICHMENT_LIMIT"] = "2"    # Limit to 2 deals per request for better performance
os.environ["DEFAULT_LOCATION"] = "Berlin, Germany"  # Restrict all searches to Berlin, Germany
os.environ["RESTRICT_TO_BERLIN"] = "true"           # Flag to restrict all results to Berlin only

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "backyard-billboards-local-dev-secret-key")

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Import and register Jinja filters
from utils import get_time_ago
app.jinja_env.filters['to_time_ago'] = get_time_ago
logging.getLogger(__name__).info("Successfully registered Jinja filters")

# Configure error handling
@app.errorhandler(Exception)
def handle_exception(e):
    """Handle all exceptions during request processing"""
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return render_template('error.html', error=str(e)), 500

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors"""
    return render_template('error.html', error="Page not found"), 404

# Health check endpoint for deployment monitoring
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    from datetime import datetime
    try:
        # Quick DB connectivity check
        deals_count = len(deal_db.get_all_deals())
        gems_count = len(deal_db.get_hidden_gems())
        
        return jsonify({
            "status": "ok", 
            "timestamp": datetime.now().isoformat(),
            "app_name": "Backyard Billboards",
            "version": "1.0.0",
            "db_status": "connected",
            "deals_count": deals_count,
            "hidden_gems_count": gems_count
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return jsonify({
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "app_name": "Backyard Billboards",
            "message": str(e)
        }), 500

# Ensure the app is accessible for testing tools
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

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
        
        # Clean the dataset - filter out non-Berlin locations and USD prices
        filtered_deals = []
        for deal in deals:
            location = deal.get('location', '').lower()
            deal_text = deal.get('deal', '')
            
            # Skip any deals with dollar sign ($) instead of Euro (€)
            if '$' in deal_text:
                continue
                
            # Keep only deals with Berlin in the location or that have a district set
            if 'berlin' in location or deal.get('district'):
                filtered_deals.append(deal)
        
        # Get filter parameters
        district = request.args.get('district', '')
        search_query = request.args.get('search', '')
        deal_type = request.args.get('deal_type', '')
        # Removed sort_by parameter for simplified user experience
        
        # We're already using filtered_deals from above
        
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
        districts = sorted(list(set(d.get('district') for d in filtered_deals if d.get('district'))))
        
        # First sort by district match (if district filter is active), then by date
        if district:
            # Prioritize deals in the selected district by creating a key function
            # that returns (0, date) for deals in the selected district and (1, date) for others
            # This ensures district matches come first, and within each group, newest first
            def sort_key(deal):
                deal_district = deal.get("district", "")
                date = deal.get("scraped_at", "")
                # Return a tuple: first element determines primary sort order (0 for district match, 1 for non-match)
                # For the second element, we need to order by date (newest first)
                # When using reverse=True for sorting, we need to invert our logic:
                # - We want district matches (0) to come BEFORE non-matches (1), so with reverse=True,
                #   we need to use (1) for matches and (0) for non-matches
                # - Similarly for dates, with reverse=True, earlier dates will appear before later dates
                return (1 if deal_district == district else 0, date if date else "")
            
            # Sort using the custom key function
            # First by district match (0 before 1), then by date (newest first)
            filtered_deals = sorted(filtered_deals, key=sort_key, reverse=True)
        else:
            # If no district filter, just sort by date (newest first)
            filtered_deals = sorted(filtered_deals, key=lambda x: x.get("scraped_at", ""), reverse=True)
        
        # Return the filtered deals with all filter parameters
        # Get count of hidden gems for the navigation badge
        hidden_gems_count = len(deal_db.get_hidden_gems())
        
        return render_template(
            "index.html", 
            deals=filtered_deals, 
            districts=districts, 
            current_district=district,
            search_query=search_query,
            deal_type=deal_type,
            hidden_gems_count=hidden_gems_count
        )
    except Exception as e:
        logger.error(f"Error retrieving deals: {str(e)}")
        flash(f"Error retrieving deals: {str(e)}", "danger")
        # Still try to get hidden gems count for navigation
        try:
            hidden_gems_count = len(deal_db.get_hidden_gems())
        except:
            hidden_gems_count = 0
            
        return render_template(
            "index.html", 
            deals=[], 
            districts=[], 
            current_district=None,
            search_query='',
            deal_type='',
            hidden_gems_count=hidden_gems_count
        )

@app.route("/hidden-gems")
def hidden_gems():
    """Route to display hidden gem venues submitted by users"""
    try:
        # Get filter parameters
        district = request.args.get('district', '')
        
        # Get hidden gems, with optional district filter
        if district:
            gems = deal_db.get_hidden_gems(district=district)
        else:
            gems = deal_db.get_hidden_gems()
            
        # Set up pagination
        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_gems = len(gems)
        
        # Calculate pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_gems = gems[start_idx:end_idx]
        
        # Create pagination object
        pagination = {
            'has_prev': page > 1,
            'has_next': end_idx < total_gems,
            'prev_num': page - 1,
            'next_num': page + 1,
            'total_pages': (total_gems + per_page - 1) // per_page,
            'current_page': page
        }
        
        # Get all unique districts for filtering
        all_districts = sorted(list(set(gem.get('district') for gem in gems if gem.get('district'))))
        
        # Construct pagination URL
        pagination_url = url_for('hidden_gems')
        if district:
            pagination_url += f"?district={district}"
        
        return render_template(
            'hidden_gems.html',
            hidden_gems=paginated_gems,
            districts=all_districts,
            current_district=district,
            pagination=pagination,
            current_page=page,
            hidden_gems_count=total_gems
        )
    except Exception as e:
        logger.error(f"Error displaying hidden gems: {str(e)}")
        flash(f"Error displaying hidden gems: {str(e)}", "danger")
        return render_template('error.html', error=str(e)), 500
        
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

# Telegram functionality has been removed to simplify deployment

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.get(username)
        
        if user and user.verify_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('home'))
        
        flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('signup.html')
            
        if User.create(username, email, password):
            flash('Account created successfully. Please login.', 'success')
            return redirect(url_for('login'))
            
        flash('Username or email already exists.', 'danger')
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route("/submit", methods=["GET", "POST"])
@login_required
def submit_deal():
    """Route for manual deal submission"""
    if request.method == "POST":
        try:
            business_name = request.form.get("business_name")
            deal = request.form.get("deal")
            location = request.form.get("location")
            district = request.form.get("district")
            has_accurate_location = True if request.form.get("accurate_location") == "on" else False
            
            # Process hidden gem data
            is_hidden_gem = True if request.form.get("is_hidden_gem") == "on" else False
            hidden_gem_description = request.form.get("hidden_gem_description", "")
            hidden_gem_tips = request.form.get("hidden_gem_tips", "")
            submitted_by = request.form.get("submitted_by", "")
            
            if not business_name or not deal or not location:
                flash("All fields are required", "danger")
                return redirect(url_for("submit_deal"))
            
            # If marked as hidden gem, ensure description is provided
            if is_hidden_gem and not hidden_gem_description:
                flash("Please provide a description of what makes this place special if marking it as a hidden gem", "warning")
                return redirect(url_for("submit_deal"))
                
            # Set submission type
            submission_type = "hidden_gem" if is_hidden_gem else "regular"
            
            # Add to database with additional hidden gem fields if applicable
            kwargs = {
                "district": district,
                "has_accurate_location": has_accurate_location,
                "submission_type": submission_type
            }
            
            # Only add hidden gem fields if it's marked as a hidden gem
            if is_hidden_gem:
                kwargs.update({
                    "is_hidden_gem": True,
                    "hidden_gem_description": hidden_gem_description,
                    "hidden_gem_tips": hidden_gem_tips,
                    "submitted_by": submitted_by
                })
                
            deal_db.add_deal(
                business_name, 
                deal, 
                location, 
                **kwargs
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
    
    # Get count of hidden gems for the navigation badge
    try:
        hidden_gems_count = len(deal_db.get_hidden_gems())
    except:
        hidden_gems_count = 0
        
    return render_template("submit.html", districts=berlin_districts, hidden_gems_count=hidden_gems_count)

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

@app.route("/upvote", methods=["POST"])
def upvote_deal():
    """Route to upvote a deal"""
    try:
        business_name = request.form.get("business_name")
        
        if not business_name:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"status": "error", "message": "Business name is required"}), 400
            flash("Business name is required", "warning")
            return redirect(url_for("home"))
        
        result = deal_db.upvote_deal(business_name)
        
        if result:
            # Get the updated vote count
            vote_count = result.get('votes', 0)
            
            # If this was an AJAX request, return JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'success',
                    'vote_count': vote_count,
                    'message': f"Upvoted deal for {business_name}"
                })
            
            # Otherwise return a regular redirect with flash message
            flash(f"Upvoted deal for {business_name}", "success")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'status': 'error',
                    'message': f"Deal not found for {business_name}"
                }), 404
                
            flash(f"Deal not found for {business_name}", "warning")
            
    except Exception as e:
        logger.error(f"Error upvoting deal: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'status': 'error',
                'message': f"Error upvoting deal: {str(e)}"
            }), 500
            
        flash(f"Error upvoting deal: {str(e)}", "danger")
        
    # If it wasn't an AJAX request or if there was an error, redirect
    return redirect(url_for('home'))

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

@app.route("/remove-dollar-prices", methods=["GET"])
def remove_dollar_prices():
    """Route to remove all deals with dollar sign ($) prices instead of Euro (€)"""
    try:
        deals = deal_db.get_all_deals()
        deleted_count = 0
        
        for deal in deals:
            business_name = deal.get('business_name')
            deal_text = deal.get('deal', '').lower()
            
            # Skip if no business name
            if not business_name:
                continue
            
            # Check if this deal has dollar prices
            if '$' in deal_text:
                try:
                    deal_db.delete_deal(business_name)
                    deleted_count += 1
                    logger.info(f"Deleted deal with dollar prices: {business_name} - {deal_text}")
                except Exception as e:
                    logger.error(f"Error deleting deal {business_name}: {str(e)}")
        
        logger.info(f"Removed {deleted_count} deals with dollar prices")
        flash(f"Successfully removed {deleted_count} deals with dollar ($) prices", "success")
        return redirect(url_for("home"))
    
    except Exception as e:
        logger.error(f"Error removing dollar-priced deals: {str(e)}")
        flash(f"Error removing dollar-priced deals: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route("/fix-currency-placeholders", methods=["GET"])
def fix_currency_placeholders():
    """Route to fix currency placeholders in deal texts, replacing {currency} with € symbol"""
    try:
        deals = deal_db.get_all_deals()
        fixed_count = 0
        
        for deal in deals:
            business_name = deal.get('business_name')
            deal_text = deal.get('deal', '')
            
            # Skip if no business name
            if not business_name:
                continue
            
            # Check if this deal has currency placeholders
            if '{currency}' in deal_text:
                try:
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
                    
                    # Create the updated deal text
                    updated_deal_text = deal_text.replace('{currency}', '€')
                    
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
                        scraped_at=scraped_at
                    )
                    
                    fixed_count += 1
                    logger.info(f"Fixed currency in deal: {business_name} - {deal_text} -> {updated_deal_text}")
                except Exception as e:
                    logger.error(f"Error fixing currency for deal {business_name}: {str(e)}")
        
        logger.info(f"Fixed {fixed_count} deals with currency placeholders")
        flash(f"Successfully fixed {fixed_count} deals with currency placeholders", "success")
        return redirect(url_for("home"))
    
    except Exception as e:
        logger.error(f"Error fixing currency placeholders: {str(e)}")
        flash(f"Error fixing currency placeholders: {str(e)}", "danger")
        return redirect(url_for("home"))


@app.route("/remove-austin-texas", methods=["GET"])
def remove_austin_texas():
    """Route to specifically remove Austin, Texas locations and American-style addresses"""
    try:
        import re
        # Define American/Austin indicators
        austin_indicators = [
            "austin", "texas", "atx", "tx", "6th street", "6th st", "congress avenue", 
            "rainey street", "south congress", "guadalupe", "the drag", "soco"
        ]
        
        deals = deal_db.get_all_deals()
        deleted_count = 0
        
        for deal in deals:
            business_name = deal.get('business_name')
            location = deal.get('location', '').lower()
            deal_text = deal.get('deal', '').lower()
            
            # Skip if no business name
            if not business_name:
                continue
            
            # Check if this is an Austin/Texas location
            is_austin = any(indicator in location or indicator in deal_text for indicator in austin_indicators)
            
            # Also check for American-style addresses with numbers and street names
            is_american_address = False
            if re.search(r'\d+\s+\w+\s+(st|ave|blvd|rd|dr|ln|way)', location):
                is_american_address = True
            
            # Delete if it's an Austin location or American-style address
            if is_austin or is_american_address:
                try:
                    deal_db.delete_deal(business_name)
                    deleted_count += 1
                    logger.info(f"Deleted Austin/Texas location: {business_name} - {location}")
                except Exception as e:
                    logger.error(f"Error deleting deal {business_name}: {str(e)}")
        
        logger.info(f"Removed {deleted_count} Austin/American locations from the dataset")
        flash(f"Successfully removed {deleted_count} Austin/American locations", "success")
        return redirect(url_for("home"))
    
    except Exception as e:
        logger.error(f"Error removing Austin locations: {str(e)}")
        flash(f"Error removing Austin locations: {str(e)}", "danger")
        return redirect(url_for("home"))

# Note: We've already defined page_not_found handler earlier

@app.route("/ai-recommendation", methods=["POST"])
def ai_recommendation():
    """Route to get AI-powered venue recommendations based on user preferences"""
    try:
        # Get user preferences from form
        preferences = {
            "district": request.form.get("district", ""),
            "price_range": request.form.get("price_range", ""),
            "vibe": request.form.get("vibe", ""),
            "drink_preference": request.form.get("drink_preference", ""),
            "food_preference": request.form.get("food_preference", ""),
            "time_preference": request.form.get("time_preference", "")
        }
        
        # Get all deals from database
        deals = deal_db.get_all_deals()
        
        # Get AI recommendations
        recommendations = get_ai_recommendation(preferences, deals)
        
        # Return results as JSON for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "status": "success",
                "recommendations": recommendations["recommendations"],
                "reasoning": recommendations["reasoning"]
            })
        
        # Otherwise return the recommendations in the home template
        flash("AI recommendations generated successfully!", "success")
        return render_template(
            "index.html", 
            deals=deals,
            recommendations=recommendations["recommendations"],
            recommendation_reasoning=recommendations["reasoning"],
            districts=sorted(list(set(d.get('district') for d in deals if d.get('district')))),
            current_district=preferences["district"],
            search_query="",
            deal_type=""
        )
        
    except Exception as e:
        logger.error(f"Error generating AI recommendations: {str(e)}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                "status": "error",
                "message": f"Error generating recommendations: {str(e)}"
            }), 500
            
        flash(f"Error generating recommendations: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route("/deal/<business_name>")
def view_deal(business_name):
    """Route to view a specific deal - with detailed information and custom image generation"""
    try:
        # Decode the business name (it will be URL-encoded)
        decoded_name = urllib.parse.unquote_plus(business_name)
        
        # Get the deal data
        deal_data = deal_db.get_deal(decoded_name)
        
        if not deal_data:
            flash("Deal not found", "danger")
            return redirect(url_for("home"))
        
        # Initialize variables for additional venue details
        venue_description = None
        venue_image = None
        venue_hours = None
        similar_deals = []
        
        # Generate AI description of the venue
        try:
            venue_description = get_venue_description(
                decoded_name,
                deal_data.get('deal', ''),
                deal_data.get('district', ''),
                deal_data.get('place_type', '')
            )
        except Exception as e:
            logger.error(f"Error generating AI venue description: {str(e)}")
            # Fall back to a simple description if AI fails
            if deal_data.get('place_type'):
                venue_description = f"A {deal_data.get('place_type')} with special happy hour offers. Located in {deal_data.get('district', 'Berlin')}."
        
        # Look for similar deals (strictly showing only same district)
        try:
            all_deals = deal_db.get_all_deals()
            
            # Clean the dataset - filter out non-Berlin locations
            berlin_deals = []
            for deal in all_deals:
                location = deal.get('location', '').lower()
                if 'berlin' in location or deal.get('district'):
                    berlin_deals.append(deal)
                    
            # Find deals in the same district - ONLY show deals from the same district
            similar_deals = []
            if deal_data.get('district'):
                district_deals = [d for d in berlin_deals if 
                                 d.get('district') == deal_data.get('district') and 
                                 d.get('business_name') != decoded_name]
                
                # Get up to 4 similar deals from the same district only
                similar_deals = district_deals[:4]
            
            # We no longer show random deals from other districts
            # If there are no other deals in this district, the section won't show
        except Exception as e:
            logger.error(f"Error getting similar deals: {str(e)}")
            
        # Generate a venue image if not already available
        if not venue_image:
            try:
                # Generate an image for the venue using the deal information
                venue_image_bytes = generate_venue_image(
                    decoded_name,
                    deal_data.get('deal', 'Happy Hour Deal'),
                    deal_data.get('location', 'Berlin'),
                    deal_data.get('district'),
                    deal_data.get('rating')
                )
                
                if venue_image_bytes:
                    # Convert to base64 for embedding in HTML
                    venue_image = base64.b64encode(venue_image_bytes).decode('utf-8')
            except Exception as e:
                logger.error(f"Error generating venue image: {str(e)}")
        
        # Return the deal detail template with all the gathered information
        return render_template(
            "deal_detail.html", 
            deal=deal_data,
            venue_description=venue_description,
            venue_image=venue_image,
            venue_hours=venue_hours,
            similar_deals=similar_deals
        )
    except Exception as e:
        logger.error(f"Error viewing deal: {str(e)}")
        flash(f"Error viewing deal: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.errorhandler(500)
def internal_server_error(e):
    """Handle 500 errors"""
    return render_template("index.html", deals=[], error="Internal server error"), 500

def generate_venue_image(business_name, deal_text, location, district=None, rating=None):
    """
    Generate a stylized image for a venue detail page
    
    Args:
        business_name (str): Name of the business
        deal_text (str): The deal description
        location (str): Location of the business
        district (str, optional): Berlin district
        rating (float, optional): Google Maps rating
        
    Returns:
        bytes: Image data in bytes
    """
    try:
        # Create a 1200x630 image (16:9 aspect ratio)
        width, height = 1200, 630
        
        # Create a base image with a dark gradient background
        img = Image.new('RGB', (width, height), color=(33, 37, 41))
        draw = ImageDraw.Draw(img)
        
        # Create a nice gradient background
        for y in range(height):
            # Create a gradient from dark to slightly less dark
            r = int(28 + (y / height) * 25)
            g = int(30 + (y / height) * 25)
            b = int(35 + (y / height) * 25)
            draw.line([(0, y), (width, y)], fill=(r, g, b), width=1)
        
        # Try to load fonts, fallback to default if not available
        try:
            title_font = ImageFont.truetype("Arial Bold.ttf", 60)
            subtitle_font = ImageFont.truetype("Arial.ttf", 36)
            deal_font = ImageFont.truetype("Arial.ttf", 48) 
            info_font = ImageFont.truetype("Arial.ttf", 32)
        except IOError:
            try:
                # Try with different font names
                title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 60)
                subtitle_font = ImageFont.truetype("DejaVuSans.ttf", 36)
                deal_font = ImageFont.truetype("DejaVuSans.ttf", 48)
                info_font = ImageFont.truetype("DejaVuSans.ttf", 32)
            except IOError:
                # Fallback to default font
                title_font = ImageFont.load_default()
                subtitle_font = ImageFont.load_default()
                deal_font = ImageFont.load_default()
                info_font = ImageFont.load_default()
        
        # Add a stylish header bar with gradient
        header_height = 120
        for y in range(header_height):
            # Create a gradient from primary color to secondary color
            r = int(139 - (y / header_height) * 56)
            g = int(38 + (y / header_height) * 158)
            b = int(53 + (y / header_height) * 129)
            draw.line([(0, y), (width, y)], fill=(r, g, b), width=1)
        
        # Draw a decorative line pattern in the header
        for x in range(0, width, 40):
            draw.line([(x, 0), (x + 20, header_height)], fill=(255, 255, 255, 128), width=2)
        
        # Draw logo text in header
        logo_text = "BACKYARD BILLBOARDS"
        logo_width = draw.textlength(logo_text, font=subtitle_font)
        draw.text(
            ((width - logo_width) // 2, 40),
            logo_text,
            font=subtitle_font,
            fill=(255, 255, 255)  # White text
        )
        
        # Add visual decorative elements 
        # Draw some circles in the background for visual interest
        circle_colors = [(146, 43, 60, 128), (46, 196, 182, 128), (231, 111, 81, 128)]
        for i in range(5):
            # Draw random size circles at random positions
            size = random.randint(50, 150)
            x = random.randint(0, width)
            y = random.randint(header_height + 100, height - 100)
            color = random.choice(circle_colors)
            draw.ellipse([(x - size // 2, y - size // 2), (x + size // 2, y + size // 2)], 
                         fill=color)
        
        # Draw business name with a subtle shadow for depth
        # Truncate if too long
        if len(business_name) > 25:
            business_name = business_name[:22] + "..."
            
        business_width = draw.textlength(business_name, font=title_font)
        
        # Draw shadow
        draw.text(
            ((width - business_width) // 2 + 2, 160 + 2),
            business_name,
            font=title_font,
            fill=(0, 0, 0, 180)  # Semi-transparent black for shadow
        )
        
        # Draw text
        draw.text(
            ((width - business_width) // 2, 160),
            business_name,
            font=title_font,
            fill=(248, 249, 250)  # Light color
        )
        
        # Add a decorative line under the name
        line_width = min(business_width + 100, width - 200)
        draw.line(
            [((width - line_width) // 2, 240), ((width + line_width) // 2, 240)],
            fill=(46, 196, 182),  # Teal accent color
            width=3
        )
        
        # Format and draw deal text - intelligently wrap the text
        max_chars_per_line = 40
        formatted_deal = []
        words = deal_text.split()
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) <= max_chars_per_line:
                current_line.append(word)
            else:
                formatted_deal.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            formatted_deal.append(' '.join(current_line))
        
        # Limit to 2 lines maximum to avoid crowding
        if len(formatted_deal) > 2:
            formatted_deal = formatted_deal[:1] 
            formatted_deal.append(formatted_deal[0] + "...")
        
        # Create a semi-transparent background for the deal text
        deal_box_padding = 20
        deal_box_height = len(formatted_deal) * 55 + deal_box_padding * 2
        deal_box_y = 270
        
        # Draw the semitransparent rectangle
        draw.rectangle(
            (100, deal_box_y, width - 100, deal_box_y + deal_box_height),
            fill=(0, 0, 0, 80),  # Semi-transparent black
            outline=(46, 196, 182),  # Teal accent color
            width=2
        )
        
        # Draw the deal text on the semi-transparent background
        deal_y = deal_box_y + deal_box_padding
        for line in formatted_deal:
            line_width = draw.textlength(line, font=deal_font)
            draw.text(
                ((width - line_width) // 2, deal_y),
                line,
                font=deal_font,
                fill=(248, 249, 250)  # Light text
            )
            deal_y += 55
        
        # Draw a decorative icon to represent deals
        icon_size = 40
        icon_x = (width - icon_size) // 2
        icon_y = deal_box_y + deal_box_height + 20
        
        # Draw simple drink icon (a cocktail glass)
        draw.polygon(
            [(icon_x, icon_y), (icon_x + icon_size, icon_y), (icon_x + icon_size//2, icon_y + icon_size)],
            fill=(231, 111, 81)  # Accent color for icon
        )
        draw.rectangle(
            (icon_x + icon_size//4, icon_y + icon_size, icon_x + 3*icon_size//4, icon_y + icon_size + 10),
            fill=(231, 111, 81)  # Same accent color for stem
        )
        
        # Draw location information
        location_y = deal_box_y + deal_box_height + 80
        
        # Format the location text
        location_text = location
        if district:
            location_text = f"{district} · {location}"
            
        location_width = draw.textlength(location_text, font=info_font)
        
        # Draw a pin icon next to location
        pin_radius = 10
        pin_x = (width - location_width) // 2 - 30
        pin_y = location_y + 15
        
        # Draw the pin head
        draw.ellipse(
            [(pin_x - pin_radius, pin_y - pin_radius), (pin_x + pin_radius, pin_y + pin_radius)],
            fill=(220, 53, 69)  # Red for the pin
        )
        
        # Draw the pin point
        draw.polygon(
            [(pin_x - pin_radius, pin_y), (pin_x + pin_radius, pin_y), (pin_x, pin_y + pin_radius*2)],
            fill=(220, 53, 69)  # Red for the pin
        )
        
        # Draw the location text
        draw.text(
            ((width - location_width) // 2, location_y),
            location_text,
            font=info_font,
            fill=(248, 249, 250)  # Light text
        )
        
        # Draw rating if available
        if rating:
            rating_y = location_y + 50
            rating_text = f"Rating: {rating} "
            
            # Add stars based on rating
            full_stars = int(rating)
            has_half_star = rating - full_stars >= 0.5
            
            rating_width = draw.textlength(rating_text, font=info_font)
            star_width = draw.textlength("★", font=info_font)
            total_width = rating_width + (full_stars * star_width) + (1 * star_width if has_half_star else 0)
            
            # Draw the text
            draw.text(
                ((width - total_width) // 2, rating_y),
                rating_text,
                font=info_font,
                fill=(248, 249, 250)  # Light text
            )
            
            # Draw the stars
            star_x = (width - total_width) // 2 + rating_width
            for i in range(full_stars):
                draw.text(
                    (star_x, rating_y),
                    "★",
                    font=info_font,
                    fill=(255, 193, 7)  # Yellow for stars
                )
                star_x += star_width
                
            # Draw half star if needed
            if has_half_star:
                draw.text(
                    (star_x, rating_y),
                    "★",  # We'll use the same star but make it partially transparent
                    font=info_font,
                    fill=(255, 193, 7, 128)  # Semi-transparent yellow
                )
        
        # Add a footer with website and design elements
        footer_y = height - 60
        footer_text = "www.backyardbillboards.de"
        footer_width = draw.textlength(footer_text, font=subtitle_font)
        
        # Draw a decorative line above the footer
        draw.line(
            [(100, footer_y - 20), (width - 100, footer_y - 20)],
            fill=(173, 181, 189),  # Gray for line
            width=1
        )
        
        # Draw the footer text
        draw.text(
            ((width - footer_width) // 2, footer_y),
            footer_text,
            font=subtitle_font,
            fill=(173, 181, 189)  # Gray text
        )
        
        # Convert the image to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
    except Exception as e:
        logger.error(f"Error generating venue image: {str(e)}")
        # Return default image path if there's an error
        with open("static/img/og-default.jpg", "rb") as f:
            return f.read()

def generate_og_deal_image(business_name, deal_text, location, district=None, rating=None):
    """
    Generate a dynamic Open Graph image for a specific deal
    
    Args:
        business_name (str): Name of the business
        deal_text (str): The deal description
        location (str): Location of the business
        district (str, optional): Berlin district
        rating (float, optional): Google Maps rating
        
    Returns:
        bytes: Image data in bytes
    """
    try:
        # Create a 1200x630 image (standard OG image size)
        width, height = 1200, 630
        img = Image.new('RGB', (width, height), color=(33, 37, 41))  # Dark background
        
        # Draw on the image
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts, fallback to default if not available
        try:
            title_font = ImageFont.truetype("Arial.ttf", 50)
            deal_font = ImageFont.truetype("Arial.ttf", 40)
            location_font = ImageFont.truetype("Arial.ttf", 30)
            subtitle_font = ImageFont.truetype("Arial.ttf", 24)
        except IOError:
            # Fallback to default font
            title_font = ImageFont.load_default()
            deal_font = ImageFont.load_default()
            location_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
        
        # Background styling - add a gradient effect
        for y in range(height):
            # Create a gradient from dark to slightly lighter
            r = int(33 + (y / height) * 20)
            g = int(37 + (y / height) * 20)
            b = int(41 + (y / height) * 20)
            draw.line([(0, y), (width, y)], fill=(r, g, b), width=1)
        
        # Add a header bar
        header_height = 100
        draw.rectangle(
            (0, 0, width, header_height),
            fill=(220, 53, 69)  # Bootstrap danger red
        )
        
        # Draw logo text in header
        logo_text = "BACKYARD BILLBOARDS"
        logo_width = draw.textlength(logo_text, font=subtitle_font)
        logo_position = ((width - logo_width) // 2, 40)
        draw.text(
            logo_position,
            logo_text,
            font=subtitle_font,
            fill=(255, 255, 255)  # White text
        )
        
        # Draw business name - truncate if too long
        if len(business_name) > 30:
            business_name = business_name[:27] + "..."
        
        business_width = draw.textlength(business_name, font=title_font)
        business_position = ((width - business_width) // 2, 150)
        draw.text(
            business_position,
            business_name,
            font=title_font,
            fill=(248, 249, 250)  # Light text
        )
        
        # Format and draw deal text - wrap if needed
        max_chars_per_line = 40
        formatted_deal = []
        words = deal_text.split()
        current_line = []
        
        for word in words:
            if len(' '.join(current_line + [word])) <= max_chars_per_line:
                current_line.append(word)
            else:
                formatted_deal.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            formatted_deal.append(' '.join(current_line))
        
        # Limit to 3 lines maximum
        if len(formatted_deal) > 3:
            formatted_deal = formatted_deal[:2]
            formatted_deal.append(formatted_deal[-1] + "...")
        
        # Draw the deal text
        deal_y = 240
        for line in formatted_deal:
            line_width = draw.textlength(line, font=deal_font)
            line_position = ((width - line_width) // 2, deal_y)
            draw.text(
                line_position,
                line,
                font=deal_font,
                fill=(248, 249, 250)  # Light text
            )
            deal_y += 50
        
        # Draw location
        location_text = location
        if district:
            location_text += f" - {district}"
            
        location_width = draw.textlength(location_text, font=location_font)
        location_position = ((width - location_width) // 2, 400)
        draw.text(
            location_position,
            location_text,
            font=location_font,
            fill=(248, 249, 250)  # Light gray text
        )
        
        # Draw rating if available
        if rating:
            rating_text = f"Rating: {rating} "
            rating_text += "★" * int(rating)
            
            rating_width = draw.textlength(rating_text, font=subtitle_font)
            rating_position = ((width - rating_width) // 2, 470)
            draw.text(
                rating_position,
                rating_text,
                font=subtitle_font,
                fill=(255, 193, 7)  # Yellow text for stars
            )
        
        # Add website URL at the bottom
        site_text = "www.backyardbillboards.com"
        site_width = draw.textlength(site_text, font=subtitle_font)
        site_position = ((width - site_width) // 2, height - 50)
        draw.text(
            site_position,
            site_text,
            font=subtitle_font,
            fill=(173, 181, 189)  # Gray text
        )
        
        # Convert the image to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return img_byte_arr.getvalue()
    
    except Exception as e:
        logger.error(f"Error generating OG deal image: {str(e)}")
        # Return default image path if there's an error
        with open("static/img/og-default.jpg", "rb") as f:
            return f.read()

@app.route('/og-image/<business_name>')
def og_image(business_name):
    """
    Route to generate and serve a dynamic Open Graph image for a specific deal
    
    Args:
        business_name (str): Name of the business
        
    Returns:
        Response: Image response
    """
    try:
        # Decode the business name (it will be URL-encoded)
        decoded_name = urllib.parse.unquote_plus(business_name)
        
        # Get the deal data
        deal_data = deal_db.get_deal(decoded_name)
        
        if not deal_data:
            # Return default image if deal not found
            with open("static/img/og-default.jpg", "rb") as f:
                return send_file(
                    io.BytesIO(f.read()),
                    mimetype='image/jpeg'
                )
        
        # Generate an image for this specific deal
        img_data = generate_og_deal_image(
            decoded_name,
            deal_data.get('deal', 'Happy Hour Deal'),
            deal_data.get('location', 'Berlin'),
            district=deal_data.get('district'),
            rating=deal_data.get('rating')
        )
        
        # Return the image
        response = make_response(send_file(
            io.BytesIO(img_data),
            mimetype='image/jpeg'
        ))
        response.headers['Cache-Control'] = 'public, max-age=86400'  # Cache for 24 hours
        return response
    
    except Exception as e:
        logger.error(f"Error generating OG image for {business_name}: {str(e)}")
        # Return default image on error
        with open("static/img/og-default.jpg", "rb") as f:
            return send_file(
                io.BytesIO(f.read()),
                mimetype='image/jpeg'
            )
