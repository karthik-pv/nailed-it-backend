import os
import logging
from typing import Dict, Any, Optional, Tuple, List
from supabase import Client
from supabase_client import supabase
from auth import auth_service
from storage import storage_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompanyService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client

    def create_company(
        self, company_data: Dict[str, Any], user_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Create a new company and associate it with the user
        Args:
            company_data: Company information
            user_id: ID of the user creating the company
        Returns: (company_data, error_message)
        """
        try:
            # Validate required fields
            required_fields = ["company_name", "owner_name", "email", "phone"]
            for field in required_fields:
                if not company_data.get(field):
                    return None, f"Missing required field: {field}"

            # Check if company email already exists
            existing_company = self.get_company_by_email(company_data["email"])
            if existing_company:
                return None, "A company with this email already exists"

            # Create company record
            company_insert_data = {
                "company_name": company_data["company_name"],
                "owner_name": company_data["owner_name"],
                "email": company_data["email"],
                "phone": company_data["phone"],
                "website": company_data.get("website"),
                "description": company_data.get("description"),
                "logo_url": company_data.get("logo_url"),
                "pricing_document_url": company_data.get("pricing_document_url"),
            }

            response = (
                self.supabase.table("companies").insert(company_insert_data).execute()
            )

            if response.data and len(response.data) > 0:
                company = response.data[0]

                # Update user's company_id
                success, error = auth_service.update_user_company(
                    user_id, company["id"]
                )
                if not success:
                    # Rollback company creation
                    self.delete_company(company["id"])
                    return None, f"Failed to associate user with company: {error}"

                logger.info(f"Company created successfully: {company['id']}")
                return company, None
            else:
                return None, "Failed to create company"

        except Exception as e:
            logger.error(f"Create company error: {str(e)}")
            return None, f"Failed to create company: {str(e)}"

    def get_company(self, company_id: str) -> Optional[Dict[str, Any]]:
        """
        Get company by ID
        """
        try:
            response = (
                self.supabase.table("companies")
                .select("*")
                .eq("id", company_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Get company error: {str(e)}")
            return None

    def get_company_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get company by email
        """
        try:
            response = (
                self.supabase.table("companies")
                .select("*")
                .eq("email", email)
                .execute()
            )

            if response.data and len(response.data) > 0:
                return response.data[0]
            return None

        except Exception as e:
            logger.error(f"Get company by email error: {str(e)}")
            return None

    def update_company(
        self, company_id: str, update_data: Dict[str, Any], user_id: str
    ) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
        """
        Update company information
        Args:
            company_id: Company ID to update
            update_data: Data to update
            user_id: ID of user making the update (for authorization)
        Returns: (updated_company, error_message)
        """
        try:
            # Verify user has permission to update this company
            user_profile = auth_service.get_user_profile(user_id)
            if not user_profile or user_profile.get("company_id") != company_id:
                return None, "Unauthorized to update this company"

            # Validate email uniqueness if email is being updated
            if "email" in update_data:
                existing_company = self.get_company_by_email(update_data["email"])
                if existing_company and existing_company["id"] != company_id:
                    return None, "A company with this email already exists"

            # Filter allowed update fields
            allowed_fields = [
                "company_name",
                "owner_name",
                "email",
                "phone",
                "website",
                "description",
                "logo_url",
                "pricing_document_url",
            ]
            filtered_data = {
                k: v for k, v in update_data.items() if k in allowed_fields
            }

            if not filtered_data:
                return None, "No valid fields to update"

            # Update company
            response = (
                self.supabase.table("companies")
                .update(filtered_data)
                .eq("id", company_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                logger.info(f"Company updated successfully: {company_id}")
                return response.data[0], None
            else:
                return None, "Failed to update company"

        except Exception as e:
            logger.error(f"Update company error: {str(e)}")
            return None, f"Failed to update company: {str(e)}"

    def delete_company(
        self, company_id: str, user_id: str = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a company (only if user is authorized and no other users are associated)
        Args:
            company_id: Company ID to delete
            user_id: ID of user requesting deletion (for authorization)
        Returns: (success, error_message)
        """
        try:
            if user_id:
                # Verify user has permission to delete this company
                user_profile = auth_service.get_user_profile(user_id)
                if not user_profile or user_profile.get("company_id") != company_id:
                    return False, "Unauthorized to delete this company"

            # Get all users associated with this company
            users_response = (
                self.supabase.table("users")
                .select("id")
                .eq("company_id", company_id)
                .execute()
            )

            if users_response.data and len(users_response.data) > 1:
                return False, "Cannot delete company with multiple users"

            # Delete company
            response = (
                self.supabase.table("companies").delete().eq("id", company_id).execute()
            )

            if response.data:
                logger.info(f"Company deleted successfully: {company_id}")
                return True, None
            else:
                return False, "Failed to delete company"

        except Exception as e:
            logger.error(f"Delete company error: {str(e)}")
            return False, f"Failed to delete company: {str(e)}"

    def get_company_users(
        self, company_id: str, requesting_user_id: str
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        Get all users associated with a company
        Args:
            company_id: Company ID
            requesting_user_id: ID of user making the request
        Returns: (users_list, error_message)
        """
        try:
            # Verify requesting user is part of this company
            user_profile = auth_service.get_user_profile(requesting_user_id)
            if not user_profile or user_profile.get("company_id") != company_id:
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
            logger.error(f"Get company users error: {str(e)}")
            return [], f"Failed to get company users: {str(e)}"

    def upload_company_logo(
        self, company_id: str, file_data: bytes, file_name: str, user_id: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload company logo and update company record
        Args:
            company_id: Company ID
            file_data: File bytes
            file_name: Original filename
            user_id: User ID (for authorization and storage)
        Returns: (logo_url, error_message)
        """
        try:
            # Verify user has permission to update this company
            user_profile = auth_service.get_user_profile(user_id)
            if not user_profile or user_profile.get("company_id") != company_id:
                return None, "Unauthorized to update this company"

            # Validate file
            is_valid, validation_error = storage_service.validate_file(
                file_data, file_name, max_size_mb=5
            )
            if not is_valid:
                return None, validation_error

            # Check if it's an image file
            allowed_image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
            file_extension = os.path.splitext(file_name)[1].lower()
            if file_extension not in allowed_image_extensions:
                return None, "Logo must be an image file (JPG, PNG, GIF, or WebP)"

            # Get current company data to check for existing logo
            company = self.get_company(company_id)
            if not company:
                return None, "Company not found"

            # Upload new logo
            logo_url, upload_error = storage_service.upload_file(
                file_data, file_name, user_id, "logo"
            )
            if upload_error:
                return None, upload_error

            # Update company with new logo URL
            updated_company, update_error = self.update_company(
                company_id, {"logo_url": logo_url}, user_id
            )
            if update_error:
                # Clean up uploaded file if database update fails
                storage_service.delete_file(logo_url, user_id)
                return None, update_error

            # Delete old logo if it exists
            if company.get("logo_url"):
                storage_service.delete_file(company["logo_url"], user_id)

            logger.info(f"Company logo uploaded successfully: {company_id}")
            return logo_url, None

        except Exception as e:
            logger.error(f"Upload company logo error: {str(e)}")
            return None, f"Failed to upload company logo: {str(e)}"

    def upload_pricing_document(
        self, company_id: str, file_data: bytes, file_name: str, user_id: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload pricing document and update company record
        Args:
            company_id: Company ID
            file_data: File bytes
            file_name: Original filename
            user_id: User ID (for authorization and storage)
        Returns: (document_url, error_message)
        """
        try:
            # Verify user has permission to update this company
            user_profile = auth_service.get_user_profile(user_id)
            if not user_profile or user_profile.get("company_id") != company_id:
                return None, "Unauthorized to update this company"

            # Validate file
            is_valid, validation_error = storage_service.validate_file(
                file_data, file_name, max_size_mb=10
            )
            if not is_valid:
                return None, validation_error

            # Get current company data to check for existing document
            company = self.get_company(company_id)
            if not company:
                return None, "Company not found"

            # Upload new document
            document_url, upload_error = storage_service.upload_file(
                file_data, file_name, user_id, "document"
            )
            if upload_error:
                return None, upload_error

            # Update company with new document URL
            updated_company, update_error = self.update_company(
                company_id, {"pricing_document_url": document_url}, user_id
            )
            if update_error:
                # Clean up uploaded file if database update fails
                storage_service.delete_file(document_url, user_id)
                return None, update_error

            # Delete old document if it exists
            if company.get("pricing_document_url"):
                storage_service.delete_file(company["pricing_document_url"], user_id)

            logger.info(f"Pricing document uploaded successfully: {company_id}")
            return document_url, None

        except Exception as e:
            logger.error(f"Upload pricing document error: {str(e)}")
            return None, f"Failed to upload pricing document: {str(e)}"


# Initialize company service
company_service = CompanyService(supabase)
