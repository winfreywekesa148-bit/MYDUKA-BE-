from flask import Blueprint, request, jsonify
import requests
import os
import base64
from datetime import datetime

payments_bp = Blueprint(
    "payments_bp",
    __name__,
    url_prefix="/merchant"
)


# --------------------------------------------------
# GET ACCESS TOKEN
# --------------------------------------------------

def get_mpesa_token():

    consumer_key = os.getenv("MPESA_CONSUMER_KEY")
    consumer_secret = os.getenv("MPESA_CONSUMER_SECRET")

    if not consumer_key or not consumer_secret:
        raise Exception(
            "MPESA_CONSUMER_KEY or MPESA_CONSUMER_SECRET is missing"
        )

    credentials = f"{consumer_key}:{consumer_secret}"

    encoded_credentials = base64.b64encode(
        credentials.encode()
    ).decode()

    response = requests.get(
        "https://sandbox.safaricom.co.ke/oauth/v1/generate"
        "?grant_type=client_credentials",

        headers={
            "Authorization": f"Basic {encoded_credentials}"
        },

        timeout=30
    )

    print("TOKEN RESPONSE:", response.text)

    response.raise_for_status()

    data = response.json()

    return data["access_token"]


# --------------------------------------------------
# STK PUSH
# --------------------------------------------------

@payments_bp.route("/pay", methods=["POST"])
def pay():

    try:

        data = request.get_json()

        if not data:
            return jsonify({
                "error": "Request body is required"
            }), 400

        phone = data.get("phone")
        amount = data.get("amount")

        if not phone:
            return jsonify({
                "error": "Phone number is required"
            }), 400

        if not amount:
            return jsonify({
                "error": "Amount is required"
            }), 400

        # Remove spaces
        phone = str(phone).replace(" ", "")

        # Convert 07XXXXXXXX to 2547XXXXXXXX
        if phone.startswith("07"):
            phone = "254" + phone[1:]

        elif phone.startswith("01"):
            phone = "254" + phone[1:]

        # Basic validation
        if not phone.startswith("254") or len(phone) != 12:
            return jsonify({
                "error": "Invalid Kenyan phone number"
            }), 400

        amount = int(float(amount))

        if amount <= 0:
            return jsonify({
                "error": "Amount must be greater than zero"
            }), 400

        # ------------------------------------------
        # GET TOKEN
        # ------------------------------------------

        token = get_mpesa_token()

        # ------------------------------------------
        # MPESA SETTINGS
        # ------------------------------------------

        shortcode = os.getenv("MPESA_SHORTCODE")
        passkey = os.getenv("MPESA_PASSKEY")
        callback_url = os.getenv("MPESA_CALLBACK_URL")

        if not shortcode:
            raise Exception("MPESA_SHORTCODE is missing")

        if not passkey:
            raise Exception("MPESA_PASSKEY is missing")

        if not callback_url:
            raise Exception("MPESA_CALLBACK_URL is missing")

        # ------------------------------------------
        # TIMESTAMP
        # ------------------------------------------

        timestamp = datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )

        # ------------------------------------------
        # PASSWORD
        # ------------------------------------------

        password_string = (
            shortcode +
            passkey +
            timestamp
        )

        password = base64.b64encode(
            password_string.encode()
        ).decode()

        # ------------------------------------------
        # STK PAYLOAD
        # ------------------------------------------

        payload = {

            "BusinessShortCode": shortcode,

            "Password": password,

            "Timestamp": timestamp,

            "TransactionType":
                "CustomerPayBillOnline",

            "Amount": amount,

            "PartyA": phone,

            "PartyB": shortcode,

            "PhoneNumber": phone,

            "CallBackURL": callback_url,

            "AccountReference": "MYDUKA",

            "TransactionDesc": "MyDuka Payment"
        }

        print("MPESA PAYLOAD:")
        print(payload)

        # ------------------------------------------
        # SEND TO SAFARICOM
        # ------------------------------------------

        response = requests.post(

            "https://sandbox.safaricom.co.ke/"
            "mpesa/stkpush/v1/processrequest",

            json=payload,

            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },

            timeout=30
        )

        print("MPESA RESPONSE:")
        print(response.text)

        # Safaricom should return JSON
        try:
            result = response.json()

        except ValueError:
            return jsonify({
                "error": "Safaricom returned a non-JSON response",
                "response": response.text
            }), 502

        return jsonify(result), response.status_code

    except requests.exceptions.RequestException as e:

        print("REQUEST ERROR:", str(e))

        return jsonify({
            "error": "Could not connect to M-Pesa",
            "details": str(e)
        }), 502

    except Exception as e:

        print("MPESA ERROR:", str(e))

        return jsonify({
            "error": "M-Pesa payment failed",
            "details": str(e)
        }), 500


# --------------------------------------------------
# MPESA CALLBACK
# --------------------------------------------------

@payments_bp.route("/callback", methods=["POST"])
def mpesa_callback():

    try:

        data = request.get_json()

        print("==============================")
        print("MPESA CALLBACK RECEIVED")
        print("==============================")
        print(data)

        return jsonify({
            "ResultCode": 0,
            "ResultDesc": "Accepted"
        }), 200

    except Exception as e:

        print("CALLBACK ERROR:", str(e))

        return jsonify({
            "ResultCode": 1,
            "ResultDesc": "Callback processing failed"
        }), 500
