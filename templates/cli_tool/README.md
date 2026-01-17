# CLI Tool Template with sqlite-worker

A command-line interface template for managing SQLite databases using sqlite-worker.

## Quick Start

```bash
# Make executable
chmod +x cli.py

# Show help
./cli.py --help

# List items
./cli.py list

# Add item
./cli.py add "My Item" --desc "Description"
```

## Features

- ✅ CRUD operations (Create, Read, Update, Delete)
- ✅ Search functionality
- ✅ JSON import/export
- ✅ Database statistics
- ✅ Thread-safe operations
- ✅ Clean command-line interface

## Available Commands

### List Items
```bash
./cli.py list
./cli.py list --limit 10
```

### Add Item
```bash
./cli.py add "Item Name"
./cli.py add "Item Name" --desc "Description"
```

### Get Item
```bash
./cli.py get 1
```

### Update Item
```bash
./cli.py update 1 --name "New Name"
./cli.py update 1 --desc "New Description"
./cli.py update 1 --name "New Name" --desc "New Description"
```

### Delete Item
```bash
./cli.py delete 1
```

### Search Items
```bash
./cli.py search "keyword"
```

### Export to JSON
```bash
./cli.py export output.json
```

### Import from JSON
```bash
./cli.py import data.json
```

### Show Statistics
```bash
./cli.py stats
```

## Custom Database

Use a different database file:
```bash
./cli.py --db custom.db list
./cli.py --db custom.db add "Item"
```

## Example Usage

```bash
# Add some items
./cli.py add "Task 1" --desc "Complete documentation"
./cli.py add "Task 2" --desc "Write tests"
./cli.py add "Task 3" --desc "Deploy to production"

# List all items
./cli.py list

# Search for specific items
./cli.py search "test"

# Export to JSON
./cli.py export tasks.json

# Show statistics
./cli.py stats

# Update an item
./cli.py update 1 --desc "Documentation completed"

# Delete an item
./cli.py delete 2
```

## Customization

### Add New Commands

```python
def your_command(self):
    """Your command implementation"""
    # Your logic here
    pass

# In main():
your_parser = subparsers.add_parser('your_command', help='Your help text')
your_parser.add_argument('arg', help='Argument help')
```

### Add New Fields

```python
# Update schema
self.worker.execute("""
    ALTER TABLE items ADD COLUMN your_field TEXT
""")

# Update add_item
def add_item(self, name, description=None, your_field=None):
    token = self.worker.insert("items", {
        "name": name,
        "description": description,
        "your_field": your_field
    })
```

### Add Colors

```python
# Install colorama
# pip install colorama

from colorama import Fore, Style

def list_items(self):
    print(f"{Fore.GREEN}✅ Items:{Style.RESET_ALL}")
    # ...
```

## Use Cases

### Task Manager

```bash
./cli.py add "Buy groceries" --desc "Milk, eggs, bread"
./cli.py add "Call dentist" --desc "Schedule appointment"
./cli.py list
```

### Note Taking

```bash
./cli.py add "Meeting Notes" --desc "Discussed Q4 goals..."
./cli.py search "meeting"
```

### Inventory Management

```bash
./cli.py add "Laptop" --desc "Dell XPS 15, SN: 12345"
./cli.py add "Monitor" --desc "27 inch 4K"
```

### Contact Manager

```python
# Customize for contacts
self.worker.execute("""
    CREATE TABLE contacts (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        phone TEXT
    )
""")
```

## Installation as Package

Create `setup.py`:

```python
from setuptools import setup

setup(
    name='your-cli-tool',
    version='1.0.0',
    py_modules=['cli'],
    install_requires=['sqlite-worker'],
    entry_points={
        'console_scripts': [
            'your-tool=cli:main',
        ],
    },
)
```

Install:
```bash
pip install -e .
your-tool list
```

## Testing

```python
import unittest
from cli import CLITool

class TestCLI(unittest.TestCase):
    def setUp(self):
        self.tool = CLITool(':memory:')
    
    def test_add_item(self):
        self.tool.add_item("Test", "Description")
        items = self.tool.worker.fetch_results(
            self.tool.worker.select("items")
        )
        self.assertEqual(len(items), 1)
```

## Advanced Features

### Add Confirmation Prompts

```python
def delete_item(self, item_id):
    response = input(f"Delete item #{item_id}? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled")
        return
    # ... delete logic
```

### Add Progress Bars

```python
from tqdm import tqdm

def import_json(self, filename):
    data = json.load(open(filename))
    for item in tqdm(data, desc="Importing"):
        self.worker.insert("items", item)
```

### Add Configuration File

```python
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
db_path = config.get('database', 'path', fallback='data.db')
```

## Troubleshooting

**Permission Denied**
```bash
chmod +x cli.py
```

**Database Locked**
- Ensure no other process is using the database
- WAL mode is enabled by default for better concurrency

**Module Not Found**
```bash
pip install sqlite-worker
```

## Resources

- [argparse Documentation](https://docs.python.org/3/library/argparse.html)
- [sqlite-worker Repository](https://github.com/roshanlam/sqlite-worker)
- [Click Framework](https://click.palletsprojects.com/) - Alternative CLI framework

## Next Steps

- Add authentication
- Implement backup/restore
- Add shell completion
- Create man pages
- Package as executable
- Add logging
- Implement undo/redo
- Add bulk operations

Perfect starting point for building command-line tools with SQLite!
