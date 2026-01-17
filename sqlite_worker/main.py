import logging
import sqlite3
import threading
import uuid
import queue
import time
import re
from typing import Dict, List, Tuple, Any, Optional, Callable

LOGGER = logging.getLogger("SqliteWorker")
SILENT_TOKEN_SUFFIX = '-silent'


def _validate_identifier(identifier: str) -> str:
    """
    Validate and sanitize SQL identifiers (table/column names).
    Raises ValueError if identifier is invalid.
    """
    if not identifier or not isinstance(identifier, str):
        raise ValueError("Identifier must be a non-empty string")
    
    # Allow alphanumeric, underscore, but must start with letter or underscore
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(
            f"Invalid identifier '{identifier}': must contain only alphanumeric characters "
            f"and underscores, and start with a letter or underscore"
        )
    
    return identifier


class SqliteWorker:
    """Sqlite thread-safe object."""

    def __init__(self, file_name, max_queue_size=100, execute_init=(), max_count=50, 
                 auto_reconnect=True, max_retries=3, retry_delay=1.0):
        self._file_name = file_name
        self._sql_queue = queue.Queue(maxsize=max_queue_size)
        self._results = {}
        self._tokens = set()
        self._select_events = {}
        self._lock = threading.Lock()
        self._close_event = threading.Event()
        self.execute_init = execute_init
        self.max_count = max_count
        
        # Auto-reconnection settings
        self.auto_reconnect = auto_reconnect
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Transaction support
        self._in_transaction = False
        self._transaction_lock = threading.Lock()
        
        # Observable queries - hooks
        self._query_hooks: Dict[str, List[Callable]] = {}
        self._hooks_lock = threading.Lock()
        
        # Start worker thread after all attributes are set
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self._process_queries()
        except Exception as err:
            LOGGER.critical(
                "Unhandled exception in query processor: %s", err, exc_info=True)
            raise

    def _process_queries(self):
        conn = None
        retry_count = 0
        
        while retry_count <= self.max_retries:
            try:
                conn = sqlite3.connect(self._file_name, check_same_thread=False, 
                                      detect_types=sqlite3.PARSE_DECLTYPES, timeout=30.0)
                cursor = conn.cursor()
                for action in self.execute_init:
                    cursor.execute(action)
                conn.commit()
                
                # Initialize migration table if needed
                self._init_migration_table(cursor, conn)

                count = 0
                while not self._close_event.is_set() or not self._sql_queue.empty():
                    try:
                        token, query, values = self._sql_queue.get(timeout=1)
                    except queue.Empty:
                        continue
                    if query:
                        count += 1
                        self._execute_query_with_retry(conn, cursor, token, query, values)

                    # Only commit if not in transaction
                    if not self._in_transaction and (count >= self.max_count or self._sql_queue.empty()):
                        count = 0
                        conn.commit()
                
                # Successful execution, break retry loop
                if conn:
                    conn.close()
                break
                
            except (sqlite3.OperationalError, sqlite3.DatabaseError) as err:
                LOGGER.error("Database connection error: %s", err)
                if conn:
                    try:
                        conn.close()
                    except:
                        pass
                
                if not self.auto_reconnect or retry_count >= self.max_retries:
                    raise
                
                retry_count += 1
                LOGGER.info("Attempting reconnection %d/%d in %s seconds...", 
                           retry_count, self.max_retries, self.retry_delay)
                time.sleep(self.retry_delay)
    
    def _init_migration_table(self, cursor, conn):
        """Initialize the migrations tracking table."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _migrations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                version TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

    def _execute_query_with_retry(self, conn, cursor, token: str, query, values):
        """Execute query with retry logic."""
        retry_count = 0
        last_error = None
        
        while retry_count <= self.max_retries:
            try:
                self._execute_query(cursor, token, query, values)
                return
            except sqlite3.OperationalError as err:
                last_error = err
                if "locked" in str(err).lower() and self.auto_reconnect:
                    retry_count += 1
                    if retry_count <= self.max_retries:
                        LOGGER.warning("Database locked, retrying %d/%d...", 
                                     retry_count, self.max_retries)
                        time.sleep(self.retry_delay)
                        continue
                raise
        
        # If we exhausted retries, raise the last error
        if last_error:
            raise last_error

    def _execute_query(self, cursor, token: str, query, values):
        try:
            cursor.execute(query, values)
            
            # Trigger hooks for this query
            self._trigger_hooks(query, values)
            
            if not token.endswith(SILENT_TOKEN_SUFFIX):
                with self._lock:
                    self._results[token] = cursor.fetchall()
        except sqlite3.Error as err:
            LOGGER.error("Query error: %s: %s: %s", query, values, err)
            self._handle_query_error(token, err)
        self._notify_query_done(token)

    def _is_select_query(self, query):
        return query.lower().lstrip().startswith("select")

    def _notify_query_begin(self, token):
        self._select_events.setdefault(token, threading.Event())

    def _notify_query_done(self, token):
        event = self._select_events.get(token)
        if event:
            event.set()

    def _handle_query_error(self, token, err):
        with self._lock:
            self._results[token] = err

    def close(self):
        self._close_event.set()
        self._sql_queue.put((None, None, None), timeout=5)
        self._thread.join()

    def execute(self, query, values=None, always_return_token=False):
        if self._close_event.is_set():
            raise RuntimeError("Worker is closed")

        should_return_token = (
            always_return_token or
            self._is_select_query(query)
        )

        token = uuid.uuid4().hex
        if not should_return_token:
            token += SILENT_TOKEN_SUFFIX

        self._sql_queue.put((token, query, values or []), timeout=5)
        self._notify_query_begin(token)

        if should_return_token:
            return token
        return None


    def execute_and_fetch(self, query, values=None, always_synchronous=True):
        return self.fetch_results(self.execute(query, values, always_return_token=always_synchronous))

    def fetch_results(self, token):
        if token is None:
            return
        with self._lock:
            event = self._select_events.get(token)
        if event is None:
            return
        event.wait()
        with self._lock:
            return self._results.pop(token, None)

    @property
    def queue_size(self):
        return self._sql_queue.qsize()
    
    # ============= Transaction Support =============
    
    def begin_transaction(self):
        """Begin a manual transaction."""
        with self._transaction_lock:
            if self._in_transaction:
                raise RuntimeError("Transaction already in progress")
            self._in_transaction = True
            self.execute("BEGIN TRANSACTION")
    
    def commit_transaction(self):
        """Commit the current transaction."""
        with self._transaction_lock:
            if not self._in_transaction:
                raise RuntimeError("No transaction in progress")
            self.execute("COMMIT")
            self._in_transaction = False
    
    def rollback_transaction(self):
        """Rollback the current transaction."""
        with self._transaction_lock:
            if not self._in_transaction:
                raise RuntimeError("No transaction in progress")
            self.execute("ROLLBACK")
            self._in_transaction = False
    
    def transaction(self):
        """Context manager for transactions."""
        return TransactionContext(self)
    
    # ============= ORM-like CRUD Methods =============
    
    def insert(self, table_name: str, data: Dict[str, Any]) -> Optional[str]:
        """
        Insert a row into a table.
        
        Args:
            table_name: Name of the table
            data: Dictionary of column names to values
            
        Returns:
            Token for retrieving results
        """
        if not data:
            raise ValueError("Data dictionary cannot be empty")
        
        # Validate table and column names
        table_name = _validate_identifier(table_name)
        for col in data.keys():
            _validate_identifier(col)
        
        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        values = tuple(data.values())
        
        return self.execute(query, values, always_return_token=True)
    
    def update(self, table_name: str, data: Dict[str, Any], 
               conditions: Dict[str, Any]) -> Optional[str]:
        """
        Update rows in a table.
        
        Args:
            table_name: Name of the table
            data: Dictionary of column names to new values
            conditions: Dictionary of column names to condition values (WHERE clause)
            
        Returns:
            Token for retrieving results
        """
        if not data:
            raise ValueError("Data dictionary cannot be empty")
        if not conditions:
            raise ValueError("Conditions dictionary cannot be empty (use with caution)")
        
        # Validate table and column names
        table_name = _validate_identifier(table_name)
        for col in data.keys():
            _validate_identifier(col)
        for col in conditions.keys():
            _validate_identifier(col)
        
        set_clause = ", ".join([f"{col} = ?" for col in data.keys()])
        where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"
        values = tuple(list(data.values()) + list(conditions.values()))
        
        return self.execute(query, values, always_return_token=True)
    
    def delete(self, table_name: str, conditions: Dict[str, Any]) -> Optional[str]:
        """
        Delete rows from a table.
        
        Args:
            table_name: Name of the table
            conditions: Dictionary of column names to condition values (WHERE clause)
            
        Returns:
            Token for retrieving results
        """
        if not conditions:
            raise ValueError("Conditions dictionary cannot be empty (use with caution)")
        
        # Validate table and column names
        table_name = _validate_identifier(table_name)
        for col in conditions.keys():
            _validate_identifier(col)
        
        where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
        query = f"DELETE FROM {table_name} WHERE {where_clause}"
        values = tuple(conditions.values())
        
        return self.execute(query, values, always_return_token=True)
    
    def select(self, table_name: str, columns: List[str] = None, 
               conditions: Dict[str, Any] = None, order_by: str = None, 
               limit: int = None) -> str:
        """
        Select rows from a table.
        
        Args:
            table_name: Name of the table
            columns: List of column names to select (defaults to *)
            conditions: Optional dictionary of column names to condition values
            order_by: Optional ORDER BY clause (e.g., 'column_name ASC')
            limit: Optional LIMIT value (must be a positive integer)
            
        Returns:
            Token for retrieving results
        """
        # Validate table name
        table_name = _validate_identifier(table_name)
        
        # Validate columns if provided
        if columns:
            validated_cols = [_validate_identifier(col) for col in columns]
            cols = ", ".join(validated_cols)
        else:
            cols = "*"
        
        query = f"SELECT {cols} FROM {table_name}"
        values = []
        
        if conditions:
            # Validate condition column names
            for col in conditions.keys():
                _validate_identifier(col)
            where_clause = " AND ".join([f"{col} = ?" for col in conditions.keys()])
            query += f" WHERE {where_clause}"
            values = list(conditions.values())
        
        if order_by:
            # Validate order_by - allow column names with ASC/DESC
            order_parts = order_by.strip().split()
            if len(order_parts) not in [1, 2]:
                raise ValueError("order_by must be 'column' or 'column ASC/DESC'")
            _validate_identifier(order_parts[0])
            if len(order_parts) == 2 and order_parts[1].upper() not in ['ASC', 'DESC']:
                raise ValueError("order_by direction must be ASC or DESC")
            query += f" ORDER BY {order_by}"
        
        if limit is not None:
            if not isinstance(limit, int) or limit < 0:
                raise ValueError("limit must be a non-negative integer")
            query += f" LIMIT {limit}"
        
        return self.execute(query, tuple(values))
    
    # ============= Observable Queries (Hooks) =============
    
    def register_hook(self, hook_name: str, callback: Callable):
        """
        Register a callback hook for database events.
        
        Args:
            hook_name: Name of the hook (e.g., 'before_query', 'after_query', 'on_insert')
            callback: Callable that will be invoked when the hook is triggered
        """
        with self._hooks_lock:
            if hook_name not in self._query_hooks:
                self._query_hooks[hook_name] = []
            self._query_hooks[hook_name].append(callback)
    
    def unregister_hook(self, hook_name: str, callback: Callable = None):
        """
        Unregister a callback hook.
        
        Args:
            hook_name: Name of the hook
            callback: Specific callback to remove (if None, removes all callbacks for this hook)
        """
        with self._hooks_lock:
            if hook_name in self._query_hooks:
                if callback is None:
                    del self._query_hooks[hook_name]
                else:
                    self._query_hooks[hook_name] = [
                        cb for cb in self._query_hooks[hook_name] if cb != callback
                    ]
    
    def _trigger_hooks(self, query: str, values: tuple):
        """Trigger registered hooks for a query."""
        with self._hooks_lock:
            hooks_to_call = list(self._query_hooks.get('on_query', []))
            
            # Trigger specific hooks based on query type
            query_lower = query.lower().lstrip()
            if query_lower.startswith('insert'):
                hooks_to_call.extend(self._query_hooks.get('on_insert', []))
            elif query_lower.startswith('update'):
                hooks_to_call.extend(self._query_hooks.get('on_update', []))
            elif query_lower.startswith('delete'):
                hooks_to_call.extend(self._query_hooks.get('on_delete', []))
            elif query_lower.startswith('select'):
                hooks_to_call.extend(self._query_hooks.get('on_select', []))
        
        # Execute hooks outside the lock to avoid deadlocks
        for hook in hooks_to_call:
            try:
                hook(query, values)
            except Exception as err:
                LOGGER.error("Hook execution error: %s", err, exc_info=True)
    
    # ============= Database Migrations =============
    
    def apply_migration(self, version: str, name: str, up_sql: str) -> bool:
        """
        Apply a database migration.
        
        Args:
            version: Version identifier (e.g., '001', '002')
            name: Human-readable migration name
            up_sql: SQL to apply for the migration. Multiple statements should be
                   separated by semicolons. Note: This simple split won't handle
                   semicolons in strings/comments - for complex migrations, pass
                   single statements or use executescript manually.
            
        Returns:
            True if migration was applied, False if already applied
        """
        # Check if migration already applied
        token = self.execute(
            "SELECT version FROM _migrations WHERE version = ?", 
            (version,)
        )
        results = self.fetch_results(token)
        
        if results and len(results) > 0:
            LOGGER.info("Migration %s (%s) already applied", version, name)
            return False
        
        # Apply migration in a transaction
        try:
            self.begin_transaction()
            
            # Execute migration SQL - split on semicolons
            # NOTE: This is a simple split and doesn't handle semicolons in strings/comments
            # For complex migrations, consider passing single statements or use raw SQL
            statements = [s.strip() for s in up_sql.split(';') if s.strip()]
            
            for statement in statements:
                token = self.execute(statement)
                # Wait for statement to complete
                if token:
                    self.fetch_results(token)
            
            # Record migration
            token = self.execute(
                "INSERT INTO _migrations (version, name) VALUES (?, ?)",
                (version, name)
            )
            if token:
                self.fetch_results(token)
            
            self.commit_transaction()
            LOGGER.info("Migration %s (%s) applied successfully", version, name)
            return True
            
        except Exception as err:
            LOGGER.error("Migration %s (%s) failed: %s", version, name, err)
            self.rollback_transaction()
            raise
    
    def rollback_migration(self, version: str, down_sql: str) -> bool:
        """
        Rollback a database migration.
        
        Args:
            version: Version identifier to rollback
            down_sql: SQL to rollback the migration. Multiple statements should be
                     separated by semicolons. Note: This simple split won't handle
                     semicolons in strings/comments - for complex migrations, pass
                     single statements or use executescript manually.
            
        Returns:
            True if migration was rolled back, False if not found
        """
        # Check if migration exists
        token = self.execute(
            "SELECT version FROM _migrations WHERE version = ?",
            (version,)
        )
        results = self.fetch_results(token)
        
        if not results or len(results) == 0:
            LOGGER.info("Migration %s not found or already rolled back", version)
            return False
        
        # Rollback migration in a transaction
        try:
            self.begin_transaction()
            
            # Execute rollback SQL - split on semicolons
            # NOTE: This is a simple split and doesn't handle semicolons in strings/comments
            statements = [s.strip() for s in down_sql.split(';') if s.strip()]
            
            for statement in statements:
                token = self.execute(statement)
                # Wait for statement to complete
                if token:
                    self.fetch_results(token)
            
            # Remove migration record
            token = self.execute(
                "DELETE FROM _migrations WHERE version = ?",
                (version,)
            )
            if token:
                self.fetch_results(token)
            
            self.commit_transaction()
            LOGGER.info("Migration %s rolled back successfully", version)
            return True
            
        except Exception as err:
            LOGGER.error("Migration rollback %s failed: %s", version, err)
            self.rollback_transaction()
            raise
    
    def get_applied_migrations(self) -> List[Tuple[str, str, str]]:
        """
        Get list of applied migrations.
        
        Returns:
            List of tuples (version, name, applied_at)
        """
        token = self.execute(
            "SELECT version, name, applied_at FROM _migrations ORDER BY id"
        )
        results = self.fetch_results(token)
        return results if results else []


class TransactionContext:
    """Context manager for database transactions."""
    
    def __init__(self, worker: SqliteWorker):
        self.worker = worker
    
    def __enter__(self):
        self.worker.begin_transaction()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.worker.rollback_transaction()
            return False
        else:
            self.worker.commit_transaction()
            return True
