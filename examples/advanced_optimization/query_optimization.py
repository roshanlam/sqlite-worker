"""
Advanced SQLite Query Optimization with sqlite-worker

This example demonstrates various techniques to optimize SQLite queries
when using sqlite-worker for better performance.
"""

from sqlite_worker import SqliteWorker
import time
import random
from typing import List, Tuple


class QueryOptimizer:
    """Demonstrates SQLite query optimization techniques"""
    
    def __init__(self, db_path: str = "optimization_demo.db"):
        """Initialize with optimized settings"""
        self.worker = SqliteWorker(
            db_path,
            execute_init=[
                # Performance optimizations
                "PRAGMA journal_mode=WAL;",
                "PRAGMA synchronous=NORMAL;",
                "PRAGMA cache_size=-64000;",  # 64MB cache
                "PRAGMA temp_store=MEMORY;",
                "PRAGMA mmap_size=268435456;",  # 256MB memory map
                "PRAGMA page_size=4096;",
                # Query optimization
                "PRAGMA optimize;",
            ],
            max_count=1000  # Batch commits for better performance
        )
        self._setup_demo_data()
    
    def _setup_demo_data(self):
        """Create sample tables with data"""
        # Create tables
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                country TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (customer_id) REFERENCES customers(id)
            )
        """)
        
        # Check if data already exists
        token = self.worker.execute("SELECT COUNT(*) FROM customers")
        count = self.worker.fetch_results(token)[0][0]
        
        if count == 0:
            print("Creating sample data...")
            self._populate_sample_data()
    
    def _populate_sample_data(self):
        """Populate tables with sample data"""
        countries = ["USA", "UK", "Canada", "Germany", "France"]
        products = ["Widget A", "Widget B", "Gadget X", "Gadget Y", "Tool Z"]
        
        # Insert customers
        with self.worker.transaction():
            for i in range(1000):
                self.worker.insert("customers", {
                    "name": f"Customer {i}",
                    "email": f"customer{i}@example.com",
                    "country": random.choice(countries)
                })
        
        # Insert orders
        with self.worker.transaction():
            for i in range(5000):
                self.worker.insert("orders", {
                    "customer_id": random.randint(1, 1000),
                    "product_name": random.choice(products),
                    "quantity": random.randint(1, 10),
                    "price": round(random.uniform(10, 500), 2)
                })
        
        print("✅ Sample data created: 1000 customers, 5000 orders")
    
    def demo_1_index_benefits(self):
        """Demonstrate the benefits of indexes"""
        print("\n" + "=" * 60)
        print("DEMO 1: Index Benefits")
        print("=" * 60)
        
        # Query without index
        print("\n1. Query WITHOUT index on customer_id:")
        start = time.time()
        token = self.worker.execute("""
            SELECT customer_id, COUNT(*) as order_count, SUM(price * quantity) as total
            FROM orders
            GROUP BY customer_id
            HAVING total > 1000
            ORDER BY total DESC
            LIMIT 10
        """)
        results = self.worker.fetch_results(token)
        elapsed_no_index = time.time() - start
        print(f"   Time: {elapsed_no_index:.4f}s")
        print(f"   Results: {len(results)} customers")
        
        # Create index
        print("\n2. Creating index on customer_id...")
        self.worker.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id)")
        
        # Query with index
        print("\n3. Query WITH index on customer_id:")
        start = time.time()
        token = self.worker.execute("""
            SELECT customer_id, COUNT(*) as order_count, SUM(price * quantity) as total
            FROM orders
            GROUP BY customer_id
            HAVING total > 1000
            ORDER BY total DESC
            LIMIT 10
        """)
        results = self.worker.fetch_results(token)
        elapsed_with_index = time.time() - start
        print(f"   Time: {elapsed_with_index:.4f}s")
        print(f"   Results: {len(results)} customers")
        
        improvement = ((elapsed_no_index - elapsed_with_index) / elapsed_no_index) * 100
        print(f"\n   📊 Performance improvement: {improvement:.1f}%")
    
    def demo_2_covering_index(self):
        """Demonstrate covering indexes"""
        print("\n" + "=" * 60)
        print("DEMO 2: Covering Index")
        print("=" * 60)
        
        print("\nCovering index includes all columns needed by query")
        print("SQLite doesn't need to access the main table data")
        
        # Create covering index
        self.worker.execute("""
            CREATE INDEX IF NOT EXISTS idx_orders_covering 
            ON orders(customer_id, price, quantity)
        """)
        
        start = time.time()
        token = self.worker.execute("""
            SELECT customer_id, SUM(price * quantity) as total_spent
            FROM orders
            GROUP BY customer_id
            ORDER BY total_spent DESC
            LIMIT 20
        """)
        results = self.worker.fetch_results(token)
        elapsed = time.time() - start
        
        print(f"   Time with covering index: {elapsed:.4f}s")
        print(f"   Top spender: Customer #{results[0][0]} - ${results[0][1]:.2f}")
    
    def demo_3_query_planning(self):
        """Demonstrate EXPLAIN QUERY PLAN"""
        print("\n" + "=" * 60)
        print("DEMO 3: Query Planning")
        print("=" * 60)
        
        print("\nUsing EXPLAIN QUERY PLAN to understand query execution:")
        
        query = """
            SELECT c.name, COUNT(o.id) as order_count
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            WHERE c.country = 'USA'
            GROUP BY c.id, c.name
            HAVING order_count > 3
        """
        
        # Show query plan
        token = self.worker.execute(f"EXPLAIN QUERY PLAN {query}")
        plan = self.worker.fetch_results(token)
        
        print("\nQuery Plan:")
        for row in plan:
            print(f"   {row}")
        
        # Execute the actual query
        start = time.time()
        token = self.worker.execute(query)
        results = self.worker.fetch_results(token)
        elapsed = time.time() - start
        
        print(f"\n   Query execution time: {elapsed:.4f}s")
        print(f"   Results: {len(results)} customers from USA with >3 orders")
    
    def demo_4_bulk_inserts(self):
        """Demonstrate optimized bulk insert strategies"""
        print("\n" + "=" * 60)
        print("DEMO 4: Bulk Insert Optimization")
        print("=" * 60)
        
        # Create temporary table for testing
        self.worker.execute("""
            CREATE TEMP TABLE test_inserts (
                id INTEGER PRIMARY KEY,
                data TEXT
            )
        """)
        
        # Method 1: Individual inserts without transaction
        print("\n1. Individual inserts (100 records):")
        start = time.time()
        for i in range(100):
            self.worker.execute(
                "INSERT INTO test_inserts (data) VALUES (?)",
                (f"data_{i}",)
            )
        elapsed_individual = time.time() - start
        print(f"   Time: {elapsed_individual:.4f}s")
        
        # Clear table
        self.worker.execute("DELETE FROM test_inserts")
        
        # Method 2: Bulk insert with transaction
        print("\n2. Bulk insert with transaction (100 records):")
        start = time.time()
        with self.worker.transaction():
            for i in range(100):
                self.worker.execute(
                    "INSERT INTO test_inserts (data) VALUES (?)",
                    (f"data_{i}",)
                )
        elapsed_bulk = time.time() - start
        print(f"   Time: {elapsed_bulk:.4f}s")
        
        improvement = ((elapsed_individual - elapsed_bulk) / elapsed_individual) * 100
        print(f"\n   📊 Transaction speedup: {improvement:.1f}x faster")
    
    def demo_5_query_optimization_tips(self):
        """Show various query optimization tips"""
        print("\n" + "=" * 60)
        print("DEMO 5: Query Optimization Tips")
        print("=" * 60)
        
        tips = [
            {
                "tip": "Use LIMIT for large result sets",
                "bad": "SELECT * FROM orders",
                "good": "SELECT * FROM orders LIMIT 100"
            },
            {
                "tip": "Avoid SELECT * - specify columns",
                "bad": "SELECT * FROM orders WHERE customer_id = 1",
                "good": "SELECT id, product_name, price FROM orders WHERE customer_id = 1"
            },
            {
                "tip": "Use EXISTS instead of COUNT for existence checks",
                "bad": "SELECT COUNT(*) > 0 FROM orders WHERE customer_id = 1",
                "good": "SELECT EXISTS(SELECT 1 FROM orders WHERE customer_id = 1)"
            },
            {
                "tip": "Index columns used in WHERE, JOIN, and ORDER BY",
                "bad": "No index on frequently queried columns",
                "good": "CREATE INDEX idx_name ON table(column)"
            },
            {
                "tip": "Use prepared statements (parameterized queries)",
                "bad": "f\"SELECT * FROM orders WHERE id = {user_input}\"",
                "good": "SELECT * FROM orders WHERE id = ? (with parameters)"
            }
        ]
        
        for i, item in enumerate(tips, 1):
            print(f"\n{i}. {item['tip']}:")
            print(f"   ❌ Bad:  {item['bad']}")
            print(f"   ✅ Good: {item['good']}")
    
    def demo_6_analyze_statistics(self):
        """Demonstrate ANALYZE for query optimization"""
        print("\n" + "=" * 60)
        print("DEMO 6: ANALYZE - Gather Statistics")
        print("=" * 60)
        
        print("\nANALYZE collects statistics about table contents")
        print("Helps SQLite choose better query plans")
        
        start = time.time()
        self.worker.execute("ANALYZE")
        elapsed = time.time() - start
        
        print(f"\n   ✅ Statistics gathered in {elapsed:.4f}s")
        print("   SQLite can now make better optimization decisions")
        
        # Show some statistics
        token = self.worker.execute("""
            SELECT name, tbl 
            FROM sqlite_stat1 
            WHERE tbl IN ('customers', 'orders')
        """)
        stats = self.worker.fetch_results(token)
        
        print("\n   Statistics collected for:")
        for stat in stats:
            print(f"      - {stat[1]} (index: {stat[0]})")
    
    def demo_7_pragma_optimization(self):
        """Demonstrate PRAGMA optimization settings"""
        print("\n" + "=" * 60)
        print("DEMO 7: PRAGMA Settings for Performance")
        print("=" * 60)
        
        pragmas = [
            ("journal_mode", "WAL mode for better concurrent writes"),
            ("synchronous", "NORMAL for balanced performance/safety"),
            ("cache_size", "Larger cache for better query performance"),
            ("temp_store", "MEMORY for faster temporary tables"),
            ("mmap_size", "Memory-mapped I/O for large databases"),
        ]
        
        print("\nRecommended PRAGMA settings:")
        for pragma, description in pragmas:
            token = self.worker.execute(f"PRAGMA {pragma}")
            value = self.worker.fetch_results(token)
            print(f"\n   PRAGMA {pragma}")
            print(f"   Current value: {value[0][0]}")
            print(f"   Purpose: {description}")
    
    def run_all_demos(self):
        """Run all optimization demonstrations"""
        print("=" * 60)
        print("SQLite Query Optimization with sqlite-worker")
        print("=" * 60)
        
        self.demo_1_index_benefits()
        self.demo_2_covering_index()
        self.demo_3_query_planning()
        self.demo_4_bulk_inserts()
        self.demo_5_query_optimization_tips()
        self.demo_6_analyze_statistics()
        self.demo_7_pragma_optimization()
        
        print("\n" + "=" * 60)
        print("✅ All optimization demos completed!")
        print("=" * 60)
    
    def close(self):
        """Close database connection"""
        self.worker.close()


def main():
    """Main demonstration"""
    optimizer = QueryOptimizer()
    
    try:
        optimizer.run_all_demos()
    finally:
        optimizer.close()


if __name__ == "__main__":
    main()
