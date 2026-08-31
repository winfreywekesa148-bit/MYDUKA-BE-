from flask import Blueprint, request, jsonify
from extensions import db
from models.clerk import Clerk
from models.records import Record
from datetime import datetime
from sqlalchemy import func

clerk_bp = Blueprint("clerk", __name__)

# A clerk route to create a new clerk
@clerk_bp.route("/clerks", methods=["POST"])
def create_clerk():
    data = request.get_json()

    clerk_name = data.get("clerk_name")
    admin_id = data.get("admin_id")
    store_id = data.get("store_id")

    if not clerk_name or not admin_id or not store_id:
        return jsonify({"error": "clerk_name, admin_id and store_id are required."}), 400

    new_clerk = Clerk(clerk_name=clerk_name, admin_id=admin_id,
        store_id=store_id )

    db.session.add(new_clerk)
    db.session.commit()

    return jsonify({"message": "Clerk created successfully.",
        "clerk_id": new_clerk.clerk_id }), 201

# Route to get all clerks
@clerk_bp.route("/clerks", methods=["GET"])
def get_clerks():
    clerks = Clerk.query.all()

    return jsonify([
        {"clerk_id": c.clerk_id, "clerk_name": c.clerk_name,
            "admin_id": c.admin_id, "store_id": c.store_id,
            "created_at": c.created_at}
        for c in clerks
    ]), 200

@clerk_bp.route("/clerk/dashboard", methods=["GET"])
def clerk_dashboard():
    records = Record.query

    received = records.with_entities(
        func.coalesce(func.sum(Record.items_received), 0)
    ).scalar()

    stock = records.with_entities(
        func.coalesce(func.sum(Record.items_in_stock), 0)
    ).scalar()

    spoilt = records.with_entities(
        func.coalesce(func.sum(Record.items_spoilt), 0)
    ).scalar()

    unpaid = records.filter_by(payment_status="unpaid").count()

    return jsonify({"received": received,
        "stock": stock,
        "spoilt": spoilt,
        "unpaid": unpaid,
        "last_updated": datetime.now().isoformat()
    }), 200

# Route to get one clerk
@clerk_bp.route("/clerks/<int:clerk_id>", methods=["GET"])
def get_clerk(clerk_id):
    clerk = Clerk.query.get(clerk_id)

    if not clerk:
        return jsonify({"error": "Clerk not found."}), 404

    return jsonify({ "clerk_id": clerk.clerk_id,
        "clerk_name": clerk.clerk_name, "admin_id": clerk.admin_id,
        "store_id": clerk.store_id, "created_at": clerk.created_at
    }), 200

# Route to update a clerk
@clerk_bp.route("/clerks/<int:clerk_id>", methods=["PATCH"])
def update_clerk(clerk_id):
    clerk = Clerk.query.get(clerk_id)

    if not clerk:
        return jsonify({"error": "Clerk not found."}), 404
    data = request.get_json()

    if "clerk_name" in data:
        clerk.clerk_name = data["clerk_name"]
    db.session.commit()

    return jsonify({"message": "Clerk updated successfully."}), 200

# Route to delete a clerk
@clerk_bp.route("/clerks/<int:clerk_id>", methods=["DELETE"])
def delete_clerk(clerk_id):
    clerk = Clerk.query.get(clerk_id)

    if not clerk:
        return jsonify({"error": "Clerk not found."}), 404

    db.session.delete(clerk)
    db.session.commit()

    return jsonify({ "message": "Clerk deleted successfully."}), 200
