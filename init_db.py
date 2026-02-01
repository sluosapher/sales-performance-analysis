import os
from models import db, User
from flask import Flask
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

def init_database_and_create_users():
    """Initialize the database, create tables, and add test users."""
    # Ensure data directory exists before any database operations
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)

    # Setup a minimal Flask app for context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(data_dir, "users.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt.init_app(app)

    with app.app_context():
        db.create_all() # Create tables defined in models.py
        print("Database initialized successfully")

        # Create test users only if they don't already exist
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                role='admin',
                can_upload=True,
                can_list_results=True
            )
            # ensure hash is utf-8 encoded string
            admin.password_hash = bcrypt.generate_password_hash('admin123').decode('utf-8')
            admin.generate_token()
            db.session.add(admin)
            print(f"  Admin user created: admin / admin123 (token: {admin.secret_token})")

        if not User.query.filter_by(username='user').first():
            user = User(
                username='user',
                role='user',
                can_upload=False,
                can_list_results=True
            )
            # ensure hash is utf-8 encoded string
            user.password_hash = bcrypt.generate_password_hash('user123').decode('utf-8')
            user.generate_token()
            db.session.add(user)
            print(f"  Regular user created: user / user123 (token: {user.secret_token})")

        if not User.query.filter_by(username='uploader').first():
            uploader = User(
                username='uploader',
                role='user',
                can_upload=True,
                can_list_results=True
            )
            # ensure hash is utf-8 encoded string
            uploader.password_hash = bcrypt.generate_password_hash('upload123').decode('utf-8')
            uploader.generate_token()
            db.session.add(uploader)
            print(f"  Uploader user created: uploader / upload123 (token: {uploader.secret_token})")

        db.session.commit()
        print("Test users added/ensured.")

if __name__ == "__main__":
    init_database_and_create_users()
