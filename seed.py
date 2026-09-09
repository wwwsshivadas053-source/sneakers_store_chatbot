import json
import os
from dotenv import load_dotenv
from app import app
from models import db, User, Product, Order

load_dotenv()

def seed_database():
    with app.app_context():
        # Drop and recreate all tables for clean schema upgrade
        db.drop_all()
        db.create_all()
        
        # Seed Admin User
        admin = User(
            name='Prajwal (Admin)',
            email='admin@sneakerstore.com',
            role='admin',
            telegram_id='789456123'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("[OK] Created Admin User (admin@sneakerstore.com / admin123)")

        # Seed Demo Customer User
        customer = User(
            name='Alex Rivera',
            email='alex@example.com',
            role='customer',
            telegram_id='123456789'
        )
        customer.set_password('customer123')
        db.session.add(customer)
        print("[OK] Created Demo Customer (alex@example.com / customer123)")

        # Expanded Premium Sneakers Inventory (15 Models)
        products_data = [
            {
                "name": "Air Jordan 1 Retro High OG 'Lost & Found'",
                "brand": "Jordan",
                "category": "High-Top",
                "price": 210.00,
                "stock": 24,
                "sizes": json.dumps(["US 7.5", "US 8", "US 8.5", "US 9", "US 9.5", "US 10", "US 10.5", "US 11", "US 12"]),
                "image_url": "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80",
                "description": "The iconic Air Jordan 1 Chicago colorway reimagined with a vintage aesthetic, cracked leather details, and authentic 1985 shape packaging.",
                "featured": True
            },
            {
                "name": "Travis Scott x Air Jordan 1 Low OG 'Reverse Mocha'",
                "brand": "Jordan",
                "category": "Low-Top",
                "price": 450.00,
                "stock": 12,
                "sizes": json.dumps(["US 8", "US 8.5", "US 9", "US 9.5", "US 10", "US 10.5", "US 11"]),
                "image_url": "https://images.unsplash.com/photo-1597045566677-8cf032ed6634?auto=format&fit=crop&w=800&q=80",
                "description": "Premium sail and brown suede upper featuring Travis Scott's signature oversized reverse Swoosh and Cactus Jack heel branding.",
                "featured": True
            },
            {
                "name": "Yeezy Boost 350 V2 'Zebra'",
                "brand": "Yeezy",
                "category": "Running",
                "price": 230.00,
                "stock": 35,
                "sizes": json.dumps(["US 7", "US 8", "US 8.5", "US 9", "US 9.5", "US 10", "US 10.5", "US 11", "US 12"]),
                "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80",
                "description": "Black and white Primeknit pattern with bold red SPLY-350 lettering resting atop responsive full-length Boost cushioning.",
                "featured": True
            },
            {
                "name": "Nike Dunk Low 'Panda White Black'",
                "brand": "Nike",
                "category": "Low-Top",
                "price": 115.00,
                "stock": 50,
                "sizes": json.dumps(["US 6", "US 7", "US 8", "US 9", "US 10", "US 11", "US 12", "US 13"]),
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
                "description": "Timeless monochromatic black and white leather construction suitable for everyday streetwear styling.",
                "featured": True
            },
            {
                "name": "New Balance 2002R 'Protection Pack Rain Cloud'",
                "brand": "New Balance",
                "category": "Retro",
                "price": 175.00,
                "stock": 20,
                "sizes": json.dumps(["US 8", "US 8.5", "US 9", "US 9.5", "US 10", "US 11"]),
                "image_url": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
                "description": "Deconstructed raw-edge suede panels layered over mesh with N-ERGY shock absorbing outsole technology.",
                "featured": False
            },
            {
                "name": "Adidas Samba OG 'Cloud White Core Black'",
                "brand": "Adidas",
                "category": "Low-Top",
                "price": 100.00,
                "stock": 45,
                "sizes": json.dumps(["US 7", "US 8", "US 9", "US 10", "US 11", "US 12"]),
                "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=800&q=80",
                "description": "Classic indoor soccer silhouette turned global fashion icon with white leather, suede T-toe, and gum rubber outsole.",
                "featured": False
            },
            {
                "name": "Nike Kobe 6 Protro 'Reverse Grinch'",
                "brand": "Nike",
                "category": "Performance Basketball",
                "price": 380.00,
                "stock": 10,
                "sizes": json.dumps(["US 9", "US 10", "US 10.5", "US 11", "US 12"]),
                "image_url": "https://images.unsplash.com/photo-1515955656352-a1fa3ffcd111?auto=format&fit=crop&w=800&q=80",
                "description": "Crimson snake-scale textured upper with electric green laces and Air Zoom Turbo unit for elite hardwood performance.",
                "featured": True
            },
            {
                "name": "Air Jordan 4 Retro 'Military Black'",
                "brand": "Jordan",
                "category": "High-Top",
                "price": 220.00,
                "stock": 18,
                "sizes": json.dumps(["US 8", "US 8.5", "US 9", "US 9.5", "US 10", "US 11"]),
                "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80",
                "description": "Smooth white leather upper complemented by neutral grey suede overlays and dark black wing eyelets.",
                "featured": False
            },
            {
                "name": "Asics Gel-Kayano 14 'Silver Cream'",
                "brand": "Asics",
                "category": "Running",
                "price": 160.00,
                "stock": 22,
                "sizes": json.dumps(["US 7.5", "US 8.5", "US 9.5", "US 10.5", "US 11.5"]),
                "image_url": "https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?auto=format&fit=crop&w=800&q=80",
                "description": "Late 2000s technical running aesthetic with GEL technology cushioning and metallic silver synthetic overlays.",
                "featured": False
            },
            {
                "name": "New Balance 9060 'Sea Salt White'",
                "brand": "New Balance",
                "category": "Retro",
                "price": 150.00,
                "stock": 28,
                "sizes": json.dumps(["US 7", "US 8", "US 9", "US 10", "US 11"]),
                "image_url": "https://images.unsplash.com/photo-1539185441755-769473a23570?auto=format&fit=crop&w=800&q=80",
                "description": "Futuristic wave lines with exaggerated midsole pods and dual-density ABZORB cushioning.",
                "featured": False
            },
            {
                "name": "Travis Scott x Air Jordan 4 'Cactus Jack'",
                "brand": "Jordan",
                "category": "High-Top",
                "price": 520.00,
                "stock": 8,
                "sizes": json.dumps(["US 8.5", "US 9.5", "US 10", "US 11"]),
                "image_url": "https://images.unsplash.com/photo-1552346154-21d32810aba3?auto=format&fit=crop&w=800&q=80",
                "description": "University blue suede upper honoring Houston football history with speckled black heel tab.",
                "featured": True
            },
            {
                "name": "Yeezy Foam Runner 'Onyx'",
                "brand": "Yeezy",
                "category": "Low-Top",
                "price": 140.00,
                "stock": 30,
                "sizes": json.dumps(["US 7", "US 8", "US 9", "US 10", "US 11", "US 12"]),
                "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?auto=format&fit=crop&w=800&q=80",
                "description": "Lightweight harvested algae and EVA foam compound molded design with strategic ventilation cutouts.",
                "featured": False
            },
            {
                "name": "Nike Off-White Air Force 1 Low 'MCA'",
                "brand": "Nike",
                "category": "Low-Top",
                "price": 1250.00,
                "stock": 4,
                "sizes": json.dumps(["US 9", "US 10", "US 11"]),
                "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?auto=format&fit=crop&w=800&q=80",
                "description": "University blue leather upper with silver foil Swoosh, exposed foam tongue, and signature red zip tie.",
                "featured": True
            },
            {
                "name": "Adidas Gazelle Bold 'Pink Glow'",
                "brand": "Adidas",
                "category": "Low-Top",
                "price": 120.00,
                "stock": 25,
                "sizes": json.dumps(["US 6", "US 7", "US 8", "US 9", "US 10"]),
                "image_url": "https://images.unsplash.com/photo-1608231387042-66d1773070a5?auto=format&fit=crop&w=800&q=80",
                "description": "Triple-stacked gum rubber platform outsole layered with vibrant suede upper styling.",
                "featured": False
            },
            {
                "name": "Air Max 1 'Big Bubble 86 OG'",
                "brand": "Nike",
                "category": "Retro",
                "price": 150.00,
                "stock": 19,
                "sizes": json.dumps(["US 7.5", "US 8.5", "US 9.5", "US 10.5", "US 11.5"]),
                "image_url": "https://images.unsplash.com/photo-1600185365926-3a2ce3cdb9eb?auto=format&fit=crop&w=800&q=80",
                "description": "Faithful recreation of the original 1986 Air Max 1 prototype with enlarged exposed Air unit window.",
                "featured": False
            }
        ]

        for p_data in products_data:
            product = Product(**p_data)
            db.session.add(product)
        db.session.commit()
        print(f"[OK] Seeded {len(products_data)} premium sneakers into database")

        # Seed sample orders
        sample_product = Product.query.first()
        if sample_product:
            sample_order = Order(
                user_id=customer.id,
                customer_name="Alex Rivera",
                customer_phone="+1 (555) 234-5678",
                shipping_address="742 Evergreen Terrace, Springfield, OR 97477",
                product_id=sample_product.id,
                size="US 10",
                quantity=1,
                total_price=sample_product.price,
                status="Processing",
                source="Telegram"
            )
            db.session.add(sample_order)
            db.session.commit()
            print("[OK] Seeded initial customer order")

if __name__ == '__main__':
    seed_database()
