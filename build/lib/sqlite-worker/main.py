import logging
import sqlite3
import threading
import uuid
import queue

LOGGER = logging.getLogger("SqliteWorker")


class SqliteWorker:
    """Sqlite thread-safe object."""

    def __init__(self, file_name, max_queue_size=100):
        self._file_name = file_name
        self._sql_queue = queue.Queue(maxsize=max_queue_size)
        self._results = {}
        self._select_events = {}
        self._close_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name=__name__, daemon=True)
        self._thread.start()

    def _run(self):
        try:
            self._process_queries()
        except Exception as e:
            LOGGER.critical(
                "Unhandled exception in query processor: %s", e, exc_info=True)
            raise

    def _process_queries(self):
        with sqlite3.connect(self._file_name, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.cursor()
            while not self._close_event.is_set() or not self._sql_queue.empty():
                try:
                    token, query, values = self._sql_queue.get(timeout=1)
                except queue.Empty:
                    continue

                if query:
                    self._execute_query(cursor, token, query, values)

                if self._sql_queue.empty():
                    conn.commit()

    def _execute_query(self, cursor, token, query, values):
        try:
            cursor.execute(query, values)
            if query.lower().startswith("select"):
                self._results[token] = cursor.fetchall()
                self._notify_query_done(token)
        except sqlite3.Error as err:
            LOGGER.error("Query error: %s: %s: %s", query, values, err)
            self._handle_query_error(token, err)

    def _notify_query_done(self, token):
        self._select_events.setdefault(token, threading.Event()).set()

    def _handle_query_error(self, token, err):
        self._results[token] = err
        self._notify_query_done(token)

    def close(self):
        self._close_event.set()
        self._sql_queue.put(("", "", ""), timeout=5)
        self._thread.join()

    def execute(self, query, values=None):
        if self._close_event.is_set():
            raise RuntimeError("Worker is closed")

        token = str(uuid.uuid4())
        self._sql_queue.put((token, query, values or []), timeout=5)
        if query.lower().startswith("select"):
            return self._fetch_query_results(token)

    def _fetch_query_results(self, token):
        event = self._select_events.setdefault(token, threading.Event())
        event.wait()
        return self._results.pop(token, None)

    @property
    def queue_size(self):
        return self._sql_queue.qsize()
