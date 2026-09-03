from flask import Flask, jsonify
from flask_cors import CORS

from models.user import user
from models.store import Store
from models.store_admin import StoreAdmin
from models.merchants import Merchant
from models.clerk import Clerk
from models.product import Product
from models.suppliers import Supplier
from models.supply_rep import SupplyRequest
from models.payments import Payment
from models.records import Record
from models.invitation import Invitation
from extensions import db, jwt, ma
from config import Config

from routes.auth_routes import auth_bp
from routes.store_routes import store_bp
from routes.payment_routes import payment_bp
from routes.login_routes import login_bp
from routes.clerks_routes import clerk_bp
from routes.reg_routes import reg_bp
from routes.invitation_route import merchant_bp
from routes.merchants_routes import merchants_bp
from routes.store_admin_routes import store_admin_bp
from routes.products_routes import products_bp
from routes.records_routes import records_bp
from routes.suppliers_routes import suppliers_bp
from routes.supply_req_routes import supply_req_bp

app = Flask(__name__)

app.config.from_object(Config)

# =========================================================
# INITIALIZE EXTENSIONS
# =========================================================

db.init_app(app)
jwt.init_app(app)
ma.init_app(app)
CORS(app,
    resources={
        r"/*": {
            "origins": [
                "https://myduka-fe-ke8m.vercel.app"
            ]
        }
    },
     supports_credentials=True)

# =========================================================
# REGISTER BLUEPRINTS
# =========================================================

app.register_blueprint(auth_bp)
app.register_blueprint(login_bp)
app.register_blueprint(reg_bp)
app.register_blueprint(products_bp)
app.register_blueprint(suppliers_bp)
app.register_blueprint(supply_req_bp)
app.register_blueprint(payment_bp)
app.register_blueprint(store_bp)
app.register_blueprint(store_admin_bp)
app.register_blueprint(clerk_bp)
app.register_blueprint(records_bp)
app.register_blueprint(merchant_bp)
app.register_blueprint(merchants_bp)

@app.route("/")
def home():

    return jsonify({
        "message": "MyDuka API is running"
    })

#create database tables if they don't exist
with app.app_context():
    db.create_all()

if __name__ == "__main__":

    import os
    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=False
    )
