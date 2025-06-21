import os
import logging
from flask import Flask, jsonify, request, current_app
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge
from functools import wraps
import jwt

from supabase_client import supabase
from auth import auth_service
from storage import storage_service
from companies import company_service
from users import user_service

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10MB max file size

# Enable CORS
CORS(
    app,
    origins=[
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    supports_credentials=True,
)

# JWT Secret (get from environment or Supabase)
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")


def require_auth(f):
    """
    Decorator to require authentication for routes
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Get token from Authorization header
            auth_header = request.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return (
                    jsonify({"error": "Missing or invalid authorization header"}),
                    401,
                )

            token = auth_header.replace("Bearer ", "")

            # Verify token with Supabase
            try:
                # Use Supabase client to verify token
                user = supabase.auth.get_user(token)
                if not user:
                    return jsonify({"error": "Invalid token"}), 401

                # Add user info to request context
                request.current_user = user.user

            except Exception as e:
                return jsonify({"error": "Token verification failed"}), 401

            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Auth middleware error: {str(e)}")
            return jsonify({"error": "Authentication failed"}), 401

    return decorated_function


def handle_file_upload():
    """
    Helper function to handle file uploads from request
    Returns: (file_data, filename, error)
    """
    try:
        logger.info(f"Request files: {request.files}")
        logger.info(f"Request form: {request.form}")
        logger.info(f"Request content type: {request.content_type}")

        # Check if file is in request
        if "file" not in request.files:
            logger.error("No 'file' key found in request.files")
            return None, None, "No file provided"

        file = request.files["file"]
        logger.info(f"File object: {file}")
        logger.info(f"File filename: {file.filename}")
        logger.info(f"File content type: {file.content_type}")

        if file.filename == "" or file.filename is None:
            logger.error("Empty filename provided")
            return None, None, "No file selected"

        # Read file data
        file.seek(0)  # Reset file pointer to beginning
        file_data = file.read()
        logger.info(f"File data length: {len(file_data) if file_data else 0} bytes")

        if not file_data or len(file_data) == 0:
            logger.error("Empty file data")
            return None, None, "Empty file provided"

        # Reset file pointer for potential future reads
        file.seek(0)

        logger.info(f"File upload successful: {file.filename}, {len(file_data)} bytes")
        return file_data, file.filename, None

    except Exception as e:
        logger.error(f"File upload handler error: {str(e)}")
        import traceback

        logger.error(f"File upload traceback: {traceback.format_exc()}")
        return None, None, f"File upload error: {str(e)}"


# Error handlers
@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({"error": "File size exceeds 10MB limit"}), 413


@app.errorhandler(404)
def handle_not_found(e):
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def handle_internal_error(e):
    logger.error(f"Internal server error: {str(e)}")
    return jsonify({"error": "Internal server error"}), 500


# Health check
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "NailedIt Backend API"}), 200


# Authentication routes
@app.route("/auth/signup", methods=["POST"])
def signup():
    """Register a new user"""
    try:
        data = request.get_json()
        logger.info(f"Signup request received for email: {data.get('email')}")

        # Validate required fields
        required_fields = ["email", "password", "full_name"]
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Register user
        user_data, error = auth_service.signup_user(
            email=data["email"], password=data["password"], full_name=data["full_name"]
        )

        if error:
            logger.error(f"Auth service returned error: {error}")
            return jsonify({"error": error}), 400

        logger.info(f"Auth service returned user_data type: {type(user_data)}")
        logger.info(
            f"User data keys: {user_data.keys() if isinstance(user_data, dict) else 'Not a dict'}"
        )

        response_data = {"message": "User registered successfully", "user": user_data}
        logger.info(f"About to jsonify response_data: {type(response_data)}")

        return jsonify(response_data), 201

    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": "Registration failed"}), 500


@app.route("/auth/signin", methods=["POST"])
def signin():
    """Sign in a user"""
    try:
        data = request.get_json()

        # Validate required fields
        if not data.get("email") or not data.get("password"):
            return jsonify({"error": "Email and password are required"}), 400

        # Sign in user
        user_data, error = auth_service.signin_user(
            email=data["email"], password=data["password"]
        )

        if error:
            return jsonify({"error": error}), 401

        return jsonify({"message": "Sign in successful", "user": user_data}), 200

    except Exception as e:
        logger.error(f"Signin error: {str(e)}")
        return jsonify({"error": "Sign in failed"}), 500


@app.route("/auth/signout", methods=["POST"])
@require_auth
def signout():
    """Sign out current user"""
    try:
        success, error = auth_service.signout_user()

        if error:
            return jsonify({"error": error}), 400

        return jsonify({"message": "Signed out successfully"}), 200

    except Exception as e:
        logger.error(f"Signout error: {str(e)}")
        return jsonify({"error": "Sign out failed"}), 500


@app.route("/auth/user", methods=["GET"])
@require_auth
def get_current_user():
    """Get current user profile"""
    try:
        user_profile = user_service.get_user_with_company(request.current_user.id)

        if not user_profile:
            return jsonify({"error": "User profile not found"}), 404

        return jsonify({"user": user_profile}), 200

    except Exception as e:
        logger.error(f"Get current user error: {str(e)}")
        return jsonify({"error": "Failed to get user profile"}), 500


# Company routes
@app.route("/companies", methods=["POST"])
@require_auth
def create_company():
    """Create a new company"""
    try:
        data = request.get_json()

        # Create company
        company, error = company_service.create_company(data, request.current_user.id)

        if error:
            return jsonify({"error": error}), 400

        return (
            jsonify({"message": "Company created successfully", "company": company}),
            201,
        )

    except Exception as e:
        logger.error(f"Create company error: {str(e)}")
        return jsonify({"error": "Failed to create company"}), 500


@app.route("/companies/<company_id>", methods=["GET"])
@require_auth
def get_company(company_id):
    """Get company by ID"""
    try:
        company = company_service.get_company(company_id)

        if not company:
            return jsonify({"error": "Company not found"}), 404

        # Check if user has access to this company
        user_profile = user_service.get_user(request.current_user.id)
        if not user_profile or user_profile.get("company_id") != company_id:
            return jsonify({"error": "Unauthorized access"}), 403

        return jsonify({"company": company}), 200

    except Exception as e:
        logger.error(f"Get company error: {str(e)}")
        return jsonify({"error": "Failed to get company"}), 500


@app.route("/companies/<company_id>", methods=["PUT"])
@require_auth
def update_company(company_id):
    """Update company information"""
    try:
        data = request.get_json()

        # Update company
        updated_company, error = company_service.update_company(
            company_id, data, request.current_user.id
        )

        if error:
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {"message": "Company updated successfully", "company": updated_company}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Update company error: {str(e)}")
        return jsonify({"error": "Failed to update company"}), 500


@app.route("/companies/<company_id>", methods=["DELETE"])
@require_auth
def delete_company(company_id):
    """Delete company"""
    try:
        success, error = company_service.delete_company(
            company_id, request.current_user.id
        )

        if error:
            return jsonify({"error": error}), 400

        return jsonify({"message": "Company deleted successfully"}), 200

    except Exception as e:
        logger.error(f"Delete company error: {str(e)}")
        return jsonify({"error": "Failed to delete company"}), 500


@app.route("/companies/<company_id>/users", methods=["GET"])
@require_auth
def get_company_users(company_id):
    """Get all users in a company"""
    try:
        users, error = company_service.get_company_users(
            company_id, request.current_user.id
        )

        if error:
            return jsonify({"error": error}), 400

        return jsonify({"users": users}), 200

    except Exception as e:
        logger.error(f"Get company users error: {str(e)}")
        return jsonify({"error": "Failed to get company users"}), 500


@app.route("/companies/<company_id>/logo", methods=["POST"])
@require_auth
def upload_company_logo(company_id):
    """Upload company logo"""
    try:
        file_data, filename, error = handle_file_upload()
        if error:
            return jsonify({"error": error}), 400

        # Upload logo
        logo_url, error = company_service.upload_company_logo(
            company_id, file_data, filename, request.current_user.id
        )

        if error:
            return jsonify({"error": error}), 400

        return (
            jsonify({"message": "Logo uploaded successfully", "logo_url": logo_url}),
            200,
        )

    except Exception as e:
        logger.error(f"Upload company logo error: {str(e)}")
        return jsonify({"error": "Failed to upload logo"}), 500


@app.route("/companies/<company_id>/pricing-document", methods=["POST"])
@require_auth
def upload_pricing_document(company_id):
    """Upload pricing document"""
    try:
        file_data, filename, error = handle_file_upload()
        if error:
            return jsonify({"error": error}), 400

        # Upload document
        document_url, error = company_service.upload_pricing_document(
            company_id, file_data, filename, request.current_user.id
        )

        if error:
            return jsonify({"error": error}), 400

        return (
            jsonify(
                {
                    "message": "Pricing document uploaded successfully",
                    "document_url": document_url,
                }
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Upload pricing document error: {str(e)}")
        return jsonify({"error": "Failed to upload pricing document"}), 500


@app.route("/companies/join", methods=["POST"])
@require_auth
def join_company():
    """Join an existing company by email"""
    try:
        data = request.get_json()

        if not data.get("company_email"):
            return jsonify({"error": "Company email is required"}), 400

        # Find and join company
        company_id, error = auth_service.join_existing_company(
            request.current_user.id, data["company_email"]
        )

        if error:
            return jsonify({"error": error}), 400

        # Get company details
        company = company_service.get_company(company_id)

        return (
            jsonify({"message": "Successfully joined company", "company": company}),
            200,
        )

    except Exception as e:
        logger.error(f"Join company error: {str(e)}")
        return jsonify({"error": "Failed to join company"}), 500


# User routes
@app.route("/users/<user_id>", methods=["GET"])
@require_auth
def get_user(user_id):
    """Get user by ID"""
    try:
        # Users can only get their own profile or company members
        if user_id != request.current_user.id:
            # Check if requesting user is in the same company
            requesting_user = user_service.get_user(request.current_user.id)
            target_user = user_service.get_user(user_id)

            if not requesting_user or not target_user:
                return jsonify({"error": "User not found"}), 404

            if requesting_user.get("company_id") != target_user.get("company_id"):
                return jsonify({"error": "Unauthorized access"}), 403

        user = user_service.get_user_with_company(user_id)

        if not user:
            return jsonify({"error": "User not found"}), 404

        return jsonify({"user": user}), 200

    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        return jsonify({"error": "Failed to get user"}), 500


@app.route("/users/<user_id>", methods=["PUT"])
@require_auth
def update_user(user_id):
    """Update user information"""
    try:
        data = request.get_json()

        # Update user
        updated_user, error = user_service.update_user(
            user_id, data, request.current_user.id
        )

        if error:
            return jsonify({"error": error}), 400

        return (
            jsonify({"message": "User updated successfully", "user": updated_user}),
            200,
        )

    except Exception as e:
        logger.error(f"Update user error: {str(e)}")
        return jsonify({"error": "Failed to update user"}), 500


@app.route("/users/<user_id>/leave-company", methods=["POST"])
@require_auth
def leave_company(user_id):
    """User leaves their company"""
    try:
        success, error = user_service.leave_company(user_id, request.current_user.id)

        if error:
            return jsonify({"error": error}), 400

        return jsonify({"message": "Successfully left company"}), 200

    except Exception as e:
        logger.error(f"Leave company error: {str(e)}")
        return jsonify({"error": "Failed to leave company"}), 500


# Onboarding route (combines user and company creation)
@app.route("/onboarding/complete", methods=["POST"])
@require_auth
def complete_onboarding():
    """Complete the onboarding process"""
    try:
        data = request.get_json()

        # Create company first
        company_data = {
            "company_name": data.get("company_name"),
            "owner_name": data.get("owner_name"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "website": data.get("website"),
            "description": data.get("description"),
            "logo_url": data.get("logo_url"),
            "pricing_document_url": data.get("pricing_document_url"),
        }

        company, error = company_service.create_company(
            company_data, request.current_user.id
        )

        if error:
            return jsonify({"error": error}), 400

        # Get updated user profile with company
        user_profile = user_service.get_user_with_company(request.current_user.id)

        return (
            jsonify(
                {
                    "message": "Onboarding completed successfully",
                    "user": user_profile,
                    "company": company,
                }
            ),
            201,
        )

    except Exception as e:
        logger.error(f"Complete onboarding error: {str(e)}")
        return jsonify({"error": "Failed to complete onboarding"}), 500


# File upload routes (both old and new paths for compatibility)
@app.route("/upload/logo", methods=["POST"])
@app.route("/files/upload/logo", methods=["POST"])
@require_auth
def upload_logo():
    """Upload a logo file and return URL"""
    try:
        logger.info(f"Logo upload request from user: {request.current_user.id}")
        logger.info(f"Request headers: {dict(request.headers)}")

        file_data, filename, error = handle_file_upload()
        if error:
            logger.error(f"File upload error: {error}")
            return jsonify({"error": error}), 400

        logger.info(f"File received: {filename}, size: {len(file_data)} bytes")

        # Validate file
        is_valid, validation_error = storage_service.validate_file(
            file_data, filename, max_size_mb=5
        )
        if not is_valid:
            logger.error(f"File validation failed: {validation_error}")
            return jsonify({"error": validation_error}), 400

        logger.info(f"File validation passed for: {filename}")

        # Upload file
        file_url, upload_error = storage_service.upload_file(
            file_data, filename, request.current_user.id, "logo"
        )

        if upload_error:
            logger.error(f"Storage upload error: {upload_error}")
            return jsonify({"error": upload_error}), 400

        logger.info(f"File uploaded successfully: {file_url}")
        return jsonify({"message": "File uploaded successfully", "url": file_url}), 200

    except Exception as e:
        logger.error(f"Upload logo error: {str(e)}")
        import traceback

        logger.error(f"Upload logo traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to upload file"}), 500


@app.route("/upload/document", methods=["POST"])
@app.route("/files/upload/document", methods=["POST"])
@require_auth
def upload_document():
    """Upload a document file and return URL"""
    try:
        logger.info(f"Document upload request from user: {request.current_user.id}")
        logger.info(f"Request headers: {dict(request.headers)}")

        file_data, filename, error = handle_file_upload()
        if error:
            logger.error(f"File upload error: {error}")
            return jsonify({"error": error}), 400

        logger.info(f"File received: {filename}, size: {len(file_data)} bytes")

        # Validate file
        is_valid, validation_error = storage_service.validate_file(
            file_data, filename, max_size_mb=10
        )
        if not is_valid:
            logger.error(f"File validation failed: {validation_error}")
            return jsonify({"error": validation_error}), 400

        logger.info(f"File validation passed for: {filename}")

        # Upload file
        file_url, upload_error = storage_service.upload_file(
            file_data, filename, request.current_user.id, "document"
        )

        if upload_error:
            logger.error(f"Storage upload error: {upload_error}")
            return jsonify({"error": upload_error}), 400

        logger.info(f"File uploaded successfully: {file_url}")
        return jsonify({"message": "File uploaded successfully", "url": file_url}), 200

    except Exception as e:
        logger.error(f"Upload document error: {str(e)}")
        import traceback

        logger.error(f"Upload document traceback: {traceback.format_exc()}")
        return jsonify({"error": "Failed to upload file"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"

    logger.info(f"Starting NailedIt Backend API on port {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
