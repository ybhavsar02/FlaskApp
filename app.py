from flask import Flask, jsonify
import os
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/')
def home():
    logger.info("Home endpoint hit")
    return jsonify({
        "message": "Hello from DevOps Pipeline!",
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "environment": os.getenv("APP_ENV", "development")
    })

@app.route('/health')
def health():
    logger.info("Health check endpoint hit")
    return jsonify({"status": "healthy"}), 200

@app.route('/info')
def info():
    return jsonify({
        "app": "flask-devops-project",
        "author": "DevOps Engineer",
        "description": "Sample Flask app for CI/CD pipeline demo"
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
