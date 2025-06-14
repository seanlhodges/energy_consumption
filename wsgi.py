# wsgi.py

import sys
import os

# Ensure your app folder is in the path
project_home = '/home/catnipmadness/scripts/energy_consumption'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Dash app's Flask server
from flask_app import server as application  # 'application' is the name PythonAnywhere expects
