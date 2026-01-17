"""
Flask Integration with sqlite-worker

A simple blog application demonstrating Flask integration with sqlite-worker
for thread-safe database operations.
"""

from flask import Flask, request, jsonify, render_template_string
from sqlite_worker import SqliteWorker
from datetime import datetime
import os

app = Flask(__name__)

# Initialize database
DB_PATH = os.path.join(os.path.dirname(__file__), "blog.db")
worker = SqliteWorker(
    DB_PATH,
    execute_init=[
        "PRAGMA journal_mode=WAL;",
        "PRAGMA synchronous=NORMAL;",
    ]
)

# Initialize schema
worker.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        author TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

worker.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER NOT NULL,
        author TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (post_id) REFERENCES posts(id)
    )
""")

# HTML template for the blog
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>SQLite-Worker Flask Blog</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
        h1 { color: #333; }
        .post { background: #f5f5f5; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .post h2 { margin-top: 0; color: #2c3e50; }
        .post-meta { color: #7f8c8d; font-size: 0.9em; }
        .comment { background: #fff; padding: 10px; margin: 10px 0; border-left: 3px solid #3498db; }
        form { background: #ecf0f1; padding: 20px; margin: 20px 0; border-radius: 5px; }
        input, textarea { width: 100%; padding: 10px; margin: 5px 0; box-sizing: border-box; }
        button { background: #3498db; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        button:hover { background: #2980b9; }
        .api-docs { background: #fff3cd; padding: 15px; margin: 20px 0; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>🚀 SQLite-Worker Flask Blog</h1>
    
    <div class="api-docs">
        <h3>API Endpoints</h3>
        <ul>
            <li><strong>GET /api/posts</strong> - List all posts</li>
            <li><strong>POST /api/posts</strong> - Create new post</li>
            <li><strong>GET /api/posts/:id</strong> - Get specific post</li>
            <li><strong>POST /api/posts/:id/comments</strong> - Add comment</li>
        </ul>
    </div>
    
    <h2>Create New Post</h2>
    <form method="POST" action="/api/posts">
        <input type="text" name="title" placeholder="Post Title" required>
        <input type="text" name="author" placeholder="Author Name" required>
        <textarea name="content" placeholder="Post Content" rows="5" required></textarea>
        <button type="submit">Create Post</button>
    </form>
    
    <h2>Recent Posts</h2>
    <div id="posts">
        {% for post in posts %}
        <div class="post">
            <h2>{{ post.title }}</h2>
            <div class="post-meta">By {{ post.author }} on {{ post.created_at }}</div>
            <p>{{ post.content }}</p>
            <p><a href="/posts/{{ post.id }}">View Comments ({{ post.comment_count }})</a></p>
        </div>
        {% endfor %}
    </div>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    """Display blog homepage"""
    token = worker.execute("""
        SELECT p.id, p.title, p.content, p.author, p.created_at,
               COUNT(c.id) as comment_count
        FROM posts p
        LEFT JOIN comments c ON p.id = c.post_id
        GROUP BY p.id
        ORDER BY p.created_at DESC
        LIMIT 10
    """)
    posts_data = worker.fetch_results(token)
    
    posts = []
    for post in posts_data:
        posts.append({
            'id': post[0],
            'title': post[1],
            'content': post[2],
            'author': post[3],
            'created_at': post[4],
            'comment_count': post[5]
        })
    
    return render_template_string(HTML_TEMPLATE, posts=posts)


@app.route('/api/posts', methods=['GET', 'POST'])
def posts():
    """List all posts or create a new post"""
    if request.method == 'POST':
        # Create new post
        data = request.form or request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        required_fields = ['title', 'content', 'author']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        token = worker.insert('posts', {
            'title': data['title'],
            'content': data['content'],
            'author': data['author']
        })
        worker.fetch_results(token)
        
        # Redirect to homepage if form submission
        if request.form:
            from flask import redirect
            return redirect('/')
        
        return jsonify({'message': 'Post created successfully'}), 201
    
    else:
        # List all posts
        token = worker.select('posts', order_by='created_at DESC')
        posts_data = worker.fetch_results(token)
        
        posts = []
        for post in posts_data:
            posts.append({
                'id': post[0],
                'title': post[1],
                'content': post[2],
                'author': post[3],
                'created_at': post[4]
            })
        
        return jsonify(posts)


@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get a specific post with its comments"""
    # Get post
    token = worker.select('posts', conditions={'id': post_id})
    posts = worker.fetch_results(token)
    
    if not posts:
        return jsonify({'error': 'Post not found'}), 404
    
    post = posts[0]
    
    # Get comments
    token = worker.select(
        'comments',
        conditions={'post_id': post_id},
        order_by='created_at ASC'
    )
    comments_data = worker.fetch_results(token)
    
    comments = []
    for comment in comments_data:
        comments.append({
            'id': comment[0],
            'author': comment[2],
            'content': comment[3],
            'created_at': comment[4]
        })
    
    return jsonify({
        'id': post[0],
        'title': post[1],
        'content': post[2],
        'author': post[3],
        'created_at': post[4],
        'comments': comments
    })


@app.route('/api/posts/<int:post_id>/comments', methods=['POST'])
def add_comment(post_id):
    """Add a comment to a post"""
    data = request.get_json()
    
    if not data or 'content' not in data or 'author' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Check if post exists
    token = worker.select('posts', conditions={'id': post_id})
    posts = worker.fetch_results(token)
    
    if not posts:
        return jsonify({'error': 'Post not found'}), 404
    
    # Add comment
    token = worker.insert('comments', {
        'post_id': post_id,
        'author': data['author'],
        'content': data['content']
    })
    worker.fetch_results(token)
    
    return jsonify({'message': 'Comment added successfully'}), 201


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'database': 'connected'})


def cleanup():
    """Cleanup function"""
    worker.close()


if __name__ == '__main__':
    import atexit
    atexit.register(cleanup)
    
    print("=" * 60)
    print("Flask Blog with sqlite-worker")
    print("=" * 60)
    print("\nStarting server at http://localhost:5000")
    print("\nAPI Endpoints:")
    print("  GET  /api/posts          - List all posts")
    print("  POST /api/posts          - Create new post")
    print("  GET  /api/posts/:id      - Get specific post")
    print("  POST /api/posts/:id/comments - Add comment")
    print("\n" + "=" * 60)
    
    # Use debug=False for production, set via environment variable for development
    import os
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, port=5000)
