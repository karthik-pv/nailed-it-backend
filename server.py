from flask import Flask, request, jsonify
from flask_cors import CORS
from controllers.userController import UserController
from controllers.companyController import CompanyController

app = Flask(__name__)
CORS(app)

user_controller = UserController()
company_controller = CompanyController()


# Auth routes
@app.route("/auth/register", methods=["POST"])
def register():
    return user_controller.register(request.json)


@app.route("/auth/login", methods=["POST"])
def login():
    return user_controller.login(request.json)


# User CRUD routes
@app.route("/users", methods=["GET"])
def get_users():
    return user_controller.get_users(request.headers.get("Authorization"))


@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    return user_controller.get_user(user_id, request.headers.get("Authorization"))


@app.route("/users/<user_id>", methods=["PUT"])
def update_user(user_id):
    return user_controller.update_user(
        user_id, request.json, request.headers.get("Authorization")
    )


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    return user_controller.delete_user(user_id, request.headers.get("Authorization"))


# Company CRUD routes
@app.route("/companies", methods=["POST"])
def create_company():
    return company_controller.create_company(
        request.json, request.headers.get("Authorization")
    )


@app.route("/companies", methods=["GET"])
def get_companies():
    return company_controller.get_companies(request.headers.get("Authorization"))


@app.route("/companies/<company_id>", methods=["GET"])
def get_company(company_id):
    return company_controller.get_company(
        company_id, request.headers.get("Authorization")
    )


@app.route("/companies/<company_id>", methods=["PUT"])
def update_company(company_id):
    return company_controller.update_company(
        company_id, request.json, request.headers.get("Authorization")
    )


@app.route("/companies/<company_id>", methods=["DELETE"])
def delete_company(company_id):
    return company_controller.delete_company(
        company_id, request.headers.get("Authorization")
    )


# Media upload route
@app.route("/upload", methods=["POST"])
def upload_media():
    return company_controller.upload_media(
        request.files, request.headers.get("Authorization")
    )


if __name__ == "__main__":
    app.run(debug=True)
