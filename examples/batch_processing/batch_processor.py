"""
Batch Processing Example: Online Store Transactions

This example demonstrates how to use sqlite-worker for batch processing
of online store transactions with proper error handling and transaction management.
"""

from sqlite_worker import SqliteWorker
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict
import csv


class OnlineStoreProcessor:
    """Process online store transactions in batches"""
    
    def __init__(self, db_path: str = "store.db"):
        """Initialize the processor with database"""
        self.worker = SqliteWorker(
            db_path,
            execute_init=[
                "PRAGMA journal_mode=WAL;",
                "PRAGMA synchronous=NORMAL;",
                "PRAGMA temp_store=MEMORY;"
            ],
            max_count=100  # Commit after 100 queries
        )
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create database schema"""
        # Create tables
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                stock INTEGER DEFAULT 0
            )
        """)
        
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                customer_email TEXT NOT NULL,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date 
            ON transactions(transaction_date)
        """)
        
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_status 
            ON transactions(status)
        """)
    
    def add_sample_products(self):
        """Add sample products to the database"""
        products = [
            {"name": "Laptop", "price": 999.99, "stock": 50},
            {"name": "Mouse", "price": 29.99, "stock": 200},
            {"name": "Keyboard", "price": 79.99, "stock": 150},
            {"name": "Monitor", "price": 299.99, "stock": 75},
            {"name": "Headphones", "price": 149.99, "stock": 100},
        ]
        
        for product in products:
            self.worker.insert("products", product)
        
        print(f"Added {len(products)} sample products")
    
    def process_transaction_batch(self, transactions: List[Dict]):
        """
        Process a batch of transactions with proper error handling
        
        Args:
            transactions: List of transaction dictionaries
        """
        successful = 0
        failed = 0
        
        print(f"\nProcessing batch of {len(transactions)} transactions...")
        
        for trans in transactions:
            try:
                with self.worker.transaction():
                    # Check product availability
                    token = self.worker.select(
                        "products",
                        conditions={"id": trans["product_id"]}
                    )
                    products = self.worker.fetch_results(token)
                    
                    if not products:
                        raise ValueError(f"Product {trans['product_id']} not found")
                    
                    product = products[0]
                    current_stock = product[3]
                    
                    if current_stock < trans["quantity"]:
                        raise ValueError(
                            f"Insufficient stock for product {trans['product_id']}. "
                            f"Available: {current_stock}, Requested: {trans['quantity']}"
                        )
                    
                    # Calculate total price
                    price = product[2]
                    total_price = price * trans["quantity"]
                    
                    # Create transaction record
                    trans_data = {
                        "product_id": trans["product_id"],
                        "quantity": trans["quantity"],
                        "total_price": total_price,
                        "customer_email": trans["customer_email"],
                        "status": "completed"
                    }
                    self.worker.insert("transactions", trans_data)
                    
                    # Update stock
                    new_stock = current_stock - trans["quantity"]
                    self.worker.update(
                        "products",
                        {"stock": new_stock},
                        {"id": trans["product_id"]}
                    )
                    
                    successful += 1
                    
            except Exception as e:
                failed += 1
                print(f"  ❌ Transaction failed: {e}")
        
        print(f"\n✅ Successful: {successful}")
        print(f"❌ Failed: {failed}")
        
        return successful, failed
    
    def generate_sample_transactions(self, count: int = 100) -> List[Dict]:
        """Generate sample transactions for testing"""
        transactions = []
        emails = [
            "alice@example.com", "bob@example.com", "charlie@example.com",
            "david@example.com", "eve@example.com"
        ]
        
        for _ in range(count):
            transactions.append({
                "product_id": random.randint(1, 5),
                "quantity": random.randint(1, 5),
                "customer_email": random.choice(emails)
            })
        
        return transactions
    
    def get_sales_summary(self):
        """Get sales summary statistics"""
        # Total sales
        token = self.worker.execute("""
            SELECT 
                COUNT(*) as total_transactions,
                SUM(total_price) as total_revenue,
                AVG(total_price) as avg_transaction_value
            FROM transactions
            WHERE status = 'completed'
        """)
        summary = self.worker.fetch_results(token)
        
        # Sales by product
        token = self.worker.execute("""
            SELECT 
                p.name,
                SUM(t.quantity) as units_sold,
                SUM(t.total_price) as revenue
            FROM transactions t
            JOIN products p ON t.product_id = p.id
            WHERE t.status = 'completed'
            GROUP BY p.id, p.name
            ORDER BY revenue DESC
        """)
        product_sales = self.worker.fetch_results(token)
        
        return summary[0], product_sales
    
    def export_transactions_to_csv(self, filename: str = "transactions.csv"):
        """Export all transactions to CSV file"""
        token = self.worker.execute("""
            SELECT 
                t.id,
                p.name as product_name,
                t.quantity,
                t.total_price,
                t.customer_email,
                t.transaction_date,
                t.status
            FROM transactions t
            JOIN products p ON t.product_id = p.id
            ORDER BY t.transaction_date DESC
        """)
        transactions = self.worker.fetch_results(token)
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([
                'Transaction ID', 'Product', 'Quantity', 
                'Total Price', 'Customer Email', 'Date', 'Status'
            ])
            writer.writerows(transactions)
        
        print(f"\n📄 Exported {len(transactions)} transactions to {filename}")
    
    def close(self):
        """Close the database connection"""
        self.worker.close()


def main():
    """Main demonstration"""
    print("=" * 60)
    print("Online Store Transaction Batch Processing Demo")
    print("=" * 60)
    
    # Initialize processor
    processor = OnlineStoreProcessor()
    
    # Add sample products
    processor.add_sample_products()
    
    # Generate and process transactions in batches
    batch_size = 50
    total_transactions = 200
    
    for batch_num in range(total_transactions // batch_size):
        print(f"\n--- Batch {batch_num + 1} ---")
        transactions = processor.generate_sample_transactions(batch_size)
        processor.process_transaction_batch(transactions)
        time.sleep(0.5)  # Simulate time between batches
    
    # Display summary
    print("\n" + "=" * 60)
    print("Sales Summary")
    print("=" * 60)
    
    summary, product_sales = processor.get_sales_summary()
    
    print(f"\n📊 Overall Statistics:")
    print(f"   Total Transactions: {summary[0]}")
    print(f"   Total Revenue: ${summary[1]:.2f}")
    print(f"   Average Transaction Value: ${summary[2]:.2f}")
    
    print(f"\n📦 Sales by Product:")
    for name, units, revenue in product_sales:
        print(f"   {name}: {units} units sold, ${revenue:.2f} revenue")
    
    # Export to CSV
    processor.export_transactions_to_csv()
    
    # Cleanup
    processor.close()
    
    print("\n✅ Demo completed successfully!")


if __name__ == "__main__":
    main()
