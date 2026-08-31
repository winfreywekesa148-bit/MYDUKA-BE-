from flask import Blueprint, request, jsonify

from extensions import db
from models.user import user
from models.invitation import Invitation

reg_bp = Blueprint("reg", __name__, url_prefix="/auth")


@reg_bp.route("/register-merchant", methods=["POST"])
def register_merchant():

    data = request.get_json()

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    #check required fields
    if not name or not email or not password:
        return jsonify({
            "error": "Name, email and password are required"
        }), 400

    existing_user = user.query.filter_by(email=email).first()

    if existing_user:
        return jsonify({
            "error": "Email already registered"
        }), 409

    merchant = user(
        name=name,
        email=email,
        role="merchant"
    )

    merchant.set_password(password)

    db.session.add(merchant)
    db.session.commit()

    return jsonify({
        "message": "Merchant registered successfully"
    }), 201

# admin registration from invitation token
@reg_bp.route("/register-admin/<token>", methods=["POST"])
def register_admin(token):

    invitation = Invitation.query.filter_by(
        token=token,
        role="admin",
        used=False
    ).first()

    if not invitation:
        return jsonify({
            "error": "Invalid or expired invitation"
        }), 400

    data = request.get_json()

    name = data.get("name")
    password = data.get("password")

    if not name or not password:
        return jsonify({
            "error": "Name and password are required"
        }), 400

    use = user(
        name=name,
        email=invitation.email,
        role="admin"
    )

    use.set_password(password)

    db.session.add(use)

    invitation.used = True

    db.session.commit()

    return jsonify({
        "message": "Admin registration successful"
    }), 201
