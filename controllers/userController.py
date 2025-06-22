from flask import jsonify
from supabase_client import supabase


class UserController:
    def register(self, data):
        try:
            print("Registration data received:", data)

            # Register user with Supabase Auth
            auth_response = supabase.auth.sign_up(
                {
                    "email": data.get("email"),
                    "password": data.get("password"),
                    "options": {"data": {"full_name": data.get("full_name")}},
                }
            )

            print("Auth response:", auth_response)

            if auth_response.user:
                # The trigger should automatically create the user record
                # But let's verify and create manually if needed
                try:
                    # Check if user was created by trigger
                    user_check = (
                        supabase.table("users")
                        .select("*")
                        .eq("id", auth_response.user.id)
                        .execute()
                    )

                    if not user_check.data:
                        # Trigger didn't work, create manually
                        user_data = {
                            "id": auth_response.user.id,
                            "full_name": data.get("full_name"),
                            "email": data.get("email"),
                            "role": "member",
                        }

                        user_response = (
                            supabase.table("users").insert(user_data).execute()
                        )
                        user_record = user_response.data[0]
                    else:
                        user_record = user_check.data[0]

                except Exception as user_error:
                    print("User table error:", user_error)
                    # If there's an issue with user table, still return auth success
                    user_record = {
                        "id": auth_response.user.id,
                        "email": data.get("email"),
                        "full_name": data.get("full_name"),
                        "role": "member",
                    }

                return (
                    jsonify(
                        {
                            "success": True,
                            "user": user_record,
                            "auth": {
                                "access_token": auth_response.session.access_token,
                                "refresh_token": auth_response.session.refresh_token,
                            },
                        }
                    ),
                    201,
                )
            else:
                return jsonify({"error": "Registration failed"}), 400

        except Exception as e:
            print("Registration error:", str(e))
            return jsonify({"error": str(e)}), 400

    def login(self, data):
        try:
            print("Login attempt for:", data.get("email"))

            response = supabase.auth.sign_in_with_password(
                {"email": data.get("email"), "password": data.get("password")}
            )

            if response.user:
                # Get user data from users table
                user_data = (
                    supabase.table("users")
                    .select("*")
                    .eq("id", response.user.id)
                    .execute()
                )

                print("User data found:", user_data.data)

                return (
                    jsonify(
                        {
                            "success": True,
                            "user": (
                                user_data.data[0]
                                if user_data.data
                                else {
                                    "id": response.user.id,
                                    "email": response.user.email,
                                    "full_name": response.user.user_metadata.get(
                                        "full_name", ""
                                    ),
                                    "role": "member",
                                }
                            ),
                            "auth": {
                                "access_token": response.session.access_token,
                                "refresh_token": response.session.refresh_token,
                            },
                        }
                    ),
                    200,
                )
            else:
                return jsonify({"error": "Login failed"}), 401

        except Exception as e:
            print("Login error:", str(e))
            return jsonify({"error": str(e)}), 401

    def get_users(self, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = supabase.table("users").select("*").execute()
            return jsonify({"users": response.data}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def get_user(self, user_id, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = supabase.table("users").select("*").eq("id", user_id).execute()

            if response.data:
                return jsonify({"user": response.data[0]}), 200
            else:
                return jsonify({"error": "User not found"}), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def update_user(self, user_id, data, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = supabase.table("users").update(data).eq("id", user_id).execute()

            if response.data:
                return jsonify({"user": response.data[0]}), 200
            else:
                return jsonify({"error": "Update failed"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def delete_user(self, user_id, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = supabase.table("users").delete().eq("id", user_id).execute()

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400
