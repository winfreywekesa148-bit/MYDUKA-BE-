from flask import Flask, request, jsonify

app = Flask(__name__)


@app.route("/api/stk", methods=["POST"])
def stk():

    data = request.get_json()

    phone = data.get("phone")
    amount = data.get("amount")

    if not phone or not amount:
        return jsonify({
            "error": "phone and amount are required"
        }), 400

    # M-Pesa STK Push code goes here

    return jsonify({
        "message": "STK request received",
        "phone": phone,
        "amount": amount,
        "CheckoutRequestID": "TEST-CHECKOUT-ID",
        "MerchantRequestID": "TEST-MERCHANT-ID"
    }), 200


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=True
    )