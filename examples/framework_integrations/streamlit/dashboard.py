"""
Streamlit Integration with sqlite-worker

A simple data analytics dashboard demonstrating Streamlit integration
with sqlite-worker for interactive data visualization.
"""

import streamlit as st
import pandas as pd
from sqlite_worker import SqliteWorker
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import os

# Page configuration
st.set_page_config(
    page_title="SQLite-Worker Analytics Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize database
@st.cache_resource
def get_worker():
    """Initialize sqlite-worker (cached for performance)"""
    db_path = os.path.join(os.path.dirname(__file__), "analytics.db")
    worker = SqliteWorker(
        db_path,
        execute_init=[
            "PRAGMA journal_mode=WAL;",
            "PRAGMA synchronous=NORMAL;",
        ]
    )
    
    # Initialize schema
    worker.execute("""
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            value REAL NOT NULL,
            category TEXT
        )
    """)
    
    worker.execute("""
        CREATE INDEX IF NOT EXISTS idx_metrics_date 
        ON metrics(date)
    """)
    
    return worker

worker = get_worker()

def generate_sample_data():
    """Generate sample data for demonstration"""
    categories = ['Sales', 'Users', 'Revenue', 'Engagement']
    metrics = ['Daily Active Users', 'Sales Amount', 'Page Views', 'Signups']
    
    # Check if data exists
    token = worker.execute("SELECT COUNT(*) FROM metrics")
    count = worker.fetch_results(token)[0][0]
    
    if count == 0:
        st.info("Generating sample data...")
        with worker.transaction():
            for days_ago in range(30):
                date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
                for metric, category in zip(metrics, categories):
                    value = random.uniform(100, 1000)
                    worker.insert('metrics', {
                        'date': date,
                        'metric_name': metric,
                        'value': value,
                        'category': category
                    })
        st.success("Sample data generated!")
        st.rerun()

# Main app
def main():
    st.title("📊 SQLite-Worker Analytics Dashboard")
    st.markdown("### Real-time data visualization with Streamlit and sqlite-worker")
    
    # Sidebar
    with st.sidebar:
        st.header("Controls")
        
        # Date range selector
        st.subheader("Date Range")
        days_back = st.slider("Days to show", 7, 30, 14)
        
        # Category filter
        st.subheader("Filters")
        token = worker.execute("SELECT DISTINCT category FROM metrics ORDER BY category")
        categories = [row[0] for row in worker.fetch_results(token)]
        selected_categories = st.multiselect(
            "Categories",
            categories,
            default=categories
        )
        
        # Data generation
        st.subheader("Data Management")
        if st.button("Generate Sample Data"):
            generate_sample_data()
        
        if st.button("Clear All Data"):
            worker.execute("DELETE FROM metrics")
            st.success("Data cleared!")
            st.rerun()
    
    # Check if we have data
    token = worker.execute("SELECT COUNT(*) FROM metrics")
    count = worker.fetch_results(token)[0][0]
    
    if count == 0:
        st.warning("No data available. Click 'Generate Sample Data' in the sidebar.")
        return
    
    # Build query with filters
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    
    if selected_categories:
        placeholders = ','.join(['?' for _ in selected_categories])
        query = f"""
            SELECT date, metric_name, value, category
            FROM metrics
            WHERE date >= ? AND category IN ({placeholders})
            ORDER BY date DESC
        """
        params = [start_date] + selected_categories
    else:
        query = """
            SELECT date, metric_name, value, category
            FROM metrics
            WHERE date >= ?
            ORDER BY date DESC
        """
        params = [start_date]
    
    token = worker.execute(query, tuple(params))
    data = worker.fetch_results(token)
    
    if not data:
        st.warning("No data found for selected filters.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(data, columns=['date', 'metric_name', 'value', 'category'])
    df['date'] = pd.to_datetime(df['date'])
    
    # Summary metrics
    st.header("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    for idx, category in enumerate(selected_categories[:4]):
        category_data = df[df['category'] == category]
        if not category_data.empty:
            current_value = category_data['value'].iloc[0]
            avg_value = category_data['value'].mean()
            change = ((current_value - avg_value) / avg_value) * 100
            
            with [col1, col2, col3, col4][idx]:
                st.metric(
                    label=category,
                    value=f"{current_value:.0f}",
                    delta=f"{change:+.1f}% vs avg"
                )
    
    # Time series chart
    st.header("📊 Trends Over Time")
    
    # Group by date and category for plotting
    daily_data = df.groupby(['date', 'category'])['value'].sum().reset_index()
    
    fig = px.line(
        daily_data,
        x='date',
        y='value',
        color='category',
        title='Metrics Trend',
        labels={'value': 'Value', 'date': 'Date', 'category': 'Category'}
    )
    fig.update_layout(hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)
    
    # Category breakdown
    st.header("🥧 Category Breakdown")
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart
        category_totals = df.groupby('category')['value'].sum().reset_index()
        fig_pie = px.pie(
            category_totals,
            values='value',
            names='category',
            title='Total Value by Category'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Bar chart
        fig_bar = px.bar(
            category_totals,
            x='category',
            y='value',
            title='Total Value by Category',
            labels={'value': 'Total Value', 'category': 'Category'}
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # Detailed metrics table
    st.header("📋 Detailed Metrics")
    
    # Add filtering options
    col1, col2 = st.columns(2)
    with col1:
        selected_metric = st.selectbox(
            "Select Metric",
            ["All"] + df['metric_name'].unique().tolist()
        )
    
    with col2:
        sort_by = st.selectbox(
            "Sort By",
            ["Date (Newest)", "Date (Oldest)", "Value (High)", "Value (Low)"]
        )
    
    # Filter data
    display_df = df.copy()
    if selected_metric != "All":
        display_df = display_df[display_df['metric_name'] == selected_metric]
    
    # Sort data
    if sort_by == "Date (Newest)":
        display_df = display_df.sort_values('date', ascending=False)
    elif sort_by == "Date (Oldest)":
        display_df = display_df.sort_values('date', ascending=True)
    elif sort_by == "Value (High)":
        display_df = display_df.sort_values('value', ascending=False)
    else:
        display_df = display_df.sort_values('value', ascending=True)
    
    # Format for display
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df['value'] = display_df['value'].round(2)
    
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Summary statistics
    st.header("📊 Summary Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Overall Statistics")
        stats_df = df.groupby('category')['value'].agg(['mean', 'std', 'min', 'max']).round(2)
        st.dataframe(stats_df)
    
    with col2:
        st.subheader("Data Quality")
        st.write(f"**Total Records:** {len(df)}")
        st.write(f"**Date Range:** {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}")
        st.write(f"**Categories:** {df['category'].nunique()}")
        st.write(f"**Metrics:** {df['metric_name'].nunique()}")
    
    # Raw data export
    st.header("💾 Export Data")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = display_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        if st.button("Show Raw SQL Query"):
            st.code(query, language='sql')
            st.write("Parameters:", params)

if __name__ == "__main__":
    main()
