import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


class SupabaseSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_ANON_KEY")
            cls._instance = create_client(url, key)
        return cls._instance


# Create and export the supabase client instance
supabase: Client = SupabaseSingleton()
