import os
import logging
from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
from models import db, User, SubscriptionTier, billing_disabled

# Single Migrate instance — Flask-Migrate finds it via `flask db ...` CLI.
migrate = Migrate()

# Load environment variables
load_dotenv()

# Configure logging. App logs at INFO; quiet the very chatty HTTP/AI client
# libraries so the console stays readable (they log every request at DEBUG).
logging.basicConfig(level=logging.INFO)
for _noisy in ('openai', 'httpx', 'httpcore', 'urllib3', 'trafilatura', 'pytrends'):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

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
    migrate.init_app(app, db)

    # Expose helpers to all Jinja templates so they can hide billing-related
    # nav links when the SaaS layer is off (DISABLE_BILLING=true) or when the
    # viewer is internal staff (is_salesperson or is_admin).
    @app.context_processor
    def inject_billing_helpers():
        from flask_login import current_user
        is_internal_user = (
            current_user.is_authenticated
            and (getattr(current_user, 'is_salesperson', False)
                 or getattr(current_user, 'is_admin', False))
        )
        return {
            'billing_disabled': billing_disabled(),
            'is_internal_user': is_internal_user,
            # Convenience: hide billing UI when EITHER condition fires.
            'hide_billing_ui': billing_disabled() or is_internal_user,
        }

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

    # When the SaaS billing layer is off (DISABLE_BILLING=true) or the viewer
    # is internal staff (salesperson/admin), redirect away from any billing /
    # pricing endpoints. Stripe blueprints stay registered so re-enabling the
    # SaaS path later is just a matter of unsetting DISABLE_BILLING; this guard
    # is the surface-level mute.
    BILLING_BLUEPRINTS = {'payment_routes', 'payments'}
    BILLING_ENDPOINTS = {'auth.pricing', 'auth.email_signup'}

    @app.before_request
    def _bypass_billing_when_disabled():
        from flask import request
        from flask_login import current_user

        endpoint = request.endpoint or ''
        # Stripe webhooks must always be reachable so providers don't retry
        # against a redirected URL — skip this guard for any *.stripe_webhook.
        if endpoint.endswith('stripe_webhook') or endpoint.endswith('webhook'):
            return None

        blueprint = endpoint.split('.', 1)[0] if '.' in endpoint else ''
        is_billing_route = (
            blueprint in BILLING_BLUEPRINTS
            or endpoint in BILLING_ENDPOINTS
        )
        if not is_billing_route:
            return None

        is_internal_user = (
            current_user.is_authenticated
            and (getattr(current_user, 'is_salesperson', False)
                 or getattr(current_user, 'is_admin', False))
        )
        if billing_disabled() or is_internal_user:
            target = url_for('dashboard.index') if current_user.is_authenticated else url_for('index')
            return redirect(target)
        return None

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

    # Schema is now owned by Flask-Migrate. Run `flask db upgrade` to apply
    # migrations (Railway does this automatically via the Procfile release
    # command). For local dev: pip install flask-migrate, then `flask db upgrade`.
    # See MIGRATIONS.md for details.

    # Register the bootstrap-admin CLI command. Invoked by the Procfile release
    # step right after `flask db upgrade` so the first admin exists before any
    # web traffic hits the app.
    register_bootstrap_admin_cli(app)

    return app


def register_bootstrap_admin_cli(app):
    """Add the `flask bootstrap-admin` CLI command to the app.

    Reads BOOTSTRAP_ADMIN_USERNAME / BOOTSTRAP_ADMIN_PASSWORD /
    BOOTSTRAP_ADMIN_EMAIL from the environment and creates the first admin
    user only if no user with is_admin=True already exists. Idempotent across
    restarts: on subsequent boots the admin already exists and the command
    is a no-op (it does NOT reset the password).

    Logged behavior:
      - If env vars are missing: warn and exit 0 (don't crash deploy).
      - If admin already exists: log "skipping" with the existing username.
      - If creation succeeds: log "created admin <username>".
    """
    import click
    from werkzeug.security import generate_password_hash

    @app.cli.command('bootstrap-admin')
    def bootstrap_admin():
        username = os.environ.get('BOOTSTRAP_ADMIN_USERNAME')
        password = os.environ.get('BOOTSTRAP_ADMIN_PASSWORD')
        email = os.environ.get('BOOTSTRAP_ADMIN_EMAIL')

        if not username or not password:
            click.echo(
                '[bootstrap-admin] BOOTSTRAP_ADMIN_USERNAME or '
                'BOOTSTRAP_ADMIN_PASSWORD is not set; skipping. Set both env '
                'vars on Railway and redeploy to create the first admin.'
            )
            return

        existing_admin = User.query.filter_by(is_admin=True).first()
        if existing_admin:
            click.echo(
                f'[bootstrap-admin] An admin already exists '
                f'(username={existing_admin.username}); skipping. The password '
                f'is NOT being reset by this command.'
            )
            return

        # Username collision check (admin doesn't exist, but a non-admin user
        # might already own that username).
        if User.query.filter_by(username=username).first():
            click.echo(
                f'[bootstrap-admin] ERROR: username "{username}" is already '
                f'taken by a non-admin user. Pick a different '
                f'BOOTSTRAP_ADMIN_USERNAME or promote that user manually.'
            )
            return

        admin = User(
            username=username,
            email=email,  # may be None — column is nullable
            password_hash=generate_password_hash(password),
            full_name=username,
            is_admin=True,
            is_salesperson=False,
            # ENTERPRISE so any code path that reads subscription_tier directly
            # (rather than going through can_access_tier) gets the highest level.
            subscription_tier=SubscriptionTier.ENTERPRISE,
            account_active=True,
            profile_completion_percentage=100,
            onboarding_completed=True,
        )
        db.session.add(admin)
        db.session.commit()
        click.echo(f'[bootstrap-admin] Created admin user "{username}".')


# Create app instance
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
