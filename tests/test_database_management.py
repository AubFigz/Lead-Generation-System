import pytest
from sqlalchemy import create_engine, text
from datetime import datetime, timedelta
from database_management import cleanup_table


@pytest.fixture
def db_conn():
    """In-memory SQLite connection with a test_table, for isolated testing."""
    engine = create_engine("sqlite:///:memory:")
    conn = engine.connect()
    conn.execute(text(
        "CREATE TABLE test_table (id INTEGER PRIMARY KEY, created_at DATETIME NOT NULL)"
    ))
    yield conn
    conn.close()
    engine.dispose()


def _insert(conn, rows):
    conn.execute(text("INSERT INTO test_table (id, created_at) VALUES (:id, :created_at)"), rows)


def test_cleanup_table(db_conn):
    _insert(db_conn, [
        {"id": 1, "created_at": datetime.now() - timedelta(days=20)},   # inside retention -> kept
        {"id": 2, "created_at": datetime.now() - timedelta(days=40)},   # older -> deleted
    ])
    cleanup_table("test_table", retention_days=30, connection=db_conn)
    count = db_conn.execute(text("SELECT COUNT(*) FROM test_table")).scalar()
    assert count == 1, "Records older than the retention window should be deleted"
    remaining = db_conn.execute(text("SELECT id FROM test_table")).scalar()
    assert remaining == 1, "The 20-day-old record should remain"


def test_cleanup_table_empty_table(db_conn):
    cleanup_table("test_table", retention_days=30, connection=db_conn)
    count = db_conn.execute(text("SELECT COUNT(*) FROM test_table")).scalar()
    assert count == 0, "An empty table should stay empty without error"


def test_cleanup_table_no_matching_records(db_conn):
    _insert(db_conn, [{"id": 1, "created_at": datetime.now()}])
    cleanup_table("test_table", retention_days=30, connection=db_conn)
    count = db_conn.execute(text("SELECT COUNT(*) FROM test_table")).scalar()
    assert count == 1, "No records should be deleted when none are older than the window"
