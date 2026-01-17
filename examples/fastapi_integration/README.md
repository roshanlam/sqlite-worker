# FastAPI Integration with sqlite-worker

This example demonstrates how to build a RESTful API using FastAPI and sqlite-worker for thread-safe database operations.

## Features

- Complete CRUD operations (Create, Read, Update, Delete)
- Thread-safe database access
- Automatic database initialization with WAL mode
- Pydantic models for request/response validation
- Error handling and HTTP status codes

## Installation

```bash
pip install fastapi uvicorn sqlite-worker
```

## Running the Application

```bash
# From the fastapi_integration directory
python main.py

# Or using uvicorn directly
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Example API Calls

### Create a User
```bash
curl -X POST "http://localhost:8000/users" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice", "email": "alice@example.com", "age": 30}'
```

### List All Users
```bash
curl "http://localhost:8000/users"
```

### Get a Specific User
```bash
curl "http://localhost:8000/users/1"
```

### Update a User
```bash
curl -X PUT "http://localhost:8000/users/1" \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice Smith", "age": 31}'
```

### Delete a User
```bash
curl -X DELETE "http://localhost:8000/users/1"
```

## Key Benefits

1. **Thread Safety**: sqlite-worker handles concurrent requests safely
2. **Simple API**: Clean and intuitive ORM-like interface
3. **Production Ready**: WAL mode and proper PRAGMA settings
4. **Error Handling**: Proper HTTP status codes and error messages

## Next Steps

- Add authentication and authorization
- Implement pagination for large datasets
- Add filtering and search capabilities
- Use database migrations for schema changes
