import unittest
import time
import os
from sqlite_worker import SqliteWorker


class TestTransactionSupport(unittest.TestCase):
    """Test transaction support features."""
    
    def setUp(self):
        self.db_file = 'test_transactions.db'
        self.worker = SqliteWorker(self.db_file)
        time.sleep(0.5)  # Allow worker to initialize
        
        # Create test table
        self.worker.execute(
            "CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY, balance INTEGER)"
        )
        time.sleep(0.5)
    
    def tearDown(self):
        self.worker.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_transaction_commit(self):
        """Test committing a transaction."""
        self.worker.begin_transaction()
        self.worker.execute("INSERT INTO accounts (id, balance) VALUES (?, ?)", (1, 100))
        self.worker.execute("INSERT INTO accounts (id, balance) VALUES (?, ?)", (2, 200))
        self.worker.commit_transaction()
        
        time.sleep(1)
        
        token = self.worker.execute("SELECT * FROM accounts ORDER BY id")
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], (1, 100))
        self.assertEqual(results[1], (2, 200))
    
    def test_transaction_rollback(self):
        """Test rolling back a transaction."""
        # Insert initial data
        self.worker.execute("INSERT INTO accounts (id, balance) VALUES (?, ?)", (1, 100))
        time.sleep(1)
        
        # Start transaction and insert more data
        self.worker.begin_transaction()
        self.worker.execute("INSERT INTO accounts (id, balance) VALUES (?, ?)", (2, 200))
        self.worker.rollback_transaction()
        
        time.sleep(1)
        
        # Should only have the first record
        token = self.worker.execute("SELECT * FROM accounts ORDER BY id")
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], (1, 100))
    
    def test_transaction_context_manager(self):
        """Test transaction context manager."""
        with self.worker.transaction():
            self.worker.execute("INSERT INTO accounts (id, balance) VALUES (?, ?)", (1, 100))
            self.worker.execute("INSERT INTO accounts (id, balance) VALUES (?, ?)", (2, 200))
        
        time.sleep(1)
        
        token = self.worker.execute("SELECT * FROM accounts ORDER BY id")
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 2)
    
    def test_transaction_context_manager_rollback(self):
        """Test transaction context manager with exception."""
        try:
            with self.worker.transaction():
                self.worker.execute("INSERT INTO accounts (id, balance) VALUES (?, ?)", (1, 100))
                raise ValueError("Test error")
        except ValueError:
            pass
        
        time.sleep(1)
        
        token = self.worker.execute("SELECT * FROM accounts")
        results = self.worker.fetch_results(token)
        
        # Should be empty due to rollback
        self.assertEqual(len(results), 0)


class TestORMFunctionality(unittest.TestCase):
    """Test ORM-like CRUD methods."""
    
    def setUp(self):
        self.db_file = 'test_orm.db'
        self.worker = SqliteWorker(self.db_file)
        time.sleep(0.5)
        
        # Create test table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT,
                age INTEGER
            )
        """)
        time.sleep(0.5)
    
    def tearDown(self):
        self.worker.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_insert_method(self):
        """Test insert method."""
        token = self.worker.insert('users', {
            'name': 'Alice',
            'email': 'alice@example.com',
            'age': 30
        })
        self.worker.fetch_results(token)
        time.sleep(1)
        
        token = self.worker.select('users', conditions={'name': 'Alice'})
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 'Alice')
        self.assertEqual(results[0][2], 'alice@example.com')
        self.assertEqual(results[0][3], 30)
    
    def test_update_method(self):
        """Test update method."""
        # Insert data
        token = self.worker.insert('users', {'name': 'Bob', 'email': 'bob@example.com', 'age': 25})
        self.worker.fetch_results(token)
        time.sleep(1)
        
        # Update data
        token = self.worker.update('users', {'age': 26}, {'name': 'Bob'})
        self.worker.fetch_results(token)
        time.sleep(1)
        
        # Verify update
        token = self.worker.select('users', conditions={'name': 'Bob'})
        results = self.worker.fetch_results(token)
        
        self.assertEqual(results[0][3], 26)
    
    def test_delete_method(self):
        """Test delete method."""
        # Insert data
        token = self.worker.insert('users', {'name': 'Charlie', 'email': 'charlie@example.com', 'age': 35})
        self.worker.fetch_results(token)
        time.sleep(1)
        
        # Delete data
        token = self.worker.delete('users', {'name': 'Charlie'})
        self.worker.fetch_results(token)
        time.sleep(1)
        
        # Verify deletion
        token = self.worker.select('users', conditions={'name': 'Charlie'})
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 0)
    
    def test_select_method_with_columns(self):
        """Test select method with specific columns."""
        # Insert data
        token = self.worker.insert('users', {'name': 'David', 'email': 'david@example.com', 'age': 40})
        self.worker.fetch_results(token)
        time.sleep(1)
        
        # Select specific columns
        token = self.worker.select('users', columns=['name', 'age'])
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0]), 2)  # Only 2 columns
        self.assertEqual(results[0][0], 'David')
        self.assertEqual(results[0][1], 40)
    
    def test_select_method_with_limit_and_order(self):
        """Test select method with limit and order by."""
        # Insert multiple records
        self.worker.insert('users', {'name': 'User1', 'age': 20})
        self.worker.insert('users', {'name': 'User2', 'age': 30})
        self.worker.insert('users', {'name': 'User3', 'age': 25})
        time.sleep(1)
        
        # Select with order and limit
        token = self.worker.select('users', order_by='age DESC', limit=2)
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], 'User2')  # age 30
        self.assertEqual(results[1][1], 'User3')  # age 25


class TestObservableQueries(unittest.TestCase):
    """Test observable queries (hooks) functionality."""
    
    def setUp(self):
        self.db_file = 'test_hooks.db'
        self.worker = SqliteWorker(self.db_file)
        self.hook_calls = []
        time.sleep(0.5)
        
        # Create test table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_name TEXT
            )
        """)
        time.sleep(0.5)
    
    def tearDown(self):
        self.worker.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_register_and_trigger_hook(self):
        """Test registering and triggering a hook."""
        def my_hook(query, values):
            self.hook_calls.append((query, values))
        
        self.worker.register_hook('on_query', my_hook)
        
        self.worker.execute("INSERT INTO events (event_name) VALUES (?)", ("test_event",))
        time.sleep(1)
        
        self.assertGreater(len(self.hook_calls), 0)
        self.assertIn("INSERT", self.hook_calls[-1][0])
    
    def test_specific_insert_hook(self):
        """Test hook specific to INSERT queries."""
        insert_calls = []
        
        def insert_hook(query, values):
            insert_calls.append((query, values))
        
        self.worker.register_hook('on_insert', insert_hook)
        
        self.worker.execute("INSERT INTO events (event_name) VALUES (?)", ("event1",))
        time.sleep(1)
        
        self.worker.execute("SELECT * FROM events")
        time.sleep(1)
        
        # Only INSERT should trigger the hook
        self.assertEqual(len(insert_calls), 1)
    
    def test_unregister_hook(self):
        """Test unregistering a hook."""
        def my_hook(query, values):
            self.hook_calls.append((query, values))
        
        self.worker.register_hook('on_query', my_hook)
        self.worker.execute("INSERT INTO events (event_name) VALUES (?)", ("event1",))
        time.sleep(1)
        
        initial_calls = len(self.hook_calls)
        
        self.worker.unregister_hook('on_query', my_hook)
        self.worker.execute("INSERT INTO events (event_name) VALUES (?)", ("event2",))
        time.sleep(1)
        
        # Should not have increased
        self.assertEqual(len(self.hook_calls), initial_calls)


class TestDatabaseMigrations(unittest.TestCase):
    """Test database migration functionality."""
    
    def setUp(self):
        self.db_file = 'test_migrations.db'
        self.worker = SqliteWorker(self.db_file)
        time.sleep(0.5)
    
    def tearDown(self):
        self.worker.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_apply_migration(self):
        """Test applying a migration."""
        migration_sql = """
            CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL
            )
        """
        
        result = self.worker.apply_migration('001', 'create_products_table', migration_sql)
        time.sleep(1)
        
        self.assertTrue(result)
        
        # Verify table was created
        token = self.worker.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='products'")
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 1)
    
    def test_migration_idempotency(self):
        """Test that applying the same migration twice doesn't fail."""
        migration_sql = "CREATE TABLE test_table (id INTEGER PRIMARY KEY)"
        
        result1 = self.worker.apply_migration('002', 'create_test_table', migration_sql)
        time.sleep(1)
        result2 = self.worker.apply_migration('002', 'create_test_table', migration_sql)
        time.sleep(1)
        
        self.assertTrue(result1)
        self.assertFalse(result2)  # Already applied
    
    def test_get_applied_migrations(self):
        """Test getting list of applied migrations."""
        self.worker.apply_migration('001', 'migration_one', "SELECT 1")
        self.worker.apply_migration('002', 'migration_two', "SELECT 2")
        time.sleep(1)
        
        migrations = self.worker.get_applied_migrations()
        
        self.assertEqual(len(migrations), 2)
        self.assertEqual(migrations[0][0], '001')
        self.assertEqual(migrations[1][0], '002')
    
    def test_rollback_migration(self):
        """Test rolling back a migration."""
        up_sql = "CREATE TABLE rollback_test (id INTEGER PRIMARY KEY)"
        down_sql = "DROP TABLE rollback_test"
        
        # Apply migration
        self.worker.apply_migration('003', 'rollback_test', up_sql)
        time.sleep(1)
        
        # Verify table exists
        token = self.worker.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rollback_test'")
        results = self.worker.fetch_results(token)
        self.assertEqual(len(results), 1)
        
        # Rollback migration
        result = self.worker.rollback_migration('003', down_sql)
        time.sleep(1)
        
        self.assertTrue(result)
        
        # Verify table is gone
        token = self.worker.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='rollback_test'")
        results = self.worker.fetch_results(token)
        self.assertEqual(len(results), 0)


class TestAutoReconnection(unittest.TestCase):
    """Test auto-reconnection functionality."""
    
    def setUp(self):
        self.db_file = 'test_reconnect.db'
    
    def tearDown(self):
        if hasattr(self, 'worker'):
            self.worker.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_auto_reconnect_enabled(self):
        """Test that auto_reconnect is enabled by default."""
        self.worker = SqliteWorker(self.db_file)
        self.assertTrue(self.worker.auto_reconnect)
        self.assertEqual(self.worker.max_retries, 3)
    
    def test_custom_retry_settings(self):
        """Test custom retry settings."""
        self.worker = SqliteWorker(
            self.db_file,
            auto_reconnect=True,
            max_retries=5,
            retry_delay=0.5
        )
        
        self.assertTrue(self.worker.auto_reconnect)
        self.assertEqual(self.worker.max_retries, 5)
        self.assertEqual(self.worker.retry_delay, 0.5)
    
    def test_basic_operations_with_reconnect(self):
        """Test that basic operations work with auto-reconnect enabled."""
        self.worker = SqliteWorker(self.db_file, auto_reconnect=True, max_retries=3)
        time.sleep(0.5)
        
        self.worker.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, value TEXT)")
        self.worker.execute("INSERT INTO test (value) VALUES (?)", ("test_value",))
        time.sleep(1)
        
        token = self.worker.execute("SELECT * FROM test")
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], "test_value")


class TestInputValidation(unittest.TestCase):
    """Test SQL injection protection and input validation."""
    
    def setUp(self):
        self.db_file = 'test_validation.db'
        self.worker = SqliteWorker(self.db_file)
        time.sleep(0.5)
        
        # Create test table
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS test_table (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        """)
        time.sleep(0.5)
    
    def tearDown(self):
        self.worker.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)
    
    def test_invalid_table_name_insert(self):
        """Test that invalid table names are rejected in insert."""
        with self.assertRaises(ValueError):
            self.worker.insert('users; DROP TABLE test_table; --', {'name': 'test'})
    
    def test_invalid_column_name_insert(self):
        """Test that invalid column names are rejected in insert."""
        with self.assertRaises(ValueError):
            self.worker.insert('test_table', {'name;DROP TABLE test': 'test'})
    
    def test_invalid_table_name_select(self):
        """Test that invalid table names are rejected in select."""
        with self.assertRaises(ValueError):
            self.worker.select('test_table; DROP TABLE test_table; --')
    
    def test_invalid_column_name_select(self):
        """Test that invalid column names are rejected in select."""
        with self.assertRaises(ValueError):
            self.worker.select('test_table', columns=['id', 'name;DROP'])
    
    def test_invalid_order_by(self):
        """Test that invalid order_by is rejected."""
        with self.assertRaises(ValueError):
            self.worker.select('test_table', order_by='name; DROP TABLE test_table')
    
    def test_invalid_limit(self):
        """Test that invalid limit is rejected."""
        with self.assertRaises(ValueError):
            self.worker.select('test_table', limit='10; DROP TABLE test_table')
    
    def test_negative_limit(self):
        """Test that negative limit is rejected."""
        with self.assertRaises(ValueError):
            self.worker.select('test_table', limit=-1)
    
    def test_valid_identifiers_work(self):
        """Test that valid identifiers work correctly."""
        token = self.worker.insert('test_table', {'name': 'Alice'})
        self.worker.fetch_results(token)
        time.sleep(0.5)
        
        token = self.worker.select('test_table', columns=['id', 'name'], 
                                   conditions={'name': 'Alice'}, 
                                   order_by='name ASC', limit=1)
        results = self.worker.fetch_results(token)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0][1], 'Alice')


if __name__ == '__main__':
    unittest.main()
