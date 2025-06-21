import logging
from typing import Dict, Any, Optional, Tuple, List
from supabase import Client
from supabase_client import supabase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by ID
        """
        try:
            response = (
                self.supabase.table("users").select("*").eq("id", user_id).execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email
        """
        try:
            response = (
                self.supabase.table("users").select("*").eq("email", email).execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Get user by email error: {str(e)}")
            return None

    def update_user(
        self, user_id: str, update_data: Dict[str, Any], requesting_user_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Update user information
        Args:
            user_id: User ID to update
            update_data: Data to update
            requesting_user_id: ID of user making the request (for authorization)
        Returns: (updated_user, error_message)
        """
        try:
            # Check authorization - users can only update their own profile
            if user_id != requesting_user_id:
                return None, "Unauthorized to update this user profile"

            # Validate email uniqueness if email is being updated
            if "email" in update_data:
                existing_user = self.get_user_by_email(update_data["email"])
                if existing_user and existing_user["id"] != user_id:
                    return None, "A user with this email already exists"

            # Filter allowed update fields
            allowed_fields = ["full_name", "email"]
            filtered_data = {
                k: v for k, v in update_data.items() if k in allowed_fields
            }

            if not filtered_data:
                return None, "No valid fields to update"

            # Update user
            response = (
                self.supabase.table("users")
                .update(filtered_data)
                .eq("id", user_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                logger.info(f"User updated successfully: {user_id}")
                return response.data[0], None
            else:
                return None, "Failed to update user"

        except Exception as e:
            logger.error(f"Update user error: {str(e)}")
            return None, f"Failed to update user: {str(e)}"

    def delete_user(
        self, user_id: str, requesting_user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a user (only the user themselves can delete their profile)
        Args:
            user_id: User ID to delete
            requesting_user_id: ID of user making the request
        Returns: (success, error_message)
        """
        try:
            # Check authorization - users can only delete their own profile
            if user_id != requesting_user_id:
                return False, "Unauthorized to delete this user profile"

            # Get user to check if they're part of a company
            user = self.get_user(user_id)
            if not user:
                return False, "User not found"

            # If user is part of a company, check if they're the only member
            if user.get("company_id"):
                company_users = (
                    self.supabase.table("users")
                    .select("id")
                    .eq("company_id", user["company_id"])
                    .execute()
                )
                if company_users.data and len(company_users.data) == 1:
                    # User is the only member, delete the company too
                    company_delete_response = (
                        self.supabase.table("companies")
                        .delete()
                        .eq("id", user["company_id"])
                        .execute()
                    )
                    if not company_delete_response.data:
                        logger.warning(
                            f"Failed to delete company when deleting user: {user['company_id']}"
                        )

            # Delete user from our users table (auth.users will be handled by Supabase)
            response = self.supabase.table("users").delete().eq("id", user_id).execute()

            if response.data:
                logger.info(f"User deleted successfully: {user_id}")
                return True, None
            else:
                return False, "Failed to delete user"

        except Exception as e:
            logger.error(f"Delete user error: {str(e)}")
            return False, f"Failed to delete user: {str(e)}"

    def get_user_with_company(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user with their company information
        """
        try:
            # Get user data
            user = self.get_user(user_id)
            if not user:
                return None

            # Get company data if user has a company
            if user.get("company_id"):
                company_response = (
                    self.supabase.table("companies")
                    .select("*")
                    .eq("id", user["company_id"])
                    .execute()
                )
                if company_response.data and len(company_response.data) > 0:
                    user["company"] = company_response.data[0]

            return user

        except Exception as e:
            logger.error(f"Get user with company error: {str(e)}")
            return None

    def leave_company(
        self, user_id: str, requesting_user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Remove user from their company
        Args:
            user_id: User ID to remove from company
            requesting_user_id: ID of user making the request
        Returns: (success, error_message)
        """
        try:
            # Check authorization - users can only leave their own company
            if user_id != requesting_user_id:
                return False, "Unauthorized to perform this action"

            # Get user to check current company
            user = self.get_user(user_id)
            if not user:
                return False, "User not found"

            if not user.get("company_id"):
                return False, "User is not part of any company"

            company_id = user["company_id"]

            # Check if user is the only member of the company
            company_users = (
                self.supabase.table("users")
                .select("id")
                .eq("company_id", company_id)
                .execute()
            )
            if company_users.data and len(company_users.data) == 1:
                # User is the only member, delete the company
                company_delete_response = (
                    self.supabase.table("companies")
                    .delete()
                    .eq("id", company_id)
                    .execute()
                )
                if not company_delete_response.data:
                    logger.warning(
                        f"Failed to delete company when user left: {company_id}"
                    )

            # Remove user from company
            response = (
                self.supabase.table("users")
                .update({"company_id": None})
                .eq("id", user_id)
                .execute()
            )

            if response.data:
                logger.info(f"User left company successfully: {user_id}")
                return True, None
            else:
                return False, "Failed to leave company"

        except Exception as e:
            logger.error(f"Leave company error: {str(e)}")
            return False, f"Failed to leave company: {str(e)}"

    def join_company(
        self, user_id: str, company_id: str, requesting_user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Add user to a company
        Args:
            user_id: User ID to add to company
            company_id: Company ID to join
            requesting_user_id: ID of user making the request
        Returns: (success, error_message)
        """
        try:
            # Check authorization - users can only join companies themselves
            if user_id != requesting_user_id:
                return False, "Unauthorized to perform this action"

            # Check if company exists
            company_response = (
                self.supabase.table("companies")
                .select("id")
                .eq("id", company_id)
                .execute()
            )
            if not company_response.data or len(company_response.data) == 0:
                return False, "Company not found"

            # Check if user is already part of a company
            user = self.get_user(user_id)
            if not user:
                return False, "User not found"

            if user.get("company_id"):
                return (
                    False,
                    "User is already part of a company. Leave current company first.",
                )

            # Add user to company
            response = (
                self.supabase.table("users")
                .update({"company_id": company_id})
                .eq("id", user_id)
                .execute()
            )

            if response.data:
                logger.info(
                    f"User joined company successfully: {user_id} -> {company_id}"
                )
                return True, None
            else:
                return False, "Failed to join company"

        except Exception as e:
            logger.error(f"Join company error: {str(e)}")
            return False, f"Failed to join company: {str(e)}"

    def update_user_role(
        self, user_id: str, new_role: str, requesting_user_id: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Update user role within their company
        Args:
            user_id: User ID to update
            new_role: New role to assign
            requesting_user_id: ID of user making the request
        Returns: (success, error_message)
        """
        try:
            # Get both users to check permissions
            target_user = self.get_user(user_id)
            requesting_user = self.get_user(requesting_user_id)

            if not target_user or not requesting_user:
                return False, "User not found"

            # Check if both users are in the same company
            if target_user.get("company_id") != requesting_user.get("company_id"):
                return False, "Users are not in the same company"

            # Check if requesting user has permission (must be admin or owner)
            if requesting_user.get("role") not in ["admin", "owner"]:
                return False, "Insufficient permissions to update user roles"

            # Validate new role
            valid_roles = ["member", "admin", "owner"]
            if new_role not in valid_roles:
                return False, f"Invalid role. Must be one of: {', '.join(valid_roles)}"

            # Update user role
            response = (
                self.supabase.table("users")
                .update({"role": new_role})
                .eq("id", user_id)
                .execute()
            )

            if response.data:
                logger.info(f"User role updated successfully: {user_id} -> {new_role}")
                return True, None
            else:
                return False, "Failed to update user role"

        except Exception as e:
            logger.error(f"Update user role error: {str(e)}")
            return False, f"Failed to update user role: {str(e)}"

    def list_users_by_company(
        self, company_id: str, requesting_user_id: str
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List all users in a company
        Args:
            company_id: Company ID
            requesting_user_id: ID of user making the request
        Returns: (users_list, error_message)
        """
        try:
            # Check if requesting user is part of the company
            requesting_user = self.get_user(requesting_user_id)
            if not requesting_user or requesting_user.get("company_id") != company_id:
                return [], "Unauthorized to view company users"

            # Get all users in the company
            response = (
                self.supabase.table("users")
                .select("id, full_name, email, role, created_at")
                .eq("company_id", company_id)
                .execute()
            )

            if response.data:
                return response.data, None
            else:
                return [], "Failed to get company users"

        except Exception as e:
            logger.error(f"List users by company error: {str(e)}")
            return [], f"Failed to list company users: {str(e)}"


# Initialize user service
user_service = UserService(supabase)
