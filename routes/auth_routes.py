from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from models.user import user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    use = user.query.filter_by(email=email).first()

    #find user by email
    if not use:
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    #check password
    if not use.check_password(password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    #check acc is active
    if not use.is_active:
        return jsonify({
            "error": "Your account has been deactivated"
        }), 403

    # Store user ID and role inside JWT
    access_token = create_access_token(
        identity=str(use.id),
        additional_claims={
            "role": use.role
        }
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": use.id,
            "name": use.name,
            "email": use.email,
            "role": use.role
        }
    }), 200
