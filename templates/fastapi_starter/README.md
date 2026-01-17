# FastAPI Starter Template with sqlite-worker

A ready-to-use FastAPI project template with sqlite-worker integration for building REST APIs quickly.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py

# Or with uvicorn
uvicorn app:app --reload
```

Visit `http://localhost:8000/docs` for interactive API documentation.

## Project Structure

```
fastapi_starter/
├── app.py                  # Main application
├── database.py             # Database configuration
├── models.py               # Pydantic models
├── requirements.txt        # Dependencies
└── README.md              # This file
```

## Features

- ✅ FastAPI with automatic OpenAPI docs
- ✅ sqlite-worker for thread-safe database operations
- ✅ Pydantic models for validation
- ✅ CRUD operations template
- ✅ Error handling
- ✅ Health check endpoint

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /items` - List all items
- `POST /items` - Create new item
- `GET /items/{item_id}` - Get specific item
- `PUT /items/{item_id}` - Update item
- `DELETE /items/{item_id}` - Delete item

## Customization

### 1. Add Your Models

Edit `models.py`:
```python
class YourModel(BaseModel):
    field1: str
    field2: int
```

### 2. Add Your Endpoints

Edit `app.py`:
```python
@app.post("/your-endpoint")
def your_endpoint(data: YourModel):
    # Your logic here
    pass
```

### 3. Modify Database Schema

Edit `database.py`:
```python
def init_database():
    worker.execute("""
        CREATE TABLE your_table (
            id INTEGER PRIMARY KEY,
            field TEXT
        )
    """)
```

## Development

```bash
# Run with auto-reload
uvicorn app:app --reload

# Run on different port
uvicorn app:app --port 8080

# Run with custom host
uvicorn app:app --host 0.0.0.0
```

## Testing

```python
from fastapi.testclient import TestClient
from app import app

client = TestClient(app)

def test_create_item():
    response = client.post("/items", json={
        "name": "Test Item",
        "value": 123
    })
    assert response.status_code == 201
```

## Deployment

### Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Server

```bash
# Using gunicorn with uvicorn workers
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker
```

## Next Steps

1. Add authentication (JWT, OAuth)
2. Add middleware (CORS, logging)
3. Implement pagination
4. Add database migrations
5. Set up monitoring
6. Add tests
7. Configure CI/CD

## Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [sqlite-worker Repository](https://github.com/roshanlam/sqlite-worker)
- [Pydantic Documentation](https://docs.pydantic.dev/)
