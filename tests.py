import unittest
import time
from sqlite_worker import SqliteWorker
import sqlite3
import os


class TestSqliteWorker(unittest.TestCase):
    def setUp(self):
        self.db_file = 'test_example_sqlite.db'
        self.execute_init = (
            "PRAGMA journal_mode=WAL;",
            "PRAGMA synchronous=NORMAL;",
            "PRAGMA temp_store=MEMORY;"
        )
        self.worker = SqliteWorker(
            self.db_file, execute_init=self.execute_init)
        # Give some time for the worker to initialize and execute pragmas
        time.sleep(0.5)

    def tearDown(self):
        self.worker.close()
        if os.path.exists(self.db_file):
            os.remove(self.db_file)

    def test_initialization_and_pragmas(self):
        # Verify the worker initializes correctly and pragmas are executed
        self.assertTrue(os.path.exists(self.db_file))

        # Check if the database is in WAL mode
        with sqlite3.connect(self.db_file) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode;")
            result = cursor.fetchone()
            self.assertEqual(result[0], "wal")

    def test_create_table_and_insert(self):
        # Create a table
        self.worker.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"
        )

        # Insert data
        self.worker.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        self.worker.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))

        # Allow some time for the insert queries to complete
        time.sleep(1)

        # Fetch data
        token = self.worker.execute("SELECT * FROM users")
        time.sleep(1)  # Give some time for the select query to complete
        results = self.worker.fetch_results(token)

        self.assertIsNotNone(results)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0][1], "Alice")
        self.assertEqual(results[1][1], "Bob")

    def test_multiple_queries(self):
        # Create a table and insert data
        self.worker.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"
        )
        self.worker.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
        self.worker.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))

        # Allow some time for the insert queries to complete
        time.sleep(1)

        # Perform multiple select queries
        token1 = self.worker.execute(
            "SELECT * FROM users WHERE name = ?", ("Alice",))
        token2 = self.worker.execute(
            "SELECT * FROM users WHERE name = ?", ("Bob",))
        time.sleep(1)  # Give some time for the select queries to complete

        results1 = self.worker.fetch_results(token1)
        results2 = self.worker.fetch_results(token2)

        self.assertIsNotNone(results1)
        self.assertEqual(len(results1), 1)
        self.assertEqual(results1[0][1], "Alice")
        self.assertIsNotNone(results2)
        self.assertEqual(len(results2), 1)
        self.assertEqual(results2[0][1], "Bob")

    def test_error_handling(self):
        error_token = self.worker.execute("SELECT * FROM non_existing_table")
        time.sleep(1)  # Give some time for the error to be processed
        results = self.worker.fetch_results(error_token)
        self.assertIsInstance(results, sqlite3.Error)

    def test_close_worker(self):
        # Create a table and close the worker
        self.worker.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"
        )
        self.worker.close()

        # Verify that the worker is closed
        with self.assertRaises(RuntimeError):
            self.worker.execute(
                "INSERT INTO users (name) VALUES (?)", ("Charlie",))

    def test_queue_size(self):
        initial_size = self.worker.queue_size
        self.assertEqual(initial_size, 0)

        self.worker.execute(
            "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)"
        )
        self.assertEqual(self.worker.queue_size, 1)

        # Allow some time for the queries to complete
        time.sleep(1)

        self.assertEqual(self.worker.queue_size, 0)


if __name__ == '__main__':
    unittest.main()
