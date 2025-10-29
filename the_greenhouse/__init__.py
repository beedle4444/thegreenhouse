import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

load_dotenv()

# Initialize extensions without app
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    
    # Database configuration - works with both local MySQL and Heroku PostgreSQL
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Heroku PostgreSQL
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    else:
        # Local MySQL
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/greenhouse_db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'users.login'
    
    # Import and register blueprints
    from the_greenhouse.core.views import core
    from the_greenhouse.error_pages.handlers import error_pages
    from the_greenhouse.users.views import users
    from the_greenhouse.posts.views import posts
    
    app.register_blueprint(posts)
    app.register_blueprint(users)
    app.register_blueprint(error_pages)
    app.register_blueprint(core)
    
    return app