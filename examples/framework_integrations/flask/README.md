# Flask Integration with sqlite-worker

A simple blog application demonstrating Flask integration with sqlite-worker for thread-safe database operations.

## Features

- Thread-safe database access for Flask's multi-threaded environment
- RESTful API endpoints
- Simple blog with posts and comments
- HTML interface and JSON API
- Proper error handling

## Installation

```bash
pip install flask sqlite-worker
```

## Running the Application

```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

## API Endpoints

### List All Posts
```bash
curl http://localhost:5000/api/posts
```

### Create a Post
```bash
curl -X POST http://localhost:5000/api/posts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Hello World",
    "content": "This is my first post!",
    "author": "Alice"
  }'
```

### Get Specific Post
```bash
curl http://localhost:5000/api/posts/1
```

### Add Comment
```bash
curl -X POST http://localhost:5000/api/posts/1/comments \
  -H "Content-Type: application/json" \
  -d '{
    "author": "Bob",
    "content": "Great post!"
  }'
```

## Key Features

### Thread Safety

Flask runs with multiple threads by default. sqlite-worker ensures thread-safe database access:

```python
# Initialize once
worker = SqliteWorker("blog.db")

# Use from any thread/request safely
@app.route('/api/posts')
def posts():
    token = worker.execute("SELECT * FROM posts")
    results = worker.fetch_results(token)
    return jsonify(results)
```

### Error Handling

```python
@app.route('/api/posts/<int:post_id>')
def get_post(post_id):
    token = worker.select('posts', conditions={'id': post_id})
    posts = worker.fetch_results(token)
    
    if not posts:
        return jsonify({'error': 'Post not found'}), 404
    
    return jsonify(posts[0])
```

### Database Initialization

```python
worker = SqliteWorker(
    DB_PATH,
    execute_init=[
        "PRAGMA journal_mode=WAL;",  # Better concurrency
        "PRAGMA synchronous=NORMAL;",  # Good performance
    ]
)
```

## Project Structure

```
flask/
├── app.py              # Main Flask application
├── README.md           # This file
└── requirements.txt    # Python dependencies
```

## Production Deployment

For production, consider:

1. **Use a production WSGI server:**
   ```bash
   pip install gunicorn
   gunicorn -w 4 app:app
   ```

2. **Enable WAL mode** (already done in this example)

3. **Add authentication** for write operations

4. **Implement rate limiting:**
   ```bash
   pip install flask-limiter
   ```

5. **Add logging:**
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

## Integration with Flask Extensions

### Flask-SQLAlchemy Alternative

sqlite-worker is a lightweight alternative to Flask-SQLAlchemy for simpler use cases:

| Feature | sqlite-worker | Flask-SQLAlchemy |
|---------|---------------|------------------|
| Thread-safe | ✅ Yes | ✅ Yes |
| ORM | Simple CRUD | Full ORM |
| Migrations | Manual | Alembic integration |
| Complexity | Low | Medium-High |
| Learning curve | Minimal | Moderate |

### When to Use sqlite-worker

- Simple CRUD operations
- Prototyping
- Small to medium applications
- When you prefer raw SQL
- Microservices with simple data needs

## Example Use Cases

1. **Simple Blog/CMS**
2. **Task Management System**
3. **API Backend for Mobile Apps**
4. **Data Collection API**
5. **Admin Dashboard**

## Customization

Extend the example by adding:
- User authentication
- Post categories/tags
- Search functionality
- Pagination
- File uploads
- Real-time updates with WebSockets

## Testing

```python
import unittest

class TestBlogAPI(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
    
    def test_create_post(self):
        response = self.client.post('/api/posts', json={
            'title': 'Test',
            'content': 'Test content',
            'author': 'Tester'
        })
        self.assertEqual(response.status_code, 201)
```

## Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [sqlite-worker Documentation](https://github.com/roshanlam/sqlite-worker)
- [REST API Best Practices](https://restfulapi.net/)
