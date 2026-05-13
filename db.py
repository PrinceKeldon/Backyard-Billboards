import os
import logging
import uuid
from datetime import datetime
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor

load_dotenv()
logger = logging.getLogger(__name__)

class DealDB:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL') or os.environ.get('NETLIFY_DB_URL')
        if not self.database_url:
            raise RuntimeError('DATABASE_URL or NETLIFY_DB_URL must be configured to use Netlify Database.')

    def _get_conn(self):
        return psycopg2.connect(self.database_url, cursor_factory=RealDictCursor)

    def _fetch_one(self, query, params=None):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchone()

    def _fetch_all(self, query, params=None):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                return cur.fetchall()

    def _execute(self, query, params=None, fetchone=False, fetchall=False):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                if fetchone:
                    return cur.fetchone()
                if fetchall:
                    return cur.fetchall()
                return cur.rowcount

    def _normalize_name(self, name):
        return name.strip().lower() if isinstance(name, str) else ''

    def _timestamp(self):
        return datetime.utcnow()

    def add_user(self, username, email, password_hash, role='user'):
        try:
            if not username or not email or not password_hash:
                return False
            if self._fetch_one('SELECT 1 FROM users WHERE username = %s LIMIT 1', (username,)):
                return False
            if self._fetch_one('SELECT 1 FROM users WHERE email = %s LIMIT 1', (email,)):
                return False
            query = '''
                INSERT INTO users (username, email, password_hash, role, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            '''
            params = (username, email, password_hash, role, self._timestamp(), self._timestamp())
            self._execute(query, params)
            return True
        except Exception as e:
            logger.error(f'Error adding user: {e}')
            return False

    def get_user(self, username):
        try:
            return self._fetch_one('SELECT * FROM users WHERE username = %s LIMIT 1', (username,))
        except Exception as e:
            logger.error(f'Error fetching user: {e}')
            return None

    def get_venue_id_by_name(self, business_name):
        try:
            if not business_name:
                return None
            normalized = self._normalize_name(business_name)
            row = self._fetch_one('SELECT id FROM venues WHERE name_lower = %s LIMIT 1', (normalized,))
            return row.get('id') if row else None
        except Exception as e:
            logger.error(f'Error finding venue by name: {e}')
            return None

    def get_venue(self, venue_id):
        try:
            return self._fetch_one('SELECT * FROM venues WHERE id = %s LIMIT 1', (venue_id,))
        except Exception as e:
            logger.error(f'Error fetching venue: {e}')
            return None

    def get_all_deals(self):
        try:
            return self._fetch_all('SELECT * FROM venues ORDER BY created_at DESC') or []
        except Exception as e:
            logger.error(f'Error fetching all deals: {e}')
            return []

    def get_hidden_gems(self):
        try:
            return self._fetch_all('SELECT * FROM venues WHERE is_hidden_gem = TRUE ORDER BY votes DESC') or []
        except Exception as e:
            logger.error(f'Error fetching hidden gems: {e}')
            return []

    def search_venues(self, query=None, district=None):
        try:
            query = self._normalize_name(query) if query else ''
            venues = self.get_all_deals()
            results = []
            for venue in venues:
                if district and venue.get('district', '').lower() != district.strip().lower():
                    continue
                if query:
                    name_matches = query in self._normalize_name(venue.get('name', ''))
                    district_matches = query in self._normalize_name(venue.get('district', ''))
                    description_matches = query in self._normalize_name(venue.get('description', ''))
                    if not (name_matches or district_matches or description_matches):
                        continue
                results.append(venue)
            return results
        except Exception as e:
            logger.error(f'Error searching venues: {e}')
            return []

    def get_late_night_deals(self):
        try:
            keywords = ['22:00', '10pm', '10 pm', 'late night', 'after 10', 'night']
            venues = self.get_all_deals()
            return [venue for venue in venues if any(keyword in (venue.get('deal') or '').lower() for keyword in keywords)]
        except Exception as e:
            logger.error(f'Error fetching late night deals: {e}')
            return []

    def create_venue(self, name, address, owner_id, district, deal, is_hidden_gem=False, hidden_gem_description='', hidden_gem_tips='', has_accurate_location=False):
        try:
            if not name or not address:
                return None
            venue_id = str(uuid.uuid4())
            query = '''
                INSERT INTO venues (
                    id, name, name_lower, address, owner_id, district, location, deal,
                    votes, created_at, updated_at, is_hidden_gem, hidden_gem_description,
                    hidden_gem_tips, has_accurate_location, opening_hours, happy_hour_price,
                    latitude, longitude, description, place_type, rating
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            '''
            params = (
                venue_id,
                name,
                self._normalize_name(name),
                address,
                owner_id,
                district,
                address,
                deal,
                0,
                self._timestamp(),
                self._timestamp(),
                bool(is_hidden_gem),
                hidden_gem_description,
                hidden_gem_tips,
                bool(has_accurate_location),
                '',
                '',
                None,
                None,
                '',
                '',
                None,
            )
            row = self._fetch_one(query, params)
            return row.get('id') if row else None
        except Exception as e:
            logger.error(f'Error creating venue: {e}')
            return None

    def update_venue_deal(self, venue_id, deal, name=None, address=None, district=None, has_accurate_location=None):
        try:
            columns = ['updated_at = %s']
            params = [self._timestamp()]
            if name is not None:
                columns.append('name = %s')
                columns.append('name_lower = %s')
                params.extend([name, self._normalize_name(name)])
            if address is not None:
                columns.append('address = %s')
                columns.append('location = %s')
                params.extend([address, address])
            if district is not None:
                columns.append('district = %s')
                params.append(district)
            if deal is not None:
                columns.append('deal = %s')
                params.append(deal)
            if has_accurate_location is not None:
                columns.append('has_accurate_location = %s')
                params.append(bool(has_accurate_location))
            query = f"UPDATE venues SET {', '.join(columns)} WHERE id = %s"
            params.append(venue_id)
            self._execute(query, tuple(params))
            return True
        except Exception as e:
            logger.error(f'Error updating venue deal: {e}')
            return False

    def update_venue_details(self, venue_id, updates):
        try:
            columns = ['updated_at = %s']
            params = [self._timestamp()]
            if 'opening_hours' in updates:
                columns.append('opening_hours = %s')
                params.append(updates.get('opening_hours', ''))
            if 'happy_hour_price' in updates:
                columns.append('happy_hour_price = %s')
                params.append(updates.get('happy_hour_price', ''))
            if 'latitude' in updates:
                latitude = updates.get('latitude')
                columns.append('latitude = %s')
                params.append(float(latitude) if latitude not in [None, ''] else None)
            if 'longitude' in updates:
                longitude = updates.get('longitude')
                columns.append('longitude = %s')
                params.append(float(longitude) if longitude not in [None, ''] else None)
            if 'description' in updates:
                columns.append('description = %s')
                params.append(updates.get('description', ''))
            query = f"UPDATE venues SET {', '.join(columns)} WHERE id = %s"
            params.append(venue_id)
            self._execute(query, tuple(params))
            return True
        except Exception as e:
            logger.error(f'Error updating venue details: {e}')
            return False

    def upvote_venue(self, venue_id):
        try:
            query = '''
                UPDATE venues
                SET votes = votes + 1, updated_at = %s
                WHERE id = %s
                RETURNING *
            '''
            return self._fetch_one(query, (self._timestamp(), venue_id))
        except Exception as e:
            logger.error(f'Error upvoting venue: {e}')
            return None

    def get_deals_by_venue(self, venue_id):
        try:
            return self._fetch_all('SELECT * FROM deals WHERE venue_id = %s ORDER BY created_at DESC', (venue_id,)) or []
        except Exception as e:
            logger.error(f'Error fetching deals for venue: {e}')
            return []

    def create_deal(self, venue_id, deal_data):
        try:
            if not self.get_venue(venue_id):
                return None
            deal_id = str(uuid.uuid4())
            query = '''
                INSERT INTO deals (
                    id, venue_id, name, days, start_time, end_time, discount,
                    description, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
            '''
            params = (
                deal_id,
                venue_id,
                deal_data.get('name', ''),
                deal_data.get('days', ''),
                deal_data.get('start_time', ''),
                deal_data.get('end_time', ''),
                int(deal_data.get('discount', 0)) if deal_data.get('discount') is not None else 0,
                deal_data.get('description', ''),
                self._timestamp(),
                self._timestamp(),
            )
            return self._fetch_one(query, params)
        except Exception as e:
            logger.error(f'Error creating deal: {e}')
            return None

    def update_deal(self, venue_id, deal_id, updates):
        try:
            deal = self.get_deal(deal_id)
            if not deal or str(deal.get('venue_id')) != str(venue_id):
                return False
            columns = ['updated_at = %s']
            params = [self._timestamp()]
            for key, value in updates.items():
                if key in ['name', 'days', 'start_time', 'end_time', 'description']:
                    columns.append(f'{key} = %s')
                    params.append(value)
                elif key == 'discount':
                    columns.append('discount = %s')
                    params.append(int(value) if value is not None else deal.get('discount', 0))
            query = f"UPDATE deals SET {', '.join(columns)} WHERE id = %s"
            params.append(deal_id)
            self._execute(query, tuple(params))
            return True
        except Exception as e:
            logger.error(f'Error updating deal: {e}')
            return False

    def delete_deal(self, venue_id, deal_id):
        try:
            deal = self.get_deal(deal_id)
            if not deal or str(deal.get('venue_id')) != str(venue_id):
                return False
            rowcount = self._execute('DELETE FROM deals WHERE id = %s', (deal_id,))
            return rowcount > 0
        except Exception as e:
            logger.error(f'Error deleting deal: {e}')
            return False

    def get_deal(self, deal_id):
        try:
            return self._fetch_one('SELECT * FROM deals WHERE id = %s LIMIT 1', (deal_id,))
        except Exception as e:
            logger.error(f'Error fetching deal: {e}')
            return None

    def get_venue_by_owner(self, owner_id):
        try:
            return self._fetch_one('SELECT * FROM venues WHERE owner_id = %s LIMIT 1', (owner_id,))
        except Exception as e:
            logger.error(f'Error getting venue by owner: {e}')
            return None

    def claim_venue(self, venue_id, owner_id):
        try:
            self._execute(
                'UPDATE venues SET owner_id = %s, updated_at = %s WHERE id = %s',
                (owner_id, self._timestamp(), venue_id),
            )
            return True
        except Exception as e:
            logger.error(f'Error claiming venue: {e}')
            return False

    def get_user_venues(self, owner_id):
        try:
            return self._fetch_all('SELECT * FROM venues WHERE owner_id = %s ORDER BY created_at DESC', (owner_id,)) or []
        except Exception as e:
            logger.error(f'Error fetching user venues: {e}')
            return []

