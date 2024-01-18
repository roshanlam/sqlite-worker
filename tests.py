import threading
import unittest
from sqlite_worker import SqliteWorker
import sqlite3


# Todo: Write more tests


class TestSqliteWorker(unittest.TestCase):

    def setUp(self):
        # Set up an in-memory SQLite database for testing
        self.worker = SqliteWorker(":memory:")
        self.worker.execute(
            "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")

    def tearDown(self):
        # Close the worker after each test
        self.worker.close()

    def test_execute_insert_query(self):
        # Test insert operation
        self.worker.execute("INSERT INTO test (name) VALUES (?)", ("Alice",))
        result = self.worker.execute("SELECT * FROM test")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "Alice")

    def test_execute_select_query(self):
        # Test select operation
        self.worker.execute("INSERT INTO test (name) VALUES (?)", ("Bob",))
        result = self.worker.execute(
            "SELECT * FROM test WHERE name = ?", ("Bob",))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][1], "Bob")

    def test_thread_safety(self):
        # Test thread safety by executing concurrent queries
        def insert_data():
            for _ in range(100):
                self.worker.execute(
                    "INSERT INTO test (name) VALUES (?)", ("ThreadTest",))

        threads = [threading.Thread(target=insert_data) for _ in range(10)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        result = self.worker.execute(
            "SELECT COUNT(*) FROM test WHERE name = ?", ("ThreadTest",))
        self.assertEqual(result[0][0], 1000)

    def test_close_worker(self):
        # Test closing the worker
        self.worker.close()
        with self.assertRaises(RuntimeError):
            self.worker.execute("SELECT * FROM test")


if __name__ == '__main__':
    unittest.main()
