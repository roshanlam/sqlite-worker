# sqlite-worker Examples

This directory contains comprehensive examples demonstrating real-world use cases and advanced techniques for sqlite-worker.

## 📚 Available Examples

### 1. [FastAPI Integration](./fastapi_integration/)
Build a complete RESTful API with thread-safe database operations.

**Key Features:**
- Full CRUD operations
- Request/response validation with Pydantic
- Automatic API documentation
- Production-ready error handling

**Use Cases:** Web APIs, microservices, backend services

---

### 2. [Batch Processing](./batch_processing/)
Process online store transactions in batches with proper error handling.

**Key Features:**
- High-volume transaction processing
- Inventory management
- Transaction safety with rollback
- Sales reporting and CSV export

**Use Cases:** E-commerce, data pipelines, bulk operations

---

### 3. [Task Queue System](./task_queue/)
Distributed task queue with priority scheduling and automatic retries.

**Key Features:**
- Priority-based scheduling
- Scheduled tasks
- Automatic retry logic
- Multi-worker support

**Use Cases:** Background jobs, async processing, scheduled tasks

---

### 4. [Advanced Optimization](./advanced_optimization/)
Query optimization techniques for maximum performance.

**Key Features:**
- Index strategies
- Bulk insert optimization
- Query planning analysis
- PRAGMA tuning

**Use Cases:** Performance optimization, large databases, analytics

---

## 🚀 Quick Start

Each example is self-contained with its own README. To run an example:

```bash
# Navigate to the example directory
cd examples/fastapi_integration

# Install dependencies (if any)
pip install -r requirements.txt

# Run the example
python main.py
```

## 📖 Framework Integrations

See the [Framework Integrations](./framework_integrations/) directory for examples using:
- Flask
- Django
- FastAPI
- Streamlit

## 🎓 Learning Path

**Beginners:**
1. Start with FastAPI Integration for basic CRUD operations
2. Move to Batch Processing for transaction handling
3. Explore Task Queue for async patterns

**Advanced Users:**
1. Review Advanced Optimization for performance tuning
2. Study Framework Integrations for production patterns
3. Check out the starter templates for rapid development

## 💡 Common Patterns

### Thread-Safe Database Access
All examples demonstrate proper thread-safe usage:
```python
from sqlite_worker import SqliteWorker

worker = SqliteWorker("database.db")
# Use worker from any thread safely
```

### Transaction Management
```python
with worker.transaction():
    # All operations are atomic
    worker.insert("table1", data1)
    worker.update("table2", data2)
    # Commits on success, rolls back on error
```

### Error Handling
```python
try:
    token = worker.execute(query, params)
    results = worker.fetch_results(token)
except Exception as e:
    # Handle errors appropriately
    print(f"Database error: {e}")
```

## 🎯 Use Case Guide

| Scenario | Recommended Example |
|----------|-------------------|
| Building a REST API | FastAPI Integration |
| Processing bulk data | Batch Processing |
| Background jobs | Task Queue |
| Performance issues | Advanced Optimization |
| Web application | Framework Integrations |

## 📝 Best Practices

All examples follow these best practices:

1. **Initialize with optimal settings**
   ```python
   worker = SqliteWorker(
       db_path,
       execute_init=[
           "PRAGMA journal_mode=WAL;",
           "PRAGMA synchronous=NORMAL;",
           "PRAGMA temp_store=MEMORY;"
       ]
   )
   ```

2. **Use transactions for multi-step operations**
3. **Implement proper error handling**
4. **Close connections when done**
5. **Use parameterized queries (prevents SQL injection)**

## 🔧 Customization

Each example can be customized for your needs:
- Modify database schemas
- Add custom business logic
- Integrate with external services
- Scale with multiple workers

## 📚 Additional Resources

- [Main README](../ReadMe.md) - Full documentation
- [Starter Templates](../templates/) - Quick-start projects
- [CONTRIBUTING](../CONTRIBUTING.md) - Contribution guidelines

## 🤝 Contributing

Have a great example to share? We welcome contributions!

1. Create your example following the existing structure
2. Include a detailed README
3. Add tests if applicable
4. Submit a pull request

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/roshanlam/sqlite-worker/issues)
- **Discussions**: [GitHub Discussions](https://github.com/roshanlam/sqlite-worker/discussions)
- **Questions**: Use the "Question" issue template

## 📄 License

All examples are provided under the same license as sqlite-worker. See [LICENSE](../LICENSE) for details.
