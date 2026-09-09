import os
import json
import re
import secrets
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from models import db, User, Product, Order

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sneaker-boutique-secret-2026')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///sneakerstore.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

CORS(app)
db.init_app(app)

# Helper functions
def is_admin():
    return session.get('role') == 'admin'

def get_telegram_bot_url():
    username = os.getenv('TELEGRAM_BOT_USERNAME', 'KicksStoreAssistant_bot')
    return f"https://t.me/{username}"

# --- HTML FRONTEND ROUTES ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        return redirect(url_for('login_page', next='/admin'))
    return render_template('admin.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/telegram')
def telegram_simulator():
    return render_template('telegram.html')

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

@app.route('/terms')
def terms_conditions():
    return render_template('terms.html')


# --- AUTHENTICATION API ENDPOINTS ---

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()

    if not email or not password or not name:
        return jsonify({'error': 'Name, email, and password are required.'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'Email is already registered. Please sign in.'}), 400

    user = User(name=name, email=email, role='customer')
    user.set_password(password)
    db.session.add(user)
    db.session.commit()

    session['user_id'] = user.id
    session['name'] = user.name
    session['role'] = user.role
    session['email'] = user.email

    return jsonify({
        'message': 'Registration successful',
        'redirect': '/',
        'user': user.to_dict()
    }), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'error': 'Email and password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({'error': 'Invalid email or password.'}), 401

    session['user_id'] = user.id
    session['name'] = user.name
    session['role'] = user.role
    session['email'] = user.email

    redirect_url = '/admin' if user.role == 'admin' else '/'

    return jsonify({
        'message': 'Login successful',
        'redirect': redirect_url,
        'user': user.to_dict()
    })

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()

    if not email:
        return jsonify({'error': 'Please enter your registered email address.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'If an account exists with this email, a 6-digit reset code has been sent.'})

    reset_code = f"{secrets.randbelow(900000) + 100000}"
    user.reset_token = reset_code
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=15)
    db.session.commit()

    return jsonify({
        'message': f'Verification reset code generated! Code: {reset_code}',
        'reset_code': reset_code
    })

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')

    if not email or not code or not new_password:
        return jsonify({'error': 'Email, reset code, and new password are required.'}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not user.reset_token or user.reset_token != code:
        return jsonify({'error': 'Invalid reset code or email.'}), 400

    if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
        return jsonify({'error': 'Reset code has expired. Please request a new code.'}), 400

    user.set_password(new_password)
    user.reset_token = None
    user.reset_token_expiry = None
    db.session.commit()

    return jsonify({'message': 'Password reset successful! You can now sign in.'})

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'authenticated': True, 'user': user.to_dict()})
    return jsonify({'authenticated': False, 'user': None})


# --- PRODUCT API ENDPOINTS ---

@app.route('/api/products', methods=['GET'])
def get_products():
    brand = request.args.get('brand')
    category = request.args.get('category')
    search = request.args.get('search')
    max_price = request.args.get('max_price', type=float)
    featured = request.args.get('featured')

    query = Product.query

    if brand and brand != 'All':
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if category and category != 'All':
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) | 
            (Product.brand.ilike(f"%{search}%")) |
            (Product.description.ilike(f"%{search}%"))
        )
    if max_price:
        query = query.filter(Product.price <= max_price)
    if featured == 'true':
        query = query.filter_by(featured=True)

    products = query.order_by(Product.id.desc()).all()
    return jsonify({'products': [p.to_dict() for p in products]})

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@app.route('/api/products', methods=['POST'])
def create_product():
    if not is_admin():
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

    data = request.get_json() or {}
    name = data.get('name')
    brand = data.get('brand', 'Nike')
    category = data.get('category', 'Retro')
    price = data.get('price')
    stock = data.get('stock', 10)
    sizes = data.get('sizes', ["US 7", "US 8", "US 9", "US 10", "US 11"])
    image_url = data.get('image_url')
    description = data.get('description', '')
    featured = data.get('featured', False)

    if not name or price is None or not image_url:
        return jsonify({'error': 'Product name, price, and image URL are required.'}), 400

    product = Product(
        name=name,
        brand=brand,
        category=category,
        price=float(price),
        stock=int(stock),
        sizes=json.dumps(sizes) if isinstance(sizes, list) else sizes,
        image_url=image_url,
        description=description,
        featured=bool(featured)
    )
    db.session.add(product)
    db.session.commit()

    return jsonify({'message': 'Product created successfully', 'product': product.to_dict()}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

    product = Product.query.get_or_404(product_id)
    data = request.get_json() or {}

    if 'name' in data: product.name = data['name']
    if 'brand' in data: product.brand = data['brand']
    if 'category' in data: product.category = data['category']
    if 'price' in data: product.price = float(data['price'])
    if 'stock' in data: product.stock = int(data['stock'])
    if 'sizes' in data: 
        sizes = data['sizes']
        product.sizes = json.dumps(sizes) if isinstance(sizes, list) else sizes
    if 'image_url' in data: product.image_url = data['image_url']
    if 'description' in data: product.description = data['description']
    if 'featured' in data: product.featured = bool(data['featured'])

    db.session.commit()
    return jsonify({'message': 'Product updated successfully', 'product': product.to_dict()})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({'message': 'Product deleted successfully'})


# --- ORDER API ENDPOINTS ---

@app.route('/api/orders', methods=['POST'])
def place_order():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    size = data.get('size')
    quantity = int(data.get('quantity', 1))
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    shipping_address = data.get('shipping_address', '').strip()
    source = data.get('source', 'Web Store')

    if not product_id or not size or not customer_name or not customer_phone or not shipping_address:
        return jsonify({'error': 'Product ID, size, customer name, phone, and address are required.'}), 400

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404

    if product.stock < quantity:
        return jsonify({'error': f'Only {product.stock} items left in stock.'}), 400

    product.stock -= quantity
    total_price = round(product.price * quantity, 2)
    user_id = session.get('user_id')

    order = Order(
        user_id=user_id,
        customer_name=customer_name,
        customer_phone=customer_phone,
        shipping_address=shipping_address,
        product_id=product.id,
        size=size,
        quantity=quantity,
        total_price=total_price,
        status='Pending',
        source=source
    )
    db.session.add(order)
    db.session.commit()

    return jsonify({
        'message': 'Order placed successfully!',
        'order': order.to_dict()
    }), 201

@app.route('/api/orders', methods=['GET'])
def get_orders():
    phone_param = request.args.get('phone', '').strip()
    
    if is_admin():
        orders = Order.query.order_by(Order.id.desc()).all()
        return jsonify({'orders': [o.to_dict() for o in orders]})

    user_id = session.get('user_id')
    all_orders = Order.query.order_by(Order.id.desc()).all()
    matched_orders = []

    clean_phone = re.sub(r'\D', '', phone_param) if phone_param else None

    for o in all_orders:
        o_clean_phone = re.sub(r'\D', '', o.customer_phone or '')
        
        # Match by session user_id OR phone number match
        if (user_id and o.user_id == user_id) or (clean_phone and len(clean_phone) >= 4 and clean_phone in o_clean_phone):
            matched_orders.append(o)

    return jsonify({'orders': [o.to_dict() for o in matched_orders]})

@app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
def update_order_status(order_id):
    if not is_admin():
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

    order = Order.query.get_or_404(order_id)
    data = request.get_json() or {}
    new_status = data.get('status')

    valid_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of {valid_statuses}'}), 400

    order.status = new_status
    db.session.commit()
    return jsonify({'message': f'Order status updated to {new_status}', 'order': order.to_dict()})


# --- ADMIN STATS ENDPOINT ---

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    if not is_admin():
        return jsonify({'error': 'Unauthorized. Admin access required.'}), 403

    total_products = Product.query.count()
    low_stock_products = Product.query.filter(Product.stock <= 5).all()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='Pending').count()
    
    orders = Order.query.filter(Order.status != 'Cancelled').all()
    total_revenue = sum(o.total_price for o in orders)

    recent_orders = Order.query.order_by(Order.id.desc()).limit(5).all()

    return jsonify({
        'total_revenue': round(total_revenue, 2),
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_products': total_products,
        'low_stock_count': len(low_stock_products),
        'low_stock_products': [p.to_dict() for p in low_stock_products],
        'recent_orders': [o.to_dict() for o in recent_orders]
    })


# --- DATABASE-GROUNDED AI CHATBOT ENGINE ---

@app.route('/api/chat', methods=['POST'])
def chat_bot():
    data = request.get_json() or {}
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({
            'response': 'How can I assist you with sneakers today?',
            'telegram_url': get_telegram_bot_url()
        })

    msg_lower = user_message.lower()
    all_products = Product.query.all()
    all_products_dict = [p.to_dict() for p in all_products]

    response_text = ""
    suggested_products = []
    quick_replies = []
    out_of_stock_query = False

    # 1. Greetings
    if any(word in msg_lower for word in ['hi', 'hello', 'hey', 'start', 'greetings', 'sup']):
        response_text = "👋 Welcome to **KICKS AI Store Assistant**! I'm here to help you find authentic sneakers, answer sizing questions, check live stock, and handle your order.\n\nYou can also chat with me directly in the Telegram App!"
        quick_replies = ["🔥 Trending Sneakers", "👟 Sizing Help", "💰 Under $200", "💬 Chat in Telegram"]

    # 2. Budget / Price queries
    elif 'under $' in msg_lower or 'budget' in msg_lower or 'cheap' in msg_lower or 'price' in msg_lower or re.search(r'\$\d+', msg_lower):
        prices = re.findall(r'\$?(\d+)', msg_lower)
        max_p = float(prices[0]) if prices else 200.0
        
        matches = [p for p in all_products_dict if p['price'] <= max_p]
        if matches:
            response_text = f"🎯 Here are top rated sneakers under **${max_p:.0f}** available right now in our database:"
            suggested_products = matches[:4]
        else:
            response_text = f"We currently don't have sneakers under ${max_p:.0f}, but here are our best value pairs:"
            suggested_products = sorted(all_products_dict, key=lambda x: x['price'])[:3]
        quick_replies = ["Filter by Size", "Check Shipping", "Ask Sizing"]

    # 3. Sizing Advice & Fit
    elif any(word in msg_lower for word in ['size', 'sizing', 'fit', 'true to size', 'runs small', 'runs big']):
        if 'jordan' in msg_lower:
            response_text = "📏 **Air Jordan Sizing Advice:**\nAir Jordan 1 & Jordan 4 models fit **true to size (TTS)**. For wider feet, consider going **+0.5 size UP**."
        elif 'yeezy' in msg_lower:
            response_text = "📏 **Yeezy Boost 350 Sizing Advice:**\nYeezy 350 V2s run snug due to the Primeknit structure. We recommend ordering **0.5 size UP**."
        else:
            response_text = "📏 **Sneaker Fit Guide:**\n- **Nike / Jordan / Samba**: True to Size (TTS)\n- **Yeezy 350 V2**: Order 0.5 size UP\n- **New Balance 2002R / 9060**: True to Size (Comfortable toe box)\n\nWhich pair are you checking?"
        quick_replies = ["Show Jordan 1", "Show Yeezys", "Show Dunks"]

    # 4. Delivery & Shipping
    elif any(word in msg_lower for word in ['delivery', 'shipping', 'order', 'dispatch', 'return', 'policy']):
        response_text = "🚚 **Shipping Info:**\n- **Express Delivery**: 2-4 business days worldwide.\n- **Tracking**: Order tracking sent via SMS & Email.\n- **Returns**: 30-day size exchange policy.\n\nWould you like to place an order?"
        quick_replies = ["Place Order Now", "View Catalog", "Chat in Telegram"]

    # 5. Catalog & Browse Inventory
    elif any(word in msg_lower for word in ['catalog', 'browse', 'inventory', 'stock', 'all sneakers', 'products']) or msg_lower in ['/catalog', 'browse catalog', '🔥 browse catalog']:
        response_text = "👟 **Current Premium Sneaker Inventory:**\nHere are top authentic sneakers available in stock right now:"
        suggested_products = all_products_dict[:6]
        quick_replies = ["🔥 Trending Sneakers", "📏 Sizing Help", "💰 Under $200", "💬 Chat in Telegram"]

    # 6. Specific Product / Brand Search & Database Check
    else:
        # Search against SQLite database
        matched_products = []
        for p in all_products_dict:
            # Check name or brand
            if p['name'].lower() in msg_lower or p['brand'].lower() in msg_lower or any(part in p['name'].lower() for part in msg_lower.split() if len(part) > 3):
                matched_products.append(p)

        if matched_products:
            # Found in database!
            response_text = f"Found matching sneakers in stock in our database:"
            suggested_products = matched_products[:4]
            quick_replies = ["Check Sizes", "How to Order?", "Chat in Telegram"]
        else:
            # Product NOT found in database -> Standard out-of-stock message
            out_of_stock_query = True
            response_text = f"Sorry, we currently do not have **'{user_message}'** in our inventory database.\n\nHere are featured authentic pairs available in stock right now:"
            suggested_products = [p for p in all_products_dict if p['featured']][:3]
            if not suggested_products:
                suggested_products = all_products_dict[:3]
            quick_replies = ["🔥 Trending Pairs", "💰 Under $200", "💬 Chat in Telegram App"]

    # LLM Enhancement via OpenAI or Gemini API Keys if provided
    openai_key = os.getenv('OPENAI_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    db_context = f"Database Stock: {', '.join([p['name'] + ' ($' + str(p['price']) + ')' for p in suggested_products])}"

    if openai_key and not out_of_stock_query:
        try:
            headers = {
                "Authorization": f"Bearer {openai_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": f"You are KICKS AI Sneaker Concierge. Help answer the customer query concise and politely. Strictly ground product recommendations on this inventory: {db_context}."},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": 150
            }
            res = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=4)
            if res.status_code == 200:
                response_text = res.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            pass

    elif gemini_key and not out_of_stock_query:
        try:
            llm_prompt = f"System: You are KICKS AI Sneaker Assistant. Ground response on database stock: {db_context}.\nUser: {user_message}\nKeep response concise, polite, and helpful."
            llm_res = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}",
                json={"contents": [{"parts": [{"text": llm_prompt}]}]},
                timeout=4
            )
            if llm_res.status_code == 200:
                response_text = llm_res.json()['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            pass

    return jsonify({
        'response': response_text,
        'products': suggested_products,
        'quick_replies': quick_replies,
        'telegram_url': get_telegram_bot_url()
    })


# --- STARTUP SEED & BOT AUTO-SPAWNER FOR SINGLE WEB SERVICE DEPLOYMENT ---
import subprocess
import threading

_bot_started = False

def start_telegram_bot_process():
    global _bot_started
    if _bot_started or os.getenv("DISABLE_TELEGRAM_BOT_SPAWN") == "true":
        return
    _bot_started = True
    try:
        def _spawn():
            print("[SERVER] Spawning Telegram bot.py background process for Single Web Service deployment...")
            subprocess.Popen(["python", "bot.py"])
            
        t = threading.Thread(target=_spawn, daemon=True)
        t.start()
    except Exception as e:
        print(f"[SERVER ERROR] Failed to auto-start Telegram bot process: {e}")

with app.app_context():
    db.create_all()
    if Product.query.count() == 0:
        from seed import seed_database
        seed_database()
    start_telegram_bot_process()

if __name__ == '__main__':
    print("[SERVER] Starting Sneaker Store AI Backend on http://127.0.0.1:5000 ...")
    app.run(host='0.0.0.0', port=5000, debug=True)

