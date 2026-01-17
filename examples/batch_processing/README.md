# Batch Processing: Online Store Transactions

This example demonstrates batch processing of online store transactions using sqlite-worker with proper transaction management and error handling.

## Features

- **Batch Transaction Processing**: Process multiple transactions efficiently
- **Inventory Management**: Real-time stock tracking and validation
- **Transaction Safety**: ACID compliance with automatic rollback on errors
- **Error Handling**: Graceful handling of failed transactions
- **Performance Optimization**: Bulk operations with regular commits
- **Reporting**: Sales summaries and CSV export capabilities

## Installation

```bash
pip install sqlite-worker
```

## Running the Example

```bash
python batch_processor.py
```

## What It Does

1. **Initializes Database**: Creates products and transactions tables with indexes
2. **Adds Sample Products**: Populates the database with 5 sample products
3. **Batch Processing**: Processes 200 transactions in batches of 50
4. **Validates Stock**: Checks product availability before processing
5. **Updates Inventory**: Decrements stock for successful transactions
6. **Error Handling**: Rolls back failed transactions automatically
7. **Generates Report**: Shows sales summary and revenue statistics
8. **Exports Data**: Creates CSV file with all transaction details

## Key Concepts

### Transaction Management

```python
with self.worker.transaction():
    # All operations within this block are atomic
    # Automatically commits on success
    # Automatically rolls back on any exception
    self.worker.insert("transactions", trans_data)
    self.worker.update("products", {"stock": new_stock}, {"id": product_id})
```

### Batch Processing Benefits

1. **Performance**: `max_count=100` commits after every 100 queries
2. **Memory Efficiency**: Processes data in manageable chunks
3. **Error Isolation**: Failed transactions don't affect successful ones
4. **Progress Tracking**: Real-time status updates during processing

### Use Cases

- **E-commerce Order Processing**: Handle high-volume online orders
- **Inventory Management**: Track product stock in real-time
- **Financial Transactions**: Process payments with ACID guarantees
- **Data Import/Export**: Bulk data operations with validation
- **ETL Pipelines**: Extract, transform, and load data efficiently

## Expected Output

```
============================================================
Online Store Transaction Batch Processing Demo
============================================================
Added 5 sample products

--- Batch 1 ---
Processing batch of 50 transactions...

✅ Successful: 48
❌ Failed: 2

--- Batch 2 ---
...

============================================================
Sales Summary
============================================================

📊 Overall Statistics:
   Total Transactions: 192
   Total Revenue: $28,543.08
   Average Transaction Value: $148.66

📦 Sales by Product:
   Laptop: 72 units sold, $7,199.28 revenue
   Monitor: 68 units sold, $6,119.32 revenue
   ...

📄 Exported 192 transactions to transactions.csv

✅ Demo completed successfully!
```

## Customization

You can customize the example by:
- Modifying `batch_size` for different batch sizes
- Adding more products or transaction types
- Implementing custom validation rules
- Adding more complex reporting queries
- Integrating with external payment systems

## Performance Tips

1. Use WAL mode for better concurrent write performance
2. Adjust `max_count` based on your transaction volume
3. Create indexes on frequently queried columns
4. Use transactions for multi-step operations
5. Process data in reasonable batch sizes (50-1000 records)
