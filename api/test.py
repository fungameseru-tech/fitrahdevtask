from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/api/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Vercel serverless working!'}), 200

@app.route('/api/health')
def health():
    return jsonify({'status': 'healthy'}), 200
