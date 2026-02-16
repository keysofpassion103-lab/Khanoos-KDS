from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    """Get Supabase client with service role key for admin operations"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def get_supabase_user_client() -> Client:
    """Get Supabase client with anon key for user operations"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_fresh_supabase_client() -> Client:
    """Create a fresh Supabase service role client.

    Use this after auth operations (sign_up, create_user, sign_in) to avoid
    auth state contamination where the Python SDK switches from service role
    context to the newly authenticated user's context.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Initialize clients
supabase: Client = get_supabase_client()
supabase_user: Client = get_supabase_user_client()