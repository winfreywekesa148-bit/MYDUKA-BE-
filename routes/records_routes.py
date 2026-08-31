from flask import Blueprint, jsonify, request
from extensions import db
from models.clerk import Clerk
from models.product import Product
from models.records import Record
from models.store import Store
from models.store_admin import StoreAdmin
from models.suppliers import Supplier

records_bp = Blueprint("records_bp", __name__)


def serialize_record(record):
    store = db.session.get(Store, record.store_id)
    clerk = db.session.get(Clerk, record.clerk_id)
    return {
        "record_id": record.record_id,
        "clerk_name": clerk.clerk_name if clerk else None,
        "product_name": record.product.name if record.product else None,
        "supplier_name": record.supplier.name if record.supplier else None,
        "store_name": store.st_name if store else None,
        "items_received": record.items_received,
        "items_in_stock": record.items_in_stock,
        "items_spoilt": record.items_spoilt,
        "buying_price": float(record.buying_price),
        "selling_price": float(record.selling_price),
        "payment_status": record.payment_status,
        "created_at": record.created_at,
    }


@records_bp.route("/inventory-options", methods=["GET"])
def inventory_options():
    return jsonify({
        "stores": [store.st_name for store in Store.query.order_by(Store.st_name).all()],
        "clerks": [clerk.clerk_name for clerk in Clerk.query.order_by(Clerk.clerk_name).all()],
    }), 200


@records_bp.route("/records", methods=["POST"])
def create_record():
    data = request.get_json(silent=True) or {}
    required_fields = [
        "clerk_name", "product_name", "supplier_name", "store_name",
        "items_received", "items_in_stock", "buying_price", "selling_price",
    ]
    missing = [field for field in required_fields if data.get(field) in (None, "")]
    if missing:
        return jsonify({"error": f"{', '.join(missing)} is required"}), 400

    product_name = data["product_name"].strip()
    supplier_name = data["supplier_name"].strip()
    if not product_name or not supplier_name:
        return jsonify({"error": "Product and supplier names cannot be blank."}), 400
    store = Store.query.filter_by(st_name=data["store_name"]).first()
    clerk = Clerk.query.filter_by(clerk_name=data["clerk_name"]).first()
    if not store or not clerk:
        return jsonify({"error": "Choose a valid clerk and store."}), 400
    if clerk.store_id != store.store_id:
        return jsonify({"error": "The selected clerk does not belong to that store."}), 400

    product = Product.query.filter(Product.name.ilike(product_name)).first()
    if not product:
        product = Product(
            name=product_name,
            category=data.get("category"),
            buying_price=data["buying_price"],
            selling_price=data["selling_price"],
        )
        db.session.add(product)

    supplier = Supplier.query.filter(Supplier.name.ilike(supplier_name)).first()
    if not supplier:
        supplier = Supplier(name=supplier_name)
        db.session.add(supplier)

    db.session.flush()

    record = Record(
        clerk_id=clerk.clerk_id,
        product_id=product.product_id,
        supplier_id=supplier.supplier_id,
        store_id=store.store_id,
        admin_id=clerk.admin_id,
        items_received=data["items_received"],
        items_in_stock=data["items_in_stock"],
        items_spoilt=data.get("items_spoilt", 0),
        buying_price=data["buying_price"],
        selling_price=data["selling_price"],
        payment_status=data.get("payment_status", "unpaid"),
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"message": "Inventory record created successfully", "record": serialize_record(record)}), 201


@records_bp.route("/records", methods=["GET"])
def get_records():
    records = Record.query.order_by(Record.created_at.desc()).all()
    return jsonify([serialize_record(record) for record in records]), 200


@records_bp.route("/records/<int:record_id>", methods=["GET"])
def get_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404
    return jsonify(serialize_record(record)), 200


@records_bp.route("/records/<int:record_id>", methods=["PATCH"])
def update_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404
    data = request.get_json(silent=True) or {}
    if "store_name" in data:
        store = Store.query.filter_by(st_name=data["store_name"]).first()
        if not store:
            return jsonify({"error": "Choose a valid store or branch."}), 400
        record.store_id = store.store_id
        store_admin = StoreAdmin.query.filter_by(store_id=store.store_id, is_active=True).first()
        if store_admin:
            record.admin_id = store_admin.admin_id
    if "supplier_name" in data:
        supplier_name = data["supplier_name"].strip()
        if not supplier_name:
            return jsonify({"error": "Supplier name cannot be blank."}), 400
        supplier = Supplier.query.filter(Supplier.name.ilike(supplier_name)).first()
        if not supplier:
            supplier = Supplier(name=supplier_name)
            db.session.add(supplier)
            db.session.flush()
        record.supplier_id = supplier.supplier_id
    for field in ("items_received", "items_in_stock", "items_spoilt", "buying_price", "selling_price", "payment_status"):
        if field in data:
            setattr(record, field, data[field])
    db.session.commit()
    return jsonify({"message": "Record updated successfully", "record": serialize_record(record)}), 200


@records_bp.route("/records/<int:record_id>", methods=["DELETE"])
def delete_record(record_id):
    record = db.session.get(Record, record_id)
    if not record:
        return jsonify({"error": "Record not found"}), 404
    db.session.delete(record)
    db.session.commit()
    return jsonify({"message": "Record deleted successfully"}), 200


