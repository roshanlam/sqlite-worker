"""
FastAPI Integration Example with sqlite-worker

This example demonstrates how to integrate sqlite-worker with FastAPI
for building a simple REST API with thread-safe database operations.
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlite_worker import SqliteWorker
from typing import List, Optional
import os

# Initialize FastAPI app
app = FastAPI(title="SQLite Worker FastAPI Demo")

# Initialize database worker
DB_PATH = os.path.join(os.path.dirname(__file__), "app.db")
worker = SqliteWorker(
    DB_PATH,
    execute_init=[
        "PRAGMA journal_mode=WAL;",
        "PRAGMA synchronous=NORMAL;",
        "PRAGMA temp_store=MEMORY;"
    ],
    max_count=50
)

# Initialize database schema
worker.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        age INTEGER
    )
""")


# Pydantic models
class UserCreate(BaseModel):
    name: str
    email: str
    age: Optional[int] = None


class User(BaseModel):
    id: int
    name: str
    email: str
    age: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    age: Optional[int] = None


# API Endpoints
@app.get("/")
def read_root():
    """Health check endpoint"""
    return {"message": "SQLite Worker FastAPI Demo", "status": "running"}


@app.post("/users", response_model=User)
def create_user(user: UserCreate):
    """Create a new user"""
    try:
        data = {"name": user.name, "email": user.email}
        if user.age is not None:
            data["age"] = user.age
        
        token = worker.insert("users", data)
        result = worker.fetch_results(token)
        
        # Get the created user
        token = worker.select("users", conditions={"email": user.email})
        users = worker.fetch_results(token)
        
        if users:
            return User(
                id=users[0][0],
                name=users[0][1],
                email=users[0][2],
                age=users[0][3]
            )
        raise HTTPException(status_code=500, detail="User created but not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/users", response_model=List[User])
def list_users(limit: int = 100):
    """List all users"""
    try:
        token = worker.select("users", limit=limit)
        users = worker.fetch_results(token)
        
        return [
            User(id=u[0], name=u[1], email=u[2], age=u[3])
            for u in users
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int):
    """Get a specific user by ID"""
    try:
        token = worker.select("users", conditions={"id": user_id})
        users = worker.fetch_results(token)
        
        if not users:
            raise HTTPException(status_code=404, detail="User not found")
        
        return User(
            id=users[0][0],
            name=users[0][1],
            email=users[0][2],
            age=users[0][3]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user_update: UserUpdate):
    """Update a user"""
    try:
        # Check if user exists
        token = worker.select("users", conditions={"id": user_id})
        users = worker.fetch_results(token)
        
        if not users:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Build update data
        update_data = {}
        if user_update.name is not None:
            update_data["name"] = user_update.name
        if user_update.email is not None:
            update_data["email"] = user_update.email
        if user_update.age is not None:
            update_data["age"] = user_update.age
        
        if update_data:
            token = worker.update("users", update_data, {"id": user_id})
            worker.fetch_results(token)
        
        # Return updated user
        token = worker.select("users", conditions={"id": user_id})
        users = worker.fetch_results(token)
        
        return User(
            id=users[0][0],
            name=users[0][1],
            email=users[0][2],
            age=users[0][3]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/users/{user_id}")
def delete_user(user_id: int):
    """Delete a user"""
    try:
        # Check if user exists
        token = worker.select("users", conditions={"id": user_id})
        users = worker.fetch_results(token)
        
        if not users:
            raise HTTPException(status_code=404, detail="User not found")
        
        token = worker.delete("users", {"id": user_id})
        worker.fetch_results(token)
        
        return {"message": "User deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("shutdown")
def shutdown_event():
    """Cleanup on shutdown"""
    worker.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
