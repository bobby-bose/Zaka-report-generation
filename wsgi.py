import sys
import os

# Add your project directory to the sys.path
project_home = '/home/alisha123/Alisha-web-report-generation'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import the Flask app
from main import app, db

# Create database tables if they don't exist
with app.app_context():
    db.create_all()

# PythonAnywhere will look for the 'application' variable
application = app

if __name__ == '__main__':
    app.run()
