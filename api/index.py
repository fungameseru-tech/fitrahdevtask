import sys
import os

# Add Backend directory to path
backend_path = os.path.join(os.path.dirname(__file__), '..', 'Backend')
sys.path.insert(0, backend_path)

# Import Flask app
try:
    from app import app
except Exception as e:
    # Fallback error handler
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/')
    @app.route('/api/<path:path>')
    def error_handler(path=None):
        return jsonify({
            "error": "Backend initialization failed",
            "message": str(e),
            "backend_path": backend_path,
            "sys_path": sys.path[:3]
        }), 500

# Vercel serverless handler
handler = app
