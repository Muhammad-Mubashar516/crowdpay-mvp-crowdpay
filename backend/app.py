from flask import Flask
from flask_cors import CORS
from routes.links import links_bp
from routes.contributions import contributions_bp
from routes.webhooks import webhooks_bp
from services.supabase_client import supabase
import os


def create_app():
    app = Flask(__name__)
    app.config.from_mapping(
        SUPABASE_URL=os.getenv('SUPABASE_URL'),
        SUPABASE_KEY=os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    )
    
    # Enable CORS for frontend integration
    frontend_url = os.getenv('FRONTEND_URL')
    cors_origins = [
        "http://localhost:3000",  # React dev server
        "http://localhost:5173",  # Vite dev server
        "https://*.vercel.app",   # Vercel deployments
    ]
    if frontend_url:  # Only add if not None
        cors_origins.append(frontend_url)
    
    CORS(app, origins=cors_origins)

    app.register_blueprint(links_bp, url_prefix='/api/links')
    app.register_blueprint(contributions_bp, url_prefix='/api/contributions')
    app.register_blueprint(webhooks_bp, url_prefix='/api/webhooks')

    return app


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    app = create_app()
    app.run(host=os.getenv('FLASK_RUN_HOST','0.0.0.0'), port=int(os.getenv('FLASK_RUN_PORT',5000)))