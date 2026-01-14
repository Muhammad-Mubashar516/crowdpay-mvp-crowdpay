from supabase import create_client, Client
from config import Config
from typing import Optional

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client singleton"""
    global _supabase_client
    
    if _supabase_client is None:
        if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
            raise ValueError("Supabase configuration is missing")
        
        _supabase_client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )
    
    return _supabase_client

def reset_supabase_client():
    """Reset the Supabase client (useful for testing)"""
    global _supabase_client
    _supabase_client = None
