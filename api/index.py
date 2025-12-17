import sys
import os

# Add Backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from Backend.app import app

# This is needed for Vercel
app = app
