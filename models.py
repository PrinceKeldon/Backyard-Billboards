
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from db import DealDB

class User(UserMixin):
    def __init__(self, id, username, email, password_hash):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        db = DealDB()
        user_data = db.get_user(user_id)
        if user_data:
            return User(
                id=user_id,
                username=user_data['username'],
                email=user_data.get('email', 'user@example.com'),  # Provide a default email if none exists
                password_hash=user_data['password_hash']
            )
        return None

    @staticmethod
    def create(username, email, password):
        db = DealDB()
        password_hash = generate_password_hash(password)
        return db.add_user(username, email, password_hash)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
