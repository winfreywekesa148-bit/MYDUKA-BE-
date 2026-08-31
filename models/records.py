# Records model
from extensions import db

# Create a new Record class
class Record(db.Model):
    __tablename__ = "records"

    record_id = db.Column(db.Integer,primary_key=True)
    clerk_id = db.Column(db.Integer,db.ForeignKey("clerks.clerk_id"),nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.product_id"), nullable=False)
    supplier_id = db.Column(db.Integer, db.ForeignKey("suppliers.supplier_id"), nullable=False)
    items_received = db.Column(db.Integer,nullable=False)
    items_in_stock = db.Column(db.Integer,nullable=False)
    items_spoilt = db.Column(db.Integer,default=0,nullable=False)
    buying_price = db.Column(db.Numeric(10, 2),nullable=False)
    selling_price = db.Column(db.Numeric(10, 2),nullable=False)
    payment_status = db.Column(db.String(20), nullable=False,default="unpaid")
    created_at = db.Column(db.DateTime,default=db.func.current_timestamp())
    store_id = db.Column(db.Integer,db.ForeignKey("stores.store_id"),nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey("store_admins.admin_id"),nullable=False)
 

# Set up relationships
    payments = db.relationship("Payment", back_populates="record")
    product = db.relationship("Product", back_populates="records")
    supplier = db.relationship("Supplier", back_populates="records")
