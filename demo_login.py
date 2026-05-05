"""
Demo login utility for testing dashboard
"""
import os
import sys
from datetime import datetime

# Add the current directory to Python path
sys.path.append('.')

from main_app import create_app
from models import db, User
from flask_login import login_user

def create_demo_login_route():
    """Add a demo login route for testing purposes"""
    app = create_app()
    
    @app.route('/demo-login')
    def demo_login():
        """Demo login endpoint for testing"""
        with app.app_context():
            demo_user = User.query.filter_by(email='demo@dominatemarketing.com').first()
            if demo_user:
                login_user(demo_user)
                from flask import redirect, url_for, flash
                flash('Logged in as demo user!', 'success')
                return redirect(url_for('dashboard.index'))
            else:
                from flask import render_template
                return render_template('error.html', message='Demo user not found. Run create_test_data.py first.')
    
    return app

if __name__ == '__main__':
    print("Demo login URL: /demo-login")
    print("This will automatically log you in as the demo user to test the dashboard.")