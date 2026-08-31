from datetime import datetime
from extensions import db


class Store(db.Model):
    __tablename__ = "stores"

    store_id = db.Column(db.Integer, primary_key=True)
    st_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(150), nullable=False)

    merchant_id = db.Column(
        db.Integer,
        db.ForeignKey("merchants.merchant_id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    merchant = db.relationship(
        "Merchant",
        back_populates="stores"
    )

    admins = db.relationship(
        "StoreAdmin",
        back_populates="store",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Store {self.st_name}>"

    payments = db.relationship("Payment", back_populates="store",
    cascade="all, delete-orphan")