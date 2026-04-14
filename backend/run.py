import re
from flask import Flask
from flask_cors import CORS
from routes.alert_routes import alert_bp
from services.database import init_db

app = Flask(__name__)

# Allow Vite dev server + any Vercel preview/production frontend
CORS(app, origins=[
    r"http://localhost:\d+",
    r"http://127\.0\.0\.1:\d+",
    re.compile(r"https://.*\.vercel\.app"),
])

# Register API blueprint only — frontend is now served by Vite
app.register_blueprint(alert_bp)  # API routes at /api/*

# Initialize DB (runs on import too, so gunicorn on Render will trigger it)
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001, debug=True)