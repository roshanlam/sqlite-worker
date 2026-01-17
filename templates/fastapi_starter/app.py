"""
FastAPI Starter Template with sqlite-worker
"""

from fastapi import FastAPI, HTTPException
from database import get_worker, init_database
from models import Item, ItemCreate, ItemUpdate

# Initialize FastAPI app
app = FastAPI(
    title="SQLite-Worker API",
    description="FastAPI starter template with sqlite-worker",
    version="1.0.0"
)

# Initialize database
init_database()
worker = get_worker()


@app.on_event("shutdown")
def shutdown():
    """Cleanup on shutdown"""
    worker.close()


@app.get("/")
def read_root():
    """Welcome endpoint"""
    return {
        "message": "Welcome to SQLite-Worker FastAPI Starter",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}


@app.get("/items")
def list_items(limit: int = 100):
    """List all items"""
    token = worker.select("items", limit=limit, order_by="created_at DESC")
    items_data = worker.fetch_results(token)
    
    return [
        {
            "id": item[0],
            "name": item[1],
            "description": item[2],
            "value": item[3],
            "created_at": item[4]
        }
        for item in items_data
    ]


@app.post("/items", status_code=201)
def create_item(item: ItemCreate):
    """Create a new item"""
    token = worker.insert("items", {
        "name": item.name,
        "description": item.description,
        "value": item.value
    })
    worker.fetch_results(token)
    
    # Get the created item
    token = worker.execute(
        "SELECT * FROM items WHERE rowid = last_insert_rowid()"
    )
    result = worker.fetch_results(token)
    
    if result:
        item_data = result[0]
        return {
            "id": item_data[0],
            "name": item_data[1],
            "description": item_data[2],
            "value": item_data[3],
            "created_at": item_data[4]
        }
    
    raise HTTPException(status_code=500, detail="Failed to create item")


@app.get("/items/{item_id}")
def get_item(item_id: int):
    """Get a specific item"""
    token = worker.select("items", conditions={"id": item_id})
    items = worker.fetch_results(token)
    
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    item = items[0]
    return {
        "id": item[0],
        "name": item[1],
        "description": item[2],
        "value": item[3],
        "created_at": item[4]
    }


@app.put("/items/{item_id}")
def update_item(item_id: int, item_update: ItemUpdate):
    """Update an item"""
    # Check if item exists
    token = worker.select("items", conditions={"id": item_id})
    items = worker.fetch_results(token)
    
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Build update data
    update_data = {}
    if item_update.name is not None:
        update_data["name"] = item_update.name
    if item_update.description is not None:
        update_data["description"] = item_update.description
    if item_update.value is not None:
        update_data["value"] = item_update.value
    
    if update_data:
        token = worker.update("items", update_data, {"id": item_id})
        worker.fetch_results(token)
    
    # Return updated item
    return get_item(item_id)


@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    """Delete an item"""
    # Check if item exists
    token = worker.select("items", conditions={"id": item_id})
    items = worker.fetch_results(token)
    
    if not items:
        raise HTTPException(status_code=404, detail="Item not found")
    
    token = worker.delete("items", {"id": item_id})
    worker.fetch_results(token)
    
    return {"message": "Item deleted successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
