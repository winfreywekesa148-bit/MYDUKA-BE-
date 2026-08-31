from flask import Blueprint, request, jsonify
from extensions import db
from models.records import Record
from models.payments import Payment
import requests

payment_bp = Blueprint("payment", __name__)

#  Route to create a payment
@payment_bp.route("/payments", methods=["POST"])
def create_payment():
    data = request.get_json()

    record_id = data.get("record_id")
    amount = data.get("amount")
    phone_number = data.get("phone_number")

    if not record_id or not amount or not phone_number:
        return jsonify({"error": "record_id, amount and phone_number are required"}), 400
    record = Record.query.get(record_id)

    if not record:
        return jsonify({"error": "Record not found"}), 404

    new_payment = Payment(record_id=record_id,
        amount=amount,
        phone_number=phone_number)

    db.session.add(new_payment)
    db.session.commit()

    return jsonify({"message": "Payment created successfully",
        "payment_id": new_payment.payment_id,
        "status": new_payment.status}), 201

# Route to get all payments
@payment_bp.route("/payments", methods=["GET"])
def get_payments():
    payments = Payment.query.all()

    return jsonify([
        {"payment_id": p.payment_id, "record_id": p.record_id,
            "amount": float(p.amount),"phone_number": p.phone_number,
            "status": p.status,"created_at": p.created_at
        }
        for p in payments
    ]), 200

# Route to get one payment
@payment_bp.route("/payments/<int:payment_id>", methods=["GET"])
def get_payment(payment_id):
    payment_record = Payment.query.get(payment_id)

    if not payment_record:
        return jsonify({"error": "Payment not found"}), 404

    return jsonify({"payment_id": payment_record.payment_id,
        "record_id": payment_record.record_id,
        "amount": float(payment_record.amount),
        "phone_number": payment_record.phone_number,
        "status": payment_record.status,
        "mpesa_receipt_number": payment_record.mpesa_receipt_number
    }), 200

@payment_bp.route("/payments/callback", methods=["POST"])
def payment_callback():

    data = request.get_json()

    callback = data["Body"]["stkCallback"]
    checkout = callback["CheckoutRequestID"]

    payment = Payment.query.filter_by(
        checkout_request_id=checkout).first()

    if not payment:
        return jsonify({"message": "Payment not found"}), 404

    if callback["ResultCode"] == 0:
        payment.status = "success"

        metadata = callback.get("CallbackMetadata", {})
        items = metadata.get("Item", [])

        for item in items:
            if item["Name"] == "MpesaReceiptNumber":
                payment.mpesa_receipt_number = item["Value"]

    else:
        payment.status = "Failed"
    db.session.commit()

    return jsonify({"message": "Callback received"}), 200


@payment_bp.route("/merchant/pay", methods=["POST"])
def merchant_pay():

    data = request.get_json()

    record_id = data.get("record_id")
    store_id = data.get("store_id")
    phone = data.get("phone_number")
    amount = data.get("amount")

    if not record_id or not store_id or not phone or not amount:
        return jsonify({
            "error": "record_id, store_id, phone_number and amount are required"
        }), 400

    payment = Payment( record_id=record_id,
        store_id=store_id, amount=amount,
        phone_number=phone,
        status="Pending"
    )

    db.session.add(payment)
    db.session.commit()

    response = requests.post("http://localhost:8000/api/stk",
        json={"phone": phone,
            "amount": amount})

    stk = response.json()

    payment.checkout_request_id = stk.get("CheckoutRequestID")
    payment.merchant_request_id = stk.get("MerchantRequestID")

    db.session.commit()

    return jsonify({
        "payment_id": payment.payment_id,
        "status": payment.status})
