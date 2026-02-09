from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    """Get Supabase client with service role key for admin operations"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def get_supabase_user_client() -> Client:
    """Get Supabase client with anon key for user operations"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Initialize clients
supabase: Client = get_supabase_client()
supabase_user: Client = get_supabase_user_client()