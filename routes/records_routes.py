from flask import Blueprint, jsonify, request

from extensions import db

from models.clerk import Clerk
from models.product import Product
from models.records import Record
from models.store import Store
from models.suppliers import Supplier


records_bp = Blueprint("records_bp", __name__)


# ============================================================
# SERIALIZE RECORD
# ============================================================

def serialize_record(record):

    store = db.session.get(Store, record.store_id)

    clerk = db.session.get(Clerk, record.clerk_id)

    return {
        "record_id": record.record_id,

        "clerk_id": record.clerk_id,
        "clerk_name": clerk.clerk_name if clerk else None,

        "store_id": record.store_id,
        "store_name": store.st_name if store else None,

        "product_id": record.product_id,
        "product_name": (
            record.product.name
            if record.product
            else None
        ),

        "supplier_id": record.supplier_id,
        "supplier_name": (
            record.supplier.name
            if record.supplier
            else None
        ),

        "admin_id": record.admin_id,

        "items_received": record.items_received,
        "items_in_stock": record.items_in_stock,
        "items_spoilt": record.items_spoilt,

        "buying_price": float(record.buying_price),
        "selling_price": float(record.selling_price),

        "payment_status": record.payment_status,

        "created_at": record.created_at.isoformat()
        if record.created_at
        else None,
    }


# ============================================================
# GET CLERKS AND STORES
# ============================================================
# This route is optional now because the React form uses IDs.
# It is kept in case another part of your frontend still needs it.

@records_bp.route("/inventory-options", methods=["GET"])
def inventory_options():

    stores = Store.query.order_by(
        Store.st_name
    ).all()

    clerks = Clerk.query.order_by(
        Clerk.clerk_name
    ).all()

    return jsonify({
        "stores": [
            {
                "store_id": store.store_id,
                "store_name": store.st_name
            }
            for store in stores
        ],

        "clerks": [
            {
                "clerk_id": clerk.clerk_id,
                "clerk_name": clerk.clerk_name,
                "store_id": clerk.store_id
            }
            for clerk in clerks
        ]
    }), 200


# ============================================================
# CREATE INVENTORY RECORD
# ============================================================

@records_bp.route("/records", methods=["POST"])
def create_record():

    try:

        # ----------------------------------------------------
        # GET JSON
        # ----------------------------------------------------

        data = request.get_json(silent=True) or {}

        print("====================================")
        print("CREATE RECORD REQUEST")
        print("DATA:", data)
        print("====================================")


        # ----------------------------------------------------
        # REQUIRED FIELDS
        # ----------------------------------------------------

        required_fields = [
            "clerk_id",
            "store_id",
            "product_name",
            "supplier_name",
            "items_received",
            "items_in_stock",
            "buying_price",
            "selling_price",
        ]

        missing = [
            field
            for field in required_fields
            if data.get(field) in (None, "")
        ]

        if missing:

            return jsonify({
                "error": f"{', '.join(missing)} is required"
            }), 400


        # ----------------------------------------------------
        # CONVERT IDS
        # ----------------------------------------------------

        try:

            clerk_id = int(data["clerk_id"])
            store_id = int(data["store_id"])

        except (ValueError, TypeError):

            return jsonify({
                "error": "clerk_id and store_id must be valid numbers"
            }), 400


        # ----------------------------------------------------
        # FIND CLERK
        # ----------------------------------------------------

        clerk = db.session.get(
            Clerk,
            clerk_id
        )

        if not clerk:

            return jsonify({
                "error": "Clerk not found",
                "clerk_id": clerk_id
            }), 404


        # ----------------------------------------------------
        # FIND STORE
        # ----------------------------------------------------

        store = db.session.get(
            Store,
            store_id
        )

        if not store:

            return jsonify({
                "error": "Store not found",
                "store_id": store_id
            }), 404


        # ----------------------------------------------------
        # CHECK CLERK BELONGS TO STORE
        # ----------------------------------------------------

        if clerk.store_id != store.store_id:

            return jsonify({
                "error": "This clerk does not belong to the selected store"
            }), 400


        # ----------------------------------------------------
        # PRODUCT NAME
        # ----------------------------------------------------

        product_name = str(
            data["product_name"]
        ).strip()

        if not product_name:

            return jsonify({
                "error": "Product name cannot be blank"
            }), 400


        # ----------------------------------------------------
        # FIND OR CREATE PRODUCT
        # ----------------------------------------------------

        product = Product.query.filter(
            Product.name.ilike(product_name)
        ).first()


        if not product:

            product = Product(
                name=product_name,

                category=data.get(
                    "category"
                ),

                buying_price=data[
                    "buying_price"
                ],

                selling_price=data[
                    "selling_price"
                ],
            )

            db.session.add(product)

            db.session.flush()


        # ----------------------------------------------------
        # SUPPLIER NAME
        # ----------------------------------------------------

        supplier_name = str(
            data["supplier_name"]
        ).strip()

        if not supplier_name:

            return jsonify({
                "error": "Supplier name cannot be blank"
            }), 400


        # ----------------------------------------------------
        # FIND OR CREATE SUPPLIER
        # ----------------------------------------------------

        supplier = Supplier.query.filter(
            Supplier.name.ilike(supplier_name)
        ).first()


        if not supplier:

            supplier = Supplier(
                name=supplier_name
            )

            db.session.add(supplier)

            db.session.flush()


        # ----------------------------------------------------
        # CREATE RECORD
        # ----------------------------------------------------

        record = Record(

            clerk_id=clerk_id,

            product_id=product.product_id,

            supplier_id=supplier.supplier_id,

            store_id=store_id,

            admin_id=clerk.admin_id,

            items_received=int(
                data["items_received"]
            ),

            items_in_stock=int(
                data["items_in_stock"]
            ),

            items_spoilt=int(
                data.get(
                    "items_spoilt",
                    0
                )
            ),

            buying_price=float(
                data["buying_price"]
            ),

            selling_price=float(
                data["selling_price"]
            ),

            payment_status=data.get(
                "payment_status",
                "unpaid"
            ),
        )


        db.session.add(record)

        db.session.commit()


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "message":
                "Inventory record created successfully",

            "record":
                serialize_record(record)

        }), 201


    except Exception as e:

        # ----------------------------------------------------
        # ROLLBACK DATABASE
        # ----------------------------------------------------

        db.session.rollback()

        print("====================================")
        print("CREATE RECORD ERROR")
        print(str(e))
        print("====================================")


        return jsonify({
            "Your inventory has been successfully entered",
            "details": str(e)
        }), 500


# ============================================================
# GET ALL RECORDS
# ============================================================

@records_bp.route("/records", methods=["GET"])
def get_records():

    try:

        records = Record.query.order_by(
            Record.created_at.desc()
        ).all()

        return jsonify([
            serialize_record(record)
            for record in records
        ]), 200


    except Exception as e:

        print("GET RECORDS ERROR:", str(e))

        return jsonify({
            "error": "Failed to retrieve records",
            "details": str(e)
        }), 500


# ============================================================
# GET ONE RECORD
# ============================================================

@records_bp.route(
    "/records/<int:record_id>",
    methods=["GET"]
)
def get_record(record_id):

    try:

        record = db.session.get(
            Record,
            record_id
        )

        if not record:

            return jsonify({
                "error": "Record not found",
                "record_id": record_id
            }), 404


        return jsonify(
            serialize_record(record)
        ), 200


    except Exception as e:

        print("GET RECORD ERROR:", str(e))

        return jsonify({
            "error": "Failed to retrieve record",
            "details": str(e)
        }), 500


# ============================================================
# UPDATE RECORD
# ============================================================

@records_bp.route(
    "/records/<int:record_id>",
    methods=["PATCH"]
)
def update_record(record_id):

    try:

        record = db.session.get(
            Record,
            record_id
        )

        if not record:

            return jsonify({
                "error": "Record not found",
                "record_id": record_id
            }), 404


        data = request.get_json(
            silent=True
        ) or {}


        # ----------------------------------------------------
        # UPDATE CLERK ID
        # ----------------------------------------------------

        if "clerk_id" in data:

            try:

                clerk_id = int(
                    data["clerk_id"]
                )

            except (ValueError, TypeError):

                return jsonify({
                    "error": "clerk_id must be a valid number"
                }), 400


            clerk = db.session.get(
                Clerk,
                clerk_id
            )

            if not clerk:

                return jsonify({
                    "error": "Clerk not found",
                    "clerk_id": clerk_id
                }), 404


            record.clerk_id = clerk_id

            record.admin_id = clerk.admin_id


        # ----------------------------------------------------
        # UPDATE STORE ID
        # ----------------------------------------------------

        if "store_id" in data:

            try:

                store_id = int(
                    data["store_id"]
                )

            except (ValueError, TypeError):

                return jsonify({
                    "error": "store_id must be a valid number"
                }), 400


            store = db.session.get(
                Store,
                store_id
            )

            if not store:

                return jsonify({
                    "error": "Store not found",
                    "store_id": store_id
                }), 404


            record.store_id = store_id


        # ----------------------------------------------------
        # CHECK CLERK/STORE RELATIONSHIP
        # ----------------------------------------------------

        clerk = db.session.get(
            Clerk,
            record.clerk_id
        )

        store = db.session.get(
            Store,
            record.store_id
        )


        if clerk and store:

            if clerk.store_id != store.store_id:

                return jsonify({
                    "error":
                        "This clerk does not belong to the selected store"
                }), 400


            record.admin_id = clerk.admin_id


        # ----------------------------------------------------
        # UPDATE SUPPLIER
        # ----------------------------------------------------

        if "supplier_name" in data:

            supplier_name = str(
                data["supplier_name"]
            ).strip()


            if not supplier_name:

                return jsonify({
                    "error":
                        "Supplier name cannot be blank"
                }), 400


            supplier = Supplier.query.filter(
                Supplier.name.ilike(
                    supplier_name
                )
            ).first()


            if not supplier:

                supplier = Supplier(
                    name=supplier_name
                )

                db.session.add(
                    supplier
                )

                db.session.flush()


            record.supplier_id = (
                supplier.supplier_id
            )


        # ----------------------------------------------------
        # UPDATE PRODUCT
        # ----------------------------------------------------

        if "product_name" in data:

            product_name = str(
                data["product_name"]
            ).strip()


            if not product_name:

                return jsonify({
                    "error":
                        "Product name cannot be blank"
                }), 400


            product = Product.query.filter(
                Product.name.ilike(
                    product_name
                )
            ).first()


            if not product:

                product = Product(
                    name=product_name,

                    buying_price=data.get(
                        "buying_price",
                        record.buying_price
                    ),

                    selling_price=data.get(
                        "selling_price",
                        record.selling_price
                    ),
                )

                db.session.add(
                    product
                )

                db.session.flush()


            record.product_id = (
                product.product_id
            )


        # ----------------------------------------------------
        # UPDATE OTHER FIELDS
        # ----------------------------------------------------

        if "items_received" in data:

            record.items_received = int(
                data["items_received"]
            )


        if "items_in_stock" in data:

            record.items_in_stock = int(
                data["items_in_stock"]
            )


        if "items_spoilt" in data:

            record.items_spoilt = int(
                data["items_spoilt"]
            )


        if "buying_price" in data:

            record.buying_price = float(
                data["buying_price"]
            )


        if "selling_price" in data:

            record.selling_price = float(
                data["selling_price"]
            )


        if "payment_status" in data:

            record.payment_status = (
                data["payment_status"]
            )


        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        db.session.commit()


        return jsonify({

            "message":
                "Record updated successfully",

            "record":
                serialize_record(record)

        }), 200


    except Exception as e:

        db.session.rollback()

        print("UPDATE RECORD ERROR:", str(e))

        return jsonify({
            "error": "Failed to update record",
            "details": str(e)
        }), 500


# ============================================================
# DELETE RECORD
# ============================================================

@records_bp.route(
    "/records/<int:record_id>",
    methods=["DELETE"]
)
def delete_record(record_id):

    try:

        record = db.session.get(
            Record,
            record_id
        )

        if not record:

            return jsonify({
                "error": "Record not found",
                "record_id": record_id
            }), 404


        db.session.delete(record)

        db.session.commit()


        return jsonify({
            "message":
                "Record deleted successfully"
        }), 200


    except Exception as e:

        db.session.rollback()

        print("DELETE RECORD ERROR:", str(e))

        return jsonify({
            "error": "Failed to delete record",
            "details": str(e)
        }), 500


