# Streamlit Integration with sqlite-worker

An interactive analytics dashboard demonstrating Streamlit integration with sqlite-worker for real-time data visualization.

## Features

- **Interactive Dashboard**: Real-time data visualization
- **Multiple Chart Types**: Line charts, pie charts, bar charts
- **Data Filtering**: Dynamic filters for date ranges and categories
- **Summary Metrics**: Key performance indicators
- **Data Export**: Download data as CSV
- **Thread-Safe**: sqlite-worker ensures safe concurrent access

## Installation

```bash
pip install streamlit sqlite-worker pandas plotly
```

## Running the Application

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Features Walkthrough

### 1. Key Metrics Dashboard

Displays summary metrics with:
- Current values
- Percentage change from average
- Color-coded indicators

### 2. Interactive Time Series

- Line charts showing trends over time
- Multiple categories displayed together
- Hover for detailed information
- Zoom and pan capabilities

### 3. Category Breakdown

- Pie chart for proportional view
- Bar chart for direct comparison
- Interactive legends

### 4. Detailed Data Table

- Sortable columns
- Filterable by metric
- Formatted values
- Full data export

### 5. Statistical Summary

- Mean, standard deviation, min, max
- Data quality metrics
- Record counts

## Key Benefits

### 1. Caching with `@st.cache_resource`

```python
@st.cache_resource
def get_worker():
    """Worker instance cached across reruns"""
    return SqliteWorker("analytics.db")

worker = get_worker()
```

This ensures the worker is initialized once and reused.

### 2. Thread Safety

Streamlit can have multiple sessions accessing the same data:
```python
# Safe concurrent access
token = worker.execute("SELECT * FROM metrics WHERE date = ?", (date,))
results = worker.fetch_results(token)
```

### 3. Real-time Updates

```python
# Add new data and refresh
if st.button("Add New Data"):
    worker.insert('metrics', new_data)
    st.rerun()  # Refresh dashboard
```

### 4. Interactive Queries

```python
# User-controlled filters
days_back = st.slider("Days to show", 7, 30, 14)
selected_categories = st.multiselect("Categories", categories)

# Build dynamic query
query = f"SELECT * FROM metrics WHERE date >= ? AND category IN ({placeholders})"
```

## Use Cases

### 1. Business Analytics Dashboard

- Sales metrics
- User engagement
- Revenue tracking
- KPI monitoring

### 2. Data Exploration Tool

- Quick data visualization
- Statistical analysis
- Trend identification
- Pattern discovery

### 3. Real-time Monitoring

- System metrics
- Application logs
- Performance monitoring
- Alert dashboards

### 4. Reporting Tool

- Generate reports
- Export data
- Share insights
- Schedule updates

## Advanced Features

### Custom Widgets

```python
# Add custom metric input
with st.form("add_metric"):
    date = st.date_input("Date")
    metric = st.selectbox("Metric", ["Sales", "Users"])
    value = st.number_input("Value")
    
    if st.form_submit_button("Add"):
        worker.insert('metrics', {
            'date': str(date),
            'metric_name': metric,
            'value': value
        })
        st.success("Added!")
```

### Real-time Updates

```python
# Auto-refresh every 5 seconds
import time

placeholder = st.empty()

while True:
    with placeholder.container():
        # Update dashboard
        show_metrics()
    
    time.sleep(5)
```

### Multi-page App

```python
# pages/dashboard.py
# pages/settings.py
# pages/reports.py

# Automatic page navigation
st.sidebar.selectbox("Page", ["Dashboard", "Settings", "Reports"])
```

## Performance Tips

### 1. Use Caching Wisely

```python
@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_metrics(date_range):
    token = worker.execute("SELECT * FROM metrics WHERE date >= ?", (date_range,))
    return worker.fetch_results(token)
```

### 2. Limit Data Volume

```python
# Use LIMIT and pagination
query = "SELECT * FROM metrics ORDER BY date DESC LIMIT 1000"
```

### 3. Optimize Queries

```python
# Create indexes
worker.execute("CREATE INDEX idx_date ON metrics(date)")
worker.execute("CREATE INDEX idx_category ON metrics(category)")
```

### 4. Batch Updates

```python
# Use transactions for bulk inserts
with worker.transaction():
    for record in records:
        worker.insert('metrics', record)
```

## Deployment

### Local Deployment

```bash
streamlit run dashboard.py --server.port 8501
```

### Cloud Deployment

**Streamlit Cloud (Free):**
1. Push to GitHub
2. Connect to Streamlit Cloud
3. Deploy automatically

**Docker:**
```dockerfile
FROM python:3.9
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py"]
```

**Heroku:**
```bash
# Create Procfile
web: streamlit run dashboard.py --server.port=$PORT
```

## Project Structure

```
streamlit/
├── dashboard.py          # Main Streamlit app
├── README.md            # This file
├── requirements.txt     # Dependencies
└── analytics.db         # SQLite database (created automatically)
```

## Configuration

Create `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#3498db"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
```

## Testing

```python
import unittest
from dashboard import get_worker

class TestDashboard(unittest.TestCase):
    def setUp(self):
        self.worker = get_worker()
    
    def test_data_insertion(self):
        self.worker.insert('metrics', {
            'date': '2024-01-01',
            'metric_name': 'Test',
            'value': 100,
            'category': 'Test'
        })
        
        token = self.worker.execute(
            "SELECT * FROM metrics WHERE metric_name = 'Test'"
        )
        results = self.worker.fetch_results(token)
        self.assertEqual(len(results), 1)
```

## Security Considerations

1. **Input Validation**
   ```python
   # Validate user inputs
   if not isinstance(value, (int, float)):
       st.error("Invalid value")
       return
   ```

2. **SQL Injection Prevention**
   ```python
   # Use parameterized queries
   query = "SELECT * FROM metrics WHERE category = ?"
   token = worker.execute(query, (user_input,))
   ```

3. **Authentication** (for production)
   ```python
   import streamlit_authenticator as stauth
   
   authenticator = stauth.Authenticate(...)
   name, authentication_status, username = authenticator.login()
   
   if authentication_status:
       show_dashboard()
   ```

## Troubleshooting

**Issue: "Database is locked"**
```python
# Use WAL mode (already enabled in example)
worker = SqliteWorker(
    "analytics.db",
    execute_init=["PRAGMA journal_mode=WAL;"]
)
```

**Issue: Slow performance**
```python
# Add indexes and use caching
worker.execute("CREATE INDEX idx_date ON metrics(date)")

@st.cache_data(ttl=60)
def load_data():
    # ... query ...
```

**Issue: Memory usage**
```python
# Limit query results
query = "SELECT * FROM metrics LIMIT 10000"
```

## Resources

- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Documentation](https://plotly.com/python/)
- [sqlite-worker Documentation](https://github.com/roshanlam/sqlite-worker)
- [Pandas Documentation](https://pandas.pydata.org/)

## Next Steps

Extend the dashboard by adding:
- User authentication
- Real-time data streaming
- Advanced analytics (ML predictions)
- Custom themes
- Multiple data sources
- Scheduled reports
- Email notifications

## Example Queries

```python
# Top N records
"""SELECT * FROM metrics ORDER BY value DESC LIMIT 10"""

# Date range aggregation
"""
SELECT date, SUM(value) as total
FROM metrics
GROUP BY date
ORDER BY date DESC
"""

# Moving average
"""
SELECT date, metric_name,
       AVG(value) OVER (
           PARTITION BY metric_name 
           ORDER BY date 
           ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
       ) as moving_avg
FROM metrics
"""
```
