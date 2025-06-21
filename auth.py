import os
import logging
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID
from supabase import Client
from supabase_client import supabase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def make_json_serializable(obj):
    """Convert any object to JSON serializable format"""
    if obj is None:
        return None
    elif isinstance(obj, (str, int, float, bool)):
        return obj
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, UUID):
        return str(obj)
    elif isinstance(obj, dict):
        return {key: make_json_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_json_serializable(item) for item in obj]
    else:
        # For any other object, try to convert to string
        return str(obj)


class AuthService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def signup_user(
        self, email: str, password: str, full_name: str
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Register a new user with Supabase Auth
        Returns: (user_data, error_message)
        """
        try:
            # Sign up user with Supabase Auth
            auth_response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {"data": {"full_name": full_name}},
                }
            )

            if auth_response.user:
                logger.info(f"User registered successfully: {email}")

                # Debug logging for session object
                if auth_response.session:
                    logger.info(f"Session object type: {type(auth_response.session)}")
                    logger.info(
                        f"Session object attributes: {dir(auth_response.session)}"
                    )
                    logger.info(
                        f"Session access_token type: {type(auth_response.session.access_token)}"
                    )
                    logger.info(
                        f"Session expires_at type: {type(auth_response.session.expires_at)}"
                    )
                    try:
                        logger.info(
                            f"Session expires_at value: {auth_response.session.expires_at}"
                        )
                    except Exception as e:
                        logger.error(f"Error accessing expires_at: {e}")

                # Extract only essential session fields as simple types
                session_data = None
                if auth_response.session:
                    try:
                        session_data = {
                            "access_token": (
                                str(auth_response.session.access_token)
                                if auth_response.session.access_token
                                else None
                            ),
                            "refresh_token": (
                                str(auth_response.session.refresh_token)
                                if auth_response.session.refresh_token
                                else None
                            ),
                            "token_type": (
                                str(auth_response.session.token_type)
                                if auth_response.session.token_type
                                else "bearer"
                            ),
                            "expires_in": (
                                int(auth_response.session.expires_in)
                                if auth_response.session.expires_in
                                else None
                            ),
                        }

                        # Handle expires_at carefully
                        if (
                            hasattr(auth_response.session, "expires_at")
                            and auth_response.session.expires_at
                        ):
                            try:
                                if isinstance(
                                    auth_response.session.expires_at, (int, float)
                                ):
                                    session_data["expires_at"] = int(
                                        auth_response.session.expires_at
                                    )
                                else:
                                    session_data["expires_at"] = str(
                                        auth_response.session.expires_at
                                    )
                            except Exception as e:
                                logger.error(f"Error processing expires_at: {e}")
                                session_data["expires_at"] = None
                        else:
                            session_data["expires_at"] = None

                    except Exception as e:
                        logger.error(f"Error extracting session data: {e}")
                        session_data = {
                            "access_token": (
                                str(auth_response.session.access_token)
                                if auth_response.session.access_token
                                else None
                            ),
                            "token_type": "bearer",
                        }

                # Create response data with only simple types
                response_data = {
                    "user": {
                        "id": str(auth_response.user.id),
                        "email": str(auth_response.user.email),
                        "full_name": str(full_name),
                        "created_at": (
                            str(auth_response.user.created_at)
                            if auth_response.user.created_at
                            else None
                        ),
                    },
                    "session": session_data,
                }

                logger.info(f"Final response_data structure: {response_data}")
                return response_data, None
            else:
                return {}, "Failed to create user account"

        except Exception as e:
            logger.error(f"Signup error: {str(e)}")
            import traceback

            logger.error(f"Signup traceback: {traceback.format_exc()}")
            return {}, f"Registration failed: {str(e)}"

    def signin_user(
        self, email: str, password: str
    ) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Sign in an existing user
        Returns: (user_data, error_message)
        """
        try:
            auth_response = self.supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )

            if auth_response.user:
                # Get user profile from our users table
                user_profile = self.get_user_profile(auth_response.user.id)

                logger.info(f"User signed in successfully: {email}")

                # Extract only essential session fields as simple types
                session_data = None
                if auth_response.session:
                    try:
                        session_data = {
                            "access_token": (
                                str(auth_response.session.access_token)
                                if auth_response.session.access_token
                                else None
                            ),
                            "refresh_token": (
                                str(auth_response.session.refresh_token)
                                if auth_response.session.refresh_token
                                else None
                            ),
                            "token_type": (
                                str(auth_response.session.token_type)
                                if auth_response.session.token_type
                                else "bearer"
                            ),
                            "expires_in": (
                                int(auth_response.session.expires_in)
                                if auth_response.session.expires_in
                                else None
                            ),
                        }

                        # Handle expires_at carefully
                        if (
                            hasattr(auth_response.session, "expires_at")
                            and auth_response.session.expires_at
                        ):
                            try:
                                if isinstance(
                                    auth_response.session.expires_at, (int, float)
                                ):
                                    session_data["expires_at"] = int(
                                        auth_response.session.expires_at
                                    )
                                else:
                                    session_data["expires_at"] = str(
                                        auth_response.session.expires_at
                                    )
                            except Exception as e:
                                logger.error(f"Error processing expires_at: {e}")
                                session_data["expires_at"] = None
                        else:
                            session_data["expires_at"] = None

                    except Exception as e:
                        logger.error(f"Error extracting session data: {e}")
                        session_data = {
                            "access_token": (
                                str(auth_response.session.access_token)
                                if auth_response.session.access_token
                                else None
                            ),
                            "token_type": "bearer",
                        }

                # Create response data with only simple types
                response_data = {
                    "user": {
                        "id": str(auth_response.user.id),
                        "email": str(auth_response.user.email),
                        "full_name": str(
                            auth_response.user.user_metadata.get("full_name", "")
                        ),
                        "created_at": (
                            str(auth_response.user.created_at)
                            if auth_response.user.created_at
                            else None
                        ),
                        "company_id": (
                            str(user_profile.get("company_id"))
                            if user_profile and user_profile.get("company_id")
                            else None
                        ),
                        "role": (
                            str(user_profile.get("role"))
                            if user_profile and user_profile.get("role")
                            else None
                        ),
                    },
                    "session": session_data,
                }

                return response_data, None
            else:
                return {}, "Invalid email or password"

        except Exception as e:
            logger.error(f"Signin error: {str(e)}")
            import traceback

            logger.error(f"Signin traceback: {traceback.format_exc()}")
            return {}, f"Sign in failed: {str(e)}"

    def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from users table
        """
        try:
            response = (
                self.supabase.table("users").select("*").eq("id", user_id).execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Get user profile error: {str(e)}")
            return None

    def update_user_company(
        self, user_id: str, company_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Update user's company_id after company creation
        Returns: (success, error_message)
        """
        try:
            response = (
                self.supabase.table("users")
                .update({"company_id": company_id})
                .eq("id", user_id)
                .execute()
            )

            if response.data:
                logger.info(f"User company updated: {user_id} -> {company_id}")
                return True, None
            return False, "Failed to update user company"

        except Exception as e:
            logger.error(f"Update user company error: {str(e)}")
            return False, f"Failed to update user company: {str(e)}"

    def get_current_user(self) -> Optional[Dict[str, Any]]:
        """
        Get current authenticated user
        """
        try:
            user = self.supabase.auth.get_user()
            if user and user.user:
                profile = self.get_user_profile(user.user.id)

                response_data = {
                    "user": {
                        "id": user.user.id,
                        "email": user.user.email,
                        "full_name": user.user.user_metadata.get("full_name", ""),
                        "created_at": user.user.created_at,
                        "company_id": profile.get("company_id") if profile else None,
                        "role": profile.get("role") if profile else None,
                    }
                }

                # Make everything JSON serializable
                return make_json_serializable(response_data)
            return None

        except Exception as e:
            logger.error(f"Get current user error: {str(e)}")
            return None

    def signout_user(self) -> Tuple[bool, Optional[str]]:
        """
        Sign out current user
        Returns: (success, error_message)
        """
        try:
            self.supabase.auth.sign_out()
            logger.info("User signed out successfully")
            return True, None

        except Exception as e:
            logger.error(f"Signout error: {str(e)}")
            return False, f"Sign out failed: {str(e)}"

    def join_existing_company(
        self, user_id: str, company_email: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Find and join an existing company by email
        Returns: (company_id, error_message)
        """
        try:
            # Find company by email
            response = (
                self.supabase.table("companies")
                .select("id")
                .eq("email", company_email)
                .execute()
            )

            if response.data and len(response.data) > 0:
                company_id = response.data[0]["id"]

                # Update user's company_id
                success, error = self.update_user_company(user_id, company_id)
                if success:
                    return company_id, None
                else:
                    return None, error
            else:
                return None, "Company not found with that email address"

        except Exception as e:
            logger.error(f"Join company error: {str(e)}")
            return None, f"Failed to join company: {str(e)}"


# Initialize auth service
auth_service = AuthService(supabase)
