# 🔧 sqlite-worker

[![PyPI version](https://img.shields.io/pypi/v/sqlite-worker.svg)](https://pypi.org/project/sqlite-worker/)
[![Python versions](https://img.shields.io/pypi/pyversions/sqlite-worker.svg)](https://pypi.org/project/sqlite-worker/)
[![License](https://img.shields.io/github/license/roshanlam/sqlite-worker.svg)](LICENSE)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/sqlite-worker?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads)](https://pepy.tech/projects/sqlite-worker)


Sqlite-Worker is a Python package providing a thread-safe interface for SQLite database operations. It ensures safe concurrent access to SQLite databases and simplifies executing database queries from different threads.

**Perfect for:** Multi-threaded applications • Web APIs • Background workers • Data logging • Task queues

## Features

- Thread-safe SQLite database operations
- Queue-based query execution
- Simple and easy-to-use API
- Initialization actions executed once upon database connection
- Regular commits for continuous query streams
- **Database migrations** with version control and rollback support
- **ORM-like CRUD methods** for simplified database operations
- **Observable queries** with hooks/events for real-time notifications
- **Transaction support** with manual and context manager control
- **Auto-reconnection logic** for handling database locks and connection failures

## Installation

To install, run:

```sh
pip3 install sqlite-worker
```

## Why sqlite-worker?

### SQLite vs sqlite-worker

| Feature | Standard SQLite | sqlite-worker |
|---------|----------------|---------------|
| **Thread Safety** | ❌ Requires manual locking | ✅ Built-in thread safety |
| **Queue Management** | ❌ Manual implementation | ✅ Automatic queue handling |
| **Connection Pool** | ❌ Manual management | ✅ Managed internally |
| **Transaction API** | ⚠️ Manual BEGIN/COMMIT | ✅ Context managers |
| **ORM Methods** | ❌ Raw SQL only | ✅ CRUD helpers included |
| **Hooks/Events** | ❌ Not available | ✅ Observable queries |
| **Migrations** | ❌ Manual tracking | ✅ Built-in versioning |
| **Auto-reconnect** | ❌ Manual handling | ✅ Automatic retry logic |
| **Learning Curve** | Medium | Low |

**Performance Comparison:**

![Performance Chart](sqlite_performance_comparison.png)

*sqlite-worker provides consistent performance across concurrent operations while maintaining thread safety.*

# Basic Usage

## Creating a Worker Instance
To create a basic instance of Sqlite3Worker by specifying the path to your SQLite database file:

```python
from sqlite_worker import SqliteWorker
worker = SqliteWorker("/path/to/your/database.db")
```

## Worker instance with Initialization Actions
Create a `SqliteWorker` instance with initialization actions (such as setting pragmas):

```python
from sqlite_worker import SqliteWorker

init_actions = [
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA temp_store=MEMORY;"
]

worker = SqliteWorker("/path/to/your/database.db", execute_init=init_actions)
```

## Worker Instance with Regular Commits
Create a SqliteWorker instance with initialization actions and set a maximum query count for regular commits:

```python
from sqlite_worker import SqliteWorker

init_actions = [
    "PRAGMA journal_mode=WAL;",
    "PRAGMA synchronous=NORMAL;",
    "PRAGMA temp_store=MEMORY;"
]

worker = SqliteWorker("/path/to/your/database.db", execute_init=init_actions, max_count=50)
```

## Worker Instance with Auto-Reconnection
Enable auto-reconnection with custom retry settings:

```python
worker = SqliteWorker(
    "/path/to/your/database.db",
    auto_reconnect=True,
    max_retries=5,
    retry_delay=2.0
)
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
token = worker.execute("SELECT * FROM example")
results = worker.fetch_results(token)
print(results)
```

# ORM-like CRUD Operations

The worker provides high-level methods for common database operations:

## Insert
```python
token = worker.insert('users', {
    'name': 'Alice',
    'email': 'alice@example.com',
    'age': 30
})
worker.fetch_results(token)
```

## Update
```python
token = worker.update('users', 
    {'age': 31},  # New values
    {'name': 'Alice'}  # Conditions
)
worker.fetch_results(token)
```

## Delete
```python
token = worker.delete('users', {'name': 'Alice'})
worker.fetch_results(token)
```

## Select
```python
# Select all columns
token = worker.select('users')
results = worker.fetch_results(token)

# Select specific columns with conditions
token = worker.select('users', 
    columns=['name', 'email'],
    conditions={'age': 30},
    order_by='name ASC',
    limit=10
)
results = worker.fetch_results(token)
```

# Transaction Support

## Manual Transaction Control
```python
worker.begin_transaction()
try:
    worker.execute("INSERT INTO accounts (balance) VALUES (?)", (100,))
    worker.execute("INSERT INTO accounts (balance) VALUES (?)", (200,))
    worker.commit_transaction()
except Exception as e:
    worker.rollback_transaction()
    raise
```

## Transaction Context Manager
```python
with worker.transaction():
    worker.execute("INSERT INTO accounts (balance) VALUES (?)", (100,))
    worker.execute("INSERT INTO accounts (balance) VALUES (?)", (200,))
    # Automatically commits on success, rolls back on exception
```

# Observable Queries (Hooks)

Register callbacks to be notified when queries are executed:

```python
def on_insert(query, values):
    print(f"Insert executed: {query} with {values}")

def on_query(query, values):
    print(f"Query executed: {query}")

# Register hooks
worker.register_hook('on_insert', on_insert)
worker.register_hook('on_query', on_query)

# Hooks will be triggered when queries execute
worker.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))

# Unregister when done
worker.unregister_hook('on_insert', on_insert)
```

Available hook types:
- `on_query` - Triggered for all queries
- `on_insert` - Triggered for INSERT queries
- `on_update` - Triggered for UPDATE queries
- `on_delete` - Triggered for DELETE queries
- `on_select` - Triggered for SELECT queries

# Database Migrations

## Apply a Migration
```python
migration_sql = """
    CREATE TABLE products (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL
    );
    CREATE INDEX idx_products_name ON products(name);
"""

# Apply migration
success = worker.apply_migration('001', 'create_products_table', migration_sql)
if success:
    print("Migration applied successfully")
```

## Rollback a Migration
```python
rollback_sql = """
    DROP INDEX idx_products_name;
    DROP TABLE products;
"""

success = worker.rollback_migration('001', rollback_sql)
if success:
    print("Migration rolled back successfully")
```

## Get Applied Migrations
```python
migrations = worker.get_applied_migrations()
for version, name, applied_at in migrations:
    print(f"Version {version}: {name} (applied at {applied_at})")
```

# Closing the Worker
After completing all database operations, close the worker to ensure proper cleanup:
```python
worker.close()
```

# 📚 Examples and Tutorials

## Real-World Examples

Explore comprehensive examples in the [`examples/`](examples/) directory:

- **[FastAPI Integration](examples/fastapi_integration/)** - Build REST APIs with thread-safe database operations
- **[Batch Processing](examples/batch_processing/)** - Handle high-volume transactions efficiently  
- **[Task Queue System](examples/task_queue/)** - Implement distributed task scheduling
- **[Multi-threaded Logging](examples/multi_threaded_logging/)** - High-performance concurrent logging
- **[E-commerce Platform](examples/ecommerce_prototype/)** - Complete shopping cart and order system
- **[Query Optimization](examples/advanced_optimization/)** - Advanced performance tuning techniques

## Framework Integrations

See [`examples/framework_integrations/`](examples/framework_integrations/) for:

- **Flask** - Simple blog application
- **Django** - Integration patterns with Django ORM
- **Streamlit** - Interactive analytics dashboard

## Starter Templates

Jump-start your project with ready-to-use templates in [`templates/`](templates/):

- **[FastAPI Starter](templates/fastapi_starter/)** - Complete REST API template
- **[Jupyter Notebook](templates/jupyter_notebook/)** - Data analysis template
- **[CLI Tool](templates/cli_tool/)** - Command-line interface template

# 🤝 Community and Contributing

## Getting Help

- **📖 Documentation**: Check the [examples](examples/) and [README](ReadMe.md)
- **💬 Discussions**: Ask questions in [GitHub Discussions](https://github.com/roshanlam/sqlite-worker/discussions)
- **🐛 Bug Reports**: Submit issues using our [bug report template](https://github.com/roshanlam/sqlite-worker/issues/new?template=bug_report.yml)
- **💡 Feature Requests**: Suggest improvements using our [feature request template](https://github.com/roshanlam/sqlite-worker/issues/new?template=feature_request.yml)

## Contributing

We welcome contributions! Here's how you can help:

- 🐛 **Report Bugs** - Found an issue? [Report it](https://github.com/roshanlam/sqlite-worker/issues/new?template=bug_report.yml)
- 💡 **Suggest Features** - Have an idea? [Share it](https://github.com/roshanlam/sqlite-worker/issues/new?template=feature_request.yml)
- 📝 **Improve Documentation** - Help others understand better
- 🔧 **Submit Pull Requests** - Fix bugs or add features
- ⭐ **Star the Project** - Show your support!

### Good First Issues

New to the project? Look for issues labeled [`good first issue`](https://github.com/roshanlam/sqlite-worker/labels/good%20first%20issue) - these are perfect for first-time contributors!

**Please read our [Contributing Guide](CONTRIBUTING.md) before submitting pull requests.**

## Community

- **GitHub Discussions**: Share your use cases and get help
- **Issue Tracker**: Report bugs and request features
- **Pull Requests**: Contribute code improvements

## Contributors

Thank you to all our contributors! 🎉

<a href="https://github.com/roshanlam/sqlite-worker/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=roshanlam/sqlite-worker" />
</a>

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

# Acknowledgements

Special thanks to [Johannes Ahlmann](https://github.com/codinguncut) for their valuable suggestion on initializing actions and implementing regular commits.
