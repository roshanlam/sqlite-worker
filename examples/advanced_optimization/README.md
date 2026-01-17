# Advanced SQLite Query Optimization

This example demonstrates various techniques to optimize SQLite queries when using sqlite-worker for maximum performance.

## Features

- **Index Optimization**: Benefits of proper indexing strategies
- **Covering Indexes**: Minimize table lookups
- **Query Planning**: Understanding execution plans with EXPLAIN
- **Bulk Operations**: Efficient batch insert strategies
- **PRAGMA Settings**: Performance-tuning SQLite configuration
- **Statistics**: Using ANALYZE for better query plans
- **Best Practices**: Common optimization patterns

## Installation

```bash
pip install sqlite-worker
```

## Running the Example

```bash
python query_optimization.py
```

## Optimization Techniques Covered

### 1. Index Benefits

Demonstrates the dramatic performance improvement from proper indexing:
- Before/after index creation comparison
- GROUP BY and aggregate query optimization
- Multiple index strategies

### 2. Covering Indexes

Shows how covering indexes eliminate table lookups:
```sql
-- Covering index includes all columns needed
CREATE INDEX idx_orders_covering 
ON orders(customer_id, price, quantity);

-- Query uses only indexed columns
SELECT customer_id, SUM(price * quantity) as total
FROM orders
GROUP BY customer_id;
```

### 3. Query Planning

Uses `EXPLAIN QUERY PLAN` to understand execution:
- Identify missing indexes
- Understand join strategies
- Optimize query structure

### 4. Bulk Insert Optimization

Compares different insert strategies:
- Individual inserts: ~1.0s per 100 records
- Transaction batching: ~0.05s per 100 records
- **20x performance improvement!**

### 5. PRAGMA Optimization

Key PRAGMA settings for performance:

```python
PRAGMA journal_mode=WAL;        # Better concurrent access
PRAGMA synchronous=NORMAL;      # Balanced safety/performance
PRAGMA cache_size=-64000;       # 64MB cache
PRAGMA temp_store=MEMORY;       # Fast temporary tables
PRAGMA mmap_size=268435456;     # 256MB memory map
PRAGMA page_size=4096;          # Optimal page size
```

### 6. Query Optimization Best Practices

#### ✅ DO:
- Use `LIMIT` for large result sets
- Specify columns instead of `SELECT *`
- Use `EXISTS` instead of `COUNT(*) > 0`
- Index columns in WHERE, JOIN, ORDER BY
- Use parameterized queries (prevents SQL injection)
- Run `ANALYZE` periodically

#### ❌ DON'T:
- Use `SELECT *` unless necessary
- Forget to create indexes on foreign keys
- Use string concatenation for queries
- Index every column (diminishing returns)
- Ignore query plans

## Performance Tips

### Indexing Strategy

```python
# Single-column index
CREATE INDEX idx_customer_id ON orders(customer_id);

# Composite index (order matters!)
CREATE INDEX idx_customer_date ON orders(customer_id, order_date);

# Covering index
CREATE INDEX idx_covering ON orders(customer_id, price, quantity);
```

### Transaction Usage

```python
# Slow: Individual commits
for record in records:
    worker.insert("table", record)

# Fast: Single transaction
with worker.transaction():
    for record in records:
        worker.insert("table", record)
```

### Query Optimization

```python
# Slow: Counting for existence check
token = worker.execute("SELECT COUNT(*) FROM orders WHERE customer_id = ?", (id,))
exists = worker.fetch_results(token)[0][0] > 0

# Fast: EXISTS check
token = worker.execute(
    "SELECT EXISTS(SELECT 1 FROM orders WHERE customer_id = ?)", 
    (id,)
)
exists = worker.fetch_results(token)[0][0] == 1
```

## Real-World Scenarios

### High-Volume Logging

```python
# Use bulk inserts with transactions
with worker.transaction():
    for log_entry in logs:
        worker.insert("logs", log_entry)
```

### Complex Reporting

```python
# Create indexes on report dimensions
CREATE INDEX idx_sales_date ON sales(sale_date);
CREATE INDEX idx_sales_region ON sales(region);
CREATE INDEX idx_sales_product ON sales(product_id);

# Use covering indexes for common queries
CREATE INDEX idx_sales_summary 
ON sales(sale_date, region, amount);
```

### Real-time Analytics

```python
# Use materialized views (tables) for aggregates
CREATE TABLE daily_stats AS
SELECT 
    date(timestamp) as day,
    COUNT(*) as count,
    SUM(amount) as total
FROM transactions
GROUP BY date(timestamp);

# Create index on materialized view
CREATE INDEX idx_daily_stats_day ON daily_stats(day);
```

## Benchmarking Results

Sample performance improvements demonstrated:

| Technique | Before | After | Improvement |
|-----------|--------|-------|-------------|
| Adding Index | 0.050s | 0.005s | 10x faster |
| Covering Index | 0.012s | 0.003s | 4x faster |
| Transaction Batching | 1.000s | 0.050s | 20x faster |
| Query Simplification | 0.080s | 0.020s | 4x faster |

## Monitoring Query Performance

```python
import time

def benchmark_query(worker, query, params=()):
    start = time.time()
    token = worker.execute(query, params)
    results = worker.fetch_results(token)
    elapsed = time.time() - start
    print(f"Query time: {elapsed:.4f}s")
    return results
```

## Advanced Topics

### Query Cache

sqlite-worker maintains results cache, but SQLite itself doesn't cache query results. Consider:
- Materialized views for expensive queries
- Application-level caching
- Regular ANALYZE for fresh statistics

### Connection Pooling

For multi-process scenarios:
- Each process needs its own SqliteWorker
- WAL mode supports multiple readers
- Consider SQLite's limitations for writes

### Database Size Considerations

- **< 100MB**: Most optimizations unnecessary
- **100MB - 1GB**: Indexes and PRAGMA settings important
- **> 1GB**: Consider all optimizations, ANALYZE regularly
- **> 10GB**: Evaluate if SQLite is still appropriate

## Expected Output

```
============================================================
SQLite Query Optimization with sqlite-worker
============================================================

============================================================
DEMO 1: Index Benefits
============================================================

1. Query WITHOUT index on customer_id:
   Time: 0.0234s
   Results: 87 customers

2. Creating index on customer_id...

3. Query WITH index on customer_id:
   Time: 0.0021s
   Results: 87 customers

   📊 Performance improvement: 91.0%

...

============================================================
✅ All optimization demos completed!
============================================================
```

## Additional Resources

- [SQLite Query Planning](https://www.sqlite.org/queryplanner.html)
- [SQLite Performance Tuning](https://www.sqlite.org/pragma.html)
- [Index Optimization](https://www.sqlite.org/optoverview.html)
- sqlite-worker documentation

## When to Optimize

1. **Measure First**: Profile before optimizing
2. **Focus on Bottlenecks**: Optimize slow queries first
3. **Test Changes**: Benchmark before and after
4. **Keep It Simple**: Don't over-optimize
5. **Document**: Comment why optimizations were added
