# Jupyter Notebook Template for Data Analysis

A ready-to-use Jupyter notebook template demonstrating data analysis with sqlite-worker.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start Jupyter
jupyter notebook data_analysis.ipynb
```

## Features

- ✅ Data loading from SQLite using sqlite-worker
- ✅ Pandas integration for data manipulation
- ✅ Visualization with Matplotlib and Seaborn
- ✅ Time series analysis
- ✅ Statistical summaries
- ✅ Export results to CSV

## What's Included

The notebook covers:

1. **Setup**: Database connection and configuration
2. **Data Generation**: Sample dataset creation
3. **Data Loading**: Converting SQL results to Pandas DataFrames
4. **Analysis**: Statistical summaries and aggregations
5. **Visualization**: Charts and graphs
6. **Export**: Save results to CSV

## Use Cases

- Sales analysis
- Performance metrics
- Customer behavior analysis
- Trend identification
- Report generation

## Customization

### Add Your Own Data

Replace the sample data generation with your data source:

```python
# Load from CSV
df = pd.read_csv('your_data.csv')

# Insert into database
with worker.transaction():
    for _, row in df.iterrows():
        worker.insert('your_table', row.to_dict())
```

### Custom Queries

Add your own SQL queries:

```python
token = worker.execute("""
    SELECT column1, COUNT(*) as count
    FROM your_table
    WHERE condition = ?
    GROUP BY column1
""", (value,))
results = worker.fetch_results(token)
```

### Custom Visualizations

Create your own charts:

```python
import plotly.express as px

fig = px.scatter(df, x='column1', y='column2', color='category')
fig.show()
```

## Example Output

The notebook generates:
- Bar charts of category performance
- Time series plots
- Product performance tables
- Statistical summaries
- CSV export files

## Dependencies

- `jupyter` - Notebook interface
- `sqlite-worker` - Database operations
- `pandas` - Data manipulation
- `matplotlib` - Plotting
- `seaborn` - Statistical visualization
- `numpy` - Numerical operations

## Tips

1. **Run cells in order** - Each cell depends on previous ones
2. **Save frequently** - Use Ctrl+S to save
3. **Restart kernel** - If things go wrong, restart kernel and run all
4. **Export as HTML** - Share results: File → Download as → HTML

## Advanced Usage

### Connect to Existing Database

```python
worker = SqliteWorker('path/to/your/database.db')
```

### Use with Real-time Data

```python
# Periodic data refresh
import time

while True:
    # Update data
    token = worker.execute("SELECT * FROM live_data")
    df = pd.DataFrame(worker.fetch_results(token))
    
    # Update visualization
    display(df.tail())
    
    time.sleep(60)  # Update every minute
```

### Export to Excel

```python
df.to_excel('analysis_results.xlsx', index=False, sheet_name='Sales')
```

## Resources

- [Jupyter Documentation](https://jupyter.org/documentation)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
- [Matplotlib Documentation](https://matplotlib.org/)
- [sqlite-worker Repository](https://github.com/roshanlam/sqlite-worker)
