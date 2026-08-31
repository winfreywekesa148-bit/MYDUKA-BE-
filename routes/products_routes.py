from flask import Blueprint, request, jsonify
from extensions import db
from models.product import Product

products_bp = Blueprint('products', __name__)

@products_bp.route('/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([{
        'product_id': p.product_id,
        'name': p.name,
        'category': p.category,
        'buying_price': float(p.buying_price),
        'selling_price': float(p.selling_price)
    } for p in products]), 200

@products_bp.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    new_product = Product(
        name=data['name'],
        category=data.get('category'),
        buying_price=data['buying_price'],
        selling_price=data['selling_price']
    )
    db.session.add(new_product)
    db.session.commit()
    return jsonify({'message': 'Product added successfully'}), 201
