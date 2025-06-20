from flask import Flask, request, session, jsonify
from flask_cors import CORS
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from auth import (
    handle_login,
    handle_signup,
    handle_complete_onboarding,
    handle_skip_onboarding,
    handle_logout,
    get_current_user,
    handle_google_oauth,
    handle_oauth_callback,
    login_required,
)
import uuid
import mimetypes

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "your-secret-key-here")

# Configure CORS - Fix the port to match frontend
CORS(
    app,
    origins=["*"],
    supports_credentials=True,
    allow_headers=["Content-Type", "Authorization"],
    methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
)

# Supabase configuration
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
    )

supabase: Client = create_client(supabase_url, supabase_key)


@app.route("/")
def home():
    return jsonify({"message": "Nailed It Backend API", "status": "running"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    return handle_login(supabase)


@app.route("/api/auth/signup", methods=["POST"])
def signup():
    return handle_signup(supabase)


@app.route("/api/auth/complete-onboarding", methods=["POST"])
@login_required
def complete_onboarding():
    return handle_complete_onboarding(supabase)


@app.route("/api/auth/skip-onboarding", methods=["POST"])
@login_required
def skip_onboarding():
    return handle_skip_onboarding(supabase)


@app.route("/api/auth/logout", methods=["POST"])
def logout():
    return handle_logout()


@app.route("/api/auth/user", methods=["GET"])
@login_required
def current_user():
    return get_current_user(supabase)


@app.route("/api/auth/google", methods=["GET"])
def google_oauth():
    return handle_google_oauth(supabase_url)


@app.route("/auth/callback", methods=["GET"])
def oauth_callback():
    return handle_oauth_callback()


# Company management endpoints
@app.route("/api/company/update", methods=["PUT"])
@login_required
def update_company():
    """Update company information"""
    try:
        from controller import UserController

        if not request.is_json:
            return jsonify({"error": "JSON data required"}), 400

        data = request.get_json()
        user_data = session.get("user")

        if not user_data:
            return jsonify({"error": "User not authenticated"}), 401

        user_id = user_data.get("id")
        user_controller = UserController(supabase)

        # Get user's company ID first
        user_info, _ = user_controller.get_user_with_company(user_id)
        if not user_info.get("company"):
            return jsonify({"error": "No company associated with user"}), 400

        company_id = user_info["company"]["id"]
        result, status_code = user_controller.update_company(company_id, data)

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"error": "Failed to update company", "details": str(e)}), 500


@app.route("/api/company/payment-status", methods=["PUT"])
@login_required
def update_payment_status():
    """Update payment status for company"""
    try:
        from controller import UserController

        if not request.is_json:
            return jsonify({"error": "JSON data required"}), 400

        data = request.get_json()
        user_data = session.get("user")

        if not user_data:
            return jsonify({"error": "User not authenticated"}), 401

        user_id = user_data.get("id")
        user_controller = UserController(supabase)

        # Get user's company ID first
        user_info, _ = user_controller.get_user_with_company(user_id)
        if not user_info.get("company"):
            return jsonify({"error": "No company associated with user"}), 400

        company_id = user_info["company"]["id"]
        payment_status = data.get("payment_status")
        subscription_status = data.get("subscription_status")

        result, status_code = user_controller.update_payment_status(
            company_id, payment_status, subscription_status
        )

        return jsonify(result), status_code

    except Exception as e:
        return (
            jsonify({"error": "Failed to update payment status", "details": str(e)}),
            500,
        )


# File upload endpoint
@app.route("/api/upload", methods=["POST"])
@login_required
def upload_file():
    """Upload file to Supabase storage"""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files["file"]
        file_type = request.form.get("type", "document")  # 'logo' or 'document'

        if file.filename == "":
            return jsonify({"error": "No file selected"}), 400

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Determine bucket based on file type
        bucket_name = "assets"

        # Upload to Supabase storage
        file_data = file.read()

        # Get MIME type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = "application/octet-stream"

        # Upload file
        result = supabase.storage.from_(bucket_name).upload(
            unique_filename, file_data, {"content-type": mime_type}
        )

        if hasattr(result, "error") and result.error:
            return jsonify({"error": f"Upload failed: {result.error}"}), 500

        # Get public URL
        public_url = supabase.storage.from_(bucket_name).get_public_url(unique_filename)

        return (
            jsonify({"success": True, "url": public_url, "filename": unique_filename}),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Upload failed: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
