import sys
import os

# Vercel serverless - import dari folder yang sama
try:
    from .app import app
except Exception as e:
    # Fallback to simple test app if main app fails
    from .test import app
    print(f"Warning: Main app failed to load: {e}")

# Export
app = app
