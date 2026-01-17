#!/usr/bin/env python3
"""
CLI Tool Template with sqlite-worker

A command-line interface for managing a SQLite database using sqlite-worker.
"""

import argparse
import sys
from sqlite_worker import SqliteWorker
from datetime import datetime
import json


class CLITool:
    """CLI tool for database operations"""
    
    def __init__(self, db_path: str = "data.db"):
        """Initialize the CLI tool"""
        self.worker = SqliteWorker(
            db_path,
            execute_init=[
                "PRAGMA journal_mode=WAL;",
                "PRAGMA synchronous=NORMAL;",
            ]
        )
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create database schema"""
        self.worker.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    def list_items(self, limit: int = 100):
        """List all items"""
        token = self.worker.select("items", limit=limit, order_by="created_at DESC")
        items = self.worker.fetch_results(token)
        
        if not items:
            print("No items found.")
            return
        
        print(f"\n{'ID':<5} {'Name':<30} {'Created':<20}")
        print("-" * 60)
        for item in items:
            print(f"{item[0]:<5} {item[1]:<30} {item[3]:<20}")
        print(f"\nTotal: {len(items)} items\n")
    
    def add_item(self, name: str, description: str = None):
        """Add a new item"""
        token = self.worker.insert("items", {
            "name": name,
            "description": description
        })
        self.worker.fetch_results(token)
        print(f"✅ Added item: {name}")
    
    def get_item(self, item_id: int):
        """Get item details"""
        token = self.worker.select("items", conditions={"id": item_id})
        items = self.worker.fetch_results(token)
        
        if not items:
            print(f"❌ Item #{item_id} not found")
            return
        
        item = items[0]
        print(f"\n📋 Item Details:")
        print(f"   ID:          {item[0]}")
        print(f"   Name:        {item[1]}")
        print(f"   Description: {item[2] or 'N/A'}")
        print(f"   Created:     {item[3]}\n")
    
    def update_item(self, item_id: int, name: str = None, description: str = None):
        """Update an item"""
        # Check if item exists
        token = self.worker.select("items", conditions={"id": item_id})
        items = self.worker.fetch_results(token)
        
        if not items:
            print(f"❌ Item #{item_id} not found")
            return
        
        # Build update data
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        
        if not update_data:
            print("❌ No updates specified")
            return
        
        token = self.worker.update("items", update_data, {"id": item_id})
        self.worker.fetch_results(token)
        print(f"✅ Updated item #{item_id}")
    
    def delete_item(self, item_id: int):
        """Delete an item"""
        # Check if item exists
        token = self.worker.select("items", conditions={"id": item_id})
        items = self.worker.fetch_results(token)
        
        if not items:
            print(f"❌ Item #{item_id} not found")
            return
        
        token = self.worker.delete("items", {"id": item_id})
        self.worker.fetch_results(token)
        print(f"✅ Deleted item #{item_id}")
    
    def search_items(self, query: str):
        """Search items by name"""
        token = self.worker.execute("""
            SELECT id, name, description, created_at
            FROM items
            WHERE name LIKE ? OR description LIKE ?
            ORDER BY created_at DESC
        """, (f"%{query}%", f"%{query}%"))
        items = self.worker.fetch_results(token)
        
        if not items:
            print(f"No items found matching '{query}'")
            return
        
        print(f"\nSearch results for '{query}':")
        print(f"\n{'ID':<5} {'Name':<30} {'Created':<20}")
        print("-" * 60)
        for item in items:
            print(f"{item[0]:<5} {item[1]:<30} {item[3]:<20}")
        print(f"\nFound: {len(items)} items\n")
    
    def export_json(self, filename: str = "export.json"):
        """Export all items to JSON"""
        token = self.worker.select("items")
        items = self.worker.fetch_results(token)
        
        data = [
            {
                "id": item[0],
                "name": item[1],
                "description": item[2],
                "created_at": item[3]
            }
            for item in items
        ]
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"✅ Exported {len(items)} items to {filename}")
    
    def import_json(self, filename: str):
        """Import items from JSON"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            count = 0
            with self.worker.transaction():
                for item in data:
                    self.worker.insert("items", {
                        "name": item["name"],
                        "description": item.get("description")
                    })
                    count += 1
            
            print(f"✅ Imported {count} items from {filename}")
        except FileNotFoundError:
            print(f"❌ File not found: {filename}")
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON file: {filename}")
    
    def stats(self):
        """Show database statistics"""
        token = self.worker.execute("SELECT COUNT(*) FROM items")
        total = self.worker.fetch_results(token)[0][0]
        
        token = self.worker.execute("""
            SELECT MIN(created_at), MAX(created_at) FROM items
        """)
        result = self.worker.fetch_results(token)
        first_date = result[0][0] if result[0][0] else "N/A"
        last_date = result[0][1] if result[0][1] else "N/A"
        
        print("\n📊 Database Statistics:")
        print(f"   Total Items:     {total}")
        print(f"   First Created:   {first_date}")
        print(f"   Last Created:    {last_date}\n")
    
    def close(self):
        """Close database connection"""
        self.worker.close()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="CLI tool for managing SQLite database with sqlite-worker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                              # List all items
  %(prog)s add "My Item" --desc "Description"  # Add new item
  %(prog)s get 1                             # Get item by ID
  %(prog)s update 1 --name "New Name"        # Update item
  %(prog)s delete 1                          # Delete item
  %(prog)s search "keyword"                  # Search items
  %(prog)s export output.json                # Export to JSON
  %(prog)s import data.json                  # Import from JSON
  %(prog)s stats                             # Show statistics
        """
    )
    
    parser.add_argument(
        '--db',
        default='data.db',
        help='Database file path (default: data.db)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List all items')
    list_parser.add_argument('--limit', type=int, default=100, help='Maximum items to show')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new item')
    add_parser.add_argument('name', help='Item name')
    add_parser.add_argument('--desc', '--description', help='Item description')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get item by ID')
    get_parser.add_argument('id', type=int, help='Item ID')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update an item')
    update_parser.add_argument('id', type=int, help='Item ID')
    update_parser.add_argument('--name', help='New name')
    update_parser.add_argument('--desc', '--description', help='New description')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete an item')
    delete_parser.add_argument('id', type=int, help='Item ID')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search items')
    search_parser.add_argument('query', help='Search query')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export items to JSON')
    export_parser.add_argument('filename', nargs='?', default='export.json', help='Output file')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import items from JSON')
    import_parser.add_argument('filename', help='Input file')
    
    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Show statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize CLI tool
    tool = CLITool(args.db)
    
    try:
        # Execute command
        if args.command == 'list':
            tool.list_items(args.limit)
        elif args.command == 'add':
            tool.add_item(args.name, args.desc)
        elif args.command == 'get':
            tool.get_item(args.id)
        elif args.command == 'update':
            tool.update_item(args.id, args.name, args.desc)
        elif args.command == 'delete':
            tool.delete_item(args.id)
        elif args.command == 'search':
            tool.search_items(args.query)
        elif args.command == 'export':
            tool.export_json(args.filename)
        elif args.command == 'import':
            tool.import_json(args.filename)
        elif args.command == 'stats':
            tool.stats()
    finally:
        tool.close()


if __name__ == "__main__":
    main()
