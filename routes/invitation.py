from extensions import db

class Invitation(db.Model):
    __tablename__ = "invitations"

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(
        db.String(120),
        nullable=False
    )

    role = db.Column(
        db.String(20),
        nullable=False
    )

    token = db.Column(
        db.String(255),
        unique=True,
        nullable=False
    )

    expires_at = db.Column(
        db.DateTime,
        nullable=False
    )

    used = db.Column(
        db.Boolean,
        default=False
    )

    invited_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )