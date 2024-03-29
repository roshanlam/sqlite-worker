# sqlite-worker
Sqlite-Worker is a Python package providing a thread-safe interface for SQLite database operations. It ensures safe concurrent access to SQLite databases and simplifies executing database queries from different threads.


# Features
* Thread-safe SQLite database operations
* Queue-based query execution
* Simple and easy-to-use API


# Installation

To install do the following: 

``` 
pip3 install sqlite-worker
```


# Creating a Worker Instance
Create an instance of Sqlite3Worker by specifying the path to your SQLite database file:

```python
from sqlite_worker import SqliteWorker
worker = SqliteWorker("/path/to/your/database.db")
```

# Execute Queries

## Creating a table
```python
worker.execute("CREATE TABLE example (id INTEGER PRIMARY KEY, name TEXT)")
```

## Inserting data
```python
worker.execute("INSERT INTO example (name) VALUES (?)", ("Alice",))
```

## Fetching data
```python 
results = worker.execute("SELECT * FROM example")
print(results)
```

# Closing the Worker
After completing all database operations, close the worker to ensure proper cleanup:
```python
worker.close()
```

# Contributing
Contributions to the Sqlite-Worker are welcome! Please refer to the project's issues and pull request sections for contributions.