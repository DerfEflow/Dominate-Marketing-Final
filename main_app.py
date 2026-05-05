import os
import logging
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from dotenv import load_dotenv
from models import db, User

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def create_app():
    app = Flask(__name__)

    # Configuration
    app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key-change-in-production")
    # Railway (and some Heroku-style hosts) provide postgresql:// URLs.
    # SQLAlchemy 2.x requires postgresql+psycopg2:// — fix it automatically.
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///dominate.db')
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql+psycopg2://', 1)
    elif database_url.startswith('postgresql://'):
        database_url = database_url.replace('postgresql://', 'postgresql+psycopg2://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions
    db.init_app(app)

    # Setup Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # type: ignore
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # Register Auth blueprint
    from auth import auth
    app.register_blueprint(auth, url_prefix='/auth')

    # Register Dashboard blueprint
    try:
        from dashboard import dashboard_bp
        app.register_blueprint(dashboard_bp)
    except ImportError as e:
        logging.warning(f"Could not import dashboard: {e}")

    # Register Trend API blueprint
    try:
        from services.trend_api_endpoints import trend_api
        app.register_blueprint(trend_api)
    except ImportError as e:
        logging.warning(f"Could not import trend API: {e}")

    # Register Sell Profile API
    try:
        from services.sell_profile_api_endpoints import sell_profile_api
        app.register_blueprint(sell_profile_api)
    except ImportError as e:
        logging.warning(f"Could not import sell_profile_api: {e}")

    # Register Stripe Payment System (primary payment blueprint)
    try:
        from services.stripe_payment_system import payment_bp
        app.register_blueprint(payment_bp)
    except ImportError as e:
        logging.warning(f"Could not import stripe payment system: {e}")

    # Register Payment routes (secondary - uses url_prefix to avoid collision)
    try:
        from payment import payment_routes_bp
        app.register_blueprint(payment_routes_bp)
    except ImportError as e:
        logging.warning(f"Could not import payment routes: {e}")

    # Register Licensing API
    try:
        from services.licensing_api import licensing_api
        app.register_blueprint(licensing_api)
    except ImportError as e:
        logging.warning(f"Could not import licensing API: {e}")

    # Register Marketing Strategy blueprint
    try:
        from marketing_strategy import marketing_strategy
        app.register_blueprint(marketing_strategy)
    except ImportError as e:
        logging.warning(f"Could not import marketing strategy: {e}")

    # Register Quality Control API
    try:
        from services.quality_api_endpoints import quality_api
        app.register_blueprint(quality_api)
    except ImportError as e:
        logging.warning(f"Could not import quality control API: {e}")

    # Register Admin blueprint
    try:
        from admin import admin_bp
        app.register_blueprint(admin_bp)
    except ImportError as e:
        logging.warning(f"Could not import admin module: {e}")

    # Main routes
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/features')
    def features():
        return render_template('features.html')

    @app.route('/faq')
    def faq_main():
        return render_template('faq.html')

    @app.route('/demo-login')
    def demo_login():
        from flask_login import login_user
        from flask import flash
        demo_user = User.query.filter_by(email='demo@dominatemarketing.com').first()
        if demo_user:
            login_user(demo_user)
            flash('Logged in as demo user!', 'success')
            return redirect(url_for('dashboard.index'))
        flash('Demo user not found.', 'error')
        return redirect(url_for('index'))

    @app.route('/terms')
    def terms():
        return render_template('terms.html')

    @app.route('/privacy')
    def privacy():
        return render_template('privacy.html')

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500

    # Create database tables
    with app.app_context():
        db.create_all()
        logging.info("Database tables created successfully")

    return app

# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
