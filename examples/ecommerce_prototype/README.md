# Simple E-commerce Platform Prototype

A lightweight e-commerce system demonstrating product management, shopping cart, orders, and inventory with thread-safe operations using sqlite-worker.

## Features

- **Product Catalog**: Browse and manage products with categories
- **Shopping Cart**: Add/remove items, view cart
- **Order Management**: Create orders, track status
- **Inventory Management**: Automatic stock updates
- **Customer Management**: Customer profiles and order history
- **Thread-Safe**: All operations safe for concurrent access
- **ACID Compliance**: Transactions ensure data consistency

## Installation

```bash
pip install sqlite-worker
```

## Running the Example

```bash
python ecommerce.py
```

## Quick Start

```python
from ecommerce import EcommercePlatform

# Initialize platform
platform = EcommercePlatform()

# Create customer
customer_id = platform.create_customer(
    email="user@example.com",
    name="John Doe",
    address="123 Main St"
)

# Add products
laptop_id = platform.add_product(
    name="Laptop",
    description="High-performance laptop",
    price=999.99,
    stock=10,
    category="Electronics"
)

# Add to cart
platform.add_to_cart(customer_id, laptop_id, quantity=1)

# Create order
order_id = platform.create_order(customer_id)

# View order
order = platform.get_order(order_id)
print(f"Order Total: ${order['total_amount']}")
```

## API Reference

### Customer Management

```python
# Create customer
customer_id = platform.create_customer(email, name, address, phone)

# Get customer
customer = platform.get_customer(customer_id)
```

### Product Management

```python
# Add product
product_id = platform.add_product(name, description, price, stock, category)

# Get products
products = platform.get_products(category="Electronics", limit=50)

# Update stock
platform.update_stock(product_id, quantity_delta=-5)
```

### Shopping Cart

```python
# Add to cart
platform.add_to_cart(customer_id, product_id, quantity=2)

# View cart
cart_items = platform.get_cart(customer_id)

# Clear cart
platform.clear_cart(customer_id)
```

### Order Management

```python
# Create order from cart
order_id = platform.create_order(customer_id)

# Get order details
order = platform.get_order(order_id)

# Update order status
platform.update_order_status(order_id, 'shipped')

# Get customer orders
orders = platform.get_customer_orders(customer_id)
```

## Database Schema

### Tables

1. **products**: Product catalog
2. **customers**: Customer information
3. **orders**: Order headers
4. **order_items**: Order line items
5. **cart_items**: Shopping cart items

### Key Features

- **Foreign Keys**: Referential integrity enabled
- **Constraints**: Price >= 0, Stock >= 0, Quantity > 0
- **Indexes**: Fast queries on category, customer, status
- **Timestamps**: Automatic creation timestamps

## Use Cases

### 1. Online Store

```python
# Customer browses products
electronics = platform.get_products(category="Electronics")

# Customer adds items
platform.add_to_cart(customer_id, laptop_id, 1)
platform.add_to_cart(customer_id, mouse_id, 2)

# Customer checks out
order_id = platform.create_order(customer_id)
```

### 2. Inventory Management

```python
# Receive new stock
platform.update_stock(product_id, +50)

# Stock adjustment
platform.update_stock(product_id, -5)  # Damaged items

# Check availability
products = platform.get_products()
for p in products:
    if p['stock'] < 10:
        print(f"Low stock: {p['name']}")
```

### 3. Order Processing

```python
# Get pending orders
token = worker.execute("""
    SELECT * FROM orders 
    WHERE status = 'pending'
    ORDER BY created_at
""")
pending_orders = worker.fetch_results(token)

# Process orders
for order in pending_orders:
    platform.update_order_status(order[0], 'processing')
    # ... fulfill order ...
    platform.update_order_status(order[0], 'shipped')
```

### 4. Customer Analytics

```python
# Top customers by order count
token = worker.execute("""
    SELECT c.name, COUNT(o.id) as order_count, 
           SUM(o.total_amount) as total_spent
    FROM customers c
    JOIN orders o ON c.id = o.customer_id
    GROUP BY c.id
    ORDER BY total_spent DESC
    LIMIT 10
""")
top_customers = worker.fetch_results(token)
```

### 5. Sales Reports

```python
# Daily sales
token = worker.execute("""
    SELECT DATE(created_at) as date,
           COUNT(*) as orders,
           SUM(total_amount) as revenue
    FROM orders
    WHERE status = 'delivered'
    GROUP BY DATE(created_at)
    ORDER BY date DESC
""")
daily_sales = worker.fetch_results(token)
```

## Transaction Safety

The platform uses transactions for critical operations:

```python
def create_order(self, customer_id: int) -> int:
    with self.worker.transaction():
        # Check stock
        # Create order
        # Update inventory
        # Clear cart
        # All or nothing!
```

## Error Handling

```python
try:
    order_id = platform.create_order(customer_id)
except ValueError as e:
    print(f"Order failed: {e}")  # Insufficient stock
except Exception as e:
    print(f"Error: {e}")
```

## Advanced Features

### Price History

```python
# Track price changes
worker.execute("""
    CREATE TABLE price_history (
        product_id INTEGER,
        old_price REAL,
        new_price REAL,
        changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
```

### Reviews and Ratings

```python
# Add reviews
worker.execute("""
    CREATE TABLE reviews (
        id INTEGER PRIMARY KEY,
        product_id INTEGER,
        customer_id INTEGER,
        rating INTEGER CHECK(rating BETWEEN 1 AND 5),
        comment TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")
```

### Promotions and Discounts

```python
# Add discount codes
worker.execute("""
    CREATE TABLE discount_codes (
        code TEXT PRIMARY KEY,
        discount_percent REAL,
        valid_until TIMESTAMP
    )
""")

def apply_discount(order_total, discount_code):
    # Apply discount logic
    return discounted_total
```

## Production Considerations

1. **Payment Processing**: Integrate payment gateway (Stripe, PayPal)
2. **Email Notifications**: Send order confirmations
3. **Image Storage**: Store product images externally (S3, CDN)
4. **Search**: Add full-text search for products
5. **Authentication**: Add user authentication and sessions
6. **API**: Wrap in REST API (FastAPI, Flask)
7. **Admin Panel**: Build admin interface for management
8. **Caching**: Cache product listings for performance

## Integration with Web Frameworks

### FastAPI Example

```python
from fastapi import FastAPI
from ecommerce import EcommercePlatform

app = FastAPI()
platform = EcommercePlatform()

@app.get("/products")
def list_products(category: str = None):
    return platform.get_products(category=category)

@app.post("/cart/{customer_id}/add")
def add_to_cart(customer_id: int, product_id: int, quantity: int = 1):
    platform.add_to_cart(customer_id, product_id, quantity)
    return {"status": "success"}

@app.post("/orders/{customer_id}")
def create_order(customer_id: int):
    order_id = platform.create_order(customer_id)
    return {"order_id": order_id}
```

## Testing

```python
import unittest

class TestEcommerce(unittest.TestCase):
    def setUp(self):
        self.platform = EcommercePlatform(':memory:')
    
    def test_create_order(self):
        # Create customer and product
        customer_id = self.platform.create_customer(
            "test@example.com", "Test User"
        )
        product_id = self.platform.add_product(
            "Test Product", "Description", 99.99, 10
        )
        
        # Add to cart and create order
        self.platform.add_to_cart(customer_id, product_id, 1)
        order_id = self.platform.create_order(customer_id)
        
        # Verify order
        order = self.platform.get_order(order_id)
        self.assertEqual(order['total_amount'], 99.99)
        self.assertEqual(len(order['items']), 1)
```

## Performance Tips

1. **Indexes**: Already created on key columns
2. **Batch Operations**: Use transactions for bulk inserts
3. **Query Optimization**: Limit result sets
4. **Caching**: Cache product listings
5. **WAL Mode**: Enabled for better concurrency

## Resources

- [sqlite-worker Documentation](https://github.com/roshanlam/sqlite-worker)
- [E-commerce Best Practices](https://www.shopify.com/blog/ecommerce)
- [Payment Gateway Integration](https://stripe.com/docs)

## Next Steps

- Add user authentication
- Implement payment processing
- Add product search functionality
- Create admin dashboard
- Implement email notifications
- Add product reviews and ratings
- Build responsive web interface
- Deploy to production

## Summary

This prototype demonstrates:
- ✅ Product management
- ✅ Shopping cart functionality
- ✅ Order processing
- ✅ Inventory tracking
- ✅ Transaction safety
- ✅ Thread-safe operations
- ✅ Production-ready patterns

Perfect foundation for building a full-featured e-commerce platform!
