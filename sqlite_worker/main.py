import logging
import sqlite3
import threading
import uuid
import queue

LOGGER = logging.getLogger("SqliteWorker")


class SqliteWorker:
    """Sqlite thread-safe object."""

    def __init__(self, file_name, max_queue_size=100, execute_init=(), max_count=50):
        self._file_name = file_name
        self._sql_queue = queue.Queue(maxsize=max_queue_size)
        self._results = {}
        self._select_events = {}
        self._lock = threading.Lock()
        self._close_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self.execute_init = execute_init
        self.max_count = max_count

    def _run(self):
        try:
            self._process_queries()
        except Exception as err:
            LOGGER.critical(
                "Unhandled exception in query processor: %s", err, exc_info=True)
            raise

    def _process_queries(self):
        with sqlite3.connect(self._file_name, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()
            for action in self.execute_init:
                cursor.execute(action)
            conn.commit()

            count = 0
            while not self._close_event.is_set() or not self._sql_queue.empty():
                try:
                    token, query, values = self._sql_queue.get(timeout=1)
                except queue.Empty:
                    continue
                if query:
                    count += 1
                    self._execute_query(cursor, token, query, values)

                if count >= self.max_count or self._sql_queue.empty():
                    count = 0
                    conn.commit()

    def _execute_query(self, cursor, token, query, values):
        try:
            cursor.execute(query, values)
            if query.lower().startswith("select"):
                with self._lock:
                    self._results[token] = cursor.fetchall()
            self._notify_query_done(token)
        except sqlite3.Error as err:
            LOGGER.error("Query error: %s: %s: %s", query, values, err)
            self._handle_query_error(token, err)

    def _notify_query_done(self, token):
        self._select_events.setdefault(token, threading.Event()).set()

    def _handle_query_error(self, token, err):
        with self._lock:
            self._results[token] = err
        self._notify_query_done(token)

    def close(self):
        self._close_event.set()
        self._sql_queue.put((None, None, None), timeout=5)
        self._thread.join()

    def execute(self, query, values=None):
        if self._close_event.is_set():
            raise RuntimeError("Worker is closed")
        token = str(uuid.uuid4())
        self._sql_queue.put((token, query, values or []), timeout=5)
        return token if query.lower().startswith("select") else None

    def fetch_results(self, token):
        if token:
            with self._lock:
                event = self._select_events.get(token)
            if event:
                event.wait()
                with self._lock:
                    return self._results.pop(token, None)
        return None

    @property
    def queue_size(self):
        return self._sql_queue.qsize()
