"""
Simple E-commerce Platform Prototype using sqlite-worker

A lightweight e-commerce system demonstrating product catalog, shopping cart,
orders, and inventory management with thread-safe database operations.
"""

from sqlite_worker import SqliteWorker
from datetime import datetime
from typing import Dict, List, Optional
import json


class EcommercePlatform:
    """Simple e-commerce platform with thread-safe operations"""
    
    def __init__(self, db_path: str = "ecommerce.db"):
        """Initialize the e-commerce platform"""
        self.worker = SqliteWorker(
            db_path,
            execute_init=[
                "PRAGMA journal_mode=WAL;",
                "PRAGMA synchronous=NORMAL;",
                "PRAGMA foreign_keys=ON;",
            ]
        )
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create database schema"""
        # Products table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL CHECK(price >= 0),
                stock INTEGER NOT NULL DEFAULT 0 CHECK(stock >= 0),
                category TEXT,
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Customers table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Orders table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                total_amount REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)
        
        # Order items table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                price_at_purchase REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # Shopping cart table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL CHECK(quantity > 0),
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE(customer_id, product_id)
            )
        """)
        
        # Create indexes
        self.worker.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)")
        self.worker.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)")
        self.worker.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
    
    # Customer Management
    def create_customer(self, email: str, name: str, address: str = None, phone: str = None) -> int:
        """Create a new customer"""
        token = self.worker.insert('customers', {
            'email': email,
            'name': name,
            'address': address,
            'phone': phone
        })
        self.worker.fetch_results(token)
        
        token = self.worker.execute("SELECT last_insert_rowid()")
        return self.worker.fetch_results(token)[0][0]
    
    def get_customer(self, customer_id: int) -> Optional[Dict]:
        """Get customer by ID"""
        token = self.worker.select('customers', conditions={'id': customer_id})
        results = self.worker.fetch_results(token)
        
        if results:
            c = results[0]
            return {
                'id': c[0], 'email': c[1], 'name': c[2],
                'address': c[3], 'phone': c[4], 'created_at': c[5]
            }
        return None
    
    # Product Management
    def add_product(self, name: str, description: str, price: float, 
                   stock: int, category: str = None, image_url: str = None) -> int:
        """Add a new product"""
        token = self.worker.insert('products', {
            'name': name,
            'description': description,
            'price': price,
            'stock': stock,
            'category': category,
            'image_url': image_url
        })
        self.worker.fetch_results(token)
        
        token = self.worker.execute("SELECT last_insert_rowid()")
        return self.worker.fetch_results(token)[0][0]
    
    def get_products(self, category: str = None, limit: int = 50) -> List[Dict]:
        """Get products with optional category filter"""
        if category:
            token = self.worker.select('products', 
                conditions={'category': category}, limit=limit)
        else:
            token = self.worker.select('products', limit=limit)
        
        results = self.worker.fetch_results(token)
        
        return [
            {
                'id': p[0], 'name': p[1], 'description': p[2],
                'price': p[3], 'stock': p[4], 'category': p[5],
                'image_url': p[6], 'created_at': p[7]
            }
            for p in results
        ]
    
    def update_stock(self, product_id: int, quantity_delta: int):
        """Update product stock"""
        token = self.worker.execute("""
            UPDATE products 
            SET stock = stock + ?
            WHERE id = ?
        """, (quantity_delta, product_id))
        self.worker.fetch_results(token)
    
    # Shopping Cart
    def add_to_cart(self, customer_id: int, product_id: int, quantity: int = 1):
        """Add item to shopping cart"""
        # Check if item already in cart
        token = self.worker.execute("""
            SELECT id, quantity FROM cart_items
            WHERE customer_id = ? AND product_id = ?
        """, (customer_id, product_id))
        existing = self.worker.fetch_results(token)
        
        if existing:
            # Update quantity
            new_quantity = existing[0][1] + quantity
            self.worker.update('cart_items',
                {'quantity': new_quantity},
                {'id': existing[0][0]}
            )
        else:
            # Add new item
            self.worker.insert('cart_items', {
                'customer_id': customer_id,
                'product_id': product_id,
                'quantity': quantity
            })
    
    def get_cart(self, customer_id: int) -> List[Dict]:
        """Get shopping cart items"""
        token = self.worker.execute("""
            SELECT c.id, c.product_id, p.name, p.price, c.quantity,
                   (p.price * c.quantity) as subtotal, p.stock
            FROM cart_items c
            JOIN products p ON c.product_id = p.id
            WHERE c.customer_id = ?
        """, (customer_id,))
        
        results = self.worker.fetch_results(token)
        
        return [
            {
                'cart_item_id': r[0],
                'product_id': r[1],
                'product_name': r[2],
                'price': r[3],
                'quantity': r[4],
                'subtotal': r[5],
                'available_stock': r[6]
            }
            for r in results
        ]
    
    def clear_cart(self, customer_id: int):
        """Clear shopping cart"""
        self.worker.delete('cart_items', {'customer_id': customer_id})
    
    # Order Management
    def create_order(self, customer_id: int) -> Optional[int]:
        """Create order from shopping cart"""
        cart_items = self.get_cart(customer_id)
        
        if not cart_items:
            return None
        
        with self.worker.transaction():
            # Check stock availability
            for item in cart_items:
                if item['quantity'] > item['available_stock']:
                    raise ValueError(
                        f"Insufficient stock for {item['product_name']}. "
                        f"Available: {item['available_stock']}, Requested: {item['quantity']}"
                    )
            
            # Calculate total
            total_amount = sum(item['subtotal'] for item in cart_items)
            
            # Create order
            token = self.worker.insert('orders', {
                'customer_id': customer_id,
                'status': 'pending',
                'total_amount': total_amount
            })
            self.worker.fetch_results(token)
            
            token = self.worker.execute("SELECT last_insert_rowid()")
            order_id = self.worker.fetch_results(token)[0][0]
            
            # Create order items and update stock
            for item in cart_items:
                self.worker.insert('order_items', {
                    'order_id': order_id,
                    'product_id': item['product_id'],
                    'quantity': item['quantity'],
                    'price_at_purchase': item['price']
                })
                
                # Reduce stock
                self.update_stock(item['product_id'], -item['quantity'])
            
            # Clear cart
            self.clear_cart(customer_id)
            
            return order_id
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        """Get order details"""
        token = self.worker.execute("""
            SELECT o.id, o.customer_id, c.name, c.email,
                   o.status, o.total_amount, o.created_at
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.id = ?
        """, (order_id,))
        
        results = self.worker.fetch_results(token)
        
        if not results:
            return None
        
        o = results[0]
        
        # Get order items
        token = self.worker.execute("""
            SELECT oi.product_id, p.name, oi.quantity, oi.price_at_purchase,
                   (oi.quantity * oi.price_at_purchase) as subtotal
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,))
        
        items = self.worker.fetch_results(token)
        
        return {
            'order_id': o[0],
            'customer_id': o[1],
            'customer_name': o[2],
            'customer_email': o[3],
            'status': o[4],
            'total_amount': o[5],
            'created_at': o[6],
            'items': [
                {
                    'product_id': i[0],
                    'product_name': i[1],
                    'quantity': i[2],
                    'price': i[3],
                    'subtotal': i[4]
                }
                for i in items
            ]
        }
    
    def update_order_status(self, order_id: int, status: str):
        """Update order status"""
        self.worker.update('orders', {'status': status}, {'id': order_id})
    
    def get_customer_orders(self, customer_id: int) -> List[Dict]:
        """Get all orders for a customer"""
        token = self.worker.select('orders', 
            conditions={'customer_id': customer_id},
            order_by='created_at DESC')
        
        results = self.worker.fetch_results(token)
        
        return [
            {
                'order_id': r[0],
                'status': r[2],
                'total_amount': r[3],
                'created_at': r[4]
            }
            for r in results
        ]
    
    def close(self):
        """Close database connection"""
        self.worker.close()


def demo():
    """Demonstration of e-commerce platform"""
    print("=" * 60)
    print("E-commerce Platform Demo")
    print("=" * 60)
    
    platform = EcommercePlatform()
    
    # Create customer
    print("\n1. Creating customer...")
    customer_id = platform.create_customer(
        email="alice@example.com",
        name="Alice Johnson",
        address="123 Main St, City, State",
        phone="555-0123"
    )
    print(f"   ✅ Customer created: ID {customer_id}")
    
    # Add products
    print("\n2. Adding products...")
    products = [
        ("Laptop", "High-performance laptop", 999.99, 10, "Electronics"),
        ("Mouse", "Wireless mouse", 29.99, 50, "Electronics"),
        ("Keyboard", "Mechanical keyboard", 79.99, 30, "Electronics"),
        ("Monitor", "27-inch 4K monitor", 399.99, 15, "Electronics"),
        ("Desk Lamp", "LED desk lamp", 34.99, 25, "Furniture"),
    ]
    
    product_ids = []
    for name, desc, price, stock, category in products:
        pid = platform.add_product(name, desc, price, stock, category)
        product_ids.append(pid)
        print(f"   ✅ Added: {name} - ${price}")
    
    # Browse products
    print("\n3. Browsing Electronics...")
    electronics = platform.get_products(category="Electronics")
    for p in electronics:
        print(f"   📦 {p['name']} - ${p['price']} (Stock: {p['stock']})")
    
    # Add to cart
    print("\n4. Adding items to cart...")
    platform.add_to_cart(customer_id, product_ids[0], 1)  # Laptop
    platform.add_to_cart(customer_id, product_ids[1], 2)  # Mouse x2
    platform.add_to_cart(customer_id, product_ids[2], 1)  # Keyboard
    print("   ✅ Items added to cart")
    
    # View cart
    print("\n5. Shopping cart:")
    cart = platform.get_cart(customer_id)
    cart_total = sum(item['subtotal'] for item in cart)
    for item in cart:
        print(f"   🛒 {item['product_name']} x{item['quantity']} - ${item['subtotal']:.2f}")
    print(f"   💰 Cart Total: ${cart_total:.2f}")
    
    # Create order
    print("\n6. Creating order...")
    order_id = platform.create_order(customer_id)
    print(f"   ✅ Order created: ID {order_id}")
    
    # View order
    print("\n7. Order details:")
    order = platform.get_order(order_id)
    print(f"   📝 Order #{order['order_id']}")
    print(f"   👤 Customer: {order['customer_name']}")
    print(f"   📧 Email: {order['customer_email']}")
    print(f"   📊 Status: {order['status']}")
    print(f"   💰 Total: ${order['total_amount']:.2f}")
    print(f"\n   Items:")
    for item in order['items']:
        print(f"      - {item['product_name']} x{item['quantity']} = ${item['subtotal']:.2f}")
    
    # Update order status
    print("\n8. Processing order...")
    platform.update_order_status(order_id, 'processing')
    platform.update_order_status(order_id, 'shipped')
    platform.update_order_status(order_id, 'delivered')
    print("   ✅ Order status: delivered")
    
    # View customer orders
    print("\n9. Customer order history:")
    orders = platform.get_customer_orders(customer_id)
    for o in orders:
        print(f"   📦 Order #{o['order_id']} - ${o['total_amount']:.2f} - {o['status']}")
    
    platform.close()
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    demo()
