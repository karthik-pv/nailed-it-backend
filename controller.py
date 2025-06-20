from flask import request, jsonify
from supabase import Client
import uuid
from typing import Dict, Any, Optional, Tuple
import os
from datetime import datetime


class UserController:
    def __init__(self, supabase: Client):
        self.supabase = supabase

    def create_user_and_company(
        self, user_id: str, company_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Create a new user record and optionally a company"""
        try:
            # First create or update user record
            user_data = {
                "id": user_id,
                "full_name": company_data.get("ownerName"),
                "role": "owner",
                "onboarding_completed": False,
            }

            # Check if user already exists
            existing_user = (
                self.supabase.table("users").select("*").eq("id", user_id).execute()
            )

            if existing_user.data:
                # Update existing user
                user_result = (
                    self.supabase.table("users")
                    .update(user_data)
                    .eq("id", user_id)
                    .execute()
                )
            else:
                # Create new user
                user_result = self.supabase.table("users").insert(user_data).execute()

            if not user_result.data:
                return {"error": "Failed to create user record"}, 500

            # Create company if data provided
            if company_data.get("companyName"):
                company_result, status_code = self._create_company(company_data)
                if status_code != 201:
                    return company_result, status_code

                company_id = company_result["company"]["id"]

                # Link user to company
                self.supabase.table("users").update(
                    {"company_id": company_id, "onboarding_completed": True}
                ).eq("id", user_id).execute()

                return {
                    "message": "User and company created successfully",
                    "user": user_result.data[0],
                    "company": company_result["company"],
                }, 201

            return {
                "message": "User created successfully",
                "user": user_result.data[0],
            }, 201

        except Exception as e:
            return {"error": f"Failed to create user: {str(e)}"}, 500

    def _create_company(
        self, company_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Create a new company record"""
        try:
            company_record = {
                "company_name": company_data.get("companyName"),
                "owner_name": company_data.get("ownerName"),
                "email": company_data.get("email"),
                "phone": company_data.get("phone"),
                "website": company_data.get("website"),
                "description": company_data.get("description"),
                "logo_url": company_data.get("logoUrl"),
                "selected_plan": company_data.get("selectedPlan", "professional"),
                "plan_details": company_data.get("planDetails", {}),
                "pricing_document_url": company_data.get("pricingDocumentUrl"),
                "payment_status": "pending",
                "subscription_status": "trial",
            }

            result = self.supabase.table("companies").insert(company_record).execute()

            if result.data:
                return {
                    "message": "Company created successfully",
                    "company": result.data[0],
                }, 201
            else:
                return {"error": "Failed to create company"}, 500

        except Exception as e:
            return {"error": f"Failed to create company: {str(e)}"}, 500

    def complete_onboarding(
        self, user_id: str, company_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Complete onboarding process by creating company and linking to user"""
        try:
            # Create company
            company_result, status_code = self._create_company(company_data)
            if status_code != 201:
                return company_result, status_code

            company_id = company_result["company"]["id"]

            # Update user record with company association and mark onboarding complete
            user_update = (
                self.supabase.table("users")
                .update({"company_id": company_id, "onboarding_completed": True})
                .eq("id", user_id)
                .execute()
            )

            if user_update.data:
                # Get updated user data
                user_data = user_update.data[0]

                return {
                    "message": "Onboarding completed successfully",
                    "user": user_data,
                    "company": company_result["company"],
                }, 200
            else:
                return {"error": "Failed to update user record"}, 500

        except Exception as e:
            return {"error": f"Onboarding failed: {str(e)}"}, 500

    def update_company(
        self, company_id: str, update_data: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], int]:
        """Update company information"""
        try:
            # Filter out None values and prepare update data
            filtered_data = {k: v for k, v in update_data.items() if v is not None}

            result = (
                self.supabase.table("companies")
                .update(filtered_data)
                .eq("id", company_id)
                .execute()
            )

            if result.data:
                return {
                    "message": "Company updated successfully",
                    "company": result.data[0],
                }, 200
            else:
                return {"error": "Company not found or update failed"}, 404

        except Exception as e:
            return {"error": f"Failed to update company: {str(e)}"}, 500

    def get_user_with_company(self, user_id: str) -> Tuple[Dict[str, Any], int]:
        """Get user details along with their company information"""
        try:
            # Get user data
            user_result = (
                self.supabase.table("users").select("*").eq("id", user_id).execute()
            )

            if not user_result.data:
                return {"error": "User not found"}, 404

            user_data = user_result.data[0]
            response_data = {"user": user_data}

            # Get company data if user has a company
            if user_data.get("company_id"):
                company_result = (
                    self.supabase.table("companies")
                    .select("*")
                    .eq("id", user_data["company_id"])
                    .execute()
                )

                if company_result.data:
                    response_data["company"] = company_result.data[0]

            return response_data, 200

        except Exception as e:
            return {"error": f"Failed to get user data: {str(e)}"}, 500

    def update_payment_status(
        self,
        company_id: str,
        payment_status: str,
        subscription_status: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], int]:
        """Update payment and subscription status"""
        try:
            update_data = {"payment_status": payment_status}

            if subscription_status:
                update_data["subscription_status"] = subscription_status

            if payment_status == "paid" and subscription_status == "active":
                update_data["subscription_start_date"] = datetime.utcnow().isoformat()

            result = (
                self.supabase.table("companies")
                .update(update_data)
                .eq("id", company_id)
                .execute()
            )

            if result.data:
                return {
                    "message": "Payment status updated successfully",
                    "company": result.data[0],
                }, 200
            else:
                return {"error": "Company not found"}, 404

        except Exception as e:
            return {"error": f"Failed to update payment status: {str(e)}"}, 500

    def upload_file_to_storage(
        self,
        file_data: bytes,
        file_name: str,
        user_id: str,
        file_type: str = "document",
    ) -> Tuple[Dict[str, Any], int]:
        """Upload file to Supabase storage"""
        try:
            # Create a unique file path
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{user_id}/{file_type}_{uuid.uuid4()}{file_extension}"

            # Upload to Supabase storage
            result = self.supabase.storage.from_("assets").upload(
                unique_filename, file_data
            )

            if result:
                # Get public URL
                public_url = self.supabase.storage.from_("assets").get_public_url(
                    unique_filename
                )

                return {
                    "message": "File uploaded successfully",
                    "url": public_url,
                    "filename": unique_filename,
                }, 200
            else:
                return {"error": "Failed to upload file"}, 500

        except Exception as e:
            return {"error": f"File upload failed: {str(e)}"}, 500

    def upload_pricing_document(
        self, company_id: str, document_url: str
    ) -> Tuple[Dict[str, Any], int]:
        """Update company with pricing document URL"""
        try:
            result = (
                self.supabase.table("companies")
                .update(
                    {
                        "pricing_document_url": document_url,
                        "ai_training_status": "not_started",
                    }
                )
                .eq("id", company_id)
                .execute()
            )

            if result.data:
                return {
                    "message": "Pricing document uploaded successfully",
                    "company": result.data[0],
                }, 200
            else:
                return {"error": "Company not found"}, 404

        except Exception as e:
            return {"error": f"Failed to upload pricing document: {str(e)}"}, 500

    def upload_company_logo(
        self, company_id: str, logo_url: str
    ) -> Tuple[Dict[str, Any], int]:
        """Update company with logo URL"""
        try:
            result = (
                self.supabase.table("companies")
                .update({"logo_url": logo_url})
                .eq("id", company_id)
                .execute()
            )

            if result.data:
                return {
                    "message": "Company logo uploaded successfully",
                    "company": result.data[0],
                }, 200
            else:
                return {"error": "Company not found"}, 404

        except Exception as e:
            return {"error": f"Failed to upload company logo: {str(e)}"}, 500

    def update_ai_training_status(
        self, company_id: str, status: str
    ) -> Tuple[Dict[str, Any], int]:
        """Update AI training status for a company"""
        try:
            update_data = {"ai_training_status": status}

            if status == "completed":
                update_data["ai_training_completed_at"] = datetime.utcnow().isoformat()

            result = (
                self.supabase.table("companies")
                .update(update_data)
                .eq("id", company_id)
                .execute()
            )

            if result.data:
                return {
                    "message": "AI training status updated successfully",
                    "company": result.data[0],
                }, 200
            else:
                return {"error": "Company not found"}, 404

        except Exception as e:
            return {"error": f"Failed to update AI training status: {str(e)}"}, 500
