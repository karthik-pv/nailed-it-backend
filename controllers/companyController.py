from flask import jsonify
import uuid
from supabase_client import supabase


class CompanyController:
    def create_company(self, data, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = supabase.table("companies").insert(data).execute()

            if response.data:
                return jsonify({"company": response.data[0]}), 201
            else:
                return jsonify({"error": "Creation failed"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def get_companies(self, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = supabase.table("companies").select("*").execute()
            return jsonify({"companies": response.data}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def get_company(self, company_id, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = (
                supabase.table("companies").select("*").eq("id", company_id).execute()
            )

            if response.data:
                return jsonify({"company": response.data[0]}), 200
            else:
                return jsonify({"error": "Company not found"}), 404

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def update_company(self, company_id, data, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = (
                supabase.table("companies").update(data).eq("id", company_id).execute()
            )

            if response.data:
                return jsonify({"company": response.data[0]}), 200
            else:
                return jsonify({"error": "Update failed"}), 400

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def delete_company(self, company_id, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            response = (
                supabase.table("companies").delete().eq("id", company_id).execute()
            )

            return jsonify({"success": True}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400

    def upload_media(self, files, auth_header):
        try:
            if not auth_header:
                return jsonify({"error": "Authorization required"}), 401

            token = auth_header.replace("Bearer ", "")
            supabase.auth.set_session(token, "")

            uploaded_files = {}

            for file_key, file_obj in files.items():
                if file_obj:
                    # Generate unique filename
                    file_extension = file_obj.filename.split(".")[-1]
                    unique_filename = f"{uuid.uuid4()}.{file_extension}"

                    # Upload to Supabase storage
                    response = supabase.storage.from_("company-assets").upload(
                        unique_filename,
                        file_obj.read(),
                        {"content-type": file_obj.content_type},
                    )

                    if response:
                        # Get public URL
                        public_url = supabase.storage.from_(
                            "company-media"
                        ).get_public_url(unique_filename)
                        uploaded_files[file_key] = public_url

            return jsonify({"uploaded_files": uploaded_files}), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 400
