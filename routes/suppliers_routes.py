from flask import Blueprint, request, jsonify
from extensions import db
from models.suppliers import Supplier

suppliers_bp = Blueprint('suppliers', __name__)

@suppliers_bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    suppliers = Supplier.query.all()
    return jsonify([{
        'supplier_id': s.supplier_id,
        'name': s.name,
        'phone_number': s.phone_number,
        'email': s.email,
        'address': s.address
    } for s in suppliers]), 200

@suppliers_bp.route('/suppliers', methods=['POST'])
def add_supplier():
    data = request.get_json()
    new_supplier = Supplier(
        name=data['name'],
        phone_number=data.get('phone_number'),
        email=data.get('email'),
        address=data.get('address')
    )
    db.session.add(new_supplier)
    db.session.commit()
    return jsonify({'message': 'Supplier created successfully'}), 201