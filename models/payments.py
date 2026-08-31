from extensions import db

#Create a new payment class
class Payment(db.Model):
    __tablename__ = "payments"

    payment_id = db.Column(db.Integer, primary_key=True)
    record_id = db.Column(db.Integer, db.ForeignKey("records.record_id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2),nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    checkout_request_id = db.Column(db.String(100), nullable=True)
    merchant_request_id = db.Column(db.String(100),nullable=True)
    mpesa_receipt_number = db.Column(db.String(100),nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    store_id = db.Column(db.Integer, db.ForeignKey("stores.store_id"), nullable=False)

    def __repr__(self):
        return f"<Payment {self.payment_id}>"

# Set up relationships
    record = db.relationship("Record", back_populates="payments")
    store = db.relationship("Store",back_populates="payments")
