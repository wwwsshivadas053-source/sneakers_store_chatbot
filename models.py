from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer') # 'admin' or 'customer'
    telegram_id = db.Column(db.String(50), nullable=True)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'telegram_id': self.telegram_id,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    brand = db.Column(db.String(50), nullable=False, default='Nike')
    category = db.Column(db.String(50), nullable=False, default='Retro')
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=10)
    sizes = db.Column(db.Text, nullable=False, default='["US 7", "US 8", "US 9", "US 10", "US 11"]')
    image_url = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text, nullable=True)
    featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    orders = db.relationship('Order', backref='product', lazy=True)

    def get_sizes_list(self):
        try:
            return json.loads(self.sizes)
        except Exception:
            return [s.strip() for s in self.sizes.split(',') if s.strip()]

    def set_sizes_list(self, sizes_list):
        self.sizes = json.dumps(sizes_list)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'brand': self.brand,
            'category': self.category,
            'price': self.price,
            'stock': self.stock,
            'sizes': self.get_sizes_list(),
            'image_url': self.image_url,
            'description': self.description,
            'featured': self.featured,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

class Order(db.Model):
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(30), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    size = db.Column(db.String(20), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(30), default='Pending') # Pending, Processing, Shipped, Delivered, Cancelled
    source = db.Column(db.String(20), default='Web') # Web, Telegram, AI Chat
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'shipping_address': self.shipping_address,
            'product_id': self.product_id,
            'product_name': self.product.name if self.product else 'Unknown Product',
            'product_image': self.product.image_url if self.product else '',
            'size': self.size,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'status': self.status,
            'source': self.source,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
