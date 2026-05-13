import os
import logging
import time
import urllib.parse
import io
import random
import base64
import json
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, make_response
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import User
from db import DealDB
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
os.environ["DEFAULT_LOCATION"] = "Berlin, Germany"
os.environ["RESTRICT_TO_BERLIN"] = "true"

# Simple cache implementation to reduce database calls
cache = {
    'deals': [],
    'hidden_gems': [], 
    'late_night_deals': [],
    'districts': [],
    'all_districts': [],
    'last_updated': 0
}

# Cache duration in seconds
CACHE_DURATION = 300  # 5 minutes

def clear_cache(keys=None):
    global cache
    if keys is None:
        cache = {
            'deals': [],
            'hidden_gems': [],
            'late_night_deals': [], 
            'districts': [],
            'all_districts': [],
            'last_updated': 0
        }
        logger.debug("All application cache cleared")
    else:
        if isinstance(keys, str):
            keys = [keys]
        for key in keys:
            if key in cache:
                if key == 'last_updated':
                    cache[key] = 0
                else:
                    cache[key] = []
                logger.debug(f"Cache '{key}' cleared")

def get_cached_data(key, fetch_func, *args, **kwargs):
    global cache
    current_time = time.time()
    if current_time - cache['last_updated'] > CACHE_DURATION:
        clear_cache()
        cache['last_updated'] = current_time
        data = fetch_func(*args, **kwargs)
        cache[key] = data if data is not None else []
        logger.debug(f"Cache '{key}' refreshed")
    elif not cache[key]:
        data = fetch_func(*args, **kwargs)
        cache[key] = data if data is not None else []
        logger.debug(f"Cache '{key}' refreshed while maintaining other cached data")
    return cache[key]

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "happy-hour-hub-local-dev-secret-key")
app.config["PROPAGATE_EXCEPTIONS"] = True
app.config["PREFERRED_URL_SCHEME"] = "https"

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

def venue_owner_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if getattr(current_user, 'role', 'user') != 'venue_owner':
            flash("Only venue owners can access this page.", "danger")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_user():
    return {
        'debug_mode': app.debug
    }

from utils import get_time_ago
app.jinja_env.filters['to_time_ago'] = get_time_ago

@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
    return render_template('error.html', error=str(e)), 500

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="Page not found"), 404

@app.route('/health')
def health_check():
    try:
        deals_count = len(deal_db.get_all_deals())
        gems_count = len(deal_db.get_hidden_gems())
        return jsonify({
            "status": "ok", 
            "timestamp": datetime.now().isoformat(),
            "app_name": "Happy Hour Hub",
            "version": "1.0.0",
            "db_status": "connected",
            "deals_count": deals_count,
            "hidden_gems_count": gems_count
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.template_filter('urlencode')
def urlencode_filter(s):
    if isinstance(s, str):
        return urllib.parse.quote_plus(s)
    return ''

deal_db = DealDB()

@app.route("/")
def home():
    try:
        deals = get_cached_data('deals', deal_db.get_all_deals)
        filtered_deals = []
        for deal in deals:
            location = deal.get('location', '').lower()
            deal_text = deal.get('deal', '')
            if '$' in deal_text: continue
            if 'berlin' in location or deal.get('district'):
                filtered_deals.append(deal)
        
        district = request.args.get('district', '')
        search_query = request.args.get('search', '')
        deal_type = request.args.get('deal_type', '')
        
        if district:
            filtered_deals = [d for d in filtered_deals if d.get('district') and d.get('district').lower() == district.lower()]
        
        if search_query:
            search_query = search_query.lower()
            filtered_deals = [d for d in filtered_deals if 
                search_query in d.get('business_name', '').lower() or 
                search_query in d.get('deal', '').lower() or 
                search_query in d.get('location', '').lower() or
                (d.get('district') and search_query in d.get('district', '').lower())]
        
        all_districts = get_cached_data(
            'all_districts',
            lambda: sorted(list(set(d.get('district') for d in deals if d.get('district'))))
        )
        
        if district:
            def sort_key(deal):
                deal_district = deal.get("district", "")
                date = deal.get("scraped_at", "")
                return (1 if deal_district == district else 0, date if date else "")
            filtered_deals = sorted(filtered_deals, key=sort_key, reverse=True)
        else:
            filtered_deals = sorted(filtered_deals, key=lambda x: x.get("scraped_at", ""), reverse=True)
        
        hidden_gems_count = len(get_cached_data('hidden_gems', deal_db.get_hidden_gems))
        return render_template(
            "index.html", 
            deals=filtered_deals, 
            districts=all_districts, 
            current_district=district,
            search_query=search_query,
            deal_type=deal_type,
            hidden_gems_count=hidden_gems_count
        )
    except Exception as e:
        logger.error(f"Error retrieving deals: {str(e)}")
        return render_template("index.html", deals=[], districts=[], current_district=None, search_query='', deal_type='', hidden_gems_count=0)

@app.route('/preview')
def preview():
    sample_deals = [
        {
            'name': 'The Rusty Tap',
            'district': 'Kreuzberg',
            'deal': '2-for-1 craft beers Mon–Wed 5–8 PM',
            'location': 'Kreuzberg, Berlin',
            'deal_type': 'Drinks',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'name': 'Prenzlauer Garten',
            'district': 'Prenzlauer Berg',
            'deal': '€3 house wines + €4 cocktails during happy hour',
            'location': 'Prenzlauer Berg, Berlin',
            'deal_type': 'Wine & Cocktails',
            'created_at': datetime.utcnow().isoformat()
        },
        {
            'name': 'Neukölln Nook',
            'district': 'Neukölln',
            'deal': '50% off selected snacks and pints until 10 PM',
            'location': 'Neukölln, Berlin',
            'deal_type': 'Food & Drinks',
            'created_at': datetime.utcnow().isoformat()
        }
    ]
    hidden_gems_count = len(get_cached_data('hidden_gems', deal_db.get_hidden_gems))
    return render_template('preview.html', sample_deals=sample_deals, hidden_gems_count=hidden_gems_count)

@app.route("/late-night-deals")
def late_night_deals():
    try:
        deals = get_cached_data('late_night_deals', deal_db.get_late_night_deals)
        district = request.args.get('district', '')
        if district:
            deals = [d for d in deals if d.get('district') and d.get('district').lower() == district.lower()]
        all_districts = get_cached_data(
            'all_districts',
            lambda: sorted(list(set(d.get('district') for d in deal_db.get_all_deals() if d.get('district'))))
        )
        hidden_gems_count = len(get_cached_data('hidden_gems', deal_db.get_hidden_gems))
        return render_template('late_night_deals.html', deals=deals, districts=all_districts, current_district=district, hidden_gems_count=hidden_gems_count)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

@app.route("/hidden-gems")
def hidden_gems():
    try:
        district = request.args.get('district', '')
        all_gems = get_cached_data('hidden_gems', deal_db.get_hidden_gems)
        gems = [gem for gem in all_gems if gem.get('district') == district] if district else all_gems
        page = request.args.get('page', 1, type=int)
        per_page = 10
        total_gems = len(gems)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_gems = gems[start_idx:end_idx]
        pagination = {
            'has_prev': page > 1,
            'has_next': end_idx < total_gems,
            'prev_num': page - 1,
            'next_num': page + 1,
            'total_pages': (total_gems + per_page - 1) // per_page,
            'current_page': page
        }
        all_districts = get_cached_data(
            'all_districts',
            lambda: sorted(list(set(d.get('district') for d in deal_db.get_all_deals() if d.get('district'))))
        )
        pagination_url = url_for('hidden_gems') + (f"?district={district}" if district else "")
        return render_template('hidden_gems.html', hidden_gems=paginated_gems, districts=all_districts, current_district=district, pagination=pagination, current_page=page, pagination_url=pagination_url, hidden_gems_count=total_gems)
    except Exception as e:
        return render_template('error.html', error=str(e)), 500

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
        is_venue_owner = request.form.get('venue_owner') == 'true'
        role = 'venue_owner' if is_venue_owner else 'user'
        if not username or not email or not password:
            flash('All fields are required.', 'danger')
            return render_template('signup.html')
        if User.create(username, email, password, role):
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
def submit_deal():
    if request.method == "POST":
        try:
            business_name = request.form.get("business_name")
            deal = request.form.get("deal")
            location = request.form.get("location")
            district = request.form.get("district")
            has_accurate_location = True if request.form.get("accurate_location") == "on" else False
            is_hidden_gem = True if request.form.get("is_hidden_gem") == "on" else False
            hidden_gem_description = request.form.get("hidden_gem_description", "")
            hidden_gem_tips = request.form.get("hidden_gem_tips", "")
            submitted_by = current_user.username if current_user.is_authenticated else request.form.get("submitted_by", "")
            if not business_name or not deal or not location:
                flash("All fields are required", "danger")
                return redirect(url_for("submit_deal"))
            if is_hidden_gem and not hidden_gem_description:
                flash("Please provide a description of what makes this place special if marking it as a hidden gem", "warning")
                return redirect(url_for("submit_deal"))
            venue_id = deal_db.get_venue_id_by_name(business_name)
            if venue_id:
                deal_db.update_venue_deal(venue_id, deal, district=district, has_accurate_location=has_accurate_location)
            else:
                owner_id = current_user.username if current_user.is_authenticated and current_user.role == 'venue_owner' else 'community'
                deal_db.create_venue(name=business_name, address=location, owner_id=owner_id, district=district, deal=deal, is_hidden_gem=is_hidden_gem, hidden_gem_description=hidden_gem_description, hidden_gem_tips=hidden_gem_tips, has_accurate_location=has_accurate_location)
            clear_cache()
            flash("Deal submitted successfully!", "success")
            return redirect(url_for("home"))
        except Exception as e:
            logger.error(f"Error submitting deal: {str(e)}")
            flash(f"Error submitting deal: {str(e)}", "danger")
            return redirect(url_for("submit_deal"))
    berlin_districts = sorted(["Mitte", "Prenzlauer Berg", "Neukölln", "Wedding", "Kreuzberg", "Charlottenburg", "Schöneberg", "Friedrichshain", "Moabit", "Tiergarten", "Lichtenberg", "Köpenick", "Spandau", "Steglitz", "Marzahn", "Wilmersdorf", "Tempelhof", "Treptow", "Pankow", "Reinickendorf", "Zehlendorf"])
    try:
        deals = deal_db.get_all_deals()
        existing_districts = set(d.get('district') for d in deals if d.get('district'))
        for d in existing_districts:
            if d not in berlin_districts: berlin_districts.append(d)
        berlin_districts.sort()
    except: pass
    try:
        hidden_gems_count = len(deal_db.get_hidden_gems())
    except:
        hidden_gems_count = 0
    return render_template("submit.html", districts=berlin_districts, hidden_gems_count=hidden_gems_count)

@app.route("/manage-venue")
@venue_owner_required
def manage_venue():
    try:
        venues = deal_db.get_user_venues(current_user.username)
        venue = venues[0] if venues else None
        deals = deal_db.get_deals_by_venue(venue['id']) if venue else []
        return render_template("manage_venue.html", venue=venue, deals=deals)
    except Exception as e:
        logger.error(f"Error managing venue: {str(e)}")
        flash(f"Error managing venue: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route('/venues/details', methods=['POST'])
@venue_owner_required
def update_venue_details():
    try:
        venue = deal_db.get_venue_by_owner(current_user.username)
        if not venue:
            flash("You don't have a venue associated with your account.", "warning")
            return redirect(url_for('manage_venue'))
        updates = {
            'opening_hours': request.form.get('opening_hours', '').strip(),
            'happy_hour_price': request.form.get('happy_hour_price', '').strip(),
            'latitude': request.form.get('latitude', '').strip(),
            'longitude': request.form.get('longitude', '').strip(),
            'description': request.form.get('description', '').strip()
        }
        if deal_db.update_venue_details(venue['id'], updates):
            clear_cache()
            flash('Venue details updated successfully!', 'success')
        else:
            flash('Unable to update venue details.', 'danger')
        return redirect(url_for('manage_venue'))
    except Exception as e:
        logger.error(f"Error updating venue details: {str(e)}")
        flash(f"Error updating venue details: {str(e)}", 'danger')
        return redirect(url_for('manage_venue'))

@app.route('/venues/deals', methods=['POST'])
@venue_owner_required
def create_deal():
    try:
        venue = deal_db.get_venue_by_owner(current_user.username)
        if not venue:
            flash("You don't have a venue associated with your account.", "warning")
            return redirect(url_for('manage_venue'))

        deal_id = request.form.get('deal_id', '').strip() or None
        deal_name = request.form.get('deal_name', '').strip()
        days = request.form.get('days', '').strip()
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()
        discount = request.form.get('discount', '').strip()
        description = request.form.get('description', '').strip()

        if not deal_name or not days or not start_time or not end_time or not discount:
            flash('Please complete all required deal fields.', 'danger')
            return redirect(url_for('manage_venue'))

        try:
            discount_value = int(discount)
        except ValueError:
            flash('Discount must be a number.', 'danger')
            return redirect(url_for('manage_venue'))

        if discount_value < 1 or discount_value > 100:
            flash('Discount must be between 1 and 100.', 'danger')
            return redirect(url_for('manage_venue'))

        deal_data = {
            'name': deal_name,
            'days': days,
            'start_time': start_time,
            'end_time': end_time,
            'discount': discount_value,
            'description': description
        }

        if deal_id:
            success = deal_db.update_deal(venue['id'], deal_id, deal_data)
            message = 'Deal updated successfully!' if success else 'Unable to update deal.'
        else:
            success = deal_db.create_deal(venue['id'], deal_data)
            message = 'Deal created successfully!' if success else 'Unable to create deal.'

        if success:
            clear_cache()
            flash(message, 'success')
        else:
            flash(message, 'danger')
        return redirect(url_for('manage_venue'))
    except Exception as e:
        logger.error(f"Error creating or updating deal: {str(e)}")
        flash(f"Error creating or updating deal: {str(e)}", 'danger')
        return redirect(url_for('manage_venue'))

@app.route('/venues/deals/<deal_id>/delete', methods=['POST'])
@venue_owner_required
def delete_deal(deal_id):
    try:
        venue = deal_db.get_venue_by_owner(current_user.username)
        if not venue:
            flash("You don't have a venue associated with your account.", "warning")
            return redirect(url_for('manage_venue'))

        if deal_db.delete_deal(venue['id'], deal_id):
            clear_cache()
            flash('Deal deleted successfully!', 'success')
        else:
            flash('Unable to delete deal.', 'danger')
        return redirect(url_for('manage_venue'))
    except Exception as e:
        logger.error(f"Error deleting deal: {str(e)}")
        flash(f"Error deleting deal: {str(e)}", 'danger')
        return redirect(url_for('manage_venue'))

@app.route("/claim-venue", methods=["GET", "POST"])
@venue_owner_required
def claim_venue():
    try:
        search_query = request.args.get('venue_name', '').strip()
        district = request.args.get('district', '').strip()
        venues = []
        search_attempted = False
        if request.method == "POST":
            venue_id = request.form.get("venue_id")
            if not venue_id:
                flash("Venue selection is required to claim.", "danger")
                return redirect(url_for("claim_venue"))
            venue = deal_db.get_venue(venue_id)
            if not venue:
                flash("Venue not found in our directory.", "warning")
                return redirect(url_for("claim_venue"))
            if venue.get('owner_id') and venue.get('owner_id') != 'community':
                flash("This venue has already been claimed.", "warning")
                return redirect(url_for("claim_venue"))
            if deal_db.claim_venue(venue_id, current_user.username):
                flash(f"Successfully claimed {venue.get('name')}!", "success")
                return redirect(url_for("manage_venue"))
            flash("Unable to claim this venue. Please try again.", "danger")
            return redirect(url_for("claim_venue"))
        if search_query or district:
            venues = deal_db.search_venues(search_query, district)
            search_attempted = bool(search_query or district)
        berlin_districts = sorted(["Mitte", "Prenzlauer Berg", "Neukölln", "Wedding", "Kreuzberg", "Charlottenburg", "Schöneberg", "Friedrichshain", "Moabit", "Tiergarten", "Lichtenberg", "Köpenick", "Spandau", "Steglitz", "Marzahn", "Wilmersdorf", "Tempelhof", "Treptow", "Pankow", "Reinickendorf", "Zehlendorf"])
        return render_template("claim_venue.html", venues=venues, search_attempted=search_attempted, districts=berlin_districts, current_district=district)
    except Exception as e:
        logger.error(f"Error accessing claim page: {str(e)}")
        flash(f"Error accessing claim page: {str(e)}", "danger")
        return redirect(url_for("home"))

@app.route("/deal/<business_name>")
def view_deal(business_name):
    try:
        decoded_name = urllib.parse.unquote_plus(business_name)
        venue_id = deal_db.get_venue_id_by_name(decoded_name)
        if not venue_id:
            flash("Deal not found", "danger")
            return redirect(url_for("home"))
        deal_data = deal_db.get_venue(venue_id)
        if not deal_data:
            flash("Deal not found", "danger")
            return redirect(url_for("home"))
        venue_description = None
        venue_image = None
        similar_deals = []
        try:
            venue_description = get_venue_description(decoded_name, deal_data.get('deal', ''), deal_data.get('district', ''), deal_data.get('place_type', ''))
        except:
            venue_description = f"A {deal_data.get('place_type', 'venue')} with special happy hour offers. Located in {deal_data.get('district', 'Berlin')}."
        try:
            all_deals = deal_db.get_all_deals()
            berlin_deals = [d for d in all_deals if 'berlin' in d.get('location', '').lower() or d.get('district')]
            similar_deals = [d for d in berlin_deals if d.get('district') == deal_data.get('district') and d.get('venue_id') != venue_id][:4] if deal_data.get('district') else []
        except: pass
        try:
            venue_image_bytes = generate_venue_image(decoded_name, deal_data.get('deal', 'Happy Hour Deal'), deal_data.get('address', 'Berlin'), deal_data.get('district'), deal_data.get('rating'))
            venue_image = base64.b64encode(venue_image_bytes).decode('utf-8') if venue_image_bytes else None
        except: pass
        return render_template("deal_detail.html", deal=deal_data, venue_description=venue_description, venue_image=venue_image, similar_deals=similar_deals)
    except Exception as e:
        logger.error(f"Error viewing deal: {str(e)}")
        return redirect(url_for("home"))

@app.route("/upvote", methods=["POST"])
def upvote_deal():
    try:
        venue_id = request.form.get("venue_id")
        if not venue_id:
            return jsonify({"status": "error", "message": "Venue ID is required"}), 400
        result = deal_db.upvote_venue(venue_id)
        if result:
            clear_cache(['deals'])
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'success', 'vote_count': result.get('votes', 0), 'message': 'Upvoted!'})
            flash("Upvoted deal!", "success")
        else:
            return jsonify({"status": "error", "message": "Deal not found"}), 404
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    return redirect(url_for('home'))

def generate_venue_image(business_name, deal_text, location, district=None, rating=None):
    try:
        width, height = 1200, 630
        img = Image.new('RGB', (width, height), color=(33, 37, 41))
        draw = ImageDraw.Draw(img)
        for y in range(height):
            r, g, b = int(28 + (y/height)*25), int(30 + (y/height)*25), int(35 + (y/height)*25)
            draw.line([(0, y), (width, y)], fill=(r, g, b), width=1)
        try:
            title_font = ImageFont.truetype("Arial Bold.ttf", 60)
            subtitle_font = ImageFont.truetype("Arial.ttf", 36)
            deal_font = ImageFont.truetype("Arial.ttf", 48)
            info_font = ImageFont.truetype("Arial.ttf", 32)
        except:
            title_font = subtitle_font = deal_font = info_font = ImageFont.load_default()
        header_height = 120
        for y in range(header_height):
            r, g, b = int(139 - (y/header_height)*56), int(38 + (y/header_height)*158), int(53 + (y/header_height)*129)
            draw.line([(0, y), (width, y)], fill=(r, g, b), width=1)
        logo_text = "HAPPY HOUR HUB"
        logo_width = draw.textlength(logo_text, font=subtitle_font)
        draw.text(((width - logo_width) // 2, 40), logo_text, font=subtitle_font, fill=(255, 255, 255))
        if len(business_name) > 25: business_name = business_name[:22] + "..."
        business_width = draw.textlength(business_name, font=title_font)
        draw.text(((width - business_width) // 2 + 2, 160 + 2), business_name, font=title_font, fill=(0, 0, 0, 180))
        draw.text(((width - business_width) // 2, 160), business_name, font=title_font, fill=(248, 249, 250))
        line_width = min(business_width + 100, width - 200)
        draw.line([((width - line_width) // 2, 240), ((width + line_width) // 2, 240)], fill=(46, 196, 182), width=3)
        words = deal_text.split()
        formatted_deal = []
        current_line = []
        for word in words:
            if len(' '.join(current_line + [word])) <= 40: current_line.append(word)
            else:
                formatted_deal.append(' '.join(current_line))
                current_line = [word]
        if current_line: formatted_deal.append(' '.join(current_line))
        if len(formatted_deal) > 2: formatted_deal = [formatted_deal[0], formatted_deal[0] + "..."]
        deal_box_y = 270
        deal_box_height = len(formatted_deal) * 55 + 40
        draw.rectangle((100, deal_box_y, width - 100, deal_box_y + deal_box_height), fill=(0, 0, 0, 80), outline=(46, 196, 182), width=2)
        deal_y = deal_box_y + 20
        for line in formatted_deal:
            line_width = draw.textlength(line, font=deal_font)
            draw.text(((width - line_width) // 2, deal_y), line, font=deal_font, fill=(248, 249, 250))
            deal_y += 55
        location_text = f"{district} · {location}" if district else location
        location_width = draw.textlength(location_text, font=info_font)
        draw.text(((width - location_width) // 2, deal_box_y + deal_box_height + 80), location_text, font=info_font, fill=(248, 249, 250))
        
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='JPEG')
        return img_byte_arr.getvalue()
    except: return None

@app.errorhandler(500)
def internal_server_error(e):
    return render_template("index.html", deals=[], error="Internal server error"), 500
