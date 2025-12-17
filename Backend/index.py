from app import app

# Vercel serverless function handler
def handler(event, context):
    return app(event, context)

# For local testing
if __name__ == '__main__':
    app.run()
