import os
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Tuple, List
from supabase import Client
from supabase_client import supabase

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StorageService:
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.bucket_name = "company-assets"

    def upload_file(
        self,
        file_data: bytes,
        file_name: str,
        user_id: str,
        file_type: str = "document",
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Upload a file to Supabase Storage
        Args:
            file_data: The file bytes
            file_name: Original filename
            user_id: User ID for folder organization
            file_type: Type of file ('logo', 'document', etc.)
        Returns: (file_url, error_message)
        """
        try:
            logger.info(
                f"Starting file upload: {file_name}, size: {len(file_data)} bytes"
            )

            # Generate unique filename
            file_extension = os.path.splitext(file_name)[1]
            unique_filename = f"{uuid.uuid4()}{file_extension}"

            # Create folder structure: user_id/file_type/filename
            file_path = f"{user_id}/{file_type}/{unique_filename}"
            logger.info(f"Upload path: {file_path}")

            # Get content type
            content_type = self._get_content_type(file_extension)
            logger.info(f"Content type: {content_type}")

            # Upload file to Supabase Storage
            try:
                response = self.supabase.storage.from_(self.bucket_name).upload(
                    file_path,
                    file_data,
                    file_options={
                        "content-type": content_type,
                        "cache-control": "3600",
                    },
                )
                logger.info(f"Supabase upload response: {response}")

            except Exception as upload_error:
                logger.error(f"Supabase upload failed: {str(upload_error)}")
                # Try to get more specific error info
                error_msg = str(upload_error)
                if "already exists" in error_msg.lower():
                    # If file exists, try with a different name
                    unique_filename = f"{uuid.uuid4()}-{int(datetime.now().timestamp())}{file_extension}"
                    file_path = f"{user_id}/{file_type}/{unique_filename}"
                    logger.info(f"Retrying with new path: {file_path}")

                    response = self.supabase.storage.from_(self.bucket_name).upload(
                        file_path,
                        file_data,
                        file_options={
                            "content-type": content_type,
                            "cache-control": "3600",
                        },
                    )
                else:
                    raise upload_error

            # Check if upload was successful
            if response and not hasattr(response, "error"):
                try:
                    # Get public URL
                    public_url = self.supabase.storage.from_(
                        self.bucket_name
                    ).get_public_url(file_path)

                    logger.info(f"File uploaded successfully: {file_path}")
                    logger.info(f"Public URL: {public_url}")
                    return public_url, None

                except Exception as url_error:
                    logger.error(f"Error getting public URL: {str(url_error)}")
                    return (
                        None,
                        f"Upload succeeded but failed to get public URL: {str(url_error)}",
                    )
            else:
                error_msg = "Unknown upload error"
                if hasattr(response, "error") and response.error:
                    error_msg = str(response.error)
                logger.error(f"Upload failed: {error_msg}")
                return None, f"Failed to upload file: {error_msg}"

        except Exception as e:
            logger.error(f"File upload error: {str(e)}")
            import traceback

            logger.error(f"Upload traceback: {traceback.format_exc()}")
            return None, f"File upload failed: {str(e)}"

    def delete_file(self, file_url: str, user_id: str) -> Tuple[bool, Optional[str]]:
        """
        Delete a file from Supabase Storage
        Args:
            file_url: The public URL of the file
            user_id: User ID for security check
        Returns: (success, error_message)
        """
        try:
            # Extract file path from URL
            file_path = self._extract_path_from_url(file_url)

            # Verify user owns this file
            if not file_path.startswith(user_id):
                return False, "Unauthorized to delete this file"

            # Delete from storage
            response = self.supabase.storage.from_(self.bucket_name).remove([file_path])

            if response:
                logger.info(f"File deleted successfully: {file_path}")
                return True, None
            else:
                return False, "Failed to delete file"

        except Exception as e:
            logger.error(f"File deletion error: {str(e)}")
            return False, f"File deletion failed: {str(e)}"

    def update_file(
        self,
        old_file_url: str,
        new_file_data: bytes,
        new_file_name: str,
        user_id: str,
        file_type: str = "document",
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Update an existing file (delete old, upload new)
        Args:
            old_file_url: URL of the file to replace
            new_file_data: New file bytes
            new_file_name: New filename
            user_id: User ID
            file_type: Type of file
        Returns: (new_file_url, error_message)
        """
        try:
            # Delete old file if it exists
            if old_file_url:
                delete_success, delete_error = self.delete_file(old_file_url, user_id)
                if not delete_success:
                    logger.warning(f"Could not delete old file: {delete_error}")

            # Upload new file
            return self.upload_file(new_file_data, new_file_name, user_id, file_type)

        except Exception as e:
            logger.error(f"File update error: {str(e)}")
            return None, f"File update failed: {str(e)}"

    def get_file_info(self, file_url: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from Supabase Storage
        Args:
            file_url: The public URL of the file
        Returns: File info dict or None
        """
        try:
            file_path = self._extract_path_from_url(file_url)

            # Get file info from storage
            response = self.supabase.storage.from_(self.bucket_name).list(
                path=os.path.dirname(file_path), limit=1000
            )

            if response:
                # Find the specific file
                filename = os.path.basename(file_path)
                for file_info in response:
                    if file_info["name"] == filename:
                        return file_info

            return None

        except Exception as e:
            logger.error(f"Get file info error: {str(e)}")
            return None

    def list_user_files(
        self, user_id: str, file_type: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], Optional[str]]:
        """
        List all files for a user
        Args:
            user_id: User ID
            file_type: Optional file type filter
        Returns: (file_list, error_message)
        """
        try:
            # Construct path
            if file_type:
                path = f"{user_id}/{file_type}"
            else:
                path = user_id

            # List files
            response = self.supabase.storage.from_(self.bucket_name).list(
                path=path, limit=1000
            )

            if response:
                # Add full URLs to each file
                files_with_urls = []
                for file_info in response:
                    file_path = f"{path}/{file_info['name']}"
                    public_url = self.supabase.storage.from_(
                        self.bucket_name
                    ).get_public_url(file_path)

                    files_with_urls.append(
                        {**file_info, "url": public_url, "path": file_path}
                    )

                return files_with_urls, None
            else:
                return [], "Failed to list files"

        except Exception as e:
            logger.error(f"List files error: {str(e)}")
            return [], f"Failed to list files: {str(e)}"

    def _extract_path_from_url(self, url: str) -> str:
        """
        Extract file path from public URL
        """
        # Remove the base URL and extract the path
        # URL format: https://project.supabase.co/storage/v1/object/public/bucket/path
        try:
            parts = url.split(f"/object/public/{self.bucket_name}/")
            if len(parts) > 1:
                return parts[1]
            return ""
        except:
            return ""

    def _get_content_type(self, file_extension: str) -> str:
        """
        Get content type based on file extension
        """
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".txt": "text/plain",
            ".csv": "text/csv",
        }

        return content_types.get(file_extension.lower(), "application/octet-stream")

    def validate_file(
        self, file_data: bytes, file_name: str, max_size_mb: int = 10
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate file before upload
        Args:
            file_data: File bytes
            file_name: Original filename
            max_size_mb: Maximum file size in MB
        Returns: (is_valid, error_message)
        """
        try:
            # Check file size
            file_size_mb = len(file_data) / (1024 * 1024)
            if file_size_mb > max_size_mb:
                return False, f"File size exceeds {max_size_mb}MB limit"

            # Check file extension
            file_extension = os.path.splitext(file_name)[1].lower()
            allowed_extensions = {
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
                ".webp",
                ".pdf",
                ".doc",
                ".docx",
                ".xls",
                ".xlsx",
                ".txt",
                ".csv",
            }

            if file_extension not in allowed_extensions:
                return False, f"File type {file_extension} not allowed"

            return True, None

        except Exception as e:
            logger.error(f"File validation error: {str(e)}")
            return False, f"File validation failed: {str(e)}"


# Initialize storage service
storage_service = StorageService(supabase)
