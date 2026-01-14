import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    
    # Bitnob API
    BITNOB_API_KEY = os.getenv('BITNOB_API_KEY')
    BITNOB_API_URL = os.getenv('BITNOB_API_URL', 'https://api.bitnob.co')
    BITNOB_WEBHOOK_SECRET = os.getenv('BITNOB_WEBHOOK_SECRET')
    
    # Polling Configuration
    POLLING_INTERVAL = int(os.getenv('POLLING_INTERVAL', '30'))  # seconds
    POLLING_TIMEOUT = int(os.getenv('POLLING_TIMEOUT', '3600'))  # 1 hour
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required = [
            'SUPABASE_URL',
            'SUPABASE_KEY',
            'BITNOB_API_KEY',
            'BITNOB_WEBHOOK_SECRET'
        ]
        
        missing = [key for key in required if not getattr(cls, key)]
        
        if missing:
            raise ValueError(f"Missing required configuration: {', '.join(missing)}")
        
        return True
