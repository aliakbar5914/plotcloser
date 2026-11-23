"""One shared pool of database connections for the whole app."""
from pathlib import Path

from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app import config

# These settings are what LangGraph's Postgres checkpointer/store expect,
# so the same pool can be shared by our own queries and by LangGraph memory.
pool = ConnectionPool(
    conninfo=config.DATABASE_URL,
    min_size=1,
    max_size=5,
    kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    # Neon sleeps when idle and closes connections; this re-checks a
    # connection before giving it to us, so we never use a dead one.
    check=ConnectionPool.check_connection,
    open=False,
)


def open_pool() -> None:
    pool.open(wait=True, timeout=60)  # Neon can take a few seconds to wake up


def close_pool() -> None:
    pool.close()


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchall()


def fetch_one(sql: str, params: tuple = ()) -> dict | None:
    with pool.connection() as conn:
        return conn.execute(sql, params).fetchone()


def execute(sql: str, params: tuple = ()) -> None:
    with pool.connection() as conn:
        conn.execute(sql, params)


def create_tables() -> None:
    schema_sql = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
    with pool.connection() as conn:
        # prepare=False: a file with many SQL commands can't be a prepared statement
        conn.execute(schema_sql, prepare=False)
