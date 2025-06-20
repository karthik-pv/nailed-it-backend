from flask import request, session, jsonify
from supabase import Client
from functools import wraps
from controller import UserController


def login_required(f):
    """Decorator to require authentication for routes"""

    @wraps(f)
    def decorated(*args, **kwargs):
        if "user" not in session:
            return jsonify({"error": "Authentication required"}), 401
        return f(*args, **kwargs)

    return decorated


def handle_login(supabase: Client):
    """Handle user login with email and password"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
        else:
            email = request.form.get("email")
            password = request.form.get("password")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if response.user:
            session["user"] = response.user.dict()
            return jsonify(
                {
                    "user": response.user.dict(),
                    "session": response.session.dict() if response.session else None,
                    "message": "Login successful",
                }
            )
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({"error": "Login failed", "details": str(e)}), 500


def handle_signup(supabase: Client):
    """Handle user signup with email and password - basic registration only"""
    try:
        # Handle both JSON and form data
        if request.is_json:
            data = request.get_json()
            email = data.get("email")
            password = data.get("password")
            full_name = data.get("fullName")
        else:
            email = request.form.get("email")
            password = request.form.get("password")
            full_name = request.form.get("fullName")

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        # Sign up with Supabase Auth only - no company creation yet
        user_data = {"email": email, "password": password}
        if full_name:
            user_data["options"] = {"data": {"full_name": full_name}}

        response = supabase.auth.sign_up(user_data)

        if response.user:
            # Create user record in our users table
            user_controller = UserController(supabase)
            user_record_data = {
                "id": response.user.id,
                "company_id": None,  # No company yet
                "full_name": full_name,
                "role": "owner",
                "onboarding_completed": False,
            }

            user_record_response = (
                supabase.table("users").insert(user_record_data).execute()
            )

            session["user"] = response.user.dict()
            return jsonify(
                {
                    "user": response.user.dict(),
                    "session": response.session.dict() if response.session else None,
                    "message": "Signup successful - Complete onboarding to create your company",
                }
            )
        else:
            return jsonify({"error": "Signup failed"}), 400

    except Exception as e:
        print(f"Signup error: {e}")
        return jsonify({"error": "Signup failed", "details": str(e)}), 500


def handle_complete_onboarding(supabase: Client):
    """Handle onboarding completion with company creation"""
    try:
        if not request.is_json:
            return jsonify({"error": "JSON data required"}), 400

        data = request.get_json()

        # Get user ID from session or request
        user_data = session.get("user")
        if not user_data:
            return jsonify({"error": "User not authenticated"}), 401

        user_id = user_data.get("id")
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400

        # Extract company data from request
        company_data = {
            "companyName": data.get("companyName"),
            "ownerName": data.get("ownerName"),
            "email": data.get("email"),
            "phone": data.get("phone"),
            "website": data.get("website"),
            "description": data.get("description"),
            "logoUrl": data.get("logoUrl"),
            "pricingDocumentUrl": data.get("pricingDocumentUrl"),
            "selectedPlan": data.get("selectedPlan", "professional"),
            "planDetails": data.get("planDetails", {}),
        }

        # Validate required fields
        required_fields = ["companyName", "ownerName", "email", "phone"]
        missing_fields = [
            field for field in required_fields if not company_data.get(field)
        ]

        if missing_fields:
            return (
                jsonify(
                    {"error": f"Missing required fields: {', '.join(missing_fields)}"}
                ),
                400,
            )

        # Use controller to complete onboarding
        user_controller = UserController(supabase)

        # Check if payment is required (for now, we'll create company immediately)
        # Later, you can add payment gateway logic here
        create_company = True  # Set to False if payment fails

        result, status_code = user_controller.complete_onboarding(user_id, company_data)

        return jsonify(result), status_code

    except Exception as e:
        print(f"Onboarding completion error: {e}")
        return (
            jsonify({"error": "Onboarding completion failed", "details": str(e)}),
            500,
        )


def handle_skip_onboarding(supabase: Client):
    """Handle skipping onboarding - mark user as onboarding completed without company"""
    try:
        # Get user ID from session
        user_data = session.get("user")
        if not user_data:
            return jsonify({"error": "User not authenticated"}), 401

        user_id = user_data.get("id")
        if not user_id:
            return jsonify({"error": "User ID not found"}), 400

        # Update user record to mark onboarding as completed
        update_result = (
            supabase.table("users")
            .update({"onboarding_completed": True})
            .eq("id", user_id)
            .execute()
        )

        if update_result.data:
            # Get updated user info
            user_controller = UserController(supabase)
            result, status_code = user_controller.get_user_with_company(user_id)

            if status_code == 200:
                return (
                    jsonify(
                        {
                            "message": "Onboarding skipped successfully",
                            "user": result.get("user"),
                        }
                    ),
                    200,
                )
            else:
                return jsonify(result), status_code
        else:
            return jsonify({"error": "Failed to update user record"}), 500

    except Exception as e:
        print(f"Skip onboarding error: {e}")
        return (
            jsonify({"error": "Failed to skip onboarding", "details": str(e)}),
            500,
        )


def handle_logout():
    """Handle user logout"""
    try:
        session.pop("user", None)
        return jsonify({"message": "Logout successful"})
    except Exception as e:
        return jsonify({"error": "Logout failed", "details": str(e)}), 500


def get_current_user(supabase: Client):
    """Get current authenticated user with company information"""
    try:
        user_data = session.get("user")
        if not user_data:
            return jsonify({"error": "User not authenticated"}), 401

        user_id = user_data.get("id")
        user_controller = UserController(supabase)
        result, status_code = user_controller.get_user_with_company(user_id)

        return jsonify(result), status_code

    except Exception as e:
        return jsonify({"error": "Failed to get user data", "details": str(e)}), 500


def handle_google_oauth(supabase_url: str):
    """Handle Google OAuth redirect"""
    from flask import redirect

    redirect_url = f"{supabase_url}/auth/v1/authorize?provider=google&redirect_to=http://localhost:5000/auth/callback"
    return redirect(redirect_url)


def handle_oauth_callback():
    """Handle OAuth callback"""
    return "Google OAuth successful. Frontend should parse the access_token from URL fragment."
