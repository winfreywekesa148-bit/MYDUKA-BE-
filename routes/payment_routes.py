from flask import Blueprint, request, jsonify
from extensions import db
from models.records import Record
from models.payments import Payment

import requests
import os
import base64
from datetime import datetime


# ============================================================
# BLUEPRINT
# ============================================================

payment_bp = Blueprint("payment", __name__)


# ============================================================
# GET MPESA ACCESS TOKEN
# ============================================================

def get_mpesa_token():

    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")

    if not consumer_key:
        raise Exception("MPESA_CONSUMER_KEY is missing")

    if not consumer_secret:
        raise Exception("MPESA_CONSUMER_SECRET is missing")

    credentials = f"{consumer_key}:{consumer_secret}"

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    response = requests.get(
        "https://sandbox.safaricom.co.ke/"
        "oauth/v1/generate"
        "?grant_type=client_credentials",

        headers={
            "Authorization": f"Basic {encoded_credentials}"
        },

        timeout=30
    )

    print("==============================")
    print("MPESA TOKEN RESPONSE")
    print("==============================")
    print(response.status_code)
    print(response.text)

    response.raise_for_status()

    data = response.json()

    if "access_token" not in data:
        raise Exception(
            f"Access token missing from Safaricom response: {data}"
        )

    return data["access_token"]


# ============================================================
# CREATE PAYMENT
# ============================================================

@payment_bp.route("/payments", methods=["POST"])
def create_payment():

    try:

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400

        record_id = data.get("record_id")
        store_id = data.get("store_id")
        amount = data.get("amount")
        phone_number = data.get("phone_number")

        if not record_id or not amount or not phone_number:
            return jsonify({
                "error": "record_id, amount and phone_number are required"
            }), 400

        new_payment = Payment(
            record_id=record_id,
            amount=amount,
            phone_number=phone_number
        )

        db.session.add(new_payment)
        db.session.commit()

        return jsonify({
            "message": "Payment created successfully",
            "payment_id": new_payment.payment_id,
            "status": new_payment.status
        }), 201

    except Exception as e:

        db.session.rollback()

        print("CREATE PAYMENT ERROR:")
        print(str(e))

        return jsonify({
            "error": "Could not create payment",
            "details": str(e)
        }), 500


# ============================================================
# GET ALL PAYMENTS
# ============================================================

@payment_bp.route("/payments", methods=["GET"])
def get_payments():

    try:

        payments = Payment.query.all()

        return jsonify([
            {
                "payment_id": p.payment_id,
                "record_id": p.record_id,
                "amount": float(p.amount),
                "phone_number": p.phone_number,
                "status": p.status,
                "created_at": p.created_at
            }
            for p in payments
        ]), 200

    except Exception as e:

        print("GET PAYMENTS ERROR:")
        print(str(e))

        return jsonify({
            "error": "Could not retrieve payments",
            "details": str(e)
        }), 500


# ============================================================
# GET ONE PAYMENT
# ============================================================

@payment_bp.route("/payments/<int:payment_id>", methods=["GET"])
def get_payment(payment_id):

    try:

        payment = Payment.query.get(payment_id)

        if not payment:
            return jsonify({
                "error": "Payment not found"
            }), 404

        return jsonify({

            "payment_id":
                payment.payment_id,

            "record_id":
                payment.record_id,

            "amount":
                float(payment.amount),

            "phone_number":
                payment.phone_number,

            "status":
                payment.status,

            "mpesa_receipt_number":
                payment.mpesa_receipt_number

        }), 200

    except Exception as e:

        print("GET PAYMENT ERROR:")
        print(str(e))

        return jsonify({
            "error": "Could not retrieve payment",
            "details": str(e)
        }), 500


# ============================================================
# MERCHANT M-PESA PAYMENT
# ============================================================

@payment_bp.route("/merchant/pay", methods=["POST"])
def merchant_pay():

    try:

        data = request.get_json(silent=True)

        if not data:

            return jsonify({
                "error": "Request body is required"
            }), 400


        # ----------------------------------------------------
        # DATA FROM REACT
        # ----------------------------------------------------

        record_id = data.get("record_id")
        store_id = data.get("store_id")
        phone = data.get("phone_number")
        amount = data.get("amount")


        print("==============================")
        print("MPESA PAYMENT REQUEST")
        print("==============================")

        print("record_id:", record_id)
        print("store_id:", store_id)
        print("phone:", phone)
        print("amount:", amount)


        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not record_id:

            return jsonify({
                "error": "record_id is required"
            }), 400


        if not store_id:

            return jsonify({
                "error": "store_id is required"
            }), 400


        if not phone:

            return jsonify({
                "error": "phone_number is required"
            }), 400


        if not amount:

            return jsonify({
                "error": "amount is required"
            }), 400


        # ----------------------------------------------------
        # CHECK RECORD
        # ----------------------------------------------------

        record = Record.query.get(record_id)

        if not record:

            return jsonify({
                "error": "Record not found",
                "record_id": record_id
            }), 404


        # ----------------------------------------------------
        # FORMAT PHONE NUMBER
        # ----------------------------------------------------

        phone = str(phone).strip()

        phone = phone.replace(" ", "")
        phone = phone.replace("-", "")
        phone = phone.replace("+", "")


        if phone.startswith("07"):

            phone = "254" + phone[1:]


        elif phone.startswith("01"):

            phone = "254" + phone[1:]


        # Example:
        # 0712345678 -> 254712345678
        # +254712345678 -> 254712345678


        if not phone.startswith("254"):

            return jsonify({
                "error": "Invalid Kenyan phone number"
            }), 400


        if len(phone) != 12:

            return jsonify({
                "error": "Invalid Kenyan phone number"
            }), 400


        # ----------------------------------------------------
        # FORMAT AMOUNT
        # ----------------------------------------------------

        try:

            amount = int(float(amount))

        except (ValueError, TypeError):

            return jsonify({
                "error": "Amount must be a valid number"
            }), 400


        if amount <= 0:

            return jsonify({
                "error": "Amount must be greater than zero"
            }), 400


        # ----------------------------------------------------
        # GET MPESA ENVIRONMENT VARIABLES
        # ----------------------------------------------------

        shortcode = os.getenv("MPESA_SHORTCODE")
        passkey = os.getenv("MPESA_PASSKEY")
        callback_url = os.getenv("MPESA_CALLBACK_URL")


        if not shortcode:

            raise Exception(
                "MPESA_SHORTCODE is missing"
            )


        if not passkey:

            raise Exception(
                "MPESA_PASSKEY is missing"
            )


        if not callback_url:

            raise Exception(
                "MPESA_CALLBACK_URL is missing"
            )


        # ----------------------------------------------------
        # GET MPESA TOKEN
        # ----------------------------------------------------

        token = get_mpesa_token()


        # ----------------------------------------------------
        # TIMESTAMP
        # ----------------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )


        # ----------------------------------------------------
        # GENERATE MPESA PASSWORD
        # ----------------------------------------------------

        password_string = (
            shortcode +
            passkey +
            timestamp
        )


        password = base64.b64encode(
            password_string.encode()
        ).decode()


        # ----------------------------------------------------
        # STK PUSH PAYLOAD
        # ----------------------------------------------------

        payload = {

            "BusinessShortCode":
                shortcode,

            "Password":
                password,

            "Timestamp":
                timestamp,

            "TransactionType":
                "CustomerPayBillOnline",

            "Amount":
                amount,

            "PartyA":
                phone,

            "PartyB":
                shortcode,

            "PhoneNumber":
                phone,

            "CallBackURL":
                callback_url,

            "AccountReference":
                "MYDUKA",

            "TransactionDesc":
                "MyDuka Payment"
        }


        print("==============================")
        print("STK PAYLOAD")
        print("==============================")

        print(payload)


        # ----------------------------------------------------
        # SEND STK PUSH TO SAFARICOM
        # ----------------------------------------------------

        response = requests.post(

            "https://sandbox.safaricom.co.ke/"
            "mpesa/stkpush/v1/processrequest",

            json=payload,

            headers={

                "Authorization":
                    f"Bearer {token}",

                "Content-Type":
                    "application/json"
            },

            timeout=30
        )


        print("==============================")
        print("SAFARICOM RESPONSE")
        print("==============================")

        print(response.status_code)
        print(response.text)


        # ----------------------------------------------------
        # READ RESPONSE
        # ----------------------------------------------------

        try:

            result = response.json()

        except ValueError:

            return jsonify({

                "error":
                    "Safaricom returned an invalid response",

                "details":
                    response.text

            }), 502


        # ----------------------------------------------------
        # SAFARICOM REJECTED REQUEST
        # ----------------------------------------------------

        if response.status_code >= 400:

            return jsonify({

                "error":
                    "Safaricom rejected the payment",

                "details":
                    result

            }), response.status_code


        # ----------------------------------------------------
        # MAKE SURE CHECKOUT ID EXISTS
        # ----------------------------------------------------

        checkout_request_id = result.get(
            "CheckoutRequestID"
        )

        merchant_request_id = result.get(
            "MerchantRequestID"
        )


        if not checkout_request_id:

            return jsonify({

                "error":
                    "Safaricom did not return CheckoutRequestID",

                "details":
                    result

            }), 502


        # ----------------------------------------------------
        # SAVE PAYMENT
        # ----------------------------------------------------

        payment = Payment(

            record_id=record_id,

            store_id=store_id,

            amount=amount,

            phone_number=phone,

            status="Pending"

        )


        db.session.add(payment)

        db.session.commit()


        # ----------------------------------------------------
        # SAVE MPESA REQUEST IDs
        # ----------------------------------------------------

        payment.checkout_request_id = \
            checkout_request_id

        payment.merchant_request_id = \
            merchant_request_id


        db.session.commit()


        # ----------------------------------------------------
        # RETURN RESPONSE TO REACT
        # ----------------------------------------------------

        return jsonify({

            "success": True,

            "payment_id":
                payment.payment_id,

            "status":
                payment.status,

            "merchant_request_id":
                merchant_request_id,

            "checkout_request_id":
                checkout_request_id,

            "customer_message":
                result.get(
                    "CustomerMessage"
                ),

            "response_code":
                result.get(
                    "ResponseCode"
                )

        }), 200


    except requests.exceptions.RequestException as e:

        db.session.rollback()

        print("==============================")
        print("MPESA REQUEST ERROR")
        print("==============================")

        print(str(e))


        return jsonify({

            "error":
                "Could not connect to M-Pesa",

            "details":
                str(e)

        }), 502


    except Exception as e:

        db.session.rollback()

        print("==============================")
        print("MPESA ERROR")
        print("==============================")

        print(str(e))


        return jsonify({

            "error":
                "M-Pesa payment failed",

            "details":
                str(e)

        }), 500


# ============================================================
# M-PESA CALLBACK
# ============================================================

@payment_bp.route("/payments/callback", methods=["POST"])
def payment_callback():

    try:

        data = request.get_json(silent=True)


        print("==============================")
        print("MPESA CALLBACK RECEIVED")
        print("==============================")

        print(data)


        if not data:

            return jsonify({
                "ResultCode": 1,
                "ResultDesc": "No callback data received"
            }), 400


        callback = data.get(
            "Body",
            {}
        ).get(
            "stkCallback",
            {}
        )


        checkout_request_id = callback.get(
            "CheckoutRequestID"
        )


        if not checkout_request_id:

            return jsonify({
                "ResultCode": 1,
                "ResultDesc":
                    "CheckoutRequestID missing"
            }), 400


        # ----------------------------------------------------
        # FIND PAYMENT
        # ----------------------------------------------------

        payment = Payment.query.filter_by(
            checkout_request_id=
                checkout_request_id
        ).first()


        if not payment:

            print(
                "Payment not found for:",
                checkout_request_id
            )

            # Still acknowledge callback
            return jsonify({

                "ResultCode": 0,

                "ResultDesc":
                    "Accepted"

            }), 200


        # ----------------------------------------------------
        # SUCCESSFUL PAYMENT
        # ----------------------------------------------------

        result_code = callback.get(
            "ResultCode"
        )


        if result_code == 0:

            payment.status = "success"


            metadata = callback.get(
                "CallbackMetadata",
                {}
            )


            items = metadata.get(
                "Item",
                []
            )


            for item in items:

                if item.get(
                    "Name"
                ) == "MpesaReceiptNumber":

                    payment.mpesa_receipt_number = \
                        item.get("Value")


        # ----------------------------------------------------
        # FAILED / CANCELLED PAYMENT
        # ----------------------------------------------------

        else:

            payment.status = "Failed"


        db.session.commit()


        print("==============================")
        print("PAYMENT STATUS UPDATED")
        print("==============================")

        print(
            "Payment ID:",
            payment.payment_id
        )

        print(
            "Status:",
            payment.status
        )


        # ----------------------------------------------------
        # ACKNOWLEDGE SAFARICOM
        # ----------------------------------------------------

        return jsonify({

            "ResultCode": 0,

            "ResultDesc":
                "Accepted"

        }), 200


    except Exception as e:

        db.session.rollback()

        print("==============================")
        print("CALLBACK ERROR")
        print("==============================")

        print(str(e))


        return jsonify({

            "ResultCode": 1,

            "ResultDesc":
                "Callback processing failed"

        }), 500
