from flask import Flask
from flask_cors import CORS
from routes.alert_routes import alert_bp
from services.database import init_db

app = Flask(__name__)

# Allow Vite dev server (localhost:5173) to call the API
CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"])

# Register API blueprint only — frontend is now served by Vite
app.register_blueprint(alert_bp)  # API routes at /api/*


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=3000, debug=True)