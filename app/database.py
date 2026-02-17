from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    """Get Supabase client with service role key for admin operations"""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

def get_anon_supabase_client() -> Client:
    """Create a Supabase client with the anon/public key.

    Use this for user-facing auth operations like sign_in_with_password.
    The service role key must NOT be used for these calls.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_fresh_supabase_client() -> Client:
    """Create a fresh Supabase service role client.

    Use this after auth operations (sign_up, create_user, sign_in) to avoid
    auth state contamination where the Python SDK switches from service role
    context to the newly authenticated user's context.
    """
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

# Initialize global client for non-auth operations
supabase: Client = get_supabase_client()